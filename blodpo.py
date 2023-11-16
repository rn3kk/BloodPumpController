import sys
import wx
import model
from Window import Window

if __name__ == '__main__':
    com_port = list()
    com_port.append(str(sys.argv[1]))
    com_port.append(str(sys.argv[2]))
    com_port.append(str(sys.argv[3]))
    try:
        app = wx.App(0)
        frame = Window(parent=None, port_path=com_port)
        app.SetTopWindow(frame)
        frame.Show()
        model.fig.set_size_inches(14, 8, forward=True)
        bck = model.plt.get_backend()
        figManager = model.plt.get_current_fig_manager()
        if (bck == "TkAgg"):
            figManager.window.state('zoomed') #
            #figManager.resize(figManager.window.maxsize())
        elif (bck == "QT4Agg"):
            figManager.frame.Maximize(True)
        else:
            figManager.window.showMaximized()
        model.plt.show()
        app.MainLoop()
    except Exception as e:
        print(e)
    exit(0)
