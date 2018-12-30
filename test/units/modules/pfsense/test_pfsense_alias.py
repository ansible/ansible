# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from copy import copy
from xml.etree.ElementTree import fromstring, ElementTree

from units.compat.mock import patch
from units.modules.utils import set_module_args
from ansible.modules.pfsense import pfsense_alias

from .pfsense_module import TestPFSenseModule, load_fixture


def args_from_var(var, state='present', **kwargs):
    """ return arguments for pfsense_alias module from var """
    args = {}
    for field in ['name', 'address', 'descr', 'type', 'updatefreq']:
        if field in var:
            args[field] = var[field]

    args['state'] = state
    for key, value in kwargs.items():
        args[key] = value

    return args


class TestPFSenseAliasModule(TestPFSenseModule):

    module = pfsense_alias

    def setUp(self):
        """ mocking up """
        super(TestPFSenseAliasModule, self).setUp()

        self.mock_parse = patch('xml.etree.ElementTree.parse')
        self.parse = self.mock_parse.start()

        self.mock_shutil_move = patch('shutil.move')
        self.shutil_move = self.mock_shutil_move.start()

        self.mock_phpshell = patch('ansible.module_utils.pfsense.pfsense.PFSenseModule.phpshell')
        self.phpshell = self.mock_phpshell.start()
        self.phpshell.return_value = (0, '', '')

        self.maxDiff = None

    def tearDown(self):
        """ mocking down """
        super(TestPFSenseAliasModule, self).tearDown()

        self.mock_parse.stop()
        self.mock_shutil_move.stop()
        self.mock_phpshell.stop()

    def load_fixtures(self, commands=None):
        """ loading data """
        config_file = 'pfsense_alias_config.xml'
        self.parse.return_value = ElementTree(fromstring(load_fixture(config_file)))

    ########################################################
    # Generic set of funcs used for testing aliases
    # First we run the module
    # Then, we check return values
    # Finally, we check the xml
    def do_alias_creation_test(self, alias):
        """ test creation of a new alias """
        set_module_args(args_from_var(alias))
        result = self.execute_module(changed=True)

        diff = dict(before='', after=alias)
        self.assertEqual(result['diff'], diff)
        self.assert_xml_elt_dict('aliases', dict(name=alias['name'], type=alias['type']), diff['after'])

    def do_alias_deletion_test(self, alias):
        """ test deletion of an alias """
        set_module_args(args_from_var(alias, 'absent'))
        result = self.execute_module(changed=True)

        diff = dict(before=alias, after='')
        self.assertEqual(result['diff'], diff)
        self.assert_has_xml_tag('aliases', dict(name=alias['name'], type=alias['type']), absent=True)

    def do_alias_update_noop_test(self, alias):
        """ test not updating an alias """
        set_module_args(args_from_var(alias))
        result = self.execute_module(changed=False)

        diff = dict(before=alias, after=alias)
        self.assertEqual(result['diff'], diff)
        self.assertFalse(self.load_xml_result())

    def do_alias_update_field(self, alias, set_after=None, **kwargs):
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

    ##############
    # hosts
    #
    def test_host_create(self):
        """ test creation of a new host alias """
        alias = dict(name='adservers', address='10.0.0.1 10.0.0.2', descr='', type='host', detail='')
        self.do_alias_creation_test(alias)

    def test_host_delete(self):
        """ test deletion of an host alias """
        alias = dict(name='ad_poc1', address='192.168.1.3', descr='', type='host', detail='')
        self.do_alias_deletion_test(alias)

    def test_host_update_noop(self):
        """ test not updating an host alias """
        alias = dict(name='ad_poc1', address='192.168.1.3', descr='', type='host', detail='')
        self.do_alias_update_noop_test(alias)

    def test_host_update_ip(self):
        """ test updating address of an host alias """
        alias = dict(name='ad_poc1', address='192.168.1.3', descr='', type='host', detail='')
        self.do_alias_update_field(alias, address='192.168.1.4')

    def test_host_update_descr(self):
        """ test updating descr of an host alias """
        alias = dict(name='ad_poc1', address='192.168.1.3', descr='', type='host', detail='')
        self.do_alias_update_field(alias, descr='ad server')

    ##############
    # ports
    #
    def test_port_create(self):
        """ test creation of a new port alias """
        alias = dict(name='port_proxy', address='8080 8443', descr='', type='port', detail='')
        self.do_alias_creation_test(alias)

    def test_port_delete(self):
        """ test deletion of a port alias """
        alias = dict(name='port_ssh', address='22', descr='', type='port', detail='')
        self.do_alias_deletion_test(alias)

    def test_port_update_noop(self):
        """ test not updating a port alias """
        alias = dict(name='port_ssh', address='22', descr='', type='port', detail='')
        self.do_alias_update_noop_test(alias)

    def test_port_update_port(self):
        """ test updating port of a port alias """
        alias = dict(name='port_ssh', address='22', descr='', type='port', detail='')
        self.do_alias_update_field(alias, address='2222')

    def test_port_update_descr(self):
        """ test updating descr of a port alias """
        alias = dict(name='port_ssh', address='22', descr='', type='port', detail='')
        self.do_alias_update_field(alias, descr='ssh port')

    ##############
    # networks
    #
    def test_network_create(self):
        """ test creation of a new network alias """
        alias = dict(name='data_networks', address='192.168.1.0/24 192.168.2.0/24', descr='', type='network', detail='')
        self.do_alias_creation_test(alias)

    def test_network_delete(self):
        """ test deletion of a network alias """
        alias = dict(name='lan_data_poc3', address='192.168.3.0/24', descr='', type='network', detail='')
        self.do_alias_deletion_test(alias)

    def test_network_update_noop(self):
        """ test not updating a network alias """
        alias = dict(name='lan_data_poc3', address='192.168.3.0/24', descr='', type='network', detail='')
        self.do_alias_update_noop_test(alias)

    def test_network_update_network(self):
        """ test updating address of a network alias """
        alias = dict(name='lan_data_poc3', address='192.168.3.0/24', descr='', type='network', detail='')
        self.do_alias_update_field(alias, address='192.168.2.0/24')

    def test_network_update_descr(self):
        """ test updating descr of a network alias """
        alias = dict(name='lan_data_poc3', address='192.168.3.0/24', descr='', type='network', detail='')
        self.do_alias_update_field(alias, descr='data network')

    ##############
    # urltables
    #
    def test_urltable_create(self):
        """ test creation of a new urltable alias """
        alias = dict(name='acme', address='http://www.acme.com', descr='', type='urltable', updatefreq='10', detail='')
        alias['url'] = alias['address']
        self.do_alias_creation_test(alias)

    def test_urltable_delete(self):
        """ test deletion of a urltable alias """
        alias = dict(
            name='acme_corp', address='http://www.acme-corp.com', url='http://www.acme-corp.com', descr='', type='urltable', updatefreq='10', detail='')
        self.do_alias_deletion_test(alias)

    def test_urltable_update_noop(self):
        """ test not updating a urltable alias """
        alias = dict(
            name='acme_corp', address='http://www.acme-corp.com', url='http://www.acme-corp.com', descr='', type='urltable', updatefreq='10', detail='')
        self.do_alias_update_noop_test(alias)

    def test_urltable_update_url(self):
        """ test updating address of a urltable alias """
        alias = dict(
            name='acme_corp', address='http://www.acme-corp.com', url='http://www.acme-corp.com', descr='', type='urltable', updatefreq='10', detail='')
        self.do_alias_update_field(alias, address='http://www.new-acme-corp.com', set_after=dict(url='http://www.new-acme-corp.com'))

    def test_urltable_update_descr(self):
        """ test updating descr of a urltable alias """
        alias = dict(
            name='acme_corp', address='http://www.acme-corp.com', url='http://www.acme-corp.com', descr='', type='urltable', updatefreq='10', detail='')
        self.do_alias_update_field(alias, descr='acme corp urls')

    def test_urltable_update_freq(self):
        """ test updating updatefreq of a urltable alias """
        alias = dict(
            name='acme_corp', address='http://www.acme-corp.com', url='http://www.acme-corp.com', descr='', type='urltable', updatefreq='10', detail='')
        self.do_alias_update_field(alias, updatefreq='20')

    ##############
    # misc
    #
    def test_default_type(self):
        """ test creation of a new host alias without type """
        alias = dict(name='adservers', address='10.0.0.1 10.0.0.2', descr='', type='host', detail='')
        args = args_from_var(alias)
        del args['type']
        set_module_args(args)
        result = self.execute_module(changed=True)

        diff = dict(before='', after=alias)
        self.assertEqual(result['diff'], diff)
        self.assert_xml_elt_dict('aliases', dict(name=alias['name'], type=alias['type']), diff['after'])

    def test_check_mode(self):
        """ test updating an host alias without generating result """
        alias = dict(name='ad_poc1', address='192.168.1.3', descr='', type='host', detail='')
        set_module_args(args_from_var(alias, address='192.168.1.4', _ansible_check_mode=True))
        result = self.execute_module(changed=True)

        diff = dict(before=alias, after=copy(alias))
        diff['after']['address'] = '192.168.1.4'
        self.assertEqual(result['diff'], diff)
        self.assertFalse(self.load_xml_result())

    def test_urltable_required_if(self):
        """ test creation of a new urltable alias without giving updatefreq (should fail) """
        alias = dict(name='acme', address='http://www.acme.com', descr='', type='urltable', detail='')
        set_module_args(args_from_var(alias))
        self.execute_module(failed=True)
