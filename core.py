import copy
import merge

class DataSet(object):
    def __init__(self, objects):
        self.objects = objects
        self.objects_map = {}
        for object in self.objects:
            self.objects_map[object.type + object.name] = object
        
    def get_object(self, type, name):
        key = type + name
        if key not in self.objects_map:
            return None
        return self.objects_map[key]
        
    def add_object(self, object):
        self.objects.append(object)
        
    def delete_object(self, object):
        current_object = self.get_object(object.type, object.name)
        if not current_object.modified:
            self.objects.remove(current_object)
            return True
        else:
            return False
    
            
    def apply_mod(self, mod, core_dataset):
        for object in mod.added_objects:
            self.add_object(object)
        for object in mod.modified_objects:
            current_object = self.get_object(object.type, object.name)
            core_object = core_dataset.get_object(object.type, object.name)
            if not current_object.modified:
                current_object.extra_data = object.extra_data
                current_object.modified = True
            else:
                result = merge.merge_data(core_object.extra_data, current_object.extra_data, object.extra_data)
                if result:
                    current_object.extra_data = result
                    current_object.modified = True
                    print 'Merged edit to [%s:%s] from mod %s with prior edits' % (object.type, object.name, mod.name)
                else:
                    print 'Failed to apply edit to [%s:%s] from mod "%s" due to prior edit' % (object.type, object.name, mod.name)
        for object in mod.deleted_objects:
            if not self.delete_object(object):
                print 'Failed to apply deletion of [%s:%s] from mod "%s" due to prior edit' % (object.type, object.name, mod.name)
            
    def apply_mod_for_editing(self, mod):
        for object in mod.objects:
            current_object = self.get_object(object.type, object.name)
            if current_object:
                self.objects.remove(current_object)
            self.objects.append(object)
            
    def difference(self, other):
        ''' Returns a list of objects corresponding to the changes made by the given dataset'''
        my_objects = set(self.objects)
        other_objects = set(other.objects)
        other_filenames = set([o.file_name for o in other.objects])
        changes = []
        for object in other_objects - my_objects: # Added
            o = copy.deepcopy(object)
            o.added = True
            changes.append(o)
        for object in my_objects - other_objects: # Deleted
            if object.file_name not in other_filenames:
                continue # If the other set doesn't have the core file, assume it should be kept
            o = copy.deepcopy(object)
            o.deleted = True
            changes.append(o)
        for object in my_objects:
            other_object = other.get_object(object.type, object.name)
            if other_object and object.extra_data != other_object.extra_data:
                o = copy.deepcopy(object)
                o.modified = True
                o.extra_data = other_object.extra_data
                changes.append(o)
        return changes

class Mod(object):
    ''' A mod object stores only the objects it changes..'''
    def __init__(self, name, path, objects):
        self.name = name
        self.path = path
        self.objects = objects
        
    @property
    def changed_objects(self):
        return [o for o in self.objects if o.added or o.modified or o.deleted]
        
    @property
    def added_objects(self):
        return [o for o in self.objects if o.added]
        
    @property
    def modified_objects(self):
        return [o for o in self.objects if o.modified]
        
    @property
    def deleted_objects(self):
        return [o for o in self.objects if o.deleted]

  

class Object(object):
    def __init__(self, file_name, type, root_type, name):
        self.file_name = file_name
        self.type = type
        self.root_type = root_type
        self.name = name
        self.tags = []
        self.extra_data = ''
        
        self.added = False
        self.modified = False
        self.deleted = False
        
    def add_tag(self, tag):
        self.tags.append(tag)
    def add_data(self, data):
        self.extra_data += data
    def __repr__(self):
        return '%s:%s' % (self.type, self.name)
        
    def __eq__(self, other):
        return self.type == other.type and self.name == other.name
    
    def __hash__(self):
        return hash(self.type + self.name)
        
    def to_dfmm_command(self):
        id = '%s|%s|%s|%s' % (self.file_name, self.root_type, self.type, self.name)
        if self.added:
            return 'DFMM|ADD|%s|%s' % (id, self.extra_data)
        if self.modified:
            return 'DFMM|MODIFY|%s|%s' % (id, self.extra_data)
        if self.deleted:
            return 'DFMM|DELETE|%s|' % id

