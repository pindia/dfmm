import wx
from decode import *
from editor import *

class MainFrame(wx.Frame):
    
    def update_mod_list(self):
        self.mods = decode_all_mods()
        self.listbox.DeleteAllItems()
        for mod in self.mods:
            #i = self.listbox.InsertStringItem(0, mod.name)
            #print i
            print mod.name
            self.listbox.Append((mod.name, len(mod.added_objects), len(mod.modified_objects), len(mod.deleted_objects)))
    
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="DF Mod Manager", size=(400, 300))
        
        self.core_dataset = decode_core()
        
        
        self.listbox = wx.ListCtrl(self, wx.ID_ANY, pos=(0,0), size=(-1, -1), style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_HRULES|wx.LC_SINGLE_SEL)
        self.listbox.InsertColumn(0, 'Name')
        self.listbox.InsertColumn(1, 'Added')
        self.listbox.InsertColumn(2, 'Modified')
        self.listbox.InsertColumn(3, 'Deleted')
        #self.listbox.SetColumnWidth(0, 100)
        
        self.update_mod_list()
        
        self.filemenu = wx.Menu()
        menu_save = self.filemenu.Append(wx.ID_ANY, "&Install","")
        #menu_save_exit = self.filemenu.Append(wx.ID_OPEN, "Save and &exit","")
        #menu_exit = self.filemenu.Append(wx.ID_EXIT, "Exit without saving","")
        
        #self.Bind(wx.EVT_MENU, self.save, menu_save)
        
        self.objectmenu = wx.Menu()
        menu_new = self.objectmenu.Append(wx.ID_ANY, "&New mod","")
        menu_edit = self.objectmenu.Append(wx.ID_ANY, "&Edit mod","")
        menu_delete = self.objectmenu.Append(wx.ID_ANY, "&Delete mod","")
        
        self.Bind(wx.EVT_MENU, self.edit_mod, menu_edit)
        
        

        
        self.importmenu = wx.Menu()
        menu_import_dfmod = self.importmenu.Append(wx.ID_ANY, "Import .dfmod","")
        menu_import_files = self.importmenu.Append(wx.ID_ANY, "Import files","")
        
        
        #self.Bind(wx.EVT_MENU, self.revert_object, menu_revert)

        
        menuBar = wx.MenuBar()
        menuBar.Append(self.filemenu,"&File")
        menuBar.Append(self.objectmenu,"&Mod")
        menuBar.Append(self.importmenu,"&Import")
        self.SetMenuBar(menuBar)
        
    def edit_mod(self, event):
        i = self.listbox.GetFirstSelected()
        mod = self.mods[i]
        frame = ModEditorFrame(self, self.core_dataset, mod)
        frame.Show()
        
app = wx.App(False)
frame = MainFrame(None)

frame.Show()
app.MainLoop()

