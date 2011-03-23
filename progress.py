import wx, threading, time, os

class ProcessingThread(threading.Thread):
    def __init__(self, fn, *args, **kwds):
        threading.Thread.__init__(self)
        self.fn = fn
        self.args = args
        self.kwds = kwds
    def run(self):
        self.fn(*self.args, **self.kwds)

def thread_wrapper(fn):
    def wrapped_function(*args, **kwds):
        thread = ProcessingThread(fn, *args, **kwds)
        thread.start()
    return wrapped_function

class DummyCallback(object):
    def set_task_number(self, number):
        ''' Sets the number of tasks that will be performed '''
        pass
    
    def task_started(self, label='', i=None):
        ''' Indicates that a task is beginning. Passed the index of the task
        to update the progress bar and an optional label for display.
        If index not specifed, assumed to increment by one'''
        pass
    
    def done(self):
        ''' All tasks are done, hide the progress bar'''
        pass
    
dummy_callback = DummyCallback()


class ProgressDialog(wx.Dialog):
    def __init__(self, parent, title="Progress"):
        wx.Dialog.__init__(self, parent, title=title, size=(300,60))
        self.title_base = title
        self.task_number = 0
        self.gauge = wx.Gauge(self, range=100, pos=(0,0), size=(300,20))
        self.label = wx.StaticText(self, pos=(0, 20), size=(300, 20))
        
    def set_task_number(self, number):
        self.Show()
        self.task_number = number
        self.i = 0
        
    def task_started(self, label='', i=None):
        if self.task_number == 0:
            return
        if i is not None:
            self.i = i
        percent = self.i * 100 / self.task_number
        self.gauge.SetValue(percent)
        self.gauge.Update()
        self.SetTitle('%s (%d%%)' % (self.title_base, percent))
        self.label.SetLabel(label)
        if i is None:
            self.i += 1

    def done(self):
        self.gauge.SetValue(100)
        self.SetTitle('%s (%d%%)' % (self.title_base, 100))
        self.Close()
        


if __name__ == '__main__':
    app = wx.App(False)
    dialog = ProgressDialog(None, 'Importing files')
    dialog.Show()
    
    dialog.set_task_number(10)
    
    
    class FakeTimerThread(threading.Thread):
        def __init__(self, dialog):
            threading.Thread.__init__(self)
            self.dialog = dialog
        def run(self):
            for i in range(0, 10):
                dialog.task_started()
                time.sleep(0.5)
            os._exit(0)
            
    t = FakeTimerThread(dialog)
    t.start()
    
    
    app.MainLoop()