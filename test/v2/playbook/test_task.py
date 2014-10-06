# TODO: header

from ansible.playbook.task import Task
import unittest

basic_shell_task = dict(
   name  = 'Test Task',
   shell = 'echo hi'
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

    def test_load_simple_task(self):
        t = Task.load(basic_shell_task)
        assert t is not None
        assert t.name == basic_shell_task['name']
        assert t.module == 'shell'
        assert t.args == 'echo hi'

    def test_can_load_action_kv_form(self):
        pass

    def test_can_load_action_complex_form(self):
        pass

    def test_can_load_module_complex_form(self):
        pass 

    def test_local_action_implies_delegate(self):
        pass 
 
    def test_local_action_conflicts_with_delegate(self):
        pass 

    def test_delegate_to_parses(self):
        pass 
