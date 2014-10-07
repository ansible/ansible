from yaml.constructor import Constructor
from ansible.parsing.yaml.objects import AnsibleMapping

class AnsibleConstructor(Constructor):
    def construct_yaml_map(self, node):
        data = AnsibleMapping()
        yield data
        value = self.construct_mapping(node)
        data.update(value)
        data._line_number   = value._line_number
        data._column_number = value._column_number
        data._data_source   = value._data_source

    def construct_mapping(self, node, deep=False):
        ret = AnsibleMapping(super(Constructor, self).construct_mapping(node, deep))
        ret._line_number   = node.__line__
        ret._column_number = node.__column__
        ret._data_source   = node.__datasource__
        return ret

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:map',
    AnsibleConstructor.construct_yaml_map)

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:python/dict',
    AnsibleConstructor.construct_yaml_map)

