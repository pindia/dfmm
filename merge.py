from diff_match_patch import diff_match_patch 

def merge_data(base, current, new):
    ''' Given base (core) data, the current data after previous mods have been applied, and
    the data as specified by another mod, attempts to merge them together'''
    differ = diff_match_patch()
    patches = differ.patch_make(base.strip(), new.strip())
    print map(str, patches)
    results = differ.patch_apply(patches, current.strip())
    if False in results[1]:
        print results[1]
        return None # At least one patch failed, abort
    return results[0]
    
if __name__ == '__main__':
        
    base = '''
    [TAG1]
    [TAG2]
    [TAG3]'''
    
    current = '''
    [TAGA]
    [TAG2]
    [TAG3]'''
    
    new = '''
    [TAG1]
    [TAG2]
    [ADDED2]
    [TAG3]'''
    
    print merge_data(base, current, new)