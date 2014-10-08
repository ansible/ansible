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
        mod, args, to = self.m.parse(dict(action='shell echo hi'))
        assert mod == 'command'
        assert args == dict(
            _raw_params = 'echo hi',
            _uses_shell = True,
        )
        assert to is None

    def test_basic_shell(self):
        mod, args, to = self.m.parse(dict(shell='echo hi'))
        assert mod == 'command'
        assert args == dict(
           _raw_params = 'echo hi',
           _uses_shell = True,
        )
        assert to is None

    def test_basic_command(self):
        mod, args, to = self.m.parse(dict(command='echo hi'))
        assert mod == 'command'
        assert args == dict(
           _raw_params = 'echo hi',
        )
        assert to is None

    def test_shell_with_modifiers(self):
        mod, args, to = self.m.parse(dict(shell='/bin/foo creates=/tmp/baz removes=/tmp/bleep'))
        assert mod == 'command'
        assert args == dict(
           creates     = '/tmp/baz',
           removes     = '/tmp/bleep',
           _raw_params = '/bin/foo',
           _uses_shell = True,
        )
        assert to is None

    def test_normal_usage(self):
        mod, args, to = self.m.parse(dict(copy='src=a dest=b'))
        assert mod == 'copy'
        assert args == dict(src='a', dest='b')
        assert to is None

    def test_complex_args(self):
        mod, args, to = self.m.parse(dict(copy=dict(src='a', dest='b')))
        assert mod == 'copy'
        assert args == dict(src='a', dest='b')
        assert to is None

    def test_action_with_complex(self):
        mod, args, to = self.m.parse(dict(action=dict(module='copy', src='a', dest='b')))
        assert mod == 'copy'
        assert args == dict(src='a', dest='b')
        assert to is None

    def test_action_with_complex_and_complex_args(self):
        mod, args, to = self.m.parse(dict(action=dict(module='copy', args=dict(src='a', dest='b'))))
        assert mod == 'copy'
        assert args == dict(src='a', dest='b')
        assert to is None

    def test_local_action_string(self):
        mod, args, to = self.m.parse(dict(local_action='copy src=a dest=b'))
        assert mod == 'copy'
        assert args == dict(src='a', dest='b')
        assert to is 'localhost' 

