import wx
import shelve, sys, shutil, traceback
import frame
from decode import *
from editor import *
from split import *
from progress import ProgressDialog, thread_wrapper, dummy_callback


class MainFrame(frame.ExtendedFrame, frame.TreeController):
    
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="DF Mod Manager", size=(500, 300))
        

        def except_hook(type, value, tb):
            self.show_exception_dialog(type, value, tb)
            sys.exit(0)
        
        sys.excepthook = except_hook
        
        
        if not os.path.exists('core'):
            dialog = wx.MessageDialog(self, 'It appears that you are running DFMM for the first time. Are the files currently in your raws folder unmodified?',
                                  'Setup',style=wx.YES|wx.NO)
            if dialog.ShowModal() == wx.ID_YES:
                if not os.path.exists(os.path.join('..','raw','objects')):
                    dialog = wx.MessageDialog(self, 'Unable to find DF files. The "dfmm" folder should be on the same level as "Dwarf Fortress.exe".', style=wx.OK)
                    dialog.ShowModal()
                    sys.exit(0)                    
                shutil.copytree(os.path.join('..','raw','objects'), 'core')
            else:
                dialog = wx.MessageDialog(self, 'Please restore the raw files to their unmodified state and relaunch DFMM. (Backup your changes to another directory for later import)', style=wx.OK)
                dialog.ShowModal()
                sys.exit(0)
                
        if not os.path.exists('mods'):
            os.mkdir('mods')
        
        self.core_dataset = decode_core()
        
        
        self.tree = wx.TreeCtrl(self, wx.ID_ANY, pos=(0,0), size=(-1, -1), style=wx.TR_HAS_BUTTONS)
        
        self.init_image_list()
        self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.toggle_mod)
        self.tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.mod_context_menu)
        self.tree.Bind(wx.EVT_TREE_BEGIN_DRAG, self.begin_drag)
        self.tree.Bind(wx.EVT_TREE_END_DRAG, self.end_drag)
        
        self.mod_db = shelve.open(os.path.join('mods','mods.db'), 'c', writeback=True)
        
        self.reload_mods(initial=True)
        
        self.update_title()

        
        
        self.filemenu = wx.Menu()
        menu_new = self.filemenu.Append(wx.ID_ANY, "&New mod\tCtrl+N","")
        self.filemenu.AppendSeparator()
        menu_merge = self.filemenu.Append(wx.ID_ANY, "&Merge mods\tCtrl+M","")
        menu_install = self.filemenu.Append(wx.ID_ANY, "&Install mods\tCtrl+S","")
        self.filemenu.AppendSeparator()
        menu_exit = self.filemenu.Append(wx.ID_EXIT, "Exit","")
        
        self.Bind(wx.EVT_MENU, self.merge, menu_merge)
        self.Bind(wx.EVT_MENU, self.install, menu_install)
        self.Bind(wx.EVT_MENU, self.new_mod, menu_new)
        self.Bind(wx.EVT_MENU, self.exit, menu_exit)

        self.importmenu = wx.Menu()
        menu_import_dfmod = self.importmenu.Append(wx.ID_ANY, "Import .dfmod","")
        menu_import_dfmod_zip = self.importmenu.Append(wx.ID_ANY, "Import .dfmod zip","")
        menu_import_files = self.importmenu.Append(wx.ID_ANY, "Import from directory","")
        
        self.Bind(wx.EVT_MENU, self.import_dfmod, menu_import_dfmod)
        self.Bind(wx.EVT_MENU, self.import_dfmod_zip, menu_import_dfmod_zip)
        self.Bind(wx.EVT_MENU, self.import_files, menu_import_files)
        
        OPTIONS = [['_merge_changes','Merge changes'],
            ['_partial_merge','Allow partial merge'],
            ['_delete_override','Delete overrides edit'],
            ['_show_numbers','Show detailed change numbers']]
        
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
        
    # Basic methods
    
    @property
    def selected_mod(self):
        if self.tree.GetSelection() == self.root:
            return None
        return self.tree.GetPyData(self.tree.GetSelection())['object']
        #return self.mods[self.listbox.GetFirstSelected()]
        
    @property
    def enabled_mods(self):
        ''' Returns only the enabled mods in the proper order for application '''
        mods = []
        for item in self.item_children(self.root):
            mods.append(self.tree.GetPyData(item)['object'])
            for child in self.item_children(item):
                mods.append(self.tree.GetPyData(child)['object'])
        return [m for m in mods if self.mod_db[m.path]['enabled']]
    
    def mods_checksum(self):
        ''' Computes a checksum of the currently enabled mods and their order '''
        c = sum([mod.checksum() for mod in self.enabled_mods]) # Mod contents
        c += hash(''.join([mod.path for mod in self.enabled_mods])) # Mod ordering
        return c
        

    # Mod loading methods
    
    def reload_mods(self, initial=False, progress=True):
        ''' This method clears the currently loaded mod list and reloads every mod in
        the mods directory. Should be used as rarely as possible due to long execution time'''
        
        dialog = ProgressDialog(self, 'Loading mods', show=progress)
        
        self.mods = []
        notified = False
        mod_headers = {}
        
        # First, let's read the headers of all the mods
        for mod in get_mod_list():
            path = os.path.join('mods', mod)
            mod_headers[path] = decode_mod_headers(path)
            
        dialog.set_task_number(len(mod_headers))
            
        # Now, let's verify the checksums of all the mods and update if needed
        core_checksum = str(self.core_dataset.checksum())
        for mod, headers in mod_headers.items():
            if 'meta' in headers:
                continue # Verify only core files for now
            if headers['checksum'] != core_checksum:
                if not notified:
                    notified = True
                    print 'Updating mods...'
                    self.info_dialog('DFMM has detected a change in your core files. The patches defined in your mods will be re-rolled. Depending on the number and size of your mods, this may take several minutes. Watch the console window for possible notifications about changes that cannot be applied to the new files.', 'Core files changed')
                print 'Processing mod "%s"...' % mod
                mod = decode_mod(mod, self.core_dataset)
                encode_mod(mod, overwrite=True)
        if notified:
            print 'Done updating mods.'
            
            
        # First, process the normal mods. This makes them available for the
        # metamods to reference
        for path, headers in mod_headers.items():
            if 'meta' not in headers:
                dialog.task_started(label=headers['name'])
                self.load_normal_mod(path)
                
        # Then, the metamods
        for path, headers in mod_headers.items():
            if 'meta' in headers:
                dialog.task_started(label=headers['name'])
                self.load_metamod(path, headers)
                
        dialog.done()
                
        self.update_mod_list()
        self.update_title()
        
    def load_normal_mod(self, path):
        mod = decode_mod(path, self.core_dataset)
        self.mods.append(mod)
        return mod
        
    def load_metamod(self, path, headers=None):
        if not headers:
            headers = decode_mod_headers(path)
        parent_path = headers['meta']
        parent = [mod for mod in self.mods if os.path.split(mod.path)[-1] == parent_path]
        if len(parent) == 0:
            self.warning_dialog('The metamod "%s" could not be loaded because the the file it references, "%s", was not found.' % (path, parent_path), 'Mod not loaded')
            return
        parent = parent[0]
        dataset = copy.deepcopy(self.core_dataset)
        dataset.apply_mod(parent)
        dataset.strip_object_status()
        mod = decode_mod(path, dataset)
        mod.parent = parent
        self.mods.append(mod)
        return mod
    
            
        
    
    def update_mod_list(self):
        ''' Adds loaded mods to the main mod tree. Can be called more frequently than
        update_mod_list, but still introduces visible flashing. Does not reload mods.'''
        
        # Save the currently expanded items
        expanded = []

        if hasattr(self, 'root'): # If we have already set up the tree, save the items
            for item in self.item_children(self.root):
                if self.tree.IsExpanded(item):
                    expanded.append(self.tree.GetItemPyData(item)['object'].path)
        
        self.tree.DeleteAllItems()
        self.add_root("Mods")
        for mod in self.mods:
            if mod.path not in self.mod_db: # Make sure it's in the database
                self.mod_db[mod.path] = {'enabled':False, 'index':0}
        self.mods.sort(key=lambda m: self.mod_db[m.path]['index'])
        
        
        # The common logic for both normal and meta mods
        def process_mod(i, mod, parent):
            if self.mod_db['_show_numbers']:
                item = self.add_item(parent, '%s (%d/%d/%d)' % (mod.name, len(mod.added_objects), len(mod.modified_objects), len(mod.deleted_objects)), mod)
            else:
                item = self.add_item(parent, '%s (%d)' % (mod.name, len(mod.objects)), mod)
            mod.item = item
            if self.mod_db[mod.path]['enabled']:
                self.tree.SetItemImage(item, self.img_tick, wx.TreeItemIcon_Normal)
            else:
                self.tree.SetItemImage(item, self.img_cross, wx.TreeItemIcon_Normal)
            self.mod_db[mod.path]['index'] = i
        
        for i, mod in enumerate(self.mods):
            if not mod.parent:
                process_mod(i, mod, self.root)
                for j, metamod in enumerate([m for m in self.mods if m.parent == mod]):
                    process_mod(j, metamod, mod.item)
            if mod.path in expanded:
                self.tree.Expand(mod.item)
            
            
        self.tree.Expand(self.root)
        self.mod_db.sync()


    # Event handlers
    
    
    def begin_drag(self, event):
        self.drag_item = event.GetItem()
        if self.drag_item != self.root:
            event.Allow()
            
    def end_drag(self, event):
        target = event.GetItem()
        if not hasattr(self, 'drag_item') or not self.drag_item.IsOk() or not target.IsOk():
            return
        target_mod = self.tree.GetPyData(target)['object']
        mod = self.tree.GetPyData(self.drag_item)['object']
        if mod.parent != target_mod.parent:
            if mod.parent:
                self.warning_dialog('A metamod may not be moved out of its parent.','Cannot move')
            else:
                self.warning_dialog('A normal mod may not be moved into a metamod position.','Cannot move')
            return
        # Perform the swap
        i = self.mod_db[mod.path]['index']
        self.mod_db[mod.path]['index'] = self.mod_db[target_mod.path]['index']
        self.mod_db[target_mod.path]['index'] = i
        self.mod_db.sync()
        self.update_mod_list()
        self.dirty = True

        
        
        
    def mod_context_menu(self, event):
        self.tree.SelectItem(event.GetItem())
        mod = self.selected_mod
        if not mod:
            return
        
        menu = wx.Menu()
        
        menu_enable = menu.Append(wx.ID_ANY, "Enable mod","", kind=wx.ITEM_CHECK)
        if self.mod_db[mod.path]['enabled']:
            menu_enable.Check()
        menu.AppendSeparator()
        menu_export_dfmod = menu.Append(wx.ID_ANY, "Export .dfmod","")
        menu_export_dfmod_zip = menu.Append(wx.ID_ANY, "Export .dfmod zip","")
        menu_export_files = menu.Append(wx.ID_ANY, "Export to directory","")
        menu.AppendSeparator()
        menu_edit = menu.Append(wx.ID_ANY, "&Edit mod","")
        menu_split = menu.Append(wx.ID_ANY, "&Split mod","")
        menu_rename = menu.Append(wx.ID_ANY, "&Rename mod","")
        menu_delete = menu.Append(wx.ID_ANY, "&Delete mod","")
        
        menu.AppendSeparator()
        menu_meta = menu.Append(wx.ID_ANY, "&Create metamod","")
        menu_import_meta = menu.Append(wx.ID_ANY, "&Import metamod","")

        if mod.meta:
            menu_import_meta.Enable(False)
            menu_meta.Enable(False)
            menu_export_dfmod_zip.Enable(False)
            menu_export_files.Enable(False)
        
        self.Bind(wx.EVT_MENU, self.toggle_mod, menu_enable)
        self.Bind(wx.EVT_MENU, self.export_dfmod, menu_export_dfmod)
        self.Bind(wx.EVT_MENU, self.export_dfmod_zip, menu_export_dfmod_zip)
        self.Bind(wx.EVT_MENU, self.export_files, menu_export_files)
        self.Bind(wx.EVT_MENU, self.split_mod, menu_split)
        self.Bind(wx.EVT_MENU, self.edit_mod, menu_edit)
        self.Bind(wx.EVT_MENU, self.create_metamod, menu_meta)
        self.Bind(wx.EVT_MENU, self.import_metamod, menu_import_meta)
        self.Bind(wx.EVT_MENU, self.rename_mod, menu_rename)
        self.Bind(wx.EVT_MENU, self.delete_mod, menu_delete)
        
        self.PopupMenu(menu, event.GetPoint())
        
    def toggle_mod(self, event):
        mod = self.selected_mod
        if not mod:
            return
        if self.mod_db[mod.path]['enabled']:
            self.disable_mod(mod)
        else:
            self.enable_mod(mod)
        self.update_title()
            
    def enable_mod(self, mod):
        self.mod_db[mod.path]['enabled'] = True
        self.tree.SetItemImage(mod.item, self.img_tick, wx.TreeItemIcon_Normal)
        for other_mod in self.mods:
            if mod.parent == other_mod:
                self.enable_mod(other_mod)
        
    def disable_mod(self, mod):
        self.mod_db[mod.path]['enabled'] = False
        self.tree.SetItemImage(mod.item, self.img_cross, wx.TreeItemIcon_Normal)
        for other_mod in self.mods:
            if other_mod.parent == mod:
                self.disable_mod(other_mod)
                
        
    def new_mod(self, event):
        name = self.text_entry_dialog('Enter name for new mod', 'New mod')
        if name:
            fname = encode_filename(name)
            encode_mod(Mod(name, os.path.join('mods', fname), self.core_dataset, []))
            self.reload_mods()
            
    def rename_mod(self, event):
        mod = self.selected_mod
        name = self.text_entry_dialog('Enter new name for "%s"' % mod.name, 'Rename mod', mod.name)
        if name:
            mod.name = name
            encode_mod(mod, overwrite=True)
            self.update_mod_list()
            
    def create_metamod(self, event):
        mod = self.selected_mod
        name = self.text_entry_dialog('Enter name for meta mod', 'New mod', default=mod.name + ': ')
        if name:
            fname = encode_filename(name)
            path = str(os.path.join('mods', fname))
            encode_mod(Mod(name, path, self.core_dataset, [], parent=mod))
            self.reload_mods()
            
    def import_metamod(self, event):
        mod = self.selected_mod
        if self.ok_cancel_dialog('The "import metamod" command is very specialized. Only use it if:\n\n1. You have an existing mod that you have already imported and have selected this option from\n2.You have made modifications to the raw files of this mod that are not present in the previous import\n3. You wish to import these changes as a metamod to the existing mod. \n\nYou will need to locate the modified files in the next dialog. Proceed?', 'Import metamod'):
            dialog = wx.DirDialog(self, 'Select directory', style=wx.DD_DIR_MUST_EXIST)
            if dialog.ShowModal() == wx.ID_OK:
                path = dialog.GetPath()
                name = self.text_entry_dialog('Enter name for imported metamod', 'Import metamod', default=mod.name + ': ')
                if name:
                    parent_dataset = copy.deepcopy(self.core_dataset)
                    parent_dataset.apply_mod(mod)
                    parent_dataset.strip_object_status()
                    mod_dataset = decode_directory(path)
                    
                    fname = encode_filename(name)
                    save_path = str(os.path.join('mods', fname))
                                        
                    metamod = Mod(name, save_path, parent_dataset, parent_dataset.difference(mod_dataset), parent=mod)                    
                    encode_mod(metamod)
                    
                    self.reload_mods()
                
    def split_mod(self, event):
        mod = self.selected_mod
        frame = ModSplitterFrame(self, mod, self.core_dataset)
        frame.Show()
        frame.SetSize((800,600))

        
    def edit_mod(self, event):
        mod = self.selected_mod
        frame = ModEditorFrame(self)
        frame.load_mod(mod)
        frame.Show()
        
    def delete_mod(self, event):
        mod = self.selected_mod
        if [m for m in self.mods if m.parent == mod]:
            self.warning_dialog('Cannot delete "%s" because it has metamods. Delete them first.' % mod.name, 'Delete failed')
            return
        dialog = wx.MessageDialog(self, 'Are you sure you want to delete "%s"?' % mod.name,
                                  'Delete mod',style=wx.OK|wx.CANCEL)
        if dialog.ShowModal() == wx.ID_OK:
            os.remove(mod.path)
            del self.mod_db[mod.path]
        self.reload_mods()
        
    def export_dfmod(self, event):
        mod = self.selected_mod
        dialog = wx.FileDialog(self, 'Select File', wildcard='*.dfmod', style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            shutil.copy(mod.path, path)
            
    def export_dfmod_zip(self, event):
        mod = self.selected_mod
        dialog = wx.FileDialog(self, 'Select File', wildcard='*.zip', style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            mods = [mod]
            for m in self.mods:
                if m.parent == mod:
                    mods.append(m)
            encode_mods(mods, path)
            
    def export_files(self, event):
        mod = self.selected_mod
        dialog = wx.DirDialog(self, 'Select directory')
        if dialog.ShowModal() == wx.ID_OK:
            dataset = copy.deepcopy(self.core_dataset)
            dataset.apply_mod(mod)
            path = dialog.GetPath()
            encode_to_directory(dataset.objects, path)
        
    def import_dfmod(self, event):
        dialog = wx.FileDialog(self, 'Select File', wildcard='*.dfmod')
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            try:
                mod = decode_mod(path, self.core_dataset)
                fname = encode_filename(mod.name)
                mod.path = os.path.join('mods', fname)
                encode_mod(mod)
                self.reload_mods()
            except:
                self.show_current_exception()
                
    def import_dfmod_zip(self, event):
        dialog = wx.FileDialog(self, 'Select File', wildcard='*.zip')
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            try:
                zf = zipfile.ZipFile(path)
                paths = [name for name in zf.namelist() if name.endswith('.dfmod')]
                if not paths:
                    self.warning_dialog('No .dfmod files found in the selected zip file','Import failed')
                    return
                mod_headers = []
                for path in paths:
                    mod_headers.append(decode_mod_headers(zf.open(path)))
                for path, headers in zip(paths, mod_headers):
                    if 'meta' not in headers:
                        mod = self.load_normal_mod(zf.open(path))
                        fname = path_to_filename(path)
                        mod.path = os.path.join('mods', fname)
                        encode_mod(mod)
                for path, headers in zip(paths, mod_headers):
                    if 'meta' in headers:
                        mod = self.load_metamod(zf.open(path), headers)
                        fname = path_to_filename(path)
                        if mod:
                            mod.path = os.path.join('mods', fname)
                            encode_mod(mod)
                self.reload_mods()
            except:
                self.show_current_exception()        
        
    def import_files(self, event):
        dialog = wx.DirDialog(self, 'Select directory', style=wx.DD_DIR_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            dialog = wx.TextEntryDialog(self, 'Enter name for imported mod', 'Import mod', '')
            if dialog.ShowModal() == wx.ID_OK:
                name = dialog.GetValue()
                fname = encode_filename(name)
                dialog1 = ProgressDialog(self, 'Importing mod')
                dialog2 = ProgressDialog(self, 'Saving .dfmod')
                def process():
                    try:
                        mod_dataset = decode_directory(path, callback=dialog1)
                        mod = Mod(name, os.path.join('mods', fname), self.core_dataset, self.core_dataset.difference(mod_dataset))
                        encode_mod(mod, callback=dialog2)
                    except:
                        self.show_current_exception()
                        dialog1.Close()
                        dialog2.Close()
                    self.reload_mods()
                thread_wrapper(process)()

           
    
        
    def merge_selected_mods(self, callback=dummy_callback):
        # Common logic for both normal and meta mods

        dataset = copy.deepcopy(self.core_dataset)
        mods = self.enabled_mods
        callback.set_task_number(len(mods))
        for mod in self.enabled_mods:
            callback.task_started(mod.name)
            dataset.apply_mod(mod,
                                merge_changes=self.mod_db['_merge_changes'],
                                partial_merge=self.mod_db['_partial_merge'],
                                delete_override=self.mod_db['_delete_override'])
        callback.done()
        return dataset
        
    def install(self, event):
        print 'Installing mods'
        print '-' * 20
        dataset = self.merge_selected_mods(callback=ProgressDialog(self, 'Merging mods'))
        path = os.path.join('..','raw','objects')
        current_files = os.listdir(path)
        for f in current_files:
            if os.path.isfile(os.path.join(path, f)):
                os.remove(os.path.join(path, f))
        encode_objects(dataset.objects, path, callback=ProgressDialog(self, 'Installing data'))
        self.last_checksum = self.mods_checksum()
        print 'Install complete'
        
    def merge(self, event):
        name = self.text_entry_dialog(
            'The enabled mods will be merged together to form one new mod.\nThe original mods will be kept.\nMerge settings will be followed the same way as installation.\n\nEnter name for new mod:',
            'Merge mods')
        if name:
            fname = encode_filename(name)
            print 'Merging mods'
            print '-' * 20
            dataset = self.merge_selected_mods()
            mod = Mod(name, os.path.join('mods', fname), self.core_dataset, self.core_dataset.difference(dataset))
            encode_mod(mod)
            print 'Merge complete'
            self.reload_mods()
        
    def exit(self, event):
        self.Close(True)
        
    def toggle_option(self, option):
        def perform_toggle(event):
            self.mod_db[option] = not self.mod_db[option]
            self.options_menu[option].Check(self.mod_db[option])
            self.mod_db.sync()
            if option == '_show_numbers':
                self.update_mod_list()
        return perform_toggle
    
    def set_checksum(self, c):
        self.mod_db['_checksum'] = c
        self.mod_db.sync()
        self.update_title()
        
    def update_title(self):
        if self.last_checksum != self.mods_checksum():
            self.SetTitle('DF Mod Manager (uninstalled changes)')
        else:
            self.SetTitle('DF Mod Manager')

        
    def get_checksum(self):
        if '_checksum' not in self.mod_db:
            self.last_checksum = 0
        return self.mod_db['_checksum']
        
    last_checksum = property(get_checksum, set_checksum)
        
if __name__ == '__main__':
    app = wx.App(False)
    frame = MainFrame(None)
    
    
    frame.Show()
    app.MainLoop()

