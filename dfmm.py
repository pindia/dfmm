import wx
from decode import *
from editor import *

class MainFrame(wx.Frame):
    
    def update_mod_list(self):
        self.mods = decode_all_mods()
        self.listbox.DeleteAllItems()
        for mod in self.mods:
            self.listbox.Append((mod.name, len(mod.added_objects), len(mod.modified_objects), len(mod.deleted_objects)))
    
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="DF Mod Manager", size=(400, 300))
        
        self.core_dataset = decode_core()
        
        
        self.listbox = wx.ListCtrl(self, wx.ID_ANY, pos=(0,0), size=(-1, -1), style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_HRULES|wx.LC_SINGLE_SEL)
        self.listbox.InsertColumn(0, 'Name')
        self.listbox.InsertColumn(1, 'Added')
        self.listbox.InsertColumn(2, 'Modified')
        self.listbox.InsertColumn(3, 'Deleted')
        self.listbox.SetColumnWidth(0, 150)
        self.listbox.SetColumnWidth(1, 70)
        self.listbox.SetColumnWidth(2, 70)
        self.listbox.SetColumnWidth(3, 70)
        
        self.update_mod_list()
        
        self.filemenu = wx.Menu()
        menu_install = self.filemenu.Append(wx.ID_ANY, "&Install","")
        #menu_save_exit = self.filemenu.Append(wx.ID_OPEN, "Save and &exit","")
        #menu_exit = self.filemenu.Append(wx.ID_EXIT, "Exit without saving","")
        
        self.Bind(wx.EVT_MENU, self.install, menu_install)
        
        self.objectmenu = wx.Menu()
        menu_new = self.objectmenu.Append(wx.ID_ANY, "&New mod","")
        menu_edit = self.objectmenu.Append(wx.ID_ANY, "&Edit mod","")
        menu_delete = self.objectmenu.Append(wx.ID_ANY, "&Delete mod","")
        
        self.Bind(wx.EVT_MENU, self.new_mod, menu_new)
        self.Bind(wx.EVT_MENU, self.edit_mod, menu_edit)
        self.Bind(wx.EVT_MENU, self.delete_mod, menu_delete)
        
        

        
        self.importmenu = wx.Menu()
        menu_import_dfmod = self.importmenu.Append(wx.ID_ANY, "Import .dfmod","")
        menu_import_files = self.importmenu.Append(wx.ID_ANY, "Import from directory","")
        
        
        self.Bind(wx.EVT_MENU, self.import_files, menu_import_files)

        
        menuBar = wx.MenuBar()
        menuBar.Append(self.filemenu,"&File")
        menuBar.Append(self.objectmenu,"&Mod")
        menuBar.Append(self.importmenu,"&Import")
        self.SetMenuBar(menuBar)
        
    def new_mod(self, event):
        dialog = wx.TextEntryDialog(self, 'Enter name for new mod', 'New mod', '')
        if dialog.ShowModal() == wx.ID_OK:
            name = dialog.GetValue()
            fname = name.lower().replace(' ','-') + '.dfmod'
            encode_mod(Mod(name, os.path.join('mods', fname), []))
        self.update_mod_list()
        
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
        self.update_mod_list()
        
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
                encode_mod(mod)
            #fname = name.lower().replace(' ','-') + '.dfmod'
            #encode_mod(Mod(name, os.path.join('mods', fname), []))
        self.update_mod_list()
        
    def install(self, event):
        dataset = copy.deepcopy(self.core_dataset)
        for mod in self.mods:
            dataset.apply_mod(mod)
        path = os.path.join('..','raw','objects')
        current_files = os.listdir(path)
        for f in current_files:
            os.remove(os.path.join(path, f))
        encode_objects(dataset.objects, path)
        
        
app = wx.App(False)
frame = MainFrame(None)

frame.Show()
app.MainLoop()

