import wx
import shelve, sys, shutil
from decode import *
from editor import *


class MainFrame(wx.Frame):
    
    def reload_mods(self):
        self.mods = decode_all_mods(self.core_dataset)
        self.update_mod_list()
    
    def update_mod_list(self):
        self.listbox.DeleteAllItems()
        for mod in self.mods:
            if mod.name not in self.mod_db: # Make sure it's in the database
                self.mod_db[mod.name] = {'enabled':True, 'index':0}
        self.mods.sort(key=lambda m: self.mod_db[m.name]['index'])
        for i, mod in enumerate(self.mods):
            self.listbox.Append((u'\u2713' if self.mod_db[mod.name]['enabled'] else ' ', mod.name, len(mod.added_objects), len(mod.modified_objects), len(mod.deleted_objects)))
            self.mod_db[mod.name]['index'] = i
        self.mod_db.sync()

    
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="DF Mod Manager", size=(500, 300))
        
        if not os.path.exists('core'):
            dialog = wx.MessageDialog(self, 'It appears that you are running DFMM for the first time. Are the files currently in your raws folder unmodified?',
                                  'Setup',style=wx.YES|wx.NO)
            if dialog.ShowModal() == wx.ID_YES:
                shutil.copytree(os.path.join('..','raw','objects'), 'core')
            else:
                dialog = wx.MessageDialog(self, 'Please restore the raw files to their unmodified state and relaunch DFMM. (Backup your changes to another directory for later import)', style=wx.OK)
                dialog.ShowModal()
                sys.exit(0)
        
        self.core_dataset = decode_core()
        
        
        self.listbox = wx.ListCtrl(self, wx.ID_ANY, pos=(0,0), size=(-1, -1), style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_HRULES|wx.LC_SINGLE_SEL)
        self.listbox.InsertColumn(0, 'On')
        self.listbox.InsertColumn(1, 'Name')
        self.listbox.InsertColumn(2, 'Added')
        self.listbox.InsertColumn(3, 'Modified')
        self.listbox.InsertColumn(4, 'Deleted')
        self.listbox.SetColumnWidth(0, 40)
        self.listbox.SetColumnWidth(1, 150)
        self.listbox.SetColumnWidth(2, 70)
        self.listbox.SetColumnWidth(3, 70)
        self.listbox.SetColumnWidth(4, 70)
        
        self.listbox.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.mod_context_menu)
        
        self.mod_db = shelve.open(os.path.join('mods','mods.db'), writeback=True)

        
        self.reload_mods()
        
        
        self.filemenu = wx.Menu()
        menu_new = self.filemenu.Append(wx.ID_ANY, "&New mod","")
        menu_install = self.filemenu.Append(wx.ID_ANY, "&Install mods","")
        menu_exit = self.filemenu.Append(wx.ID_EXIT, "Exit","")
        
        self.Bind(wx.EVT_MENU, self.install, menu_install)
        self.Bind(wx.EVT_MENU, self.new_mod, menu_new)
        self.Bind(wx.EVT_MENU, self.exit, menu_exit)

        self.importmenu = wx.Menu()
        menu_import_dfmod = self.importmenu.Append(wx.ID_ANY, "Import .dfmod","")
        menu_import_files = self.importmenu.Append(wx.ID_ANY, "Import from directory","")
        
        self.Bind(wx.EVT_MENU, self.import_dfmod, menu_import_dfmod)
        self.Bind(wx.EVT_MENU, self.import_files, menu_import_files)
        
        OPTIONS = [['_merge_changes','Merge changes'], ['_partial_merge','Allow partial merge'], ['_delete_override','Delete overrides edit']]
        
        self.options_menu = {}
        self.optionsmenu = wx.Menu()
        for key, value in OPTIONS:
            item = self.optionsmenu.Append(wx.ID_ANY, value, '', kind=wx.ITEM_CHECK)
            if key not in self.mod_db:
                self.mod_db[key] = True if key == '_merge_changes' else False
                self.mod_db.sync()
            if self.mod_db[key]:
                item.Check()
            self.Bind(wx.EVT_MENU, self.toggle_option(key), item)
            self.options_menu[key] = item

        
        menuBar = wx.MenuBar()
        menuBar.Append(self.filemenu,"&File")
        menuBar.Append(self.importmenu,"&Import")
        menuBar.Append(self.optionsmenu,"&Options")
        self.SetMenuBar(menuBar)
        
    def mod_context_menu(self, event):
        mod = self.mods[self.listbox.GetFirstSelected()]
        
        menu = wx.Menu()
        
        menu_enable = menu.Append(wx.ID_ANY, "Enable mod","", kind=wx.ITEM_CHECK)
        if self.mod_db[mod.name]['enabled']:
            menu_enable.Check()
        menu.AppendSeparator()
        menu_up = menu.Append(wx.ID_ANY, "Move up","")
        menu_down = menu.Append(wx.ID_ANY, "Move down","")
        menu.AppendSeparator()
        menu_export_dfmod = menu.Append(wx.ID_ANY, "Export .dfmod","")
        menu_export_files = menu.Append(wx.ID_ANY, "Export to directory","")
        menu.AppendSeparator()
        menu_edit = menu.Append(wx.ID_ANY, "&Edit mod","")
        menu_delete = menu.Append(wx.ID_ANY, "&Delete mod","")
        
        self.Bind(wx.EVT_MENU, self.enable_mod, menu_enable)
        self.Bind(wx.EVT_MENU, self.move_mod_up, menu_up)
        self.Bind(wx.EVT_MENU, self.move_mod_down, menu_down)
        self.Bind(wx.EVT_MENU, self.export_dfmod, menu_export_dfmod)
        self.Bind(wx.EVT_MENU, self.export_files, menu_export_files)
        self.Bind(wx.EVT_MENU, self.edit_mod, menu_edit)
        self.Bind(wx.EVT_MENU, self.delete_mod, menu_delete)
        
        self.PopupMenu(menu, event.GetPoint())
        
    def enable_mod(self, event):
        mod = self.mods[self.listbox.GetFirstSelected()]
        self.mod_db[mod.name]['enabled'] = not self.mod_db[mod.name]['enabled']
        self.mod_db.sync()
        self.update_mod_list()
        
        
    def move_mod(self, dir):
        mod = self.mods[self.listbox.GetFirstSelected()]
        i = self.mod_db[mod.name]['index']
        old_mods = [m for m in self.mods if self.mod_db[m.name]['index'] == i + dir]
        if old_mods:
            self.mod_db[old_mods[0].name]['index'] = i
            self.mod_db[mod.name]['index'] = i + dir
            self.mod_db.sync()
            self.update_mod_list()
        else:
            print 'Failed to move'
            
    def move_mod_up(self, event):
        self.move_mod(-1)
        
    def move_mod_down(self, event):
        self.move_mod(+1)

        
    def new_mod(self, event):
        dialog = wx.TextEntryDialog(self, 'Enter name for new mod', 'New mod', '')
        if dialog.ShowModal() == wx.ID_OK:
            name = dialog.GetValue()
            fname = name.lower().replace(' ','-') + '.dfmod'
            encode_mod(Mod(name, os.path.join('mods', fname), []), self.core_dataset)
        self.reload_mods()
        
    def edit_mod(self, event):
        i = self.listbox.GetFirstSelected()
        mod = self.mods[i]
        frame = ModEditorFrame(self, self.core_dataset, mod)
        frame.Show()
        
    def delete_mod(self, event):
        i = self.listbox.GetFirstSelected()
        mod = self.mods[i]
        dialog = wx.MessageDialog(self, 'Are you sure you want to delete "%s"?' % mod.name,
                                  'Delete mod',style=wx.OK|wx.CANCEL)
        if dialog.ShowModal() == wx.ID_OK:
            os.remove(mod.path)
        self.reload_mods()
        
    def export_dfmod(self, event):
        i = self.listbox.GetFirstSelected()
        mod = self.mods[i]
        dialog = wx.FileDialog(self, 'Select File', wildcard='*.dfmod', style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            new_mod = copy.deepcopy(mod)
            new_mod.path = path
            encode_mod(new_mod, self.core_dataset)
            
    def export_files(self, event):
        dialog = wx.DirDialog(self, 'Select directory')
        i = self.listbox.GetFirstSelected()
        mod = self.mods[i]
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            encode_to_directory(mod.objects, path)
        
    def import_dfmod(self, event):
        dialog = wx.FileDialog(self, 'Select File', wildcard='*.dfmod')
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            mod = decode_mod(path, self.core_dataset)
            fname = mod.name.lower().replace(' ','-') + '.dfmod'
            mod.path = os.path.join('mods', fname)
            encode_mod(mod, self.core_dataset)
        self.reload_mods()
        
    def import_files(self, event):
        dialog = wx.DirDialog(self, 'Select directory', style=wx.DD_DIR_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            dialog = wx.TextEntryDialog(self, 'Enter name for imported mod', 'Import mod', '')
            if dialog.ShowModal() == wx.ID_OK:
                name = dialog.GetValue()
                fname = name.lower().replace(' ','-') + '.dfmod'
                mod_dataset = decode_directory(path)
                mod = Mod(name, os.path.join('mods', fname), self.core_dataset.difference(mod_dataset))
                encode_mod(mod, self.core_dataset)
            #fname = name.lower().replace(' ','-') + '.dfmod'
        self.reload_mods()
    
        
    def install(self, event):
        print 'Installing mods'
        print '-' * 20
        dataset = copy.deepcopy(self.core_dataset)
        for mod in self.mods:
            if self.mod_db[mod.name]['enabled']:
                dataset.apply_mod(mod, self.core_dataset,
                                    merge_changes=self.mod_db['_merge_changes'],
                                    partial_merge=self.mod_db['_partial_merge'],
                                    delete_override=self.mod_db['_delete_override'])
        path = os.path.join('..','raw','objects')
        current_files = os.listdir(path)
        for f in current_files:
            os.remove(os.path.join(path, f))
        encode_objects(dataset.objects, path)
        print 'Install complete'
        
    def exit(self, event):
        self.Close(True)
        
    def toggle_option(self, option):
        def perform_toggle(event):
            self.mod_db[option] = not self.mod_db[option]
            self.options_menu[option].Check(self.mod_db[option])
            self.mod_db.sync()
        return perform_toggle
        
        
app = wx.App(False)
frame = MainFrame(None)

frame.Show()
app.MainLoop()
