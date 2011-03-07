import wx

class ExtendedFrame(wx.Frame):
    ''' The ExtendedFrame class adds a few convenience methods to the Frame class
    for use in subclasses '''
    
    def info_dialog(self, message, title):
        dialog = wx.MessageDialog(self, message, title, style=wx.OK)
        dialog.ShowModal()
        
    def warning_dialog(self, message, title):
        dialog = wx.MessageDialog(self, message,title, style=wx.OK|wx.ICON_WARNING)        
        dialog.ShowModal()
        
    def error_dialog(self, message, title):
        dialog = wx.MessageDialog(self, message,title, style=wx.OK|wx.ICON_ERROR)        
        dialog.ShowModal()
        
    def yes_no_dialog(self, message, title):
        dialog = wx.MessageDialog(self, message, title, style=wx.YES|wx.NO)
        return dialog.ShowModal() == wx.ID_YES
        
    def ok_cancel_dialog(self, message, title):
        dialog = wx.MessageDialog(self, message, title, style=wx.OK|wx.CANCEL)
        return dialog.ShowModal() == wx.ID_OK
        
    def text_entry_dialog(self, message, title, default=''):
        dialog = wx.TextEntryDialog(self, message, title, default)
        if dialog.ShowModal() == wx.ID_OK:
            return dialog.GetValue()
        return None
    
    def show_current_exception(self):
        self.show_exception_dialog(*sys.exc_info())
    
    def show_exception_dialog(self, type, value, tb):
        dialog = wx.MessageDialog(self, ''.join(traceback.format_exception_only(type, value)) + '\n' + ''.join(traceback.format_tb(tb)),
                                  'Fatal error', style=wx.OK|wx.ICON_ERROR)        
        dialog.ShowModal()
    
    