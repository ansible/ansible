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

    def test_can_construct_empty_task():
        t = Task()
    
    def test_can_construct_task_with_role():
        pass

    def test_can_construct_task_with_block():
        pass

    def test_can_construct_task_with_role_and_block():
        pass

    def test_can_load_simple_task():
       t = Task.load(basic_shell_task)
       assert t.name == basic_shell_task['name']
       assert t.module == 'shell'
       assert t.args == 'echo hi'

 
