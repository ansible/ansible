from ansible.compat.tests import unittest
from ansible.module_utils.network.common.parsing import Conditional

test_results = ['result_1', 'result_2', 'result_3']
c1 = Conditional('result[1] == result_2')
c2 = Conditional('result[2] not == result_2')
c3 = Conditional('result[0] neq not result_1')

class TestNotKeyword(unittest.TestCase):
    def test_negate_instance_variable_assignment(self):
        assert c1.negate == False and c2.negate == True

    def test_key_value_instance_variable_assignment(self):
        c1_assignments = c1.key == 'result[1]' and c1.value == 'result_2'
        c2_assignments = c2.key == 'result[2]' and c2.value == 'result_2'
        assert c1_assignments and c2_assignments

    def test_conditionals_w_not_keyword(self):
        assert c1(test_results) and c2(test_results) and c3(test_results)

if __name__ == '__main__':
    unittest.main()
