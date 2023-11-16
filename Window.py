import numpy as np
import wx

import model
from controller import Controller

timer_interval = 300
class Window(wx.Frame):
    max_p = 0
    min_p = 0
    potok1_label_text = ''
    potok2_label_text = ''
    potok3_label_text = ''

    def __init__(self, parent, port_path):
        print('Window()')
        wx.Frame.__init__(self, parent, -1, "BloodTool")
        self.Bind(wx.EVT_CLOSE, self.close)
        self.SetSize((230, 150))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.__startBtn = wx.Button(self, wx.NewId(), label='Start')
        self.__status_label = wx.StaticText(self, wx.NewId(), label='-')
        self.__status_label.SetBackgroundColour(wx.NullColour)
        main_sizer.Add(self.__status_label)

        line = wx.BoxSizer(wx.HORIZONTAL)
        line.Add(wx.StaticText(self, wx.NewId(), label="Max V", size=(80, -1)))
        self.__maxv_edit = wx.TextCtrl(self, wx.NewId(), value="255", style=wx.TE_PROCESS_ENTER)
        self.__maxv_edit.Bind(wx.EVT_TEXT_ENTER, self.__max_changed)
        # self.__maxv_edit.Bind(wx.EVT_CHAR, self.onKeyPress)
        line.Add(self.__maxv_edit)
        main_sizer.Add(line)

        line = wx.BoxSizer(wx.HORIZONTAL)
        line.Add(wx.StaticText(self, wx.NewId(), label="Min V", size=(80, -1)))
        self.__minv_edit = wx.TextCtrl(self, wx.NewId(), value="75", style=wx.TE_PROCESS_ENTER)
        self.__minv_edit.Bind(wx.EVT_TEXT_ENTER, self.__min_changed)
        line.Add(self.__minv_edit)
        main_sizer.Add(line)

        line = wx.BoxSizer(wx.HORIZONTAL)
        line.Add(wx.StaticText(self, wx.NewId(), label="Rate", size=(80, -1)))
        self.__rate_edit = wx.TextCtrl(self, wx.NewId(), value="60", style=wx.TE_PROCESS_ENTER)
        self.__rate_edit.Bind(wx.EVT_TEXT_ENTER, self.__rate_changed)
        line.Add(self.__rate_edit)
        main_sizer.Add(line)

        self.__potok1 = wx.StaticText(self, wx.NewId(), label="-")
        self.__potok2 = wx.StaticText(self, wx.NewId(), label="-")
        self.__potok3 = wx.StaticText(self, wx.NewId(), label="-")
        main_sizer.Add(self.__potok1)
        main_sizer.Add(self.__potok2)
        main_sizer.Add(self.__potok3)

        line = wx.BoxSizer(wx.HORIZONTAL)
        self.__capTimeEdit = wx.TextCtrl(self, wx.NewId(), value="0")
        line.Add(self.__startBtn)
        line.Add(wx.StaticText(self, wx.NewId(), label="CaptureTime, sec"))
        line.Add(self.__capTimeEdit)
        main_sizer.Add(line)

        self.__controller = Controller(port_path)
        self.__controller.start()

        if self.__controller.data_is_capturing:
            self.__startBtn.SetLabel('Stop')
        else:
            self.__startBtn.SetLabel('Start')

        self.__maxv_edit.SetValue('')
        self.__minv_edit.SetValue('')
        self.__rate_edit.SetValue('')

        self.SetSizer(main_sizer)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.timerEvent, self.timer)
        self.timer.Start(timer_interval)
        self.Layout()

    def __max_changed(self, event):
        v = self.__maxv_edit.Value
        self.__controller.change_max(v)
        self.set_max('-')

    def __min_changed(self, event):
        v = self.__minv_edit.Value
        self.__controller.change_min(v)
        self.set_min('-')

    def __rate_changed(self, event):
        v = self.__rate_edit.Value
        self.__controller.change_rate(v)
        self.set_rate('-')

    def timerEvent(self, event):
        try:
            model.a1[0].set_ydata(model.graph_y1)
            model.a1[0].set_xdata(np.arange(0, len(model.graph_y1)))
            model.a2[0].set_ydata(model.graph_y2)
            model.a2[0].set_xdata(np.arange(0, len(model.graph_y2)))
            model.a3[0].set_ydata(model.graph_y3)
            model.a3[0].set_xdata(np.arange(0, len(model.graph_y3)))
            model.fig.canvas.draw()
        except Exception as e:
            print(e)

        if model.changed:
            self.set_max(model.max_value)
            self.set_min(model.min_value)
            self.set_rate(model.rate)
            model.changed = False
        self.board_status(model.board_status)
        self.__potok1.SetLabel(model.potok1)
        self.__potok2.SetLabel(model.potok2)
        self.__potok3.SetLabel(model.potok3)
        self.__startBtn.Bind(wx.EVT_BUTTON, self.__start_click_event)
        if self.__controller.data_is_capturing:
            self.__startBtn.SetLabel('Stop')
        else:
            self.__startBtn.SetLabel('Start')
        self.Layout()
        self.Fit()

    def __start_click_event(self, event):
        if not self.__controller.data_is_capturing:
            try:
                self.__controller.max_capture_time = int(self.__capTimeEdit.Value)
            except:
                print('Not is number in time field')
            self.__controller.start_capturing_data()
        else:
            self.__controller.stop_captuging_data()


    def close(self, event):
        model.plt.close()
        self.__controller.set_terminate()
        self.__controller.join()
        self.Destroy()


    def set_max(self, max):
        self.__maxv_edit.SetValue(str(max))

    def set_min(self, min):
        self.__minv_edit.SetValue(str(min))

    def set_rate(self, rate):
        self.__rate_edit.SetValue(str(rate))

    def board_status(self, status):
        self.__status_label.SetLabel(status)
