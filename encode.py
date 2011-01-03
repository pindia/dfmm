from core import *
import os

def encode_object(o):
    return '[%s:%s]\n' % (o.type, o.name) + o.extra_data + '\n\n'

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
    return 
    
if __name__ == '__main__':
    from decode import *
    objects = decode_directory('core')
    encode_objects(objects, '../raw/objects')
