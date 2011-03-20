import wx
import images
import sys, traceback

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
    
    def file_save_dialog(self, title, extension):
        dialog = wx.FileDialog(self, title, wildcard='*.%s' % extension, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            return dialog.GetPath()
    
    def show_current_exception(self):
        self.show_exception_dialog(*sys.exc_info())
    
    def show_exception_dialog(self, type, value, tb):
        dialog = wx.MessageDialog(self, ''.join(traceback.format_exception_only(type, value)) + '\n' + ''.join(traceback.format_tb(tb)),
                                  'Fatal error', style=wx.OK|wx.ICON_ERROR)        
        dialog.ShowModal()
        
class TreeController(object):
    ''' A tree controller has several convenience methods to manage a tree control, assumed
    to be located in self.tree.'''
    def init_image_list(self):
        isize = (16,16)
        il = wx.ImageList(isize[0], isize[1])
        self.img_folder   = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,  wx.ART_OTHER, isize))
        self.img_folder_open = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER,isize))
        self.img_file   = il.Add(wx.ArtProvider_GetBitmap(wx.ART_REPORT_VIEW, wx.ART_OTHER,isize))
        self.img_tick = il.Add(images.tick.ConvertToBitmap(16))
        self.img_cross = il.Add(images.cross.ConvertToBitmap(16))

        self.tree.SetImageList(il)
        self.il = il
        
    def add_root(self, title):
        self.root = self.tree.AddRoot(title)
        self.tree.SetPyData(self.root, {"type":"container"})
        self.tree.SetItemImage(self.root, self.img_folder, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root, self.img_folder_open, wx.TreeItemIcon_Expanded)
        
    def add_folder(self, parent, title):
        child = self.tree.AppendItem(parent, title)
        self.tree.SetPyData(child, {"type":"container"})
        self.tree.SetItemImage(child, self.img_folder, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(child, self.img_folder_open, wx.TreeItemIcon_Expanded)
        return child
    
    def add_item(self, parent, title, object=None):
        item = self.tree.AppendItem(parent, title)
        self.tree.SetPyData(item,{"type":"item",'object':object})
        self.tree.SetItemImage(item, self.img_file, wx.TreeItemIcon_Normal)
        return item
    
    def item_children(self, parent):
        ''' Generator expression for iterating over the children of a tree item '''
        item, cookie = self.tree.GetFirstChild(parent) 
        while item:
            yield item
            item, cookie = self.tree.GetNextChild(parent, cookie)
    