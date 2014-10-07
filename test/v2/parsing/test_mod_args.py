# TODO: header

from ansible.parsing.mod_args import ModuleArgsParser
import unittest

class TestModArgsDwim(unittest.TestCase):

    def setUp(self):
        self.m = ModuleArgsParser()
        pass
   
    def tearDown(self):
        pass

    def test_action_to_shell(self):
        mod, args, to = self.m.parse('action', 'shell echo hi')
        assert mod == 'shell'
        assert args == dict(
            free_form = 'echo hi',
            use_shell = True
        )
        assert to is None

    def test_basic_shell(self):
        mod, args, to = self.m.parse('shell', 'echo hi')
        assert mod == 'shell'
        assert args == dict(
           free_form = 'echo hi',
           use_shell = True
        )
        assert to is None

    def test_basic_command(self):
        mod, args, to = self.m.parse('command', 'echo hi')
        assert mod == 'command'
        assert args == dict(
           free_form = 'echo hi',
           use_shell = False
        )
        assert to is None

    def test_shell_with_modifiers(self):
        mod, args, to = self.m.parse('shell', '/bin/foo creates=/tmp/baz removes=/tmp/bleep')
        assert mod == 'shell'
        assert args == dict(
           free_form = 'echo hi',
           use_shell = False,
           creates   = '/tmp/baz',
           removes   = '/tmp/bleep'
        )
        assert to is None

    def test_normal_usage(self):
        mod, args, to = self.m.parse('copy', 'src=a dest=b')
        assert mod == 'copy'
        assert args == dict(src='a', dest='b')
        assert to is None

    def test_complex_args(self):
        mod, args, to = self.m.parse('copy', dict(src=a, dest=b))
        assert mod == 'copy'
        assert args == dict(src = 'a', dest = 'b')
        assert to is None

    def test_action_with_complex(self):
        mod, args, to = self.m.parse('action', dict(module='copy',src='a',dest='b'))
        assert mod == 'action'
        assert args == dict(src = 'a', dest = 'b')
        assert to is None

    def test_local_action_string(self):
        mod, args, to = self.m.parse('local_action', 'copy src=a dest=b')
        assert mod == 'copy'
        assert args == dict(src=a, dest=b)
        assert to is 'localhost' 


    
   
