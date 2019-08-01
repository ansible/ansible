from __future__ import (absolute_import, division, print_function)
from units.compat import unittest
from ansible.modules.system.process import validate_id_field_pattern, \
    validate_stat_field, validate_choice_field, \
    validate_number_range, INTEGER_RANGE_PATTERN, INTEGER_RANGE_FORMAT, \
    DOUBLE_RANGE_PATTERN, DOUBLE_RANGE_FORMAT, \
    did_the_task_fail, has_regex_match, validate_time_range, \
    CPU_TIME_RANGE_FORMAT, VALIDATE_CPU_TIME_PATTERN, \
    VALIDATE_ELAPSED_TIME_PATTERN, ELAPSED_TIME_RANGE_FORMAT, \
    validate_children_parameters, validate_command_regex, \
    validate_common_passed_fields_values, convert_time_to_seconds, \
    run_shell_cmd, parse_process_list_into_dictionaries, \
    filter_list_by_regex_id, filter_list_by_time_range, \
    filter_list_by_number_range, filter_list_by_exact_name, \
    filter_list_by_stat, filter_list_by_regex, FIELDS, execute_action, \
    search, run_process
import re

__metaclass__ = type


class TestModule:
    def __init__(self, argument_spec, check_mode=False):
        self.params = argument_spec
        self.check_mode = check_mode

    def fail_json(self, **kwargs):
        raise AnsibleFailJson

    def exit_json(self, **kwargs):
        raise AnsibleExitJson


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by
    the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by
    the test case"""
    pass


class ValidatorsTestCases(unittest.TestCase):

    def setUp(self):
        self.params = {
            "id_1": "\\", "id_2": "0000", "id_3": "1*96", "id_4": "1s2",
            "id_5": "132365", "id_6": "12345678",
            "id_7": "******", "id_8": "", "choice_1": "yes", "choice_2": "no",
            "choice_3": "", "choice_4": "asd",
            "stat": "", "int_range_1": "0-65", "int_range_2": "555-555",
            "int_range_3": "", "int_range_4": "50-0",
            "int_range_5": "55151", "int_range_6": "122asd123",
            "double_range_1": "", "double_range_2": "0.0-15",
            "double_range_3": "0.0-0.1", "double_range_4": "0.1-0.1",
            "double_range_5": "12.2-10",
            "double_range_6": "12.2", "double_range_7": "12.2a12",
            "cpu_time_1": "", "cpu_time_2": "00:00:00-00:00:00",
            "cpu_time_3": "00:00:00-00:00:00:00",
            "cpu_time_4": "00:00:00:00-00:00:01",
            "cpu_time_5": "01:00:00-00:00:59:00",
            "cpu_time_6": "01:00:00-00:24:59:00", "cpu_time_7": "00:00-00:00",
            "cpu_time_8": "00:23:23_23:23:23", "elapsed_time_1": "",
            "elapsed_time_2": "00:00:00:01-00:00:00:02",
            "elapsed_time_3": "00:00:01-00:00:02",
            "elapsed_time_4": "00:01-00:02",
            "elapsed_time_5": "00:00:01-00:01",
            "elapsed_time_6": "00:00-00:00:00:00",
            "elapsed_time_7": "01:00-00:00:00:59",
            "elapsed_time_8": "24:23:23-23:23:23",
            "elapsed_time_9": "00:23:23_23:23:23", "get_children": False,
            "has_children": "", "command": "",
        }
        self.succesful_validate_result = {'msg': '', 'rc': 0, 'stderr': ''}

    def test_validate_id_field_pattern(self):
        self.assertTrue("value can consist of numbers" in
                        validate_id_field_pattern(self.params, "id_1")[
                            "stderr"])
        self.assertEqual("wrong parameter format",
                         validate_id_field_pattern(self.params, "id_2")[
                             "stderr"])
        self.assertEqual(self.succesful_validate_result,
                         validate_id_field_pattern(self.params, "id_3"))
        self.assertTrue("value can consist of numbers" in
                        validate_id_field_pattern(self.params, "id_4")[
                            "stderr"])
        self.assertEqual(self.succesful_validate_result,
                         validate_id_field_pattern(self.params, "id_5"))
        self.assertTrue("value can consist of numbers" in
                        validate_id_field_pattern(self.params, "id_6")[
                            "stderr"])
        self.assertEqual(self.succesful_validate_result,
                         validate_id_field_pattern(self.params, "id_7"))
        self.assertEqual(self.succesful_validate_result,
                         validate_id_field_pattern(self.params, "id_8"))

    def test_validate_choice_field(self):
        self.assertEqual(self.succesful_validate_result,
                         validate_choice_field(self.params, ["yes", "no"],
                                               "choice_1"))
        self.assertEqual(self.succesful_validate_result,
                         validate_choice_field(self.params, ["yes", "no"],
                                               "choice_2"))
        self.assertEqual(self.succesful_validate_result,
                         validate_choice_field(self.params, ["yes", "no"],
                                               "choice_3"))
        self.assertEqual(1, validate_choice_field(self.params, ["yes", "no"],
                                                  "choice_4")["rc"])

    def test_validate_stat_field(self):
        self.assertEqual(self.succesful_validate_result,
                         validate_stat_field(self.params))
        self.params["stat"] = "DRS*"
        self.assertEqual(self.succesful_validate_result,
                         validate_stat_field(self.params))
        self.params["stat"] = "iS"
        self.assertTrue(
            "'i' is not permitted" in validate_stat_field(self.params)[
                "stderr"])
        self.params["stat"] = "SS"
        self.assertTrue(
            "'S' occurred more than once" in validate_stat_field(self.params)[
                "stderr"])

    def test_validate_number_range(self):
        self.assertEqual(self.succesful_validate_result,
                         validate_number_range(self.params, "int_range_1",
                                               INTEGER_RANGE_PATTERN,
                                               INTEGER_RANGE_FORMAT))
        self.assertEqual(self.succesful_validate_result,
                         validate_number_range(self.params, "int_range_2",
                                               INTEGER_RANGE_PATTERN,
                                               INTEGER_RANGE_FORMAT))
        self.assertEqual(self.succesful_validate_result,
                         validate_number_range(self.params, "int_range_3",
                                               INTEGER_RANGE_PATTERN,
                                               INTEGER_RANGE_FORMAT))
        self.assertTrue("the lower boundary value must be smaller" in
                        validate_number_range(self.params, "int_range_4",
                                              INTEGER_RANGE_PATTERN,
                                              INTEGER_RANGE_FORMAT)[
                            "stderr"])
        self.assertTrue("is not a valid range" in
                        validate_number_range(self.params, "int_range_5",
                                              INTEGER_RANGE_PATTERN,
                                              INTEGER_RANGE_FORMAT)[
                            "stderr"])
        self.assertTrue("is not a valid range" in
                        validate_number_range(self.params, "int_range_6",
                                              INTEGER_RANGE_PATTERN,
                                              INTEGER_RANGE_FORMAT)[
                            "stderr"])
        self.assertEqual(self.succesful_validate_result,
                         validate_number_range(self.params, "double_range_1",
                                               DOUBLE_RANGE_PATTERN,
                                               DOUBLE_RANGE_FORMAT))
        self.assertEqual(self.succesful_validate_result,
                         validate_number_range(self.params, "double_range_2",
                                               DOUBLE_RANGE_PATTERN,
                                               DOUBLE_RANGE_FORMAT))
        self.assertEqual(self.succesful_validate_result,
                         validate_number_range(self.params, "double_range_3",
                                               DOUBLE_RANGE_PATTERN,
                                               DOUBLE_RANGE_FORMAT))
        self.assertEqual(self.succesful_validate_result,
                         validate_number_range(self.params, "double_range_4",
                                               DOUBLE_RANGE_PATTERN,
                                               DOUBLE_RANGE_FORMAT))
        self.assertTrue("the lower boundary value must be smaller" in
                        validate_number_range(self.params, "double_range_5",
                                              DOUBLE_RANGE_PATTERN,
                                              DOUBLE_RANGE_FORMAT)[
                            "stderr"])
        self.assertTrue("is not a valid range" in
                        validate_number_range(self.params, "double_range_6",
                                              DOUBLE_RANGE_PATTERN,
                                              DOUBLE_RANGE_FORMAT)[
                            "stderr"])
        self.assertTrue("is not a valid range" in
                        validate_number_range(self.params, "double_range_7",
                                              DOUBLE_RANGE_PATTERN,
                                              DOUBLE_RANGE_FORMAT)[
                            "stderr"])

    def test_validate_time_range(self):
        self.assertEqual(self.succesful_validate_result,
                         validate_time_range(self.params, "cpu_time_1",
                                             VALIDATE_CPU_TIME_PATTERN,
                                             CPU_TIME_RANGE_FORMAT))
        self.assertEqual(self.succesful_validate_result,
                         validate_time_range(self.params, "cpu_time_2",
                                             VALIDATE_CPU_TIME_PATTERN,
                                             CPU_TIME_RANGE_FORMAT))
        self.assertEqual(self.succesful_validate_result,
                         validate_time_range(self.params, "cpu_time_3",
                                             VALIDATE_CPU_TIME_PATTERN,
                                             CPU_TIME_RANGE_FORMAT))
        self.assertEqual(self.succesful_validate_result,
                         validate_time_range(self.params, "cpu_time_4",
                                             VALIDATE_CPU_TIME_PATTERN,
                                             CPU_TIME_RANGE_FORMAT))
        self.assertTrue(
            "lower boundary can't be greater than upper boundary" in
            validate_time_range(self.params, "cpu_time_5",
                                VALIDATE_CPU_TIME_PATTERN,
                                CPU_TIME_RANGE_FORMAT)["stderr"])
        self.assertTrue("hours must be within range [0-23]" in
                        validate_time_range(self.params, "cpu_time_6",
                                            VALIDATE_CPU_TIME_PATTERN,
                                            CPU_TIME_RANGE_FORMAT)["stderr"])
        self.assertTrue("Range must be in the form" in
                        validate_time_range(self.params, "cpu_time_7",
                                            VALIDATE_CPU_TIME_PATTERN,
                                            CPU_TIME_RANGE_FORMAT)["stderr"])
        self.assertTrue("Range must be in the form" in
                        validate_time_range(self.params, "cpu_time_8",
                                            VALIDATE_CPU_TIME_PATTERN,
                                            CPU_TIME_RANGE_FORMAT)["stderr"])
        self.assertEqual(self.succesful_validate_result,
                         validate_time_range(self.params, "elapsed_time_1",
                                             VALIDATE_ELAPSED_TIME_PATTERN,
                                             ELAPSED_TIME_RANGE_FORMAT))
        self.assertEqual(self.succesful_validate_result,
                         validate_time_range(self.params, "elapsed_time_2",
                                             VALIDATE_ELAPSED_TIME_PATTERN,
                                             ELAPSED_TIME_RANGE_FORMAT))
        self.assertEqual(self.succesful_validate_result,
                         validate_time_range(self.params, "elapsed_time_3",
                                             VALIDATE_ELAPSED_TIME_PATTERN,
                                             ELAPSED_TIME_RANGE_FORMAT))
        self.assertEqual(self.succesful_validate_result,
                         validate_time_range(self.params, "elapsed_time_4",
                                             VALIDATE_ELAPSED_TIME_PATTERN,
                                             ELAPSED_TIME_RANGE_FORMAT))
        self.assertEqual(self.succesful_validate_result,
                         validate_time_range(self.params, "elapsed_time_5",
                                             VALIDATE_ELAPSED_TIME_PATTERN,
                                             ELAPSED_TIME_RANGE_FORMAT))
        self.assertEqual(self.succesful_validate_result,
                         validate_time_range(self.params, "elapsed_time_6",
                                             VALIDATE_ELAPSED_TIME_PATTERN,
                                             ELAPSED_TIME_RANGE_FORMAT))
        self.assertTrue(
            "lower boundary can't be greater than upper boundary" in
            validate_time_range(self.params, "elapsed_time_7",
                                VALIDATE_ELAPSED_TIME_PATTERN,
                                ELAPSED_TIME_RANGE_FORMAT)["stderr"])
        self.assertTrue("hours must be within range [0-23]" in
                        validate_time_range(self.params, "elapsed_time_8",
                                            VALIDATE_ELAPSED_TIME_PATTERN,
                                            ELAPSED_TIME_RANGE_FORMAT)[
                            "stderr"])
        self.assertTrue("Range must be in the form" in
                        validate_time_range(self.params, "elapsed_time_9",
                                            VALIDATE_ELAPSED_TIME_PATTERN,
                                            ELAPSED_TIME_RANGE_FORMAT)[
                            "stderr"])

    def test_validate_children_parameters(self):
        self.assertEqual(self.succesful_validate_result,
                         validate_children_parameters(self.params))
        self.params["has_children"] = "yes"
        self.assertEqual(
            "has_children must be used with get_children set to True",
            validate_children_parameters(self.params)["stderr"])
        self.params["has_children"] = "no"
        self.assertEqual(
            "has_children must be used with get_children set to True",
            validate_children_parameters(self.params)["stderr"])
        self.params["get_children"] = True
        self.assertEqual(self.succesful_validate_result,
                         validate_children_parameters(self.params))
        self.params["has_children"] = "true"
        self.assertEqual("wrong has_children value",
                         validate_children_parameters(self.params)["stderr"])

    def test_validate_command_regex(self):
        self.assertEqual(self.succesful_validate_result,
                         validate_command_regex(self.params))
        self.params["command"] = "Web Service"
        self.assertEqual(self.succesful_validate_result,
                         validate_command_regex(self.params))
        self.params["command"] = "\\"
        self.assertNotEqual(self.succesful_validate_result,
                            validate_command_regex(self.params))

    def test_validate_search_passed_fields_values(self):
        self.params["action"] = "search"
        self.params["pgid"] = "**"
        self.params["ppid"] = "**"
        self.params["stat"] = "Ss+"
        self.params["rss"] = "0-5000"
        self.params["vsz"] = "0-5000"
        self.params["cpu_utilization"] = "30.0-98.0"
        self.params["memory_usage"] = "0.0-99.9"
        self.params["cpu_time"] = "00:00:00:00-00:00:00:5"
        self.params["elapsed_time"] = "99:23:59:59-99:23:59:59"
        self.params["command"] = "test_validate_search_passed_field"
        self.params["get_children"] = True
        self.params["has_children"] = "yes"
        self.assertEqual(self.succesful_validate_result,
                         validate_command_regex(self.params))

    def test_validate_common_passed_fields_values(self):
        self.params["pid"] = "*****"
        self.assertEqual(self.succesful_validate_result,
                         validate_common_passed_fields_values(self.params))


class CommonUnitsTestCases(unittest.TestCase):

    def setUp(self):
        self.module = TestModule({}, False)

    def test_did_the_task_fail(self):
        with self.assertRaises(AnsibleFailJson):
            did_the_task_fail(self.module, {"rc": 1})
        self.assertIsNone(did_the_task_fail(self.module, {"rc": 0}))

    def test_has_regex_match(self):
        with self.assertRaises(re.error):
            has_regex_match("\\", "")
        self.assertTrue(has_regex_match("012", "13232012332"))
        self.assertFalse(has_regex_match("012", "1323212332"))

    def test_convert_time_to_seconds(self):
        self.assertEqual(0, convert_time_to_seconds("00:00:00"))
        self.assertEqual(90000, convert_time_to_seconds("01:01:00:00"))

    def test_run_shell_cmd(self):
        output, err, rc = run_shell_cmd("ps -e")
        self.assertEqual(0, rc)
        output, err, rc = run_shell_cmd("ps -asdsade")
        self.assertNotEqual(0, rc)

    def test_parse_process_list_into_dictionaries(self):
        self.assertEqual('[]', parse_process_list_into_dictionaries([], []))
        self.assertEqual('[]', parse_process_list_into_dictionaries(None, []))
        self.assertEqual('[]', parse_process_list_into_dictionaries("", []))
        processes_list = [
            "1 2 user_1",
            "3 4 user_2",
            "5 6 user_3",
            "7 8 user_4",
        ]
        headers = ["pid", "pgid", "user"]
        expected_result = [{'pid': '1', 'pgid': '2', 'user': 'user_1'},
                           {'pid': '3', 'pgid': '4', 'user': 'user_2'},
                           {'pid': '5', 'pgid': '6', 'user': 'user_3'},
                           {'pid': '7', 'pgid': '8', 'user': 'user_4'}
                           ]
        self.assertEqual(expected_result,
                         parse_process_list_into_dictionaries(processes_list,
                                                              headers))


class FiltersTestCases(unittest.TestCase):
    def setUp(self):
        self.processes_list = [
            {"name": "user1", "time": "00:00:01", "number": "0000",
             "id": "11",
             "stat": "S", "command": "web service"},
            {"name": "user1", "time": "00:01:59", "number": "0001",
             "id": "12",
             "stat": "Ss", "command": "web server"},
            {"name": "user2", "time": "00:59:00", "number": "1000",
             "id": "13",
             "stat": "Ss+",
             "command": "web browser"},
            {"name": "user2", "time": "00:59:59", "number": "2000",
             "id": "14",
             "stat": "I", "command": "game 1"},
            {"name": "user2", "time": "01:00:00", "number": "3000",
             "id": "15",
             "stat": "T", "command": "game 2"},
            {"name": "user3", "time": "02:00:00", "number": "4000",
             "id": "16",
             "stat": "X", "command": "game 3"},
            {"name": "user3", "time": "03:00:00", "number": "5000",
             "id": "17",
             "stat": "D", "command": "bash"},
            {"name": "user3", "time": "04:00:00", "number": "6000",
             "id": "18",
             "stat": "S", "command": "cpp"},
            {"name": "user3", "time": "05:00:00", "number": "7000",
             "id": "21",
             "stat": "Ss", "command": "javascript"},
            {"name": "user3", "time": "06:00:00", "number": "8000",
             "id": "23",
             "stat": "Ss", "command": "kotlin"},
            {"name": "user3", "time": "07:00:00", "number": "9000",
             "id": "31",
             "stat": "Ss+", "command": "python"},
            {"name": "user3", "time": "08:00:00", "number": "1500",
             "id": "41",
             "stat": "IS", "command": "java"}
        ]

    def test_filter_list_by_regex_id(self):
        self.assertEqual(12, len(
            filter_list_by_regex_id("", False, self.processes_list, "id")))
        self.assertEqual(12, len(
            filter_list_by_regex_id("", True, self.processes_list, "id")))
        self.assertEqual(12, len(
            filter_list_by_regex_id("**", False, self.processes_list, "id")))
        self.assertEqual(0, len(
            filter_list_by_regex_id("**", True, self.processes_list, "id")))
        self.assertEqual(1, len(
            filter_list_by_regex_id("11", False, self.processes_list, "id")))
        self.assertEqual(11, len(
            filter_list_by_regex_id("11", True, self.processes_list, "id")))
        self.assertEqual(8, len(
            filter_list_by_regex_id("1*", False, self.processes_list, "id")))
        self.assertEqual(4, len(
            filter_list_by_regex_id("1*", True, self.processes_list, "id")))
        self.assertEqual(2, len(
            filter_list_by_regex_id("2*", False, self.processes_list, "id")))
        self.assertEqual(10, len(
            filter_list_by_regex_id("2*", True, self.processes_list, "id")))

    def test_filter_list_by_time_range(self):
        self.assertEqual(12, len(
            filter_list_by_time_range("", False, self.processes_list,
                                      "time")))
        self.assertEqual(12, len(
            filter_list_by_time_range("", True, self.processes_list, "time")))
        self.assertEqual(0, len(
            filter_list_by_time_range("00:00:00-00:00:00", False,
                                      self.processes_list, "time")))
        self.assertEqual(12, len(
            filter_list_by_time_range("00:00:00-00:00:00", True,
                                      self.processes_list, "time")))
        self.assertEqual(1, len(
            filter_list_by_time_range("00:00:00-00:00:01", False,
                                      self.processes_list, "time")))
        self.assertEqual(11, len(
            filter_list_by_time_range("00:00:00-00:00:01", True,
                                      self.processes_list, "time")))
        self.assertEqual(8, len(
            filter_list_by_time_range("01:00:00-08:00:00", False,
                                      self.processes_list, "time")))
        self.assertEqual(4, len(
            filter_list_by_time_range("01:00:00-08:00:00", True,
                                      self.processes_list, "time")))

    def test_filter_list_by_number_range(self):
        self.assertEqual(12, len(
            filter_list_by_number_range("", False, self.processes_list,
                                        "number")))
        self.assertEqual(12, len(
            filter_list_by_number_range("", True, self.processes_list,
                                        "number")))
        self.assertEqual(1, len(
            filter_list_by_number_range("0-0", False, self.processes_list,
                                        "number")))
        self.assertEqual(11, len(
            filter_list_by_number_range("0-0", True, self.processes_list,
                                        "number")))
        self.assertEqual(3, len(
            filter_list_by_number_range("0-1000", False, self.processes_list,
                                        "number")))
        self.assertEqual(9, len(
            filter_list_by_number_range("0-1000", True, self.processes_list,
                                        "number")))
        self.assertEqual(8, len(
            filter_list_by_number_range("2000-9000", False,
                                        self.processes_list, "number")))
        self.assertEqual(4, len(filter_list_by_number_range("2000-9000", True,
                                                            self.
                                                            processes_list,
                                                            "number")))
        self.assertEqual(3,
                         len(filter_list_by_number_range("1000-2000", False,
                                                         self.processes_list,
                                                         "number")))
        self.assertEqual(9, len(filter_list_by_number_range("1000-2000",
                                                            True,
                                                            self.
                                                            processes_list,
                                                            "number")))

    def test_filter_list_by_exact_name(self):
        self.assertEqual(12, len(
            filter_list_by_exact_name("", False, self.processes_list,
                                      "name")))
        self.assertEqual(12, len(
            filter_list_by_exact_name("", True, self.processes_list, "name")))
        self.assertEqual(2, len(
            filter_list_by_exact_name("user1", False, self.processes_list,
                                      "name")))
        self.assertEqual(10, len(
            filter_list_by_exact_name("user1", True, self.processes_list,
                                      "name")))
        self.assertEqual(3, len(
            filter_list_by_exact_name("user2", False, self.processes_list,
                                      "name")))
        self.assertEqual(9, len(
            filter_list_by_exact_name("user2", True, self.processes_list,
                                      "name")))
        self.assertEqual(7, len(
            filter_list_by_exact_name("user3", False, self.processes_list,
                                      "name")))
        self.assertEqual(5, len(
            filter_list_by_exact_name("user3", True, self.processes_list,
                                      "name")))

    def test_filter_list_by_regex(self):
        self.assertEqual(12, len(
            filter_list_by_regex("", False, self.processes_list, "command")))
        self.assertEqual(12, len(
            filter_list_by_regex("", True, self.processes_list, "command")))
        self.assertEqual(2, len(
            filter_list_by_regex("java", False, self.processes_list,
                                 "command")))
        self.assertEqual(10, len(
            filter_list_by_regex("java", True, self.processes_list,
                                 "command")))
        self.assertEqual(1, len(
            filter_list_by_regex("^java$", False, self.processes_list,
                                 "command")))
        self.assertEqual(11, len(
            filter_list_by_regex("^java$", True, self.processes_list,
                                 "command")))
        self.assertEqual(3, len(
            filter_list_by_regex("web", False, self.processes_list,
                                 "command")))
        self.assertEqual(9, len(
            filter_list_by_regex("web", True, self.processes_list,
                                 "command")))

    def test_filter_list_by_stat(self):
        self.assertEqual(12, len(
            filter_list_by_stat("", False, self.processes_list)))
        self.assertEqual(12, len(
            filter_list_by_stat("", True, self.processes_list)))
        self.assertEqual(8, len(
            filter_list_by_stat("S", False, self.processes_list)))
        self.assertEqual(4, len(
            filter_list_by_stat("S", True, self.processes_list)))
        self.assertEqual(2, len(
            filter_list_by_stat("S*", False, self.processes_list)))
        self.assertEqual(10, len(
            filter_list_by_stat("S*", True, self.processes_list)))


class ActionTestCases(unittest.TestCase):

    def setUp(self):
        fields = {
            "action": "search", "user": "", "ruser": "", "group": "",
            "rgroup": "", "not_user": False,
            "not_ruser": False, "not_group": False, "not_rgroup": False,
            "pid": "", "pgid": "", "ppid": "",
            "not_pid": False, "not_pgid": False, "not_ppid": False,
            "stat": "",
            "not_stat": False, "rss": "",
            "not_rss": False, "vsz": "", "not_vsz": False, "memory_usage": "",
            "not_memory_usage": False,
            "cpu_utilization": "", "not_cpu_utilization": False,
            "cpu_time": "", "not_cpu_time": False,
            "elapsed_time": "", "not_elapsed_time": False, "command": "",
            "not_command": False,
            "get_children": True, "has_children": "", "get_threads": True,
        }
        self.action_module = TestModule(fields, True)
        self.main_module = TestModule(fields, True)

    def test_search(self):
        self.assertEqual(0, search(self.action_module.params)["rc"])
        self.action_module.params["get_children"] = True
        self.action_module.params["get_Threads"] = True
        self.assertEqual(0, search(self.action_module.params)["rc"])
        self.action_module.params["has_children"] = "yes"
        self.assertEqual(0, search(self.action_module.params)["rc"])
        self.action_module.params["has_children"] = "no"
        self.assertEqual(0, search(self.action_module.params)["rc"])

    def test_execute_action(self):
        self.action_module.check_mode = True
        self.action_module.params["pid"] = ""
        self.assertEqual(1, execute_action(self.action_module.params, "9",
                                           self.action_module.check_mode)[
            "rc"])
        self.action_module.params["pid"] = "*"
        self.assertEqual(1, execute_action(self.action_module.params, "9",
                                           self.action_module.check_mode)[
            "rc"])
        self.action_module.params["pid"] = "0"
        self.assertEqual(1, execute_action(self.action_module.params, "9",
                                           self.action_module.check_mode)[
            "rc"])
        self.assertEqual(1, execute_action(self.action_module.params, "STOP",
                                           self.action_module.check_mode)[
            "rc"])
        self.assertEqual(1, execute_action(self.action_module.params, "CONT",
                                           self.action_module.check_mode)[
            "rc"])

        create_dummy_process = "exec -a test_execute_action_dummmy sleep " \
                               "1000000 >/dev/null 2>&1 &"
        output, stderr, rc = run_shell_cmd(create_dummy_process)
        get_dummy_process_pid = 'ps -eo "pid args" | grep -v grep | ' \
                                ' grep "test_execute_action_dummmy' \
                                ' 1000000" | awk \'{print $1}\' | head -1'

        output, stderr, rc = run_shell_cmd(get_dummy_process_pid)

        self.action_module.params["pid"] = output
        expected_rc = 0
        if not output:
            expected_rc = 1
        self.assertEqual(expected_rc,
                         execute_action(self.action_module.params, "STOP",
                                        self.action_module.check_mode)[
                             "rc"])
        self.assertEqual(expected_rc,
                         execute_action(self.action_module.params, "CONT",
                                        self.action_module.check_mode)[
                             "rc"])
        self.assertEqual(expected_rc,
                         execute_action(self.action_module.params, "9",
                                        self.action_module.check_mode)[
                             "rc"])
        self.action_module.check_mode = False
        self.assertEqual(expected_rc,
                         execute_action(self.action_module.params, "STOP",
                                        self.action_module.check_mode)[
                             "rc"])
        self.assertEqual(expected_rc,
                         execute_action(self.action_module.params, "CONT",
                                        self.action_module.check_mode)[
                             "rc"])
        self.assertEqual(expected_rc,
                         execute_action(self.action_module.params, "9",
                                        self.action_module.check_mode)[
                             "rc"])

    def test_run_process(self):
        self.main_module.check_mode = True

        with self.assertRaises(AnsibleExitJson):
            self.main_module.params["pid"] = ""
            self.main_module.params["action"] = "search"
            run_process(self.main_module)
        with self.assertRaises(AnsibleFailJson):
            self.main_module.params["action"] = "kill"
            run_process(self.main_module)
        with self.assertRaises(AnsibleFailJson):
            self.main_module.params["action"] = "suspend"
            run_process(self.main_module)
        with self.assertRaises(AnsibleFailJson):
            self.main_module.params["action"] = "resume"
            run_process(self.main_module)

        create_dummy_process = "exec -a test_main_dummy_process sleep " \
                               "1000000 >/dev/null 2>&1 &"
        output, stderr, rc = run_shell_cmd(create_dummy_process)
        get_dummy_process_pid = 'ps -eo "pid args" | grep -v grep |grep ' \
                                'test_main_dummy_process | awk \'{print $1}\''
        output, stderr, rc = run_shell_cmd(get_dummy_process_pid)
        expected_exception = AnsibleExitJson
        if not output:
            expected_exception = AnsibleFailJson

        self.main_module.params["pid"] = output
        self.main_module.check_mode = False
        with self.assertRaises(expected_exception):
            self.main_module.params["action"] = "suspend"
            run_process(self.main_module)
        with self.assertRaises(expected_exception):
            self.main_module.params["action"] = "resume"
            run_process(self.main_module)
        with self.assertRaises(expected_exception):
            self.main_module.params["action"] = "kill"
            run_process(self.main_module)
