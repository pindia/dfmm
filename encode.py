from core import *
from progress import dummy_callback
import merge
import os
import zipfile

def encode_object(o):
    return ('[%s:%s]\n' % (o.type, o.name) + o.extra_data + '\n\n').encode('cp437')

def encode_objects(objects, targetpath, callback=dummy_callback):
    files = {}
    for object in objects:
        if object.file_name not in files:
            files[object.file_name] = []
        files[object.file_name].append(object)
    callback.set_task_number(len(files))
    for fname, objects in files.items():
        callback.task_started(fname)
        f = open(os.path.join(targetpath, fname), 'wt')
        f.write('%s\n\n' % fname.split('.')[0])
        f.write('[OBJECT:%s]\n\n' % objects[0].root_type)
        f.write(''.join(map(encode_object, objects)))
        f.close()
    callback.done()
        
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
        if not object.patch_cache:
            object.patch_cache = merge.make_patch(core_dataset.get_object(object.root_type, object.type, object.name).extra_data, object.extra_data)
        return 'DFMM|MODIFY|%s|%s' % (id, object.patch_cache)
    if object.deleted:
        return 'DFMM|DELETE|%s|' % id

def encode_mod(mod, overwrite=False, callback=dummy_callback):
    if os.path.exists(mod.path) and not overwrite: # Rename path to avoid overwrite
        pat = '%s-%%d.dfmod' % mod.path.split('.')[0]
        i = 0
        while os.path.exists(pat % i):
            i += 1
        mod.path = pat % i
    f = open(mod.path, 'wt')
    f.write('!DFMM|NAME|%s\n' % mod.name)
    f.write('!DFMM|CHECKSUM|%s\n' % mod.base.checksum())
    if mod.parent:
        f.write('!DFMM|META|%s\n' % os.path.split(mod.parent.path)[-1])
    callback.set_task_number(len(mod.changed_objects))
    for object in mod.changed_objects:
        callback.task_started(str(object))
        try:
            f.write('!'+object_to_dfmm_command(object, mod.base).encode('cp437') + '\n')
        except UnicodeDecodeError:
            print object.type
            print object.name
            print object.extra_data
            raise
    f.close()
    callback.done()
    
def encode_mods(mods, path):
    ''' Encodes a list of mods to a .zip file at path '''
    zf = zipfile.ZipFile(path, 'w')
    for mod in mods:
        zf.write(mod.path)
    zf.close()
    
    
if __name__ == '__main__':
    from decode import *
    objects = decode_directory('core')
    encode_objects(objects, '../raw/objects')
