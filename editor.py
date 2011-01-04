import wx
from decode import *

class ModEditorFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Mod Editor", size=(800, 600))
        
        self.filemenu= wx.Menu()
        menu_save = self.filemenu.Append(wx.ID_SAVE, "&Save","")
        menu_save_exit = self.filemenu.Append(wx.ID_OPEN, "Save and &exit","")
        menu_exit = self.filemenu.Append(wx.ID_EXIT, "Exit without saving","")
        
        self.objectmenu= wx.Menu()
        menu_add = self.objectmenu.Append(wx.ID_ADD, "&Add object","")
        menu_delete = self.objectmenu.Append(wx.ID_DELETE, "&Delete object","")
        menu_revert = self.objectmenu.Append(wx.ID_UNDO, "&Revert object","")
        
        self.Bind(wx.EVT_MENU, self.add_object, menu_add)
        self.Bind(wx.EVT_MENU, self.delete_object, menu_delete)
        self.Bind(wx.EVT_MENU, self.revert_object, menu_revert)

        
        menuBar = wx.MenuBar()
        menuBar.Append(self.filemenu,"&File")
        menuBar.Append(self.objectmenu,"&Object")
        self.SetMenuBar(menuBar)
        
    def add_object(self, event):
        panel = self.nb.GetCurrentPage()
        dialog = wx.TextEntryDialog(self, 'Enter name for new object', 'Add object', '')
        if dialog.ShowModal() == wx.ID_OK:
            ref_object = panel.objects[0]
            object = Object(ref_object.file_name, ref_object.type, ref_object.root_type, dialog.GetValue())
            object.added = True
            panel.objects.append(object)
            panel.listbox.Append(object.name)
            i = len(panel.objects) - 1
            panel.listbox.Select(i)
            panel.update_listbox(i)
            panel.listbox_clicked(None)
        else:
            pass
        
    def delete_object(self, event):
        panel = self.nb.GetCurrentPage()
        i = panel.listbox.GetSelections()[0]
        object = panel.objects[i]
        if object.added:
            del panel.objects[i]
            panel.listbox.Delete(i)
        else:
            object.modified = False
            object.deleted = True
            object.extra_data = '<DELETED>'
        panel.update_listbox(i)
        panel.listbox_clicked(None)
        
        
    def revert_object(self, event):
        panel = self.nb.GetCurrentPage()
        i = panel.listbox.GetSelections()[0]
        object = panel.objects[i]
        if object.added:
            pass
        object.deleted = False
        object.modified = False
        old_object = self.core_object_lookup[object.type+object.name]
        object.extra_data = old_object.extra_data
        panel.update_listbox(i)
        panel.listbox_clicked(None)
        





class ObjectTypePanel(wx.Panel):
    def __init__(self, parent, type, objects, root_frame):
        wx.Panel.__init__(self, parent, size=(800,600))
        self.root_frame = root_frame
        self.type = type
        self.objects = objects
        
        
        self.listbox = wx.ListBox(self, pos=(0,0), size=(-1, 400))
        self.listbox.Bind(wx.EVT_LISTBOX, self.listbox_clicked)
        
        self.editor = wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(-1, 400))
        self.editor.Bind(wx.EVT_TEXT, self.data_modified)
        
        
        
        
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Add(self.listbox, 1)
        self.sizer.Add(self.editor, 3)
        self.sizer.Fit(self)
        
        objects.sort(key=lambda o: o.name)
        
        for o in objects:
            self.listbox.Append(o.name)
        
        self.Show(True)

    def listbox_clicked(self, event):
        i = self.listbox.GetSelections()[0]
        self.editor.ChangeValue(self.objects[i].extra_data)
        #self.editor.WriteText()
        self.editor.ShowPosition(0)
        
    def data_modified(self, event):
        i = self.listbox.GetSelections()[0]
        object = self.objects[i]
        if object.added or object.deleted:
            pass
        object.extra_data = self.editor.GetString(0, self.editor.GetLastPosition())
        core_object = self.root_frame.core_object_lookup[object.type+object.name]
        if core_object.extra_data != object.extra_data:
            object.modified = True
        else:
            object.modified = False
        self.update_listbox(i)        
        
    def update_listbox(self, i):
        object = self.objects[i]
        if object.deleted:
            prefix = '[D] '
        elif object.added:
            prefix = '+'
        elif object.modified:
            prefix = '*'
        else:
            prefix = ''
        self.listbox.SetString(i, prefix + object.name)
        self.listbox.Select(i)
        
        
   

        
        
        
app = wx.App(False)
frame = ModEditorFrame(None)


frame.core_objects = decode_directory('core')
frame.core_object_lookup = {}
for object in frame.core_objects:
    frame.core_object_lookup[object.type+object.name] = object
frame.objects = decode_directory('core')

headers = {}
for o in frame.objects:
    if o.type not in headers:
        headers[o.type] = []
    headers[o.type].append(o)


frame.nb = wx.Notebook(frame, -1, wx.Point(0,0), wx.Size(0,0), wx.NB_MULTILINE)

for header in headers.keys():
    frame.nb.AddPage(ObjectTypePanel(frame.nb, header, headers[header], frame), header)
frame.Show()
app.MainLoop()

