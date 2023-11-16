from threading import Thread
import sys
import signal
import time

import serial

com_port = '/dev/ttyUSB0'
terminate = False
p1 = 0.0
p2 = 0.0
p3 = 0.0
have_data_in_port = [False,False, False]
GET = b'get'
STA = b'sta'
STO = b'sto'

def handler(signum, frame):
    global terminate
    terminate = True
    print('set terminate is True')


def read_com_port(com_port_mane):
    global terminate, p1, p2, p3, have_data_in_port

    serial_port = serial.Serial(port=com_port_mane, baudrate=9600, parity=serial.PARITY_NONE,
                                timeout=0.2, bytesize=serial.EIGHTBITS,
                                stopbits=serial.STOPBITS_TWO)
    is_init = False

    while not terminate:
        time.sleep(0.001)
        if not serial_port.isOpen():
            print('com port not open. exit()')
            break
        if not is_init:
            if serial_port.isOpen():
                serial_port.write(STO + b'\n')
                serial_port.flush()
                time.sleep(3.0)
                serial_port.write(STA + b'\n')
                serial_port.flush()
                print('Send start', STA + b'\n', serial_port)
                time.sleep(1.0)

        if serial_port.in_waiting > 0:
            d = serial_port.readline()
            # print(d)
            d = d.replace(b'\n',b'')
            cmd = d[:3]
            if cmd == b'pre':

                pre = d[3:].split(b' ')
                num_det = int(pre[0])
                if not is_init:
                    is_init = True
                    print('Found detector', num_det)
                if num_det == 1:
                    p1 = float(pre[2])
                    # print(p1, d)
                    have_data_in_port[0] = True
                elif num_det == 2:
                    p2 = float(pre[2])
                    # print(p2, d)
                    have_data_in_port[1] = True
                elif num_det == 3:
                    p3 = float(pre[2])
                    # print(p3, d)
                    have_data_in_port[2] = True
    if serial_port and serial_port.isOpen():
        serial_port.write(STO + b'\n')
        serial_port.flush()
        time.sleep(3.0)
    print('****END ', com_port_mane)

start_pre = 0
end_pre = 145
step = 5
coeff_array = list()
for i in range(start_pre, end_pre, step):
    coeff_array.append([i, 0, 0, 0])


def save_to_file():
    with open('call_coef.txt', 'wt') as f:
        for i in coeff_array:
            f.write(str(i[0]))
            f.write(' ')
            f.write(str(i[1]))
            f.write(' ')
            f.write(str(i[2]))
            f.write(' ')
            f.write(str(i[3]))
            f.write('\n')


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    com_port = list()
    com_port.append(str(sys.argv[1]))
    com_port.append(str(sys.argv[2]))
    com_port.append(str(sys.argv[3]))

    thread1 = Thread(target=read_com_port, args=(str(sys.argv[1]),))
    thread1.start()

    thread2 = Thread(target=read_com_port, args=(str(sys.argv[2]),))
    thread2.start()

    thread3 = Thread(target=read_com_port, args=(str(sys.argv[3]),))
    thread3.start()

    while not have_data_in_port[0] or not have_data_in_port[1] or not have_data_in_port[2]:
        time.sleep(0.1)

    print('Подключите датчики к калибратору')

    for i in range(start_pre, end_pre, step):
        time.sleep(1)
        value = input(f'Установите давление {i}:')
        print('Было подано:', i, 'Измерено p1:', p1, 'p2:', p2, 'p3:', p3, '\n')
        for j in range(0, len(coeff_array)):
            if coeff_array[j][0] == i:
                coeff_array[j] = [i, p1, p2, p3]
                save_to_file()
                break
    terminate = True
    thread1.join()
    thread2.join()
    thread3.join()
    print('End')
    exit(0)
