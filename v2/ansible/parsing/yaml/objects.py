class AnsibleBaseYAMLObject(object):
    '''
    the base class used to sub-class python built-in objects
    so that we can add attributes to them during yaml parsing
    
    '''
    _data_source   = None
    _line_number   = None
    _column_number = None

    def get_position_info(self):
        return (self._data_source, self._line_number, self._column_number)

class AnsibleMapping(AnsibleBaseYAMLObject, dict):
    ''' sub class for dictionaries '''
    pass

