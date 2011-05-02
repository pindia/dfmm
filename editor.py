import wx, copy
import merge
from frame import ExtendedFrame
from progress import ProgressDialog, thread_wrapper
from encode import *
from decode import *

class ModEditorFrame(ExtendedFrame):
    def __init__(self, parent, mod):
        
        title = 'Mod Editor: %s' % path_to_filename(mod.path)
        if mod.parent:
            title += ' (Metamod of %s)' % path_to_filename(mod.parent.path)
        
        wx.Frame.__init__(self, parent, title=title, size=(800, 600))
        
        self.parent = parent
        
        self.init_menu()
        self.load_templates()
        
        self.core_dataset = mod.base
        self.core_objects = self.core_dataset.objects
        
        dataset = copy.deepcopy(self.core_dataset)
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
            
        # Set up the find/replace functions
            
        self.find_data =  wx.FindReplaceData()
        self.find_data.SetFlags(wx.FR_DOWN)
        self.find_open = False
        self.Bind(wx.EVT_FIND, self.perform_find)
        self.Bind(wx.EVT_FIND_NEXT, self.perform_find)
        self.Bind(wx.EVT_FIND_REPLACE, self.perform_replace)
        self.Bind(wx.EVT_FIND_REPLACE_ALL, self.perform_replace_all)
        self.Bind(wx.EVT_FIND_CLOSE, self.find_closed)

        
        
    def load_templates(self):
        self.templates = {}
        if not os.path.exists('templates'):
            return
        for fname in os.listdir('templates'):
            object_type = fname.split('.')[0].upper()
            f = open(os.path.join('templates', fname))
            self.templates[object_type] = f.read()
            f.close()
            
        
    def init_menu(self):
        
        self.filemenu= wx.Menu()
        menu_save = self.filemenu.Append(wx.ID_ANY, "&Save\tCtrl+S","")
        menu_save_and_exit = self.filemenu.Append(wx.ID_ANY, "Save and &exit","")
        menu_exit = self.filemenu.Append(wx.ID_ANY, "Exit without saving","")
        
        self.Bind(wx.EVT_MENU, self.save, menu_save)
        self.Bind(wx.EVT_MENU, self.exit, menu_exit)
        self.Bind(wx.EVT_MENU, self.save_and_exit, menu_save_and_exit)
        
        self.objectmenu= wx.Menu()
        menu_add = self.objectmenu.Append(wx.ID_ANY, "&Add object\tCtrl+N","")
        menu_delete = self.objectmenu.Append(wx.ID_ANY, "&Delete object\tDelete","")
        menu_revert = self.objectmenu.Append(wx.ID_ANY, "&Revert object\tAlt+Delete","")
        
                
        self.Bind(wx.EVT_MENU, self.add_object, menu_add)
        self.Bind(wx.EVT_MENU, self.delete_object, menu_delete)
        self.Bind(wx.EVT_MENU, self.revert_object, menu_revert)
        
        self.editmenu = wx.Menu()
        menu_find = self.editmenu.Append(wx.ID_ANY, "&Find...\tCtrl+F")
        menu_replace = self.editmenu.Append(wx.ID_ANY, "&Replace...\tCtrl+R")
        #menu_find_all = self.editmenu.Append(wx.ID_ANY, "&Find in All...\tCtrl-Shift-F")

        self.Bind(wx.EVT_MENU, self.show_find, menu_find)
        self.Bind(wx.EVT_MENU, self.show_replace, menu_replace)


        
        self.viewmenu = wx.Menu()
        self.menu_highlight = self.viewmenu.Append(wx.ID_ANY,"Highlight changes\tCtrl+H", kind=wx.ITEM_CHECK)
        self.menu_highlight.Check(True)
        self.menu_core = self.viewmenu.Append(wx.ID_ANY,"View core data\tCtrl+D", kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.view_highlight, self.menu_highlight)
        self.Bind(wx.EVT_MENU, self.view_core, self.menu_core)
        
        menuBar = wx.MenuBar()
        menuBar.Append(self.filemenu,"&File")
        menuBar.Append(self.editmenu, "&Edit")
        menuBar.Append(self.objectmenu,"&Object")
        menuBar.Append(self.viewmenu,"&View")
        self.SetMenuBar(menuBar)
        
    def view_highlight(self, event):
        self.nb.GetCurrentPage().listbox_clicked(None)
        
    def view_core(self, event):
        self.nb.GetCurrentPage().listbox_clicked(None)

        
    def show_find(self, event):
        if not self.find_open:
            self.find_open = True
            dialog = wx.FindReplaceDialog(self, self.find_data, 'Find',style=wx.FR_NOWHOLEWORD)
            dialog.Show()
        
    def show_replace(self, event):
        if not self.find_open:
            self.find_open = True
            dialog = wx.FindReplaceDialog(self, self.find_data, 'Find', style=wx.FR_REPLACEDIALOG|wx.FR_NOWHOLEWORD)
            dialog.Show()
        
        
    def perform_find(self, event):
        editor = self.nb.GetCurrentPage().editor
        value = editor.GetValue()
        find_text = event.GetFindString()
        flags = event.GetFlags()
        pos = editor.GetInsertionPoint()
        if not wx.FR_MATCHCASE & flags:
            find_text = find_text.upper()
            value = value.upper()
        if wx.FR_DOWN & flags:
            pos = value.find(find_text, pos+1)
        else:
            pos = value.rfind(find_text, 0, pos-1)
        
        if pos > -1:
            editor.SetSelection(pos, pos+len(find_text))
            editor.SetFocus()
        else:
            self.info_dialog('Cannot find "%s"' % event.GetFindString(), 'Find')
            
    def perform_replace(self, event):
        editor = self.nb.GetCurrentPage().editor
        find_text = event.GetFindString()
        replace_text = event.GetReplaceString()
        selected_text = editor.GetStringSelection()
        if find_text == selected_text:
            pos = editor.GetInsertionPoint()
            editor.Replace(pos, pos+len(find_text), replace_text)
            
    def perform_replace_all(self, event):
        editor = self.nb.GetCurrentPage().editor
        value = editor.GetValue()
        find_text = event.GetFindString()
        replace_text = event.GetReplaceString()
        flags = event.GetFlags()
        if not wx.FR_MATCHCASE & flags:
            find_text = find_text.upper()
            value = value.upper()
        pos = value.find(find_text, 0)
        while pos != -1:
            editor.Replace(pos, pos+len(find_text), replace_text)
            value = editor.GetValue()
            if not wx.FR_MATCHCASE & flags:
                value = value.upper()
            pos += len(replace_text)+1
            pos = value.find(find_text, pos)

        
        
    def find_closed(self, event):
        self.find_open = False
        event.GetDialog().Destroy()
        
        
    def add_object(self, event):
        panel = self.nb.GetCurrentPage()
        dialog = wx.TextEntryDialog(self, 'Enter name for new object', 'Add object', '')
        if dialog.ShowModal() == wx.ID_OK:
            ref_object = panel.objects[0]
            new_fname = ref_object.file_name
            if 'dfmm' not in new_fname:
                new_fname = new_fname.split('.')[0] + '_dfmm.txt'
            object = Object(new_fname, ref_object.type, ref_object.root_type, dialog.GetValue())
            if ref_object.type in self.templates:
                object.extra_data = self.templates[ref_object.type]
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
        if self.FindFocus() == panel.editor:
            return # Abort if editor has focus
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
        
    def save(self, event, exit=False):
        self.mod.objects = self.objects
        dialog = ProgressDialog(self, 'Saving mod')
        
        # All this must be in the other thread so it doesn't get out of order
        def process():
            encode_mod(self.mod, overwrite=True, callback=dialog)
            if self.parent:
                self.parent.reload_mods(progress=False)
            if exit:
                self.Close(True)

        thread_wrapper(process)()

        
    def exit(self, event):
        self.Close(True)
        
    def save_and_exit(self, event):
        self.save(None, exit=True)





class ObjectTypePanel(wx.Panel):
    def __init__(self, parent, type, objects, root_frame):
        wx.Panel.__init__(self, parent, size=(800,600))
        self.root_frame = root_frame
        self.type = type
        self.objects = objects
        
        
        self.listbox = wx.ListBox(self, pos=(0,0), size=(-1, 400))
        self.listbox.Bind(wx.EVT_LISTBOX, self.listbox_clicked)
        #self.listbox.Bind(wx.EVT_LISTBOX_DCLICK, self.object_context_menu)
        
        self.editor = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_PROCESS_TAB, size=(-1, 400))
        self.editor.Bind(wx.EVT_TEXT, self.data_modified)
        self.suppress_modified = False
        
        
        
        
        '''self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Add(self.listbox, 1)
        self.sizer.Add(self.editor, 3)
        self.sizer.Fit(self)'''
        
        self.horizontal = wx.BoxSizer(wx.HORIZONTAL)
        self.horizontal.Add(self.listbox, 1, wx.EXPAND)
        self.horizontal.Add(self.editor, 3, wx.EXPAND)
        self.vertical = wx.BoxSizer(wx.VERTICAL)
        self.vertical.Add(self.horizontal, 1, wx.EXPAND)
        self.SetSizerAndFit(self.vertical)
        
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
        sel = self.listbox.GetSelections()
        if not sel:
            return
        i = sel[0]
        object = self.objects[i]

        if self.root_frame.menu_core.IsChecked():
            self.editor.SetBackgroundColour(wx.Colour(200,200,200))
        else:
            self.editor.SetBackgroundColour(wx.Colour(255,255,255))

        
        if object.modified and not object.added and not object.deleted:
            self.suppress_modified = True
            self.editor.Clear()
            # Highlight the changes if applicable
            core_object = self.root_frame.core_object_lookup[object.type+object.name]
            i = 0
            for op, data in merge.get_diffs(core_object.extra_data, object.extra_data):
                if op == 1: # Added
                    if not self.root_frame.menu_core.IsChecked():
                        if self.root_frame.menu_highlight.IsChecked():
                            self.editor.SetDefaultStyle(wx.TextAttr(colBack=wx.Colour(0,255,0)))
                        self.editor.AppendText(data)
                elif op == -1: # Deleted
                    if self.root_frame.menu_core.IsChecked():
                        if self.root_frame.menu_highlight.IsChecked():
                            self.editor.SetDefaultStyle(wx.TextAttr(colBack=wx.Colour(255,0,0)))
                        self.editor.AppendText(data)
                else: #Unmodified
                    if self.root_frame.menu_core.IsChecked():
                        self.editor.SetDefaultStyle(wx.TextAttr(colBack=wx.Colour(200,200,200)))
                    else:
                        self.editor.SetDefaultStyle(wx.TextAttr(colBack=wx.Colour(255,255,255)))
                    self.editor.AppendText(data)
                i += len(data)
            self.suppress_modified = False
        else:
            self.editor.ChangeValue(object.extra_data)

        
        #self.editor.WriteText()
        self.editor.ShowPosition(0)
        
    def data_modified(self, event):
        if self.suppress_modified or self.root_frame.menu_core.IsChecked(): 
            return
        i = self.listbox.GetSelections()[0]
        object = self.objects[i]
        if object.deleted:
            return
        object.extra_data = self.editor.GetString(0, self.editor.GetLastPosition())
        object.invalidate_cache()
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
    
    frame = ModEditorFrame(None, decode_mod('mods/genesis.dfmod', core_dataset))
    
    

    frame.Show()
    app.MainLoop()

