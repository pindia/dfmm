
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

