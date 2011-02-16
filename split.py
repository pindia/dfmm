#used some code from the WxPython wiki:
#-1.4 Recursively building a list into a wxTreeCtrl (yet another sample) by Rob
#-1.5 Simple Drag and Drop by Titus
#-TraversingwxTree

#tested on wxPython 2.5.4 and Python 2.4, under Windows and Linux

import  string
import  wx

from decode import *
from encode import *

#---------------------------------------------------------------------------

class MyTreeCtrl(wx.TreeCtrl):
    def __init__(self, parent, id, pos, size, style, log):
        wx.TreeCtrl.__init__(self, parent, id, pos, size, style)
        self.log = log

    def Traverse(self, func, startNode):
        """Apply 'func' to each node in a branch, beginning with 'startNode'. """
        def TraverseAux(node, depth, func):
            nc = self.GetChildrenCount(node, 0)
            child, cookie = self.GetFirstChild(node)
            # In wxPython 2.5.4, GetFirstChild only takes 1 argument
            for i in xrange(nc):
                func(child, depth)
                TraverseAux(child, depth + 1, func)
                child, cookie = self.GetNextChild(node, cookie)
        func(startNode, 0)
        TraverseAux(startNode, 1, func)

    def ItemIsChildOf(self, item1, item2):
        ''' Tests if item1 is a child of item2, using the Traverse function '''
        self.result = False
        def test_func(node, depth):
            if node == item1:
                self.result = True

        self.Traverse(test_func, item2)
        return self.result

    def SaveItemsToList(self, startnode):
        ''' Generates a python object representation of the tree (or a branch of it),
            composed of a list of dictionaries with the following key/values:
            label:      the text that the tree item had
            data:       the node's data, returned from GetItemPyData(node)
            children:   a list containing the node's children (one of these dictionaries for each)
        '''
        global list
        list = []

        def save_func(node, depth):
            tmplist = list
            for x in range(depth):
                if type(tmplist[-1]) is not dict:
                    tmplist.append({})
                tmplist = tmplist[-1].setdefault('children', [])

            item = {}
            item['label'] = self.GetItemText(node)
            item['data'] = self.GetItemPyData(node)
            item['icon-normal'] = self.GetItemImage(node, wx.TreeItemIcon_Normal)
            item['icon-selected'] = self.GetItemImage(node, wx.TreeItemIcon_Selected)
            item['icon-expanded'] = self.GetItemImage(node, wx.TreeItemIcon_Expanded)
            item['icon-selectedexpanded'] = self.GetItemImage(node, wx.TreeItemIcon_SelectedExpanded)

            tmplist.append(item)

        self.Traverse(save_func, startnode)
        return list

    def InsertItemsFromList(self, itemlist, parent, insertafter=None, appendafter=False):
        ''' Takes a list, 'itemslist', generated by SaveItemsToList, and inserts
            it in to the tree. The items are inserted as children of the
            treeitem given by 'parent', and if 'insertafter' is specified, they
            are inserted directly after that treeitem. Otherwise, they are put at
            the begining.
            
            If 'appendafter' is True, each item is appended. Otherwise it is prepended.
            In the case of children, you want to append them to keep them in the same order.
            However, to put an item at the start of a branch that has children, you need to
            use prepend. (This will need modification for multiple inserts. Probably reverse
            the list.)

            Returns a list of the newly inserted treeitems, so they can be
            selected, etc..'''
        newitems = []
        for item in itemlist:
            if insertafter:
                node = self.InsertItem(parent, insertafter, item['label'])
            elif appendafter:
                node = self.AppendItem(parent, item['label'])
            else:
                node = self.PrependItem(parent, item['label'])
            self.SetItemPyData(node, item['data'])
            self.SetItemImage(node, item['icon-normal'], wx.TreeItemIcon_Normal)
            self.SetItemImage(node, item['icon-selected'], wx.TreeItemIcon_Selected)
            self.SetItemImage(node, item['icon-expanded'], wx.TreeItemIcon_Expanded)
            self.SetItemImage(node, item['icon-selectedexpanded'], wx.TreeItemIcon_SelectedExpanded)

            newitems.append(node)
            if 'children' in item:
                self.InsertItemsFromList(item['children'], node, appendafter=True)
        return newitems

def OnCompareItems(self, item1, item2):
        t1 = self.GetItemText(item1)
        t2 = self.GetItemText(item2)
        self.log.WriteText('compare: ' + t1 + ' <> ' + t2 + '\n')
        if t1 < t2: return -1
        if t1 == t2: return 0
        return 1


#---------------------------------------------------------------------------

class TestTreeCtrlPanel(wx.Panel):
    def __init__(self, parent, log, mod, original):
        # Use the WANTS_CHARS style so the panel doesn't eat the Return key.
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.log = log
        tID = wx.NewId()

        self.tree = MyTreeCtrl(self, tID, wx.DefaultPosition, wx.DefaultSize,
                                    wx.TR_HAS_BUTTONS | wx.TR_EDIT_LABELS | wx.TR_MULTIPLE, self.log)
        # Example needs some more work to use wx.TR_MULTIPLE

        isize = (16,16)
        il = wx.ImageList(isize[0], isize[1])
        fldridx   = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,  wx.ART_OTHER, isize))
        fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER,isize))
        self.fileidx   = il.Add(wx.ArtProvider_GetBitmap(wx.ART_REPORT_VIEW, wx.ART_OTHER,isize))

        self.tree.SetImageList(il)
        self.il = il
        
        
        types = {}
        self.headers = {}

        self.objects = mod.objects[:] if original else []
        
        for object in mod.objects:
            if object.type not in types:
                types[object.type] = []
            types[object.type].append(object)

        self.root = self.tree.AddRoot("Mod 1" if original else "Mod 2")
        self.tree.SetPyData(self.root, {"type":"container"})
        self.tree.SetItemImage(self.root, fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root, fldropenidx, wx.TreeItemIcon_Expanded)

        for type in sorted(types.keys()):
            child = self.tree.AppendItem(self.root, type)
            self.headers[type] = child
            self.tree.SetPyData(child, {"type":"container"})
            self.tree.SetItemImage(child, fldridx, wx.TreeItemIcon_Normal)
            self.tree.SetItemImage(child, fldropenidx, wx.TreeItemIcon_Expanded)
            if original:
                for object in sorted(types[type], key=lambda o: self.object_title(o)):
                    item = self.tree.AppendItem(child, self.object_title(object))
                    self.tree.SetPyData(item,{"type":"item",'object':object})
                    self.tree.SetItemImage(item, self.fileidx, wx.TreeItemIcon_Normal)
                    self.tree.SetItemImage(item, self.fileidx, wx.TreeItemIcon_Selected)

                    
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

class ModSplitterFrame(wx.Frame):
    def __init__(self, parent, mod, core_dataset):
        wx.Frame.__init__(self, parent, title="Mod Splitter", size=(800, 600))
        log = MyLog()
        self.parent = parent
        self.mod = mod
        self.core_dataset = core_dataset
        
        self.tree1 = TestTreeCtrlPanel(self, log, mod, original=True)
        self.tree2 = TestTreeCtrlPanel(self, log, mod, original=False)
        self.tree1.sibling = self.tree2
        self.tree2.sibling = self.tree1
        
        self.save_button = wx.Button(self, label="Save")
        self.save_button.Bind(wx.EVT_BUTTON, self.save_clicked)
        
        self.name1 = wx.TextCtrl(self, size=(200, 20))
        self.name1.AppendText(mod.name)
        self.name2 = wx.TextCtrl(self, size=(200,20))

        self.header1 = wx.BoxSizer(wx.HORIZONTAL)
        self.header1.Add(wx.StaticText(self, label="Mod 1 name:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.header1.Add(self.name1, 0)
        self.header2 = wx.BoxSizer(wx.HORIZONTAL)
        self.header2.Add(wx.StaticText(self, label="Mod 2 name:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.header2.Add(self.name2, 0)
        
        
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
        
    def info_dialog(self, message, title):
        dialog = wx.MessageDialog(self, message, title, style=wx.OK)
        dialog.ShowModal()
        
    def ok_cancel_dialog(self, message, title):
        dialog = wx.MessageDialog(self, message, title, style=wx.OK|wx.CANCEL)
        return dialog.ShowModal() == wx.ID_OK
        
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
        
        encode_mod(Mod(name1, path1, self.core_dataset, self.tree1.objects), overwrite=True)
        encode_mod(Mod(name2, path2, self.core_dataset, self.tree2.objects))
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
    
    
    frame = ModSplitterFrame(None, decode_mod('mods/kobold-camp.dfmod', core_dataset), core_dataset)
    frame.Show()
    frame.SetSize((800,600))

    app.MainLoop()
