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