# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import copy
import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from xml.etree.ElementTree import fromstring, ElementTree

from units.compat.mock import patch
from units.modules.utils import set_module_args
from ansible.modules.networking.pfsense import pfsense_alias

from .pfsense_module import TestPFSenseModule, load_fixture


def args_from_var(var, state='present', **kwargs):
    """ return arguments for pfsense_alias module from var """
    args = {}
    for field in ['name', 'address', 'descr', 'type', 'updatefreq', 'detail']:
        if field in var and (state == 'present' or field == 'name'):
            args[field] = var[field]

    args['state'] = state
    for key, value in kwargs.items():
        args[key] = value

    return args


class TestPFSenseAliasModule(TestPFSenseModule):

    module = pfsense_alias

    def load_fixtures(self, commands=None):
        """ loading data """
        config_file = 'pfsense_alias_config.xml'
        self.parse.return_value = ElementTree(fromstring(load_fixture(config_file)))

    ########################################################
    # Generic set of funcs used for testing aliases
    # First we run the module
    # Then, we check return values
    # Finally, we check the xml
    def do_alias_creation_test(self, alias, failed=False, msg='', command=None):
        """ test creation of a new alias """
        set_module_args(args_from_var(alias))
        result = self.execute_module(changed=True, failed=failed, msg=msg)

        if not failed:
            diff = dict(before='', after=alias)
            self.assertEqual(result['diff'], diff)
            self.assert_xml_elt_dict('aliases', dict(name=alias['name'], type=alias['type']), diff['after'])
            self.assertEqual(result['commands'], [command])
        else:
            self.assertFalse(self.load_xml_result())

    def do_alias_deletion_test(self, alias, command=None):
        """ test deletion of an alias """
        set_module_args(args_from_var(alias, 'absent'))
        result = self.execute_module(changed=True)

        diff = dict(before=alias, after='')
        self.assertEqual(result['diff'], diff)
        self.assert_has_xml_tag('aliases', dict(name=alias['name'], type=alias['type']), absent=True)
        self.assertEqual(result['commands'], [command])

    def do_alias_update_noop_test(self, alias):
        """ test not updating an alias """
        set_module_args(args_from_var(alias))
        result = self.execute_module(changed=False)

        diff = dict(before=alias, after=alias)
        self.assertEqual(result['diff'], diff)
        self.assertFalse(self.load_xml_result())
        self.assertEqual(result['commands'], [])

    def do_alias_update_field(self, alias, set_after=None, command=None, **kwargs):
        """ test updating field of an host alias """
        target = copy(alias)
        target.update(kwargs)
        set_module_args(args_from_var(target))
        result = self.execute_module(changed=True)

        diff = dict(before=alias, after=copy(target))
        if set_after is not None:
            diff['after'].update(set_after)
        self.assertEqual(result['diff'], diff)
        self.assert_xml_elt_value('aliases', dict(name=alias['name'], type=alias['type']), 'address', diff['after']['address'])
        self.assertEqual(result['commands'], [command])

    ##############
    # hosts
    #
    def test_host_create(self):
        """ test creation of a new host alias """
        alias = dict(name='adservers', address='10.0.0.1 10.0.0.2', descr='', type='host', detail='')
        command = "create alias 'adservers', type='host', address='10.0.0.1 10.0.0.2', descr='', detail=''"
        self.do_alias_creation_test(alias, command=command)

    def test_host_delete(self):
        """ test deletion of an host alias """
        alias = dict(name='ad_poc1', address='192.168.1.3', descr='', type='host', detail='')
        command = "delete alias 'ad_poc1'"
        self.do_alias_deletion_test(alias, command=command)

    def test_host_update_noop(self):
        """ test not updating an host alias """
        alias = dict(name='ad_poc1', address='192.168.1.3', descr='', type='host', detail='')
        self.do_alias_update_noop_test(alias)

    def test_host_update_ip(self):
        """ test updating address of an host alias """
        alias = dict(name='ad_poc1', address='192.168.1.3', descr='', type='host', detail='')
        command = "update alias 'ad_poc1' set address='192.168.1.4'"
        self.do_alias_update_field(alias, address='192.168.1.4', command=command)

    def test_host_update_descr(self):
        """ test updating descr of an host alias """
        alias = dict(name='ad_poc1', address='192.168.1.3', descr='', type='host', detail='')
        command = "update alias 'ad_poc1' set descr='ad server'"
        self.do_alias_update_field(alias, descr='ad server', command=command)

    ##############
    # ports
    #
    def test_port_create(self):
        """ test creation of a new port alias """
        alias = dict(name='port_proxy', address='8080 8443', descr='', type='port', detail='')
        command = "create alias 'port_proxy', type='port', address='8080 8443', descr='', detail=''"
        self.do_alias_creation_test(alias, command=command)

    def test_port_delete(self):
        """ test deletion of a port alias """
        alias = dict(name='port_ssh', address='22', descr='', type='port', detail='')
        command = "delete alias 'port_ssh'"
        self.do_alias_deletion_test(alias, command=command)

    def test_port_update_noop(self):
        """ test not updating a port alias """
        alias = dict(name='port_ssh', address='22', descr='', type='port', detail='')
        self.do_alias_update_noop_test(alias)

    def test_port_update_port(self):
        """ test updating port of a port alias """
        alias = dict(name='port_ssh', address='22', descr='', type='port', detail='')
        command = "update alias 'port_ssh' set address='2222'"
        self.do_alias_update_field(alias, address='2222', command=command)

    def test_port_update_descr(self):
        """ test updating descr of a port alias """
        alias = dict(name='port_ssh', address='22', descr='', type='port', detail='')
        command = "update alias 'port_ssh' set descr='ssh port'"
        self.do_alias_update_field(alias, descr='ssh port', command=command)

    ##############
    # networks
    #
    def test_network_create(self):
        """ test creation of a new network alias """
        alias = dict(name='data_networks', address='192.168.1.0/24 192.168.2.0/24', descr='', type='network', detail='')
        command = "create alias 'data_networks', type='network', address='192.168.1.0/24 192.168.2.0/24', descr='', detail=''"
        self.do_alias_creation_test(alias, command=command)

    def test_network_delete(self):
        """ test deletion of a network alias """
        alias = dict(name='lan_data_poc3', address='192.168.3.0/24', descr='', type='network', detail='')
        command = "delete alias 'lan_data_poc3'"
        self.do_alias_deletion_test(alias, command=command)

    def test_network_update_noop(self):
        """ test not updating a network alias """
        alias = dict(name='lan_data_poc3', address='192.168.3.0/24', descr='', type='network', detail='')
        self.do_alias_update_noop_test(alias)

    def test_network_update_network(self):
        """ test updating address of a network alias """
        alias = dict(name='lan_data_poc3', address='192.168.3.0/24', descr='', type='network', detail='')
        command = "update alias 'lan_data_poc3' set address='192.168.2.0/24'"
        self.do_alias_update_field(alias, address='192.168.2.0/24', command=command)

    def test_network_update_descr(self):
        """ test updating descr of a network alias """
        alias = dict(name='lan_data_poc3', address='192.168.3.0/24', descr='', type='network', detail='')
        command = "update alias 'lan_data_poc3' set descr='data network'"
        self.do_alias_update_field(alias, descr='data network', command=command)

    ##############
    # urltables
    #
    def test_urltable_create(self):
        """ test creation of a new urltable alias """
        alias = dict(name='acme', address='http://www.acme.com', descr='', type='urltable', updatefreq='10', detail='')
        alias['url'] = alias['address']
        command = "create alias 'acme', type='urltable', address='http://www.acme.com', updatefreq='10', descr='', detail=''"
        self.do_alias_creation_test(alias, command=command)

    def test_urltable_delete(self):
        """ test deletion of a urltable alias """
        alias = dict(
            name='acme_corp', address='http://www.acme-corp.com', url='http://www.acme-corp.com', descr='', type='urltable', updatefreq='10', detail='')
        command = "delete alias 'acme_corp'"
        self.do_alias_deletion_test(alias, command=command)

    def test_urltable_update_noop(self):
        """ test not updating a urltable alias """
        alias = dict(
            name='acme_corp', address='http://www.acme-corp.com', url='http://www.acme-corp.com', descr='', type='urltable', updatefreq='10', detail='')
        self.do_alias_update_noop_test(alias)

    def test_urltable_update_url(self):
        """ test updating address of a urltable alias """
        alias = dict(
            name='acme_corp', address='http://www.acme-corp.com', url='http://www.acme-corp.com', descr='', type='urltable', updatefreq='10', detail='')
        command = "update alias 'acme_corp' set address='http://www.new-acme-corp.com'"
        self.do_alias_update_field(alias, address='http://www.new-acme-corp.com', set_after=dict(url='http://www.new-acme-corp.com'), command=command)

    def test_urltable_update_descr(self):
        """ test updating descr of a urltable alias """
        alias = dict(
            name='acme_corp', address='http://www.acme-corp.com', url='http://www.acme-corp.com', descr='', type='urltable', updatefreq='10', detail='')
        command = "update alias 'acme_corp' set descr='acme corp urls'"
        self.do_alias_update_field(alias, descr='acme corp urls', command=command)

    def test_urltable_update_freq(self):
        """ test updating updatefreq of a urltable alias """
        alias = dict(
            name='acme_corp', address='http://www.acme-corp.com', url='http://www.acme-corp.com', descr='', type='urltable', updatefreq='10', detail='')
        command = "update alias 'acme_corp' set updatefreq='20'"
        self.do_alias_update_field(alias, updatefreq='20', command=command)

    def test_urltable_ports_create(self):
        """ test creation of a new urltable_ports alias """
        alias = dict(name='acme', address='http://www.acme.com', descr='', type='urltable_ports', updatefreq='10', detail='')
        alias['url'] = alias['address']
        command = "create alias 'acme', type='urltable_ports', address='http://www.acme.com', updatefreq='10', descr='', detail=''"
        self.do_alias_creation_test(alias, command=command)

    ##############
    # misc
    #
    def test_create_alias_duplicate(self):
        """ test creation of a duplicate alias """
        alias = dict(name='port_ssh', address='10.0.0.1 10.0.0.2', type='host')
        self.do_alias_creation_test(alias, failed=True, msg='An alias with this name and a different type already exists')

    def test_create_alias_invalid_name(self):
        """ test creation of a new alias with invalid name """
        alias = dict(name='ads-ervers', address='10.0.0.1 10.0.0.2', type='host')
        self.do_alias_creation_test(alias, failed=True, msg='The name of the alias may only consist of the characters "a-z, A-Z, 0-9 and _"')

    def test_create_alias_invalid_updatefreq(self):
        """ test creation of a new host alias with incoherent params """
        alias = dict(name='adservers', address='10.0.0.1 10.0.0.2', type='host', updatefreq=10)
        self.do_alias_creation_test(alias, failed=True, msg='updatefreq is only valid with type urltable or urltable_ports')

    def test_create_alias_without_type(self):
        """ test creation of a new host alias without type """
        alias = dict(name='adservers', address='10.0.0.1 10.0.0.2')
        self.do_alias_creation_test(alias, failed=True, msg='state is present but all of the following are missing: type')

    def test_create_alias_without_address(self):
        """ test creation of a new host alias without address """
        alias = dict(name='adservers', type='host')
        self.do_alias_creation_test(alias, failed=True, msg='state is present but all of the following are missing: address')

    def test_create_alias_invalid_details(self):
        """ test creation of a new host alias with invalid details """
        alias = dict(name='adservers', address='10.0.0.1 10.0.0.2', type='host', detail='ad1||ad2||ad3')
        self.do_alias_creation_test(alias, failed=True, msg='Too many details in relation to addresses')

    def test_create_alias_invalid_details2(self):
        """ test creation of a new host alias with invalid details """
        alias = dict(name='adservers', address='10.0.0.1 10.0.0.2', type='host', detail='|ad1||ad2')
        self.do_alias_creation_test(alias, failed=True, msg='Vertical bars (|) at start or end of descriptions not allowed')

    def test_delete_inexistent_alias(self):
        """ test deletion of an inexistent alias """
        alias = dict(name='ad_poc12', address='192.168.1.3', descr='', type='host', detail='')
        set_module_args(args_from_var(alias, 'absent'))
        result = self.execute_module(changed=False)

        diff = dict(before='', after='')
        self.assertEqual(result['diff'], diff)
        self.assertEqual(result['commands'], [])

    def test_delete_invalid_param(self):
        """ test deletion of an host alias with invalid params """
        alias = dict(name='ad_poc1', address='192.168.1.3', descr='', type='host', detail='')
        args = args_from_var(alias)
        args['state'] = 'absent'
        set_module_args(args)
        self.execute_module(failed=True, msg="address is invalid with state='absent'")

    def test_check_mode(self):
        """ test updating an host alias without generating result """
        alias = dict(name='ad_poc1', address='192.168.1.3', descr='', type='host', detail='')
        set_module_args(args_from_var(alias, address='192.168.1.4', _ansible_check_mode=True))
        result = self.execute_module(changed=True)

        diff = dict(before=alias, after=copy(alias))
        diff['after']['address'] = '192.168.1.4'
        self.assertEqual(result['diff'], diff)
        self.assertFalse(self.load_xml_result())
        self.assertEqual(result['commands'], ["update alias 'ad_poc1' set address='192.168.1.4'"])

    def test_urltable_required_if(self):
        """ test creation of a new urltable alias without giving updatefreq (should fail) """
        alias = dict(name='acme', address='http://www.acme.com', descr='', type='urltable', detail='')
        set_module_args(args_from_var(alias))
        self.execute_module(failed=True, msg='type is urltable but all of the following are missing: updatefreq')

    def test_urltable_ports_required_if(self):
        """ test creation of a new urltable_ports alias without giving updatefreq (should fail) """
        alias = dict(name='acme', address='http://www.acme.com', descr='', type='urltable_ports', detail='')
        set_module_args(args_from_var(alias))
        self.execute_module(failed=True, msg='type is urltable_ports but all of the following are missing: updatefreq')
