from core import *
import re, os

TYPES = ['ITEM_FOOD','ITEM_SHIELD','SYMBOL','ITEM_TRAPCOMP','ENTITY',
         'ITEM_PANTS','TISSUE_TEMPLATE','REACTION','WORD','BUILDING_WORKSHOP',
         'COLOR','ITEM_SHOES','SHAPE','ITEM_AMMO','ITEM_INSTRUMENT','ITEM_GLOVES',
         'TRANSLATION','BODY','ITEM_ARMOR','ITEM_TOY','COLOR_PATTERN','MATERIAL_TEMPLATE',
         'ITEM_HELM','BODY_DETAIL_PLAN','PLANT','ITEM_WEAPON','ITEM_SIEGEAMMO','INORGANIC',
         'CREATURE_VARIATION','CREATURE']

ONLY_IN_SPECIFIC_TYPES = {'BODY':'BODY',
                          'CREATURE':'CREATURE',
                          'BODY_DETAIL_PLAN':'BODY_DETAIL_PLAN',
                          'ENTITY':'ENTITY',
                          'COLOR':'DESCRIPTOR_COLOR',
                          'TRANSLATION':'LANGUAGE'}

def decode_file(path):
    ''' Parses a raw file and returns a list of the objects in it '''
    fname = os.path.split(path)[-1]
    objects = []
    data = open(path, 'rt').read()
    for raw_tag in re.findall(r'\[[^\[\]]+\]', data):
        tag_data = raw_tag.strip('[]').split(':')
        tag_name = tag_data[0]
        tag_data = tag_data[1:]
        if tag_name == 'OBJECT': # Set the root type
            current_root_type = tag_data[0]
        elif tag_name in TYPES and (tag_name not in ONLY_IN_SPECIFIC_TYPES or ONLY_IN_SPECIFIC_TYPES[tag_name] == current_root_type): # A new object is being defined
            current_type = tag_name
            current_name = tag_data[0]
            current_object = Object(fname, current_type, current_root_type, current_name)
            objects.append(current_object)
        else: # Unrecognized tag; add it to the object's extra data
            current_object.add_data(raw_tag+'\n')
    return objects
   
def decode_directory(path):
    ''' Parses all files in a directory as raw files and returns all the objects '''
    objects = []
    for f in sorted(os.listdir(path)):
        objects.extend(decode_file(os.path.join(path, f)))
    return objects
   
if __name__ == '__main__': 
    #objects =  decode_file('raw/objects/inorganic_stone_layer.txt')
    objects = decode_directory('core')
    print len(objects)
    print objects[0].extra_data
    