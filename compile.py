from distutils.core import setup
import py2exe

setup(console=['dfmm.py','editor.py'], options={'py2exe':{'includes':['dbhash'], 'dist_dir':'dist'}})
