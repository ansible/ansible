from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.parser import Parser
from yaml.resolver import Resolver

from ansible.parsing.yaml.composer import AnsibleComposer
from ansible.parsing.yaml.constructor import AnsibleConstructor

class AnsibleLoader(Reader, Scanner, Parser, AnsibleComposer, AnsibleConstructor, Resolver):
    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        AnsibleComposer.__init__(self)
        AnsibleConstructor.__init__(self)
        Resolver.__init__(self)

