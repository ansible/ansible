# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from ansible.modules.network.pfsense import pfsense_haproxy_backend
from .pfsense_module import TestPFSenseModule


class TestPFSenseHaproxyBackendModule(TestPFSenseModule):

    module = pfsense_haproxy_backend

    def __init__(self, *args, **kwargs):
        super(TestPFSenseHaproxyBackendModule, self).__init__(*args, **kwargs)
        self.config_file = 'pfsense_haproxy_backend_config.xml'

    @staticmethod
    def get_args_fields():
        """ return params fields """
        fields = ['balance', 'balance_urilen', 'balance_uridepth', 'balance_uriwhole', 'connection_timeout', 'server_timeout']
        fields += ['check_type', 'check_frequency', 'retries', 'log_checks', 'httpcheck_method', 'monitor_uri']
        fields += ['monitor_httpversion', 'monitor_username', 'monitor_domain', 'name']
        return fields

    ##############
    # tests utils
    #
    def get_target_elt(self, backend, absent=False):
        """ get the generated backend xml definition """
        pkgs_elt = self.assert_find_xml_elt(self.xml_result, 'installedpackages')
        hap_elt = self.assert_find_xml_elt(pkgs_elt, 'haproxy')
        backends_elt = self.assert_find_xml_elt(hap_elt, 'ha_pools')

        for item in backends_elt:
            name_elt = item.find('name')
            if name_elt is not None and name_elt.text == backend['name']:
                return item

        if not absent:
            self.fail('haproxy_backend ' + backend['name'] + ' not found.')
        return None

    def check_target_elt(self, backend, backend_elt, backend_id=100):
        """ test the xml definition of backend """
        def _check_elt(name, fname=None, default=None):
            if fname is None:
                fname = name

            if name in backend and backend[name] is not None:
                self.assert_xml_elt_equal(backend_elt, fname, str(backend[name]))
            elif default is not None:
                self.assert_xml_elt_equal(backend_elt, fname, default)
            else:
                self.assert_xml_elt_is_none_or_empty(backend_elt, fname)

        def _check_bool_elt(name, fname=None):
            if fname is None:
                fname = name

            if backend.get(name):
                self.assert_xml_elt_equal(backend_elt, fname, 'yes')
            else:
                self.assert_xml_elt_is_none_or_empty(backend_elt, fname)

        self.assert_xml_elt_equal(backend_elt, 'id', str(backend_id))

        # checking balance
        if 'balance' in backend and backend['balance'] != 'none':
            self.assert_xml_elt_equal(backend_elt, 'balance', backend['balance'])
        else:
            self.assert_xml_elt_is_none_or_empty(backend_elt, 'balance')

        # check everything else
        _check_elt('balance_urilen')
        _check_elt('balance_uridepth')
        _check_bool_elt('balance_uriwhole')
        _check_elt('connection_timeout')
        _check_elt('server_timeout')
        _check_elt('check_type', default='none')
        _check_elt('check_frequency', 'checkinter')
        _check_elt('retries')
        _check_bool_elt('log_checks', 'log-health-checks')
        _check_elt('httpcheck_method')
        _check_elt('monitor_uri')
        _check_elt('monitor_httpversion')
        _check_elt('monitor_username')
        _check_elt('monitor_domain')

    ##############
    # tests
    #
    def test_haproxy_backend_create(self):
        """ test creation of a new backend """
        backend = dict(name='exchange')
        command = "create haproxy_backend 'exchange', balance='none', check_type='none'"
        self.do_module_test(backend, command=command, backend_id=102)

    def test_haproxy_backend_create2(self):
        """ test creation of a new backend with some parameters"""
        backend = dict(name='exchange', balance='roundrobin', check_type='HTTP')
        command = "create haproxy_backend 'exchange', balance='roundrobin', check_type='HTTP'"
        self.do_module_test(backend, command=command, backend_id=102)

    def test_haproxy_backend_create_invalid_name(self):
        """ test creation of a new backend """
        backend = dict(name='exchange test')
        msg = "The field 'name' contains invalid characters."
        self.do_module_test(backend, msg=msg, failed=True)

    def test_haproxy_backend_delete(self):
        """ test deletion of a backend """
        backend = dict(name='test-backend')
        command = "delete haproxy_backend 'test-backend'"
        self.do_module_test(backend, delete=True, command=command)

    def test_haproxy_backend_update_noop(self):
        """ test not updating a backend """
        backend = dict(
            name='test-backend', balance='uri', balance_uriwhole=True, log_checks=True, check_type='SSL', check_frequency=123456, httpcheck_method='OPTIONS'
        )
        self.do_module_test(backend, changed=False)

    def test_haproxy_backend_update_bools(self):
        """ test updating bools """
        backend = dict(name='test-backend', balance='uri', check_type='SSL', check_frequency=123456, httpcheck_method='OPTIONS')
        command = "update haproxy_backend 'test-backend' set balance_uriwhole=False, log_checks=False"
        self.do_module_test(backend, changed=True, command=command)
