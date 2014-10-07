from yaml.composer import Composer
from yaml.nodes import MappingNode

class AnsibleComposer(Composer):
    def __init__(self):
        self.__mapping_starts = []
        super(Composer, self).__init__()
    def compose_node(self, parent, index):
        # the line number where the previous token has ended (plus empty lines)
        node = Composer.compose_node(self, parent, index)
        if isinstance(node, MappingNode):
            node.__datasource__ = self.name
            try:
                (cur_line, cur_column) = self.__mapping_starts.pop()
            except:
                cur_line = None
                cur_column = None
            node.__line__   = cur_line
            node.__column__ = cur_column
        return node
    def compose_mapping_node(self, anchor):
        # the column here will point at the position in the file immediately
        # after the first key is found, which could be a space or a newline.
        # We could back this up to find the beginning of the key, but this
        # should be good enough to determine the error location.
        self.__mapping_starts.append((self.line + 1, self.column + 1))
        return Composer.compose_mapping_node(self, anchor)

