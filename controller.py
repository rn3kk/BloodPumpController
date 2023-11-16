import datetime
import os

import numpy as np
from sklearn.linear_model import LinearRegression
import threading
import time
from threading import Thread
import serial.tools.list_ports
import serial.serialutil

import model


class Controller(Thread):

    ADC = b'adc'
    MIN = b'min'
    MAX = b'max'
    RATE = b'rte'
    MAIN_NUM = b'1'
    GET = b'get'
    PRE = b'pre'
    START = b'sta'
    STOP = b'sto'

    def __init__(self, p):
        print('Controller')
        Thread.__init__(self)
        self.__data_capturing = False
        self.__max_capture_time = 0
        self.__terminate = False
        self.__mutex = threading.Lock()
        self.__serial_port = list()
        self.__A1 = 0
        self.__A2 = 0
        self.__A3 = 0
        self.__B1 = 0
        self.__B2 = 0
        self.__B3 = 0
        self.__filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.load_calib_table()
        self.__port_path = p
        self.__starting_time = datetime.datetime.now()
        self.__start_measurement_timestamp = 0
        self.__work_time = None
        self.__f = None
        self.__f1 = None
        self.__f2 = None
        self.__f3 = None
        self.__init_ok = False

    def __del__(self):
        print('~Controller')

    def __board_is_found(self):
        if self.__init_ok is False:
            self.__init_ok = True
            model.board_status = 'Main board found'

    def __write_data(self, det_num, t, local_Time, v):
        s = str(det_num)+ ';'+str(t)+';' + str(local_Time) + ';' + str(v)+';\n'
        if self.__f and self.__f.closed == False:
            self.__f.write(s)

        if det_num == 1:
            self.__f1.write(s)
        elif det_num == 2:
            self.__f2.write(s)
        elif det_num == 3:
            self.__f3.write(s)

    def run(self):
        port_list = list(serial.tools.list_ports.comports())
        for i in port_list:
            try:
                print(i.device, self.__port_path)
                if i.device not in self.__port_path:
                    continue
                print('Start open', i.device)
                serial_port = serial.Serial(port=i.device, baudrate=9600, parity=serial.PARITY_NONE,
                                            timeout=0.5, bytesize=serial.EIGHTBITS,
                                            stopbits=serial.STOPBITS_TWO)
                self.__serial_port.append(serial_port)

            except serial.serialutil.SerialException as e:
                print('!!!!!!!!!!Cant open port', i)
                continue

        model.board_status = '*******'

        count = 0

        while not self.__terminate:
            try:
                if self.__max_capture_time > 0:
                    if int((datetime.datetime.now().timestamp() - self.__starting_time.timestamp())) > self.__max_capture_time:
                        self.stop_captuging_data()

                time.sleep(0.001)
                if self.__init_ok is False:
                    for sp in self.__serial_port:
                        sp.write(self.GET + b'\n')
                        sp.flush()
                        print('Send init request', sp, self.GET + b'\n', datetime.datetime.now().timestamp())
                    time.sleep(3)
                for sp in self.__serial_port:
                    if sp.isOpen() and sp.in_waiting > 0:
                        self.__mutex.acquire()
                        d = sp.readline()
                        self.__mutex.release()
                        cmd = d[:3]
                        # print('****', d)
                        if cmd == self.MIN and d[3:4] == self.MAIN_NUM:
                            self.__board_is_found()
                            value = d[4:].replace(b'\n', b'').decode()
                            model.min_value = value
                            model.changed = True
                        elif cmd == self.MAX and d[3:4] == self.MAIN_NUM:
                            self.__board_is_found()
                            value = d[4:].replace(b'\n', b'').decode()
                            model.max_value = value
                            model.changed = True
                        elif cmd == self.RATE and d[3:4] == self.MAIN_NUM:
                            self.__board_is_found()
                            value = d[4:].replace(b'\n', b'').decode()
                            model.rate = value
                            model.changed = True
                        elif cmd == self.PRE:
                            try:
                                if not self.data_is_capturing:
                                    continue
                                d = d.replace(b'\n', b'')
                                v = d[3:].split(b' ')
                                # print(d, v)
                                if(v[0] == b'ERR'):
                                    print(d)
                                    continue
                                num = int(v[0])
                                t = int(v[1])
                                v = float(v[2])
                                if self.__start_measurement_timestamp == 0:
                                    self.__start_measurement_timestamp = round(time.time() * 1000)
                                if num == 1:
                                    m1Time = round(time.time() * 1000) - self.__start_measurement_timestamp
                                    m1 = self.correction_det1(v)
                                    model.graph_y1 = np.append(model.graph_y1, m1)
                                    if model.graph_y1.size >= model.MAX_GRAPH_COUNT:
                                        model.graph_y1 = model.graph_y1[
                                                         model.graph_y1.size - model.MAX_GRAPH_COUNT:]
                                    m = np.amax(model.graph_y1)
                                    m = int(m * 100) / 100
                                    n = np.amin(model.graph_y1)
                                    n = int(n * 100) / 100
                                    count += 1
                                    s = f'Pot1 Curr={m1} Max={m} Min={n}'
                                    model.potok1 = s
                                    self.__write_data(1,t, m1Time, m1)
                                elif num == 2:
                                    m2Time = round(time.time() * 1000)  - self.__start_measurement_timestamp
                                    m2 = self.correction_det2(v)
                                    model.graph_y2 = np.append(model.graph_y2, m2)
                                    if model.graph_y2.size >= model.MAX_GRAPH_COUNT:
                                        model.graph_y2 = model.graph_y2[
                                                         model.graph_y2.size - model.MAX_GRAPH_COUNT:]
                                    m = np.amax(model.graph_y2)
                                    m = int(m * 100) / 100
                                    n = np.amin(model.graph_y2)
                                    n = int(n * 100) / 100
                                    count += 1
                                    s = f'Pot2 Curr={m2} Max={m} Min={n}'
                                    model.potok2 = s
                                    self.__write_data(2, t, m2Time, m2)
                                elif num == 3:
                                    m3Time = round(time.time() * 1000)  - self.__start_measurement_timestamp
                                    m3 = self.correction_det3(v)
                                    model.graph_y3 = np.append(model.graph_y3, m3)
                                    if model.graph_y3.size >= model.MAX_GRAPH_COUNT:
                                        model.graph_y3 = model.graph_y3[
                                                         model.graph_y3.size - model.MAX_GRAPH_COUNT:]
                                    m = np.amax(model.graph_y3)
                                    m = int(m * 100) / 100
                                    n = np.amin(model.graph_y3)
                                    n = int(n * 100) / 100
                                    count += 1
                                    s = f'Pot3 Curr={m3} Max={m} Min={n}'
                                    model.potok3 = s
                                    self.__write_data(3, t, m3Time, m3)
                            except Exception as e:
                                print(d, e)
            except serial.SerialException as err:
                print('connection to Board is failed ' + err.strerror)
                break
            except OSError as err:
                print('OSError ', err.strerror)
                break

        if self.__f and self.__f.closed == False:
            self.__f.close()

        if serial_port.isOpen():
            print('Close port')
            serial_port.close()

    def correction_det1(self, m):
        return self.correction(m, self.__A1, self.__B1)

    def correction_det2(self, m):
        return self.correction(m, self.__A2, self.__B2)

    def correction_det3(self, m):
        return self.correction(m, self.__A3, self.__B3)

    def correction(self, x, a, b):
        y = x - ((a - 1) * x + b)
        y = int(y*10)
        y = y/10.0

        return y

    def load_calib_table(self):
        etalon_measure = []
        measure_from_detector1 = []
        measure_from_detector2 = []
        measure_from_detector3 = []
        with open('call_coef.txt', 'rt') as f:
            try:
                arr = f.readlines()
                for l in arr:
                    l = l.replace('\n', '')
                    v = l.split(' ')
                    etalon_measure.append(float(v[0]))
                    measure_from_detector1.append(float(v[1]))
                    measure_from_detector2.append(float(v[2]))
                    measure_from_detector3.append(float(v[3]))
                etalon = np.array(etalon_measure).reshape((-1, 1))
                y1 = np.array(measure_from_detector1)
                y2 = np.array(measure_from_detector2)
                y3 = np.array(measure_from_detector3)

                model = LinearRegression()
                model.fit(etalon, y1)
                r_sq1 = model.score(etalon, y1)
                self.__A1 = model.coef_[0]
                self.__B1 = model.intercept_

                model.fit(etalon, y2)
                r_sq2 = model.score(etalon, y2)
                self.__A2 = model.coef_[0]
                self.__B2 = model.intercept_

                model.fit(etalon, y3)
                r_sq3 = model.score(etalon, y3)
                self.__A3 = model.coef_[0]
                self.__B3 = model.intercept_

                print('R^2 error. For det1:', r_sq1, 'For det2:', r_sq2, 'For det3:', r_sq3)
                print('A1:', self.__A1, 'A2', self.__A2, 'A3', self.__A3)
                print('B1:', self.__B1, 'B2', self.__B2, 'B3', self.__B3)

                for i in range(0, len(etalon), 1):
                    ycorr1 = measure_from_detector1[i] - ((self.__A1 - 1) * etalon[i] + self.__B1)
                    ycorr2 = measure_from_detector2[i] - ((self.__A2 - 1) * etalon[i] + self.__B2)
                    print(etalon[i], ycorr1, ycorr2)
            except Exception as e:
                print(e)

    def set_terminate(self):
        self.__terminate = True

    def change_max(self, m):
        data = self.MAX + str(m).encode() + b'\n'
        for sp in self.__serial_port:
            self.__mutex.acquire()
            sp.write(data)
            self.__mutex.release()

    def change_min(self, m):
        data = self.MIN + str(m).encode() + b'\n'
        for sp in self.__serial_port:
            self.__mutex.acquire()
            sp.write(data)
            self.__mutex.release()

    def change_rate(self, m):
        data = self.RATE + str(m).encode() + b'\n'
        for sp in self.__serial_port:
            self.__mutex.acquire()
            sp.write(data)
            self.__mutex.release()

    @property
    def data_is_capturing(self):
        return self.__data_capturing

    def start_capturing_data(self):
        dir_name = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        os.makedirs(dir_name)
        self.__filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


        self.__starting_time = datetime.datetime.now()

        self.__f = open(dir_name + '/' + self.__filename +'.txt', 'wt')
        self.__f1 = open(dir_name + '/1.txt' , 'wt')
        self.__f2 = open(dir_name + '/2.txt', 'wt')
        self.__f3 = open(dir_name + '/3.txt', 'wt')

        model.graph_y1 = np.array([]) * 0
        model.graph_y2 = np.array([]) * 0
        model.graph_y3 = np.array([]) * 0
        self.__starting_time = datetime.datetime.now()
        self.__data_capturing = True
        for sp in self.__serial_port:
            self.__mutex.acquire()
            sp.write(self.START)
            self.__mutex.release()

    def stop_captuging_data(self):
        self.__start_measurement_timestamp = 0
        for sp in self.__serial_port:
            self.__mutex.acquire()
            sp.write(self.STOP)
            self.__mutex.release()
        self.__data_capturing = False
        self.__work_time = None
        if self.__f and self.__f.closed == False:
            self.__f.close()
            self.__f = None
        if self.__f1 and self.__f1.closed == False:
            self.__f1.close()
            self.__f1 = None
        if self.__f2 and self.__f2.closed == False:
            self.__f2.close()
            self.__f2 = None
        if self.__f3 and self.__f3.closed == False:
            self.__f3.close()
            self.__f3 = None

    @property
    def max_capture_time(self):
        return self.__max_capture_time

    @max_capture_time.setter
    def max_capture_time(self, max_time):
        self.__max_capture_time = max_time
        print('max capture time is', self.max_capture_time)


