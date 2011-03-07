#used some code from the WxPython wiki:
#-1.4 Recursively building a list into a wxTreeCtrl (yet another sample) by Rob
#-1.5 Simple Drag and Drop by Titus
#-TraversingwxTree

#tested on wxPython 2.5.4 and Python 2.4, under Windows and Linux

import  string
import  wx

import frame
from decode import *
from encode import *

#---------------------------------------------------------------------------

class TreeCtrlPanel(wx.Panel, frame.TreeController):
    def __init__(self, parent, log, mod, original):
        # Use the WANTS_CHARS style so the panel doesn't eat the Return key.
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.log = log
        tID = wx.NewId()

        self.tree = wx.TreeCtrl(self, tID, wx.DefaultPosition, wx.DefaultSize,
                                    wx.TR_HAS_BUTTONS | wx.TR_EDIT_LABELS | wx.TR_MULTIPLE)

        self.init_image_list()
        
        
        types = {}
        self.headers = {}

        self.objects = mod.objects[:] if original else []
        
        for object in mod.objects:
            if object.type not in types:
                types[object.type] = []
            types[object.type].append(object)

        self.add_root("Mod 1" if original else "Mod 2")

        for type in sorted(types.keys()):
            child = self.add_folder(self.root, type)
            self.headers[type] = child
            if original:
                for object in sorted(types[type], key=lambda o: self.object_title(o)):
                    self.add_item(child, self.object_title(object))

                    
        self.tree.Expand(self.root)
        
        self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.move_items)
        self.tree.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.collapse_sibling)
        self.tree.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.expand_sibling)

    def object_title(self, object):
        action = ''
        if object.added:
            action = 'Add'
        if object.modified:
            action = 'Modify'
        if object.deleted:
            action = 'Delete'
        return '%s: %s' % (action, object.name)
        

    def move_items(self, event):
        items = self.tree.GetSelections()
        child_items = []
        for item in items:
            if self.tree.ItemHasChildren(item):
                i, cookie = self.tree.GetFirstChild(item)
                while i.IsOk():
                    child_items.append(i)
                    i, cookie = self.tree.GetNextChild(item, cookie) 
        for item in items + child_items:
            if self.tree.ItemHasChildren(item):
                continue
            data = self.tree.GetItemPyData(item)
            if 'object' not in data:
                continue
            object = data['object']
            self.objects.remove(object)
            self.sibling.objects.append(object)
            self.tree.Delete(item)
            folder = self.sibling.headers[object.type]
            newitem = self.sibling.tree.AppendItem(folder , self.object_title(object))
            self.tree.SetPyData(newitem,{"type":"item",'object':object})
            self.tree.SetItemImage(newitem, self.fileidx, wx.TreeItemIcon_Normal)
            self.tree.SetItemImage(newitem, self.fileidx, wx.TreeItemIcon_Selected)
            self.sibling.tree.Expand(folder)
            
    def expand_sibling(self, event):
        folder = self.sibling.headers[self.tree.GetItemText(event.Item)]
        if not self.sibling.tree.IsExpanded(folder):
            self.sibling.tree.Expand(folder)

    def collapse_sibling(self, event):
        folder = self.sibling.headers[self.tree.GetItemText(event.Item)]
        if self.sibling.tree.IsExpanded(folder):
            self.sibling.tree.Collapse(folder)

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.tree.SetDimensions(0, 0, w, h)


#---------------------------------------------------------------------------

class MyLog:
    def __init__(self):
        pass
    def WriteText(self, text):
        print text

class ModSplitterFrame(frame.ExtendedFrame):
    def __init__(self, parent, mod, core_dataset):
        wx.Frame.__init__(self, parent, title="Mod Splitter", size=(800, 600))
        log = MyLog()
        self.parent = parent
        self.mod = mod
        self.core_dataset = core_dataset
        
        self.tree1 = TreeCtrlPanel(self, log, mod, original=True)
        self.tree2 = TreeCtrlPanel(self, log, mod, original=False)
        self.tree1.sibling = self.tree2
        self.tree2.sibling = self.tree1
        
        self.save_button = wx.Button(self, label="Save")
        self.save_button.Bind(wx.EVT_BUTTON, self.save_clicked)
        
        self.name1 = wx.TextCtrl(self, size=(200, 20))
        self.name1.AppendText(mod.name)
        self.name2 = wx.TextCtrl(self, size=(200,20))
        
        self.meta_checkbox = wx.CheckBox(self)
        if self.mod.parent:
            self.meta_checkbox.SetValue(True)
            self.meta_checkbox.Enable(False)

        self.header1 = wx.BoxSizer(wx.HORIZONTAL)
        self.header1.Add(wx.StaticText(self, label="Mod 1 name:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.header1.Add(self.name1, 0)
        self.header2 = wx.BoxSizer(wx.HORIZONTAL)
        self.header2.Add(wx.StaticText(self, label="Mod 2 name:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.header2.Add(self.name2, 0)
        self.header2.Add(wx.StaticText(self, label="Meta:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.header2.Add(self.meta_checkbox, 0, wx.ALIGN_CENTER_VERTICAL)

        
        
        self.mod1 = wx.BoxSizer(wx.VERTICAL)
        self.mod1.Add(self.header1, 0, wx.ALIGN_CENTER)
        self.mod1.Add(self.tree1, 1, wx.EXPAND)
        self.mod2 = wx.BoxSizer(wx.VERTICAL)
        self.mod2.Add(self.header2, 0, wx.ALIGN_CENTER)
        self.mod2.Add(self.tree2, 1, wx.EXPAND)
        self.horizontal = wx.BoxSizer(wx.HORIZONTAL)
        self.horizontal.Add(self.mod1, 1, wx.EXPAND)
        self.horizontal.Add(self.mod2, 1, wx.EXPAND)
        self.vertical = wx.BoxSizer(wx.VERTICAL)
        self.vertical.Add(self.horizontal, 1, wx.EXPAND)
        self.vertical.Add(self.save_button, 0, wx.ALIGN_CENTER)
        self.SetSizerAndFit(self.vertical)
        
    def save_clicked(self, event):
        name1 = self.name1.GetValue()
        name2 = self.name2.GetValue()
        path1 = os.path.join('mods',encode_filename(name1))
        path2 = os.path.join('mods',encode_filename(name2))
        
        if not name1 or not name2:
            self.info_dialog('You must enter names for both output mods.','Enter names')
            return
        if path1 == self.mod.path:
            if not self.ok_cancel_dialog('Warning: you have entered the same name for the first output mod as the original mod. Are you sure you want to overwrite the original mod?', 'Overwrite mod?'):
                return
        
        encode_mod(Mod(name1, path1, self.core_dataset, self.tree1.objects, self.mod.parent), overwrite=True)
        mod2parent = self.mod.parent
        if not mod2parent and self.meta_checkbox.IsChecked():
            mod2parent = self.mod
        encode_mod(Mod(name2, path2, self.core_dataset, self.tree2.objects, mod2parent))
        print 'Mod split.'
        if self.parent:
            self.parent.reload_mods()
        self.Close()






# end of class MyApp

if __name__ == "__main__":
    '''class MyApp(wx.App):
        def OnInit(self):
            wx.InitAllImageHandlers()
            core = decode_core()
            mod = decode_mod('mods/dwarf-mustard.dfmod', core)
            frame = ModSplitterFrame(None, mod)
            #self.SetTopWindow(frame_1)
            frame.Show(1)
            return 1
    app = MyApp(0)
    app.MainLoop()'''
    app = wx.App(False)
    core_dataset = decode_core()
    
    
    frame = ModSplitterFrame(None, decode_mod('mods/edit-steel.dfmod', core_dataset), core_dataset)
    frame.Show()
    frame.SetSize((800,600))

    app.MainLoop()
