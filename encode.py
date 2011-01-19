from core import *
import merge
import os

def encode_object(o):
    return ('[%s:%s]\n' % (o.type, o.name) + o.extra_data + '\n\n').encode('cp437')

def encode_objects(objects, targetpath):
    files = {}
    for object in objects:
        if object.file_name not in files:
            files[object.file_name] = []
        files[object.file_name].append(object)
    for fname, objects in files.items():
        f = open(os.path.join(targetpath, fname), 'wt')
        f.write('%s\n\n' % fname.split('.')[0])
        f.write('[OBJECT:%s]\n\n' % objects[0].root_type)
        f.write(''.join(map(encode_object, objects)))
        f.close()
        
def encode_to_directory(objects, targetpath):
    files = {}
    for object in objects: # Categorize objects into files
        if object.file_name not in files:
            files[object.file_name] = []
        files[object.file_name].append(object)
    modified_files = {}
    for fname, objects in files.items(): # Only bother saving modified files
        if True in [o.added or o.modified or o.deleted for o in objects]:
            modified_files[fname] = objects
    for fname, objects in modified_files.items():
        encode_objects(objects, targetpath)
        

def object_to_dfmm_command(object, core_dataset):
    id = '%s|%s|%s|%s' % (object.file_name, object.root_type, object.type, object.name)
    if object.added:
        return 'DFMM|ADD|%s|%s' % (id, object.extra_data)
    if object.modified:
        return 'DFMM|MODIFY|%s|%s' % (id, merge.make_patch(core_dataset.get_object(object.type, object.name).extra_data, object.extra_data))
    if object.deleted:
        return 'DFMM|DELETE|%s|' % id

def encode_mod(mod, core_dataset):
    f = open(mod.path, 'wt')
    f.write('!DFMM|NAME|%s\n' % mod.name)
    for object in mod.changed_objects:
        try:
            f.write('!'+object_to_dfmm_command(object, core_dataset).encode('cp437') + '\n')
        except UnicodeDecodeError:
            print object.type
            print object.name
            print object.extra_data
            raise
    f.close()
    
    
if __name__ == '__main__':
    from decode import *
    objects = decode_directory('core')
    encode_objects(objects, '../raw/objects')
