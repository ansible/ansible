import ansible.module_utils.artifactory as artifactory
import ast
import json

from ansible.compat.tests.unittest import TestCase


class TestArtifactoryBaseClass(TestCase):
    def setUp(self):
        self.key_config_map = {
            "test_key":
                {"valid_values": ['sweet', 'deal'],
                 "values_require_keys":
                    {"deal": ["key_value_test"]},
                 "always_required": True},
            "key_value_test":
                {"valid_values": ["value_test", "value_not_req_key",
                                  "another_key"],
                 "values_require_keys":
                    {"value_test": ["requires_this_key"],
                     "another_key": ["another_key"]}},
            "another_key":
                {"valid_values": ["valid_value"],
                 "required_keys": ["another_key_needs_me"]}}

        self.uri_key_map = {"a/cherry": self.key_config_map}
        self.uri_key_map["would/you/like/to/try/again"] = True
        self.uri_key_map["explicitly/block/url"] = False
        self.art_base = artifactory.ArtifactoryBase(
            username="user", password="pass", config_map=self.uri_key_map)

    def test_convert_config_to_dict_valid_dict(self):
        valid_dict = {"valid": "dict"}
        resp = self.art_base.convert_config_to_dict(valid_dict)
        self.assertIsInstance(resp, dict)
        self.assertEqual(valid_dict, resp)

    def test_convert_config_to_dict_valid_dict_string(self):
        valid_dict_str = '{"valid": "dict"}'
        resp = self.art_base.convert_config_to_dict(valid_dict_str)
        valid_dict = ast.literal_eval(valid_dict_str)
        self.assertIsInstance(resp, dict)
        self.assertEqual(valid_dict, resp)

    def test_convert_config_to_dict_invalid_dict_string_bad_syntax(self):
        valid_dict_str = '{"valid": }'
        with self.assertRaises(artifactory.ConfigValueTypeMismatch):
            self.art_base.convert_config_to_dict(valid_dict_str)

    def test_convert_config_to_dict_invalid_syntax(self):
        valid_dict_str = 'not_valid'
        with self.assertRaises(artifactory.ConfigValueTypeMismatch):
            self.art_base.convert_config_to_dict(valid_dict_str)

    def test_convert_config_to_dict_invalid_string_bool_not_dict(self):
        valid_dict_str = 'True'
        with self.assertRaises(artifactory.ConfigValueTypeMismatch):
            self.art_base.convert_config_to_dict(valid_dict_str)

    def test_serialize_config_data_valid_double_quote(self):
        valid_dict = {"valid": "dict"}
        resp = self.art_base.serialize_config_data(valid_dict)
        self.assertIsInstance(resp, str)
        valid_dict_str = json.dumps(valid_dict)
        self.assertEqual(valid_dict_str, resp)

    def test_serialize_config_data_valid_single_quote(self):
        valid_dict = {'valid': 'dict'}
        resp = self.art_base.serialize_config_data(valid_dict)
        self.assertIsInstance(resp, str)
        valid_dict_str = json.dumps(valid_dict)
        self.assertEqual(valid_dict_str, resp)

    def test_serialize_config_data_invalid_str_not_dict(self):
        valid_dict = "{'valid': 'dict'}"
        with self.assertRaises(artifactory.InvalidConfigurationData):
            self.art_base.serialize_config_data(valid_dict)

    def test_serialize_config_data_invalid_none(self):
        with self.assertRaises(artifactory.InvalidConfigurationData):
            self.art_base.serialize_config_data(None)

    def test_serialize_config_data_invalid_empty_str(self):
        with self.assertRaises(artifactory.InvalidConfigurationData):
            self.art_base.serialize_config_data("")

    def test_serialize_config_data_invalid_empty_dict(self):
        with self.assertRaises(artifactory.InvalidConfigurationData):
            self.art_base.serialize_config_data(dict())

    def test_get_uri_key_map_valid_url_to_map_w_dict(self):
        resp = self.art_base.get_uri_key_map("a/cherry", self.uri_key_map)
        self.assertIsInstance(resp, dict)
        self.assertEqual(self.key_config_map, resp)

    def test_get_uri_key_map_valid_url_to_map_w_bool(self):
        resp = self.art_base.get_uri_key_map("would/you/like/to/try/again",
                                             self.uri_key_map)
        self.assertIsInstance(resp, bool)
        self.assertTrue(resp)
        self.assertEqual(self.uri_key_map["would/you/like/to/try/again"], resp)

    def test_get_uri_key_map_invalid_no_uri_match(self):
        with self.assertRaises(artifactory.InvalidArtifactoryURL):
            self.art_base.get_uri_key_map("uri/not/exist", self.uri_key_map)

    def test_get_uri_key_map_invalid_explicit_block_url(self):
        with self.assertRaises(artifactory.InvalidArtifactoryURL):
            self.art_base.get_uri_key_map("explicitly/block/url",
                                          self.uri_key_map)

    def test_get_uri_key_map_invalid_config_is_none(self):
        with self.assertRaises(artifactory.InvalidConfigurationData):
            self.art_base.get_uri_key_map("bad/config/is/None",
                                          None)

    def test_get_uri_key_map_invalid_config_is_empty(self):
        with self.assertRaises(artifactory.InvalidConfigurationData):
            self.art_base.get_uri_key_map("bad/config/is/empty",
                                          dict())

    def test_get_uri_key_map_invalid_url_is_none(self):
        with self.assertRaises(artifactory.InvalidConfigurationData):
            self.art_base.get_uri_key_map(None, self.uri_key_map)

    def test_get_uri_key_map_invalid_url_is_empty(self):
        with self.assertRaises(artifactory.InvalidConfigurationData):
            self.art_base.get_uri_key_map("", self.uri_key_map)

    def test_validate_config_values_valid_url_and_dict_bool(self):
        resp = self.art_base.validate_config_values(
            "would/you/like/to/try/again", self.uri_key_map)
        self.assertEqual(resp, None)

    def test_validate_config_values_valid_key_value(self):
        test_config = {"test_key": "sweet"}
        self.art_base.validate_config_values("a/cherry", test_config)

    def test_validate_config_values_invalid_key_value(self):
        with self.assertRaises(artifactory.InvalidConfigurationData):
            test_config = {"test_key": "not_sweet"}
            self.art_base.validate_config_values("a/cherry", test_config)

    def test_validate_config_values_valid_key_not_defined(self):
        test_config = {"valid_key": "but_not_defined_in_map"}
        self.art_base.validate_config_values("a/cherry", test_config)

    def test_validate_config_values_invalid_uri(self):
        with self.assertRaises(artifactory.InvalidArtifactoryURL):
            test_config = {"test_key": "sweet"}
            self.art_base.validate_config_values("not/cherry", test_config)

    def test_validate_config_required_keys_valid_always_req_key_defined(self):
        test_config = {"test_key": "sweet"}
        self.art_base.validate_config_required_keys("a/cherry", test_config)

    def test_validate_config_required_keys_valid_always_req_not_defined(self):
        with self.assertRaises(artifactory.InvalidConfigurationData):
            test_config = {"missing": "test_key_which_is_required"}
            self.art_base.validate_config_required_keys(
                "a/cherry", test_config)

    def test_validate_config_required_keys_valid_key_values_require(self):
        # The value of key_value_test does require additional keys
        test_config = {"test_key": "sweet",
                       "key_value_test": "value_test",
                       "requires_this_key": "because_of_value_test"}
        self.art_base.validate_config_required_keys(
            "a/cherry", test_config)

    def test_validate_config_required_keys_valid_key_values_not_require(self):
        # The value of key_value_test does not require additional keys
        test_config = {"test_key": "sweet",
                       "key_value_test": "value_not_req_key"}
        self.art_base.validate_config_required_keys(
            "a/cherry", test_config)

    def test_validate_config_required_keys_invalid_missing_val_req_key(self):
        # The value of key_value_test does require "requires_this_key". It is
        # missing, so an exception is thrown.
        with self.assertRaises(artifactory.InvalidConfigurationData):
            test_config = {"test_key": "sweet",
                           "key_value_test": "value_test",
                           "missing_required_key": "because_of_value_test"}
            self.art_base.validate_config_required_keys(
                "a/cherry", test_config)

    def test_validate_config_required_keys_valid_key_requires(self):
        # The key "another_key" requires "good_value_needs_me"
        test_config = {"test_key": "sweet",
                       "another_key": "valid_value",
                       "another_key_needs_me": "another_key_needs_me"}
        self.art_base.validate_config_required_keys(
            "a/cherry", test_config)

    def test_validate_config_required_keys_invalid_missing_required_key(self):
        # The value of key_value_test does require additional keys
        with self.assertRaises(artifactory.InvalidConfigurationData):
            test_config = {"test_key": "sweet",
                           "another_key": "valid_value",
                           "missing_required_key": "another_key_needs_me"}
            self.art_base.validate_config_required_keys(
                "a/cherry", test_config)

    def test_validate_config_required_keys_test_chain_of_requirements(self):
        # The key/pair test_key/deal requires key_value_test. The key/pair
        # key_value_test/another_key requires the key another_key. The key/pair
        # another_key/valid_value requires key another_key_needs_me
        test_config = {"test_key": "deal",
                       "key_value_test": "another_key",
                       "another_key": "valid_value",
                       "another_key_needs_me": "another_key_needs_me"}
        self.art_base.validate_config_required_keys(
            "a/cherry", test_config)

    def test_validate_config_required_keys_break_first_in_chain(self):
        # The key/pair test_key/deal requires key_value_test. The key/pair
        # key_value_test/another_key requires the key another_key. The key/pair
        # another_key/valid_value requires key another_key_needs_me
        with self.assertRaises(artifactory.InvalidConfigurationData):
            test_config = {"test_key": "deal",
                           "not_key_value_test": "another_key",
                           "another_key": "valid_value",
                           "another_key_needs_me": "another_key_needs_me"}
            self.art_base.validate_config_required_keys(
                "a/cherry", test_config)

    def test_validate_config_required_keys_break_second_in_chain(self):
        # The key/pair test_key/deal requires key_value_test. The key/pair
        # key_value_test/another_key requires the key another_key. The key/pair
        # another_key/valid_value requires key another_key_needs_me
        with self.assertRaises(artifactory.InvalidConfigurationData):
            test_config = {"test_key": "deal",
                           "key_value_test": "another_key",
                           "not_another_key": "valid_value",
                           "another_key_needs_me": "another_key_needs_me"}
            self.art_base.validate_config_required_keys(
                "a/cherry", test_config)

    def test_validate_config_required_keys_break_third_in_chain(self):
        # The key/pair test_key/deal requires key_value_test. The key/pair
        # key_value_test/another_key requires the key another_key. The key/pair
        # another_key/valid_value requires key another_key_needs_me
        with self.assertRaises(artifactory.InvalidConfigurationData):
            test_config = {"test_key": "deal",
                           "key_value_test": "another_key",
                           "another_key": "valid_value",
                           "not_another_key_needs_me": "another_key_needs_me"}
            self.art_base.validate_config_required_keys(
                "a/cherry", test_config)


class TestArtifactoryValidationFunctions(TestCase):
    def setUp(self):
        self.module = self.FakeModule()
        self.module.params['rclass'] = 'local'

        self.config = dict()
        self.config['rclass'] = 'local'

        self.config_dict = dict()
        self.config_dict['rclass'] = 'local'
        self.top_level_fail = artifactory.TOP_LEVEL_FAIL
        self.fail_msg = artifactory.CONFIG_PARAM_FAIL

    class FakeModule:
        def __init__(self):
            self.params = dict()

    def test_top_level_valid_all_equal(self):
        val_fail_msgs = artifactory.validate_top_level_params(
            'rclass', self.module, self.config, self.config_dict, 'config',
            'config_dict')
        self.assertEqual(len(val_fail_msgs), 0)

    def test_top_level_valid_repo_config_top_level_equal(self):
        self.config_dict = dict()
        val_fail_msgs = artifactory.validate_top_level_params(
            'rclass', self.module, self.config, self.config_dict, 'config',
            'config_dict')
        self.assertEqual(len(val_fail_msgs), 0)

    def test_top_level_valid_repo_config_dict_top_level_equal(self):
        self.config = dict()
        val_fail_msgs = artifactory.validate_top_level_params(
            'rclass', self.module, self.config, self.config_dict, 'config',
            'config_dict')
        self.assertEqual(len(val_fail_msgs), 0)

    def test_top_level_valid_top_level_not_exist(self):
        self.module.params['rclass'] = None
        val_fail_msgs = artifactory.validate_top_level_params(
            'rclass', self.module, self.config, self.config_dict, 'config',
            'config_dict')
        self.assertEqual(len(val_fail_msgs), 0)

    def test_top_level_valid_top_level_repo_config_not_exist(self):
        self.config = None
        val_fail_msgs = artifactory.validate_top_level_params(
            'rclass', self.module, self.config, self.config_dict, 'config',
            'config_dict')
        self.assertEqual(len(val_fail_msgs), 0)

    def test_top_level_valid_top_level_repo_config_dict_not_exist(self):
        self.config_dict = None
        val_fail_msgs = artifactory.validate_top_level_params(
            'rclass', self.module, self.config, self.config_dict, 'config',
            'config_dict')
        self.assertEqual(len(val_fail_msgs), 0)

    def test_top_level_invalid_top_level_not_exist_passed_in(self):
        val_fail_msgs = artifactory.validate_top_level_params(
            None, self.module, self.config, self.config_dict, 'config',
            'config_dict')
        self.assertEqual(len(val_fail_msgs), 0)

    def test_top_level_invalid_mismatch_repo_config_top_level(self):
        self.module.params["rclass"] = 'remote'
        self.config_dict = dict()
        val_fail_msgs = artifactory.validate_top_level_params(
            'rclass', self.module, self.config, self.config_dict, 'config',
            'config_dict')
        self.assertEqual(len(val_fail_msgs), 1)
        self.assertEqual(val_fail_msgs[0],
                         self.top_level_fail.format('config', 'rclass'))

    def test_top_level_invalid_mismatch_repo_config_dict_top_level(self):
        self.module.params["rclass"] = 'remote'
        self.config = dict()
        val_fail_msgs = artifactory.validate_top_level_params(
            'rclass', self.module, self.config, self.config_dict, 'config',
            'config_dict')
        self.assertEqual(len(val_fail_msgs), 1)
        self.assertEqual(val_fail_msgs[0],
                         self.top_level_fail.format('config_dict', 'rclass'))

    def test_top_level_invalid_all_mismatch(self):
        self.module.params["rclass"] = 'remote'
        self.config['rclass'] = 'virtual'
        val_fail_msgs = artifactory.validate_top_level_params(
            'rclass', self.module, self.config, self.config_dict, 'config',
            'config_dict')
        self.assertEqual(len(val_fail_msgs), 2)
        self.assertEqual(val_fail_msgs[0],
                         self.top_level_fail.format('config_dict',
                                                    'rclass'))
        self.assertEqual(val_fail_msgs[1],
                         self.top_level_fail.format('config',
                                                    'rclass'))

    def test_config_params_valid(self):
        val_fail_msgs = artifactory.validate_config_params(
            self.config, self.config_dict, 'config', 'config_dict')
        self.assertEqual(len(val_fail_msgs), 0)

    def test_config_params_mismatch_dict_to_repo(self):
        self.config['rclass'] = 'virtual'
        val_fail_msgs = artifactory.validate_config_params(
            self.config, self.config_dict, 'config', 'config_dict')
        self.assertEqual(len(val_fail_msgs), 1)
        self.assertEqual(val_fail_msgs[0],
                         self.fail_msg.format('rclass', 'config',
                                              'config_dict'))

    def test_config_params_mismatch_dict_to_repo_multi(self):
        self.config['rclass'] = 'virtual'
        self.config['test'] = 'this'
        self.config_dict['test'] = 'me'
        val_fail_msgs = artifactory.validate_config_params(
            self.config, self.config_dict, 'config', 'config_dict')
        self.assertEqual(len(val_fail_msgs), 2)
        self.assertTrue(self.fail_msg.format('test', 'config', 'config_dict')
                        in val_fail_msgs)
        self.assertTrue(self.fail_msg.format('rclass', 'config', 'config_dict')
                        in val_fail_msgs)

    def test_config_params_invalid_repo_config_none_passed_in(self):
        val_fail_msgs = artifactory.validate_config_params(
            None, self.config_dict, 'config', 'config_dict')
        self.assertEqual(len(val_fail_msgs), 0)

    def test_config_params_invalid_repo_config_dict_none_passed_in(self):
        val_fail_msgs = artifactory.validate_config_params(
            self.config, None, 'config', 'config_dict')
        self.assertEqual(len(val_fail_msgs), 0)
