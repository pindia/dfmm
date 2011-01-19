import wx, copy
import merge
from encode import *
from decode import *

class ModEditorFrame(wx.Frame):
    def __init__(self, parent, core_dataset, mod):
        wx.Frame.__init__(self, parent, title="Mod Editor", size=(800, 600))
        
        self.parent = parent
        
        self.core_dataset = core_dataset
        self.core_objects = core_dataset.objects
        dataset = copy.deepcopy(core_dataset)
        dataset.apply_mod_for_editing(mod)
        self.objects = dataset.objects
        
        self.mod = mod
        
        self.core_object_lookup = {}
        for object in self.core_objects:
            self.core_object_lookup[object.type+object.name] = object
        
        headers = {}
        for o in self.objects:
            if o.type not in headers:
                headers[o.type] = []
            headers[o.type].append(o)
        
        
        self.nb = wx.Notebook(self, -1, wx.Point(0,0), wx.Size(0,0), wx.NB_MULTILINE)
        
        for header in sorted(headers.keys()):
            changed_objects = len([o for o in mod.changed_objects if o.type == header])
            text = header
            if changed_objects != 0:
                text += ' [%d]' % changed_objects
            self.nb.AddPage(ObjectTypePanel(self.nb, header, headers[header], self), text)
        
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
        encode_mod(Mod(self.mod.name, self.mod.path, self.objects), self.core_dataset)
        if self.parent:
            self.parent.reload_mods()
        
    def exit(self, event):
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
        #self.listbox.Bind(wx.EVT_LISTBOX_DCLICK, self.object_context_menu)
        
        self.editor = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_RICH2, size=(-1, 400))
        self.editor.Bind(wx.EVT_TEXT, self.data_modified)
        self.suppress_modified = False
        
        
        
        
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
        
        self.listbox_clicked(None)
        
        self.Show(True)
        
    def object_context_menu(self, event):
        
        menu = wx.Menu()
        menu_add = menu.Append(wx.ID_ANY, "Add object","")
        menu_delete = menu.Append(wx.ID_ANY, "Delete object","")
        menu_revert = menu.Append(wx.ID_ANY, "Revert object","")
        
        self.Bind(wx.EVT_MENU, self.root_frame.add_object, menu_add)
        self.Bind(wx.EVT_MENU, self.root_frame.delete_object, menu_delete)
        self.Bind(wx.EVT_MENU, self.root_frame.revert_object, menu_revert)

        
        self.PopupMenu(menu, event.GetPoint())

    def listbox_clicked(self, event):
        i = self.listbox.GetSelections()[0]
        object = self.objects[i]
        

        
        if object.modified and not object.added and not object.deleted:
            self.suppress_modified = True
            self.editor.Clear()
            # Highlight the changes if applicable
            core_object = self.root_frame.core_object_lookup[object.type+object.name]
            i = 0
            for op, data in merge.get_diffs(core_object.extra_data, object.extra_data):
                if op == 1: # Added
                    #text.append('*%s*' % data)
                    #self.editor.SetStyle(i, i+len(data), wx.TextAttr(colBack=wx.Colour(0,255,0)))
                    self.editor.SetDefaultStyle(wx.TextAttr(colBack=wx.Colour(0,255,0)))
                    self.editor.AppendText(data)
                elif op == -1: # Deleted
                    pass
                    #self.editor.SetDefaultStyle(wx.TextAttr(colBack=wx.Colour(255,0,0)))
                    #self.editor.AppendText(data)
                else: #Unmodified
                    self.editor.SetDefaultStyle(wx.TextAttr(colBack=wx.Colour(255,255,255)))
                    self.editor.AppendText(data)
                i += len(data)
            self.suppress_modified = False
        else:
            self.editor.ChangeValue(object.extra_data)

        
        #self.editor.WriteText()
        self.editor.ShowPosition(0)
        
    def data_modified(self, event):
        if self.suppress_modified: 
            return
        i = self.listbox.GetSelections()[0]
        object = self.objects[i]
        if object.deleted:
            return
        object.extra_data = self.editor.GetString(0, self.editor.GetLastPosition())
        if object.added:
            return
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
    
    frame = ModEditorFrame(None, core_dataset, decode_mod('mods/test.dfmod', core_dataset))
    
    

    frame.Show()
    app.MainLoop()

