from diff_match_patch import diff_match_patch 

def make_patch(base, data):
    differ = diff_match_patch()
    patches = differ.patch_make(base.strip(), data.strip())
    return differ.patch_toText(patches)
    
def apply_patch_text(base, patch_text):
    differ = diff_match_patch()
    patches = differ.patch_fromText(patch_text)
    return differ.patch_apply(patches, base.strip())


def merge_data(base, current, new):
    ''' Given base (core) data, the current data after previous mods have been applied, and
    the data as specified by another mod, attempts to merge them together'''
    differ = diff_match_patch()
    patches = differ.patch_make(base.strip(), new.strip())
    results = differ.patch_apply(patches, current.strip())
    if False in results[1]:
        return results[0], False # At least one patch failed, abort
    return results[0], True
    
def get_diffs(base, data):
    differ = diff_match_patch()
    diffs = differ.diff_main(base, data)
    differ.diff_cleanupSemantic(diffs)
    return diffs
    
if __name__ == '__main__':
        
    base = '''
    [TAG1]
    [TAG2:100]
    [TAG3]'''
    
    current = '''
    [TAG1]
    [TAG2:97]
    [ADD1]
    [TAG3]'''
    
    new = '''
    [TAG1]
    [TAG2:97]
    [ADD2]
    [TAG3]'''
    
    differ = diff_match_patch()
    patches = differ.diff_main(base.strip(), new.strip())
    
    for op, data in patches:
        print patch
        print differ.match_main(current, patch, 0)
        print
        
    
    #print merge_data(base, current, new)