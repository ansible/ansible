# TODO: header

from ansible.playbook.task import Task
import unittest

basic_shell_task = dict(
   name  = 'Test Task',
   shell = 'echo hi'
)

kv_shell_task = dict(
   action = 'shell echo hi'
)

class TestTask(unittest.TestCase):

    def setUp(self):
        pass
   
    def tearDown(self):
        pass

    def test_construct_empty_task(self):
        t = Task()
    
    def test_construct_task_with_role(self):
        pass

    def test_construct_task_with_block(self):
        pass

    def test_construct_task_with_role_and_block(self):
        pass

    def test_load_task_simple(self):
        t = Task.load(basic_shell_task)
        assert t is not None
        assert t.name == basic_shell_task['name']
        assert t.action == 'command'
        assert t.args == dict(_raw_params='echo hi', _uses_shell=True)

    def test_load_task_kv_form(self):
        t = Task.load(kv_shell_task)
        print "task action is %s" % t.action
        assert t.action == 'command'
        assert t.args == dict(_raw_params='echo hi', _uses_shell=True)

    def test_task_auto_name(self):
        assert 'name' not in kv_shell_task
        t = Task.load(kv_shell_task)
        #assert t.name == 'shell echo hi'

    def test_task_auto_name_with_role(self):
        pass

    def test_load_task_complex_form(self):
        pass

    def test_can_load_module_complex_form(self):
        pass 

    def test_local_action_implies_delegate(self):
        pass 
 
    def test_local_action_conflicts_with_delegate(self):
        pass 

    def test_delegate_to_parses(self):
        pass

 
