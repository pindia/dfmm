import wx, copy
from encode import *
from decode import *

class ModEditorFrame(wx.Frame):
    def __init__(self, parent, core_dataset, mod):
        wx.Frame.__init__(self, parent, title="Mod Editor", size=(800, 600))
        
        self.parent = parent
        
        self.core_objects = core_dataset.objects
        dataset = copy.deepcopy(core_dataset)
        dataset.apply_mod_for_editing(mod)
        self.objects = dataset.objects
        
        self.path = mod.path
        
        self.core_object_lookup = {}
        for object in self.core_objects:
            self.core_object_lookup[object.type+object.name] = object
        
        headers = {}
        for o in self.objects:
            if o.type not in headers:
                headers[o.type] = []
            headers[o.type].append(o)
        
        
        self.nb = wx.Notebook(self, -1, wx.Point(0,0), wx.Size(0,0), wx.NB_MULTILINE)
        
        for header in headers.keys():
            self.nb.AddPage(ObjectTypePanel(self.nb, header, headers[header], self), header)
        
        self.filemenu= wx.Menu()
        menu_save = self.filemenu.Append(wx.ID_SAVE, "&Save","")
        menu_save_and_exit = self.filemenu.Append(wx.ID_OPEN, "Save and &exit","")
        menu_exit = self.filemenu.Append(wx.ID_EXIT, "Exit without saving","")
        
        self.Bind(wx.EVT_MENU, self.save, menu_save)
        self.Bind(wx.EVT_MENU, self.exit, menu_exit)
        self.Bind(wx.EVT_MENU, self.save_and_exit, menu_save_and_exit)
        
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
            new_fname = ref_object.file_name
            if 'dfmm' not in new_fname:
                new_fname = new_fname.split('.')[0] + '_dfmm.txt'
            object = Object(new_fname, ref_object.type, ref_object.root_type, dialog.GetValue())
            object.added = True
            self.objects.append(object)
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
            self.objects.remove(object)
            panel.objects.remove(object)
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
        
    def save(self, event):
        encode_mod(Mod('Test', self.path, self.objects), self.path)
        
    def exit(self, event):
        if self.parent:
            self.parent.update_mod_list()
        self.Close(True)
        
    def save_and_exit(self, event):
        self.save(None)
        self.exit(None)





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
        
        for i, o in enumerate(objects):
            self.listbox.Append(o.name)
            self.update_listbox(i)
        
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
            return
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
        
        
   

        
if __name__ == '__main__':
        
        
    app = wx.App(False)
    
    core_dataset = decode_core()
    
    frame = ModEditorFrame(None, core_dataset, decode_mod('mods/test.dfmod'))
    
    

    frame.Show()
    app.MainLoop()

