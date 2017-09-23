from mock import patch, Mock, mock_open, call
import json
import os
from copy import deepcopy

from ansible.compat.tests.unittest import TestCase
from ansible.module_utils.fortios import API

interface_api_args = {
    "endpoint": ["cmdb", "system", "interface"],
    "list_identifier": "interfaces",
    "object_identifier": "name",
    "default_ignore_params": ['macaddr', 'vdom', 'type']
}

import sys
if sys.version_info[0] < 3:
    b_open = "__builtin__.open"
else:
    b_open = "builtins.open"

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')


class APITest(TestCase):

    def setUp(self):
        self.default_current_config = json.load(open(fixture_path + "/interfaceCurrentConfig.json"))['interface']
        self.default_object = json.load(open(fixture_path + "/interfaceDefaultObject.json"))['interface']

        self.mock_response = Mock()
        mock_cookie = Mock()
        mock_cookie.name = "ccsrftoken"
        mock_cookie.value = "ccsrftoken"
        self.mock_response.cookies = [mock_cookie, ]
        self.mock_response.status_code = 200
        self.mock_response.content = json.dumps({"http_status": 200})

        self.mock_get_response = deepcopy(self.mock_response)
        self.mock_get_response.content = json.dumps(
            {"results": self.default_current_config, "http_status": 200})

        self.get_patcher = patch("ansible.module_utils.fortios.requests.get")
        self.mock_get = self.get_patcher.start()
        self.mock_get.return_value = self.mock_get_response

        self.post_patcher = patch("ansible.module_utils.fortios.requests.post")
        self.mock_post = self.post_patcher.start()
        self.mock_post.return_value = self.mock_response

        self.put_patcher = patch("ansible.module_utils.fortios.requests.put")
        self.mock_put = self.put_patcher.start()
        self.mock_put.return_value = self.mock_response

        self.delete_patcher = patch(
            "ansible.module_utils.fortios.requests.delete")
        self.mock_delete = self.delete_patcher.start()
        self.mock_delete.return_value = self.mock_response

        self.default_api_args = interface_api_args
        perm_objs = ["port%d" % i for i in range(1, 11)]
        perm_objs.append('ssl.root')
        self.default_api_args['permanent_objects'] = perm_objs
        self.default_endpoint = self.default_api_args['endpoint']
        self.default_endpoint_str = "/".join(self.default_endpoint)
        self.default_list_identifier = self.default_api_args['list_identifier']
        self.default_object_identifier = self.default_api_args[
            'object_identifier']
        self.default_permanent_objects = self.default_api_args[
            'permanent_objects']
        for i in self.default_api_args['default_ignore_params']:
            del self.default_object[i]

        self.default_conn_params = {
            "fortigate_password": "test",
            "fortigate_ip": "test.fortigate.com",
            "verify": False,
            "disable_warnings": True,
            "fortigate_username": "admin",
            "port": 10443
        }
        self.default_password = self.default_conn_params['fortigate_password']
        self.default_username = self.default_conn_params['fortigate_username']
        self.default_ip = self.default_conn_params['fortigate_ip']
        self.default_port = self.default_conn_params['port']
        self.default_verify = self.default_conn_params['verify']
        self.default_url = "https://" + self.default_ip + ":%d" % self.default_port
        self.default_endpoint_url = self.default_url + \
            "/api/v2/" + self.default_endpoint_str
        self.default_update_config = json.load(open(fixture_path + "/interfaceUpdateConfig.json"))["interfaces"]
        self.default_params = {
            "conn_params": self.default_conn_params,
            "print_current_config": False,
        }

        self.default_login_call = call(self.default_url + "/logincheck", data={'username': self.default_username, "secretkey": self.default_password},
                                       proxies=None, verify=self.default_verify)

        self.load_params_patcher = patch(
            "ansible.module_utils.fortios._load_params")
        self.mock_load_params = self.load_params_patcher.start()
        self.mock_load_params.return_value = self.default_params

        self.get_arg_spec_original = API._get_argument_spec
        self.get_arg_spec_patcher = patch(
            "ansible.module_utils.fortios.API._get_argument_spec")
        self.mock_get_arg_spec = self.get_arg_spec_patcher.start()
        self.mock_get_arg_spec.return_value = json.load(open(fixture_path + "/listArgumentSpec.json"))['interface_arg_spec']

        self.get_default_object_original = API._get_default_object
        self.get_default_object_patcher = patch(
            "ansible.module_utils.fortios.API._get_default_object")
        self.mock_get_default_object = self.get_default_object_patcher.start()
        self.mock_get_default_object.return_value = self.default_object

        self.ansible_module_patcher = patch(
            "ansible.module_utils.fortios.AnsibleModule")
        self.mock_ansible_module = self.ansible_module_patcher.start()

        self.fw_api = API(self.default_api_args)
        self.fw_api._print_current_config = False
        self.fw_api._update_config = self.default_update_config
        self.fw_api._fortigate_current_config = self.default_current_config
        self.fw_api._check_mode = False

        self.mock_exit_json = Mock()
        self.fw_api._module.exit_json = self.mock_exit_json

    def tearDown(self):
        del self.fw_api
        self.get_default_object_patcher.stop()
        self.get_arg_spec_patcher.stop()
        self.load_params_patcher.stop()
        self.ansible_module_patcher.stop()
        self.delete_patcher.stop()
        self.get_patcher.stop()
        self.put_patcher.stop()
        self.post_patcher.stop()

    def test_edit_endpoint(self):
        self.mock_post.assert_called_once()
        self.fw_api._edit("/".join(self.default_endpoint))
        self.mock_put.assert_called_once_with(self.default_endpoint_url, cookies=self.fw_api.cookies, headers=self.fw_api.header,
                                              proxies=self.fw_api.proxies, json={'json': None}, params={"vdom": self.fw_api._vdom},
                                              verify=self.fw_api._verify)

    def test_process_response(self):
        # succeeded, matches original, matches update
        self.fw_api._update_config = self.default_current_config
        message, changed, failed = self.fw_api._process_response()
        assert changed is False
        assert failed is False

        # succeeded, doesn't match original, matches update
        self.fw_api._fortigate_original_config = self.default_update_config
        message, changed, failed = self.fw_api._process_response()
        assert changed is True
        assert failed is False

        # succeeded, doesn't match original, doesn't match update
        self.fw_api._update_config = self.default_update_config
        fail_patcher = patch("ansible.module_utils.fortios.API.fail")
        mock_fail = fail_patcher.start()

        try:
            self.fw_api._process_response()
        except UnboundLocalError:
            pass

        mock_fail.assert_called_once_with(
            "Configuration update failed and rollback failed, configuration appears to be in a partially applied state.")
        fail_patcher.stop()

        # failed, matches original, doesn't match update
        self.fw_api._fortigate_original_config = self.default_current_config
        message, changed, failed = self.fw_api._process_response()
        assert changed is False
        assert failed is True

    def test_setup_configs_for_diff(self):

        current_config, update_config, objects_only_in_update = self.fw_api._setup_configs_for_diff(self.default_current_config,
                                                                                                    sorted(self.default_update_config, key=lambda k: k['name']))

        update_objects = [o[self.default_object_identifier]
                          for o in self.default_update_config]
        expected_current_config = deepcopy(self.default_current_config)
        non_update_objects = [o[self.default_object_identifier] for o in expected_current_config if o[
            self.default_object_identifier] not in update_objects]
        for i, v in enumerate(expected_current_config):
            if v[self.default_object_identifier] in non_update_objects:
                del expected_current_config[i]
        expected_current_config = sorted(
            expected_current_config, key=lambda k: k['name'], )

        assert current_config == expected_current_config
        assert update_config == sorted(
            self.default_update_config, key=lambda k: k['name'], )
        assert objects_only_in_update == []

        self.default_update_config.append(
            {self.default_object_identifier: 'test_failure'})
        expected_current_config.append(None)
        current_config, update_config, objects_only_in_update = self.fw_api._setup_configs_for_diff(self.default_current_config,
                                                                                                    sorted(self.default_update_config, key=lambda k: k['name']))
        assert current_config == expected_current_config
        assert update_config == sorted(
            self.default_update_config, key=lambda k: k['name'], )
        assert objects_only_in_update == [
            {self.default_object_identifier: 'test_failure'}]

        current_config, update_config, objects_only_in_update = self.fw_api._setup_configs_for_diff(
            self.default_current_config, [])
        assert current_config == self.default_current_config
        assert update_config == []
        assert objects_only_in_update == []

        current_config, update_config, objects_only_in_update = self.fw_api._setup_configs_for_diff([
        ], [])
        assert current_config == []
        assert update_config == []
        assert objects_only_in_update == []

    def test_configs_match(self):
        examples_file = json.load(open(fixture_path + "/matchConfigs.json"))
        original = examples_file['original']
        current = examples_file['current']
        update = examples_file['updated']

        assert self.fw_api._configurations_match(current, original)

        for i in update:
            if i[self.default_object_identifier] != 'netapp_pub':
                j = self.fw_api._get_object_from_list_by_id(
                    current, i[self.default_object_identifier])
                assert self.fw_api._dictionaries_match(j, i)

        assert not self.fw_api._configurations_match(current, update)

        assert not self.fw_api._configurations_match([], update)

        assert not self.fw_api._configurations_match(current, [])

        current_config = examples_file['current2']
        update_config = examples_file['update2']

        assert not self.fw_api._dictionaries_match(
            current_config, update_config)

        assert not self.fw_api._configurations_match()

        self.fw_api._update_config = self.default_current_config
        assert self.fw_api._configurations_match()

        updated_config = deepcopy(self.default_update_config)
        for o in updated_config:
            for k, v in self.default_object.items():
                if k not in o:
                    o[k] = v
        self.fw_api._fortigate_current_config = updated_config
        self.fw_api._update_config = self.default_update_config
        assert self.fw_api._configurations_match()

        self.fw_api._fortigate_current_config = examples_file[
            'example_current']
        self.fw_api._update_config = examples_file['example_update']

        assert not self.fw_api._configurations_match()

    def test_diff_configs(self):
        examples = json.load(open(fixture_path + "/diffConfigs.json"))
        prefixes = examples['prefixes']
        current = examples['current']
        expected = examples['expected']

        assert self.fw_api._diff_configs(current, prefixes) == expected

    def test_diff_configs_failure(self):
        examples = json.load(open(fixture_path + "/diffConfigs.json"))
        self.fw_api._fortigate_original_config = examples['original_failure']
        self.fw_api._fortigate_current_config = examples['current_failure']
        self.fw_api._update_config = examples['update_failure']

        assert self.fw_api._diff_configs() == {
            'redistribute': None, 'network': None, 'neighbor': None, 'aggregate-address': None}

    def test_dictionaries_match(self):
        examples = json.load(open(fixture_path + '/matchDicts.json'))
        current_config = examples['current_config']
        update_config = examples['update_config']

        assert not self.fw_api._dictionaries_match(
            current_config, update_config)

        current_config = {
            'netflow-sampler': 'disable',
            'security-mac-auth-bypass': 'disable',
            'bfd': 'global',
            'dhcp-client-identifier': '',
            'fortilink': [],
            'password': 'ENC XXXX',
            'device-identification-active-scan': 'enable',
            'weight': '0',
            'broadcast-forticlient-discovery': 'disable',
            'auto-auth-extension-device': 'disable',
            'role': 'undefined',
            'q_origin_key': 'port1',
            'secondary-IP': 'disable',
            'vlanid': '0',
            'ident-accept': 'disable',
            'ipv6': {'autoconf': 'disable',
                     'dhcp6-client-options': 'dns',
                     'dhcp6-prefix-delegation': 'disable',
                     'dhcp6-prefix-hint': '::/0',
                     'dhcp6-prefix-hint-plt': 604800,
                     'dhcp6-prefix-hint-vlt': 2592000,
                     'dhcp6-relay-ip': '',
                     'dhcp6-relay-service': 'disable',
                     'dhcp6-relay-type': 'regular',
                     'ip6-address': '::/0',
                     'ip6-allowaccess': '',
                     'ip6-default-life': 1800,
                     'ip6-delegated-prefix-list': [],
                     'ip6-dns-server-override': 'enable',
                     'ip6-extra-addr': [],
                     'ip6-hop-limit': 0,
                     }
        }
        update_config = {
            'netflow-sampler': 'disable',
            'security-mac-auth-bypass': 'disable',
            'bfd': 'global',
            'dhcp-client-identifier': '',
            'fortilink': [],
            'password': 'ENC XXXX',
        }

        assert self.fw_api._dictionaries_match(current_config, update_config)

    def test_nested_sub_lists(self):
        examples = json.load(open(fixture_path + "/nestedSubLists.json"))
        raw = examples['raw']
        update = examples['update']
        expected = examples['expected']

        assert self.fw_api._diff_dicts(raw[1]['rule'][0], update[
                                       1]['rule'][0]) == expected

        assert self.fw_api._diff_lists(raw[1]['rule'], update[1]['rule']) == [
            {"ge": 24, "le": 26}]

        assert self.fw_api._diff_dicts(raw[1], update[1]) == {
            "rule": [{"ge": 24, "le": 26}]}
        assert self.fw_api._diff_configs(raw, update) == [
            {'name': 'advertise_blocks', 'rule': [
                None, None, {'ge': 24, 'le': 27}]},
            {'name': 'advertise_private_blocks',
                'rule': [{'ge': 24, 'le': 26}]},
            {'name': 'dwre_sf_block',
             'rule': [{'ge': 24, 'le': 26}, None, None, None, None,
                      {'ge': 21, 'le': 30}]},
        ]
        assert not self.fw_api._configurations_match(raw, update)
        examples_file = json.load(open(fixture_path + "/failedConfigs.json"))
        current = examples_file['current']
        update = examples_file['update']

        assert not self.fw_api._configurations_match(current, update)

    def test_get_argument_spec_list_endpoint_(self):
        final_spec = json.load(open(fixture_path + "/listArgumentSpec.json"))['interface_arg_spec']

        mock_schema = Mock(content=json.dumps(json.load(open(fixture_path + "/interfaceSchema.json"))['interface_schema_response']))
        self.mock_get.return_value = mock_schema

        open_patcher = patch(b_open)
        m_open = open_patcher.start()
        m_open.side_effect = IOError

        write_local_patcher = patch(
            "ansible.module_utils.fortios.API._write_local_spec")
        mock_write_local = write_local_patcher.start()

        self.get_arg_spec_patcher.stop()
        self.get_arg_spec_patcher = patch(
            "ansible.module_utils.fortios.API._get_argument_spec", self.get_arg_spec_original)
        self.get_arg_spec_patcher.start()

        spec = self.fw_api._get_argument_spec()
        self.mock_get.assert_called_once()
        assert spec == final_spec
        mock_write_local.assert_has_calls(
            [call({self.default_endpoint_str: {'arg_spec': final_spec}})])

        open_patcher.stop()
        write_local_patcher.stop()

    def test_get_argument_spec_single_object_endpoint(self):
        mock_schema = Mock(content=json.dumps(json.load(open(
            fixture_path + "/systemGlobalSchemaResponse.json"))["system_global_schema_response"]))
        self.mock_get.return_value = mock_schema
        final_spec = json.load(open(fixture_path + "/systemGlobalArgSpec.json"))['system_global_arg_spec']

        open_patcher = patch(b_open)
        m_open = open_patcher.start()
        m_open.side_effect = IOError

        write_local_patcher = patch(
            "ansible.module_utils.fortios.API._write_local_spec")
        mock_write_local = write_local_patcher.start()

        self.get_arg_spec_patcher.stop()
        self.get_arg_spec_patcher = patch(
            "ansible.module_utils.fortios.API._get_argument_spec", self.get_arg_spec_original)
        self.get_arg_spec_patcher.start()

        spec = self.fw_api._get_argument_spec()
        self.mock_get.assert_called_once()

        open_patcher.stop()
        write_local_patcher.stop()

        assert spec == final_spec
        mock_write_local.assert_has_calls(
            [call({self.default_endpoint_str: {'arg_spec': final_spec}})])

    def test_get_argument_spec_local_copy(self):
        self.get_arg_spec_patcher.stop()
        self.get_arg_spec_patcher = patch(
            "ansible.module_utils.fortios.API._get_argument_spec", self.get_arg_spec_original)
        self.get_arg_spec_patcher.start()

        list_argument_spec = json.load(open(fixture_path + "/listArgumentSpec.json"))['interface_arg_spec']

        m_open = mock_open(read_data=json.dumps(
            {self.default_endpoint_str: {'arg_spec': list_argument_spec}}))
        m_open.side_effect = None
        open_patcher = patch(b_open, m_open)
        open_patcher.start()

        write_local_patcher = patch(
            "ansible.module_utils.fortios.API._write_local_spec")
        mock_write_local = write_local_patcher.start()

        spec = self.fw_api._get_argument_spec()
        final_spec = list_argument_spec

        m_open.assert_has_calls([
            call('FortiosAPIArgSpecs.json', 'r+'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
        ])
        self.mock_get.assert_not_called()
        assert spec == final_spec
        mock_write_local.assert_not_called()

        open_patcher.stop()
        write_local_patcher.stop()

    def test_get_default_object_from_endpoint(self):
        example_object = json.load(open(fixture_path + "/interfaceDefaultObject.json"))['interface']
        expected_final_object = deepcopy(example_object)
        for i in self.fw_api._api_info['default_ignore_params']:
            del expected_final_object[i]
        mock_object = Mock(content=json.dumps({'results': example_object}))
        self.mock_get.return_value = mock_object

        open_patcher = patch(b_open)
        m_open = open_patcher.start()
        m_open.side_effect = IOError

        write_local_patcher = patch(
            "ansible.module_utils.fortios.API._write_local_spec")
        mock_write_local = write_local_patcher.start()

        self.get_default_object_patcher.stop()
        self.get_default_object_patcher = patch(
            "ansible.module_utils.fortios.API._get_default_object", self.get_default_object_original)
        self.get_default_object_patcher.start()

        final_object = self.fw_api._get_default_object()

        self.mock_get.assert_called_once()
        assert final_object == expected_final_object
        mock_write_local.assert_has_calls(
            [call({self.default_endpoint_str: {'default_object': expected_final_object}})])

        open_patcher.stop()
        write_local_patcher.stop()

    def test_get_default_object_local_copy(self):
        self.mock_get_default_object.side_effect = self.get_default_object_original

        m_open = mock_open(read_data=json.dumps(
            {self.default_endpoint_str: {'default_object': self.default_object}}))
        open_patcher = patch(b_open, m_open)
        open_patcher.start()

        write_local_patcher = patch(
            "ansible.module_utils.fortios.API._write_local_spec")
        mock_write_local = write_local_patcher.start()

        self.get_default_object_patcher.stop()
        self.get_default_object_patcher = patch(
            "ansible.module_utils.fortios.API._get_default_object", self.get_default_object_original)
        self.get_default_object_patcher.start()

        assert self.fw_api._get_default_object() == self.default_object
        self.mock_get.assert_not_called()
        mock_write_local.assert_not_called()

        open_patcher.stop()
        write_local_patcher.stop()

    def test_create_new_objects(self):
        self.fw_api._object_map = [None for i in self.default_current_config]

        self.fw_api._create_new_objects()
        self.mock_post.assert_has_calls([self.default_login_call])

    def test_apply_configuration_failure(self):
        # raises a StopIteration error for reasons I don't understand
        failed_response = deepcopy(self.mock_response)
        failed_response.content = json.dumps({"http_status": 405})

        self.fw_api._update_config[0]['name'] = 'test1'
        self.fw_api._update_config[1]['name'] = 'test2'

        fail_patcher = patch("ansible.module_utils.fortios.API.fail")
        mock_fail = fail_patcher.start()

        self.mock_post.return_value = None
        self.mock_post.side_effect = [failed_response, failed_response]

        self.fw_api._object_map = [None for i in self.default_current_config]

        self.fw_api._create_new_objects()

        mock_fail.assert_called_once_with(
            'Failed to create objects:\n ', msg_args={'test1': 'HTTP method not allowed for this resource.',
                                                      'test2': 'HTTP method not allowed for this resource.'})

        calls = [self.default_login_call, ]
        for policy in self.fw_api._update_config[:2]:
            calls.append(call(self.default_endpoint_url, headers=self.fw_api.header, cookies=self.fw_api.cookies, verify=False,
                              proxies=None, params={"vdom": self.fw_api._vdom}, json={'json': policy}))
        self.mock_post.assert_has_calls(calls)

        fail_patcher.stop()

    def test_apply_configuration_update_all_objects(self):
        objects = [o for o in self.default_update_config if o[
            self.default_object_identifier] not in ('port1', 'port5')]
        object1_data = deepcopy(self.default_object)
        object1_data['name'] = 'port1'
        objects.append(object1_data)
        object2_data = deepcopy(self.default_object)
        object2_data['name'] = 'port5'
        object2_data['q_origin'] = 'port5'
        objects.append(object2_data)

        calls = []
        for obj in objects:
            calls.append(call(self.default_endpoint_url + '/%s' % obj['name'], headers=self.fw_api.header, cookies=self.fw_api.cookies,
                              verify=False, proxies=None, params={"vdom": self.fw_api._vdom}, json={'json': obj}))

        self.fw_api._update_config = objects
        self.fw_api.apply_configuration_to_endpoint()
        self.mock_put.assert_has_calls(calls)

    def test_apply_configuration_update_unspecified_permanent_objects_to_default(self):
        self.fw_api._update_config = deepcopy(
            self.fw_api._fortigate_current_config)
        del self.fw_api._update_config[0]
        del self.fw_api._update_config[1]

        self.fw_api.apply_configuration_to_endpoint()

        call_ids = ['port1', 'port3']
        calls = []
        for call_id in call_ids:
            data = deepcopy(self.default_object)
            data['name'] = call_id
            calls.append(call(self.default_endpoint_url + '/%s' % call_id, cookies=self.fw_api.cookies, headers=self.fw_api.header, json={'json': data},
                              params={"vdom": self.fw_api._vdom}, proxies=None, verify=False))

        self.mock_put.assert_has_calls(calls)

    def test_remove_policy_from_current_config(self):
        fw_policy_config = json.load(open(fixture_path + "/firewallCurrentConfig.json"))['firewall_policy']
        self.fw_api._fortigate_current_config = fw_policy_config
        self.fw_api._object_identifier = 'policyid'

        supplied_config = deepcopy(fw_policy_config)

        self.fw_api._remove_object_from_current_config(5)
        del supplied_config[1]
        assert self.fw_api._fortigate_current_config == supplied_config

        self.fw_api._remove_object_from_current_config(2)
        assert self.fw_api._fortigate_current_config == supplied_config

        self.fw_api._remove_object_from_current_config(14)
        del supplied_config[0]
        assert self.fw_api._fortigate_current_config == supplied_config

        self.fw_api._remove_object_from_current_config(18)
        del supplied_config[2]
        assert self.fw_api._fortigate_current_config == supplied_config

        self.fw_api._remove_object_from_current_config(15)
        del supplied_config[1]
        assert self.fw_api._fortigate_current_config == supplied_config

        self.fw_api._remove_object_from_current_config(16)
        del supplied_config[0]
        assert self.fw_api._fortigate_current_config == supplied_config

    def test_apply_existing_and_new_objects(self):
        fw_policy_config = json.load(open(fixture_path + "/firewallCurrentConfig.json"))['firewall_policy']
        self.mock_get_response.content = json.dumps({"results": fw_policy_config, "http_status": 200})
        self.fw_api._update_config = json.load(open(fixture_path + "/firewallUpdateConfig.json"))['policies']
        self.fw_api._object_identifier = 'policyid'

        modified_update = deepcopy(fw_policy_config)
        modified_update.insert(0, modified_update[2])
        del modified_update[3]
        del modified_update[2]
        modified_update[3]['policyid'] = 24
        self.fw_api._update_config = modified_update

        self.fw_api.apply_configuration_to_endpoint()

        delete_calls = [
            call(self.default_endpoint_url + '/5', headers=self.fw_api.header, cookies=self.fw_api.cookies,
                 params={"vdom": self.fw_api._vdom}, proxies=None, verify=False, json={'json': None}),
            call(self.default_endpoint_url + '/18', headers=self.fw_api.header, cookies=self.fw_api.cookies,
                 params={"vdom": self.fw_api._vdom}, proxies=None, verify=False, json={'json': None})
        ]
        self.mock_delete.assert_has_calls(delete_calls)

        expected = fw_policy_config[4]
        expected['policyid'] = 24

        post_calls = [
            self.default_login_call,
            call(self.default_endpoint_url, headers=self.fw_api.header, cookies=self.fw_api.cookies,
                 params={"vdom": self.fw_api._vdom}, proxies=None, verify=False, json={'json': expected}),
        ]

        self.mock_post.assert_has_calls(post_calls)

    def test_apply_configuration_delete_all_objects(self):
        firewall_config = json.load(open(fixture_path + "/firewallCurrentConfig.json"))['firewall_policy']
        self.mock_get_response.content = json.dumps({"results": firewall_config, "http_status": 200})
        self.fw_api._update_config = []
        self.fw_api.apply_configuration_to_endpoint()

        calls = []
        for i, pol in enumerate([p for p in firewall_config if p[self.default_object_identifier]]):
            calls.append(call(self.default_endpoint_url + "/%s" % str(pol[self.default_object_identifier]), headers=self.fw_api.header,
                              cookies=self.fw_api.cookies, params={"vdom": self.fw_api._vdom}, proxies=None, verify=False, json={'json': None}))
        self.mock_delete.assert_has_calls(calls)

    def test_delete_unused_objects(self):
        self.fw_api._object_identifier = 'policyid'
        self.fw_api._object_map = [
            None,
            None,
            None,
            None,
            None,
        ]
        self.fw_api._fortigate_current_config = [{'policyid': 4}, {'policyid': 1}, {'policyid': 2}, {'policyid': 5}, {'policyid': 3}]
        self.fw_api._existing_object_ids = [k['policyid'] for k in self.fw_api._fortigate_current_config]

        self.fw_api._delete_unused_objects()
        calls = []
        for pol in self.fw_api._fortigate_current_config:
            calls.append(call(self.default_url + '/' + str(pol['policyid']), headers=self.fw_api.header, cookies=self.fw_api.cookies,
                              verify=False, proxies=None, params={"vdom": self.fw_api._vdom}, json={'json': None}))
        self.mock_delete.assert_has_calls(calls)

    def test_create_new_objects_no_new(self):
        self.fw_api._create_new_objects()
        self.mock_post.assert_has_calls([self.default_login_call])

    def test_delete_unused_objects_no_deletes(self):
        self.fw_api._create_new_objects()
        self.mock_delete.assert_not_called()

    def test_process_schema_single_object_endpoint(self):
        arg_spec = self.fw_api._process_schema(json.load(open(
            fixture_path + "/systemGlobalSchemaResponse.json"))["system_global_schema_response"]['results'])
        assert arg_spec == json.load(open(fixture_path + "/systemGlobalArgSpec.json"))['system_global_arg_spec']

    def test_process_schema_list_object_endpoint(self):
        arg_spec = self.fw_api._process_schema(json.load(open(
            fixture_path + "/interfaceSchema.json"))["interface_schema_response"]['results'])
        assert arg_spec == json.load(open(fixture_path + "/listArgumentSpec.json"))['interface_arg_spec']

    def test_check_mode(self):
        self.fw_api._check_mode = True

        self.fw_api.apply_configuration_to_endpoint()

        self.mock_delete.assert_not_called()
        self.mock_put.assert_not_called()
        self.mock_post.assert_has_calls([self.default_login_call])

        self.mock_exit_json.assert_called_once()
        assert self.mock_exit_json.mock_calls[0].startswith("Check Mode")

    def test_clear_endpoint_for_empty_update(self):
        self.fw_api._update_config = []
        self.fw_api.apply_configuration_to_endpoint()
        self.mock_delete.assert_has_calls([
            call(self.default_endpoint_url, cookies=self.fw_api.cookies, headers=self.fw_api.header,
                 json={'json': None}, params=None, proxies=None, verify=False)
        ])

    def test_original_or_update_match_current_configuration(self):
        self.fw_api._fortigate_original_config = deepcopy(
            self.fw_api._fortigate_current_config)
        self.fw_api._fortigate_original_config.append(
            {"name": "longer_original_diff"})

        orig, update = self.fw_api._original_or_update_match_current_configuration()

        assert not orig
        assert not update

        self.fw_api._fortigate_original_config = self.fw_api._fortigate_original_config[
            :-2]

        orig, update = self.fw_api._original_or_update_match_current_configuration()

        assert not orig
        assert not update

        self.fw_api._fortigate_original_config = deepcopy(
            self.fw_api._fortigate_current_config)
        self.fw_api._update_config = deepcopy(
            self.fw_api._fortigate_current_config)

        orig, update = self.fw_api._original_or_update_match_current_configuration()

        assert orig
        assert update
