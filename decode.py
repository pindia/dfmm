from core import *
import merge
import re, os, itertools

def decode_file(path):
    ''' Parses a raw file and returns a list of the objects in it '''
    fname = os.path.split(path)[-1]
    objects = []
    data = open(path, 'rt').read().decode('cp437')
    
    pat = re.compile(r'\[([^\[\]]+):([^\[\]]+)\]')

    match = pat.search(data)
    if not match or match.group(1) != 'OBJECT':
        raise Exception('No [OBJECT:<type>] tag found when parsing file %s' % path)
    root_type = match.group(2)
    
    match2 = pat.search(data, pos=match.end())
    if not match2:
        return []
    type = match2.group(1)


    split = re.split(r'\[%s:([^\[\]]+)\]' % type, data)[1:]

    comment = ''
    for name, raw_data in itertools.izip(
            itertools.islice(split, 0, None, 2),
            itertools.islice(split, 1, None, 2)):
        raw_data = raw_data.strip('\n') # Strip  extra newlines from start/end
        
        if comment:
            raw_data = comment + '\n' + raw_data
            comment = ''
        before_last_line, sep, last_line = raw_data.rpartition('\n')
        if sep and '[' not in last_line and ']' not in last_line:
            # If the last line has no tags, assume it's a comment for the next one
            comment = last_line
            raw_data = before_last_line.strip('\n')
        object = Object(fname, type, root_type, name)
        object.extra_data = raw_data
        objects.append(object)

   
    return objects
   
def decode_directory(path):
    ''' Parses all files in a directory as raw files and returns all the objects '''
    objects = []
    for f in sorted(os.listdir(path)):
        if f.endswith('.txt') and 'readme' not in f.lower():
            objects.extend(decode_file(os.path.join(path, f)))
    return DataSet(objects, included_files=os.listdir(path))

def decode_core():
    return decode_directory('core')
    
def get_mod_list():
    return [f for f in os.listdir('mods') if f.endswith('.dfmod')]
    
  
def decode_mod_headers(path):
    ''' Returns only the header information from the mod as a dictionary '''
    d = {}
    f = open(path, 'rt')
    for line in f:
        if '!DFMM' not in line:
            return False
        dfmm, keyword, value = line.strip().split('|', 2)
        if keyword in ['ADD', 'MODIFY', 'DELETE']:
            # We have reached the end of the header; now we have a "real" command
            return d
        else:
            d[keyword.lower()] = value
    return d
    
    
    
def decode_mod(path, base_dataset):
    f = open(path, 'rt')
    commands = f.read().decode('cp437').split('!DFMM')[1:]
    for command in commands:
        dfmm, keyword, value = command.strip().split('|', 2)
        if keyword == 'NAME':
            mod = Mod(value, path, base_dataset, [])
            continue          
        if keyword not in ['ADD', 'MODIFY', 'DELETE']:
            continue
        dfmm, keyword, filename, root_type, type, name, patch_data = command.strip().split('|', 6)
        o = Object(filename, type, root_type, name)
        if keyword == 'ADD':
            o.extra_data = patch_data
            o.added = True
        elif keyword == 'MODIFY':
            try:
                core_object = base_dataset.get_object(o.root_type,o.type, o.name)
                if not core_object:
                    print 'Error decoding modification to object [%s:%s] in mod %s: object does not exist. Skipping.' % (o.type, o.name, path)
                    continue
                else:
                    # Add the ampersand on the front to prevent stripping of initial tab, if any
                    results = merge.apply_patch_text('&'+core_object.extra_data, patch_data)
                    n = results[1].count(False)
                    t = len(results[1])
                    if n != 0:
                        print 'Warning:  %d/%d modifications to object [%s:%s] in mod %s could not be applied and have been skipped.' % (n, t, o.type, o.name, path)
                    o.extra_data = results[0][1:] # Remove ampersand
            except:
                print 'Error decoding modification to object [%s:%s] in mod %s. Skipping.' % (o.type, o.name, path)
                continue
            o.modified = True
        elif keyword == 'DELETE':
            o.deleted = True
        else:
            continue
        mod.objects.append(o)
    return mod
        
        
   
if __name__ == '__main__': 
    #objects =  decode_file('raw/objects/inorganic_stone_layer.txt')
    #import cProfile
    #cProfile.run('decode_directory("core")','out.dat')
    #print len(objects)
    #print objects[0].extra_data
    core_dataset = decode_core()
    #print decode_mod('mods2/genesis.dfmod', core_dataset)
    #print decode_file('core/item_food.txt')
    print verify_mod_checksum('mods/genesis.dfmod', core_dataset)
    #print decode_all_mods()
    
    #defense_dataset = decode_directory('defense')
    #print core_dataset.difference(defense_dataset)
    