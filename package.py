import zipfile, os

VERSION = "0.7"
EXCLUDE = ['compile', 'package']

# Make source zip
zf = zipfile.ZipFile('releases/dfmm-%s-src.zip' % VERSION, 'w', zipfile.ZIP_DEFLATED)
for fname in os.listdir('.'):
    if fname.endswith('.py') and fname.split('.')[0] not in EXCLUDE:
        zf.write(fname, 'dfmm/%s' % fname)
zf.close()

# Compile and make exe zip
os.system('python compile.py py2exe')
zf = zipfile.ZipFile('releases/dfmm-%s-exe.zip' % VERSION, 'w', zipfile.ZIP_DEFLATED)
dir = os.path.join(os.getcwd(), 'dist')
for base, dirs, files in os.walk(dir):
    for file in files:
        path = os.path.join(os.getcwd(), 'dist', file)
        zf.write(path, os.path.join('dfmm',file))
zf.close()