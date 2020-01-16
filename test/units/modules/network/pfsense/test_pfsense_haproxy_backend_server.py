# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from ansible.modules.network.pfsense import pfsense_haproxy_backend_server
from .pfsense_module import TestPFSenseModule


class TestPFSenseHaproxyBackendServerModule(TestPFSenseModule):

    module = pfsense_haproxy_backend_server

    def __init__(self, *args, **kwargs):
        super(TestPFSenseHaproxyBackendServerModule, self).__init__(*args, **kwargs)
        self.config_file = 'pfsense_haproxy_backend_server_config.xml'

    @staticmethod
    def get_args_fields():
        """ return params fields """
        fields = ['backend', 'name', 'mode', 'forwardto', 'address', 'port']
        fields += ['ssl', 'checkssl', 'weight', 'sslserververify', 'verifyhost', 'ca']
        fields += ['crl', 'clientcert', 'cookie', 'maxconn', 'advanced', 'istemplate']
        return fields

    ##############
    # tests utils
    #
    def get_target_elt(self, server, absent=False):
        """ get the generated backend server xml definition """
        pkgs_elt = self.assert_find_xml_elt(self.xml_result, 'installedpackages')
        hap_elt = self.assert_find_xml_elt(pkgs_elt, 'haproxy')
        backends_elt = self.assert_find_xml_elt(hap_elt, 'ha_pools')

        for item in backends_elt:
            name_elt = item.find('name')
            if name_elt is not None and name_elt.text == server['backend']:
                backend_elt = item
                break

        if backend_elt is None:
            self.fail('haproxy backend ' + server['backend'] + ' not found.')

        servers_elt = self.assert_find_xml_elt(backend_elt, 'ha_servers')
        for item in servers_elt:
            name_elt = item.find('name')
            if name_elt is not None and name_elt.text == server['name']:
                return item

        if not absent:
            self.fail('haproxy backend server ' + server['name'] + ' not found.')
        return None

    @staticmethod
    def caref(descr):
        """ return refid for ca """
        if descr == 'test ca':
            return '5d85d3071588f'
        if descr == 'test ca2':
            return '5df5ec5668d9f'
        return ''

    @staticmethod
    def crlref(descr):
        """ return refid for crl """
        if descr == 'test crl':
            return '5df5edf6cae0f'
        if descr == 'test crl2':
            return '5df5ee048c106'
        return ''

    @staticmethod
    def certref(descr):
        """ return refid for cert """
        if descr == 'test cert':
            return '5df5ec78b3048'
        if descr == 'test cert2':
            return '5df5ec97dfd07'
        return ''

    @staticmethod
    def idem(descr):
        """ return value passed """
        return descr

    def check_target_elt(self, server, server_elt, server_id):
        """ test the xml definition of server """
        def _check_elt(name, fname=None, default=None, fvalue=self.idem):
            if fname is None:
                fname = name

            if name in server and server[name] is not None:
                self.assert_xml_elt_equal(server_elt, fname, fvalue(str(server[name])))
            elif default is not None:
                self.assert_xml_elt_equal(server_elt, fname, fvalue(default))
            elif name in server:
                self.assert_xml_elt_is_none_or_empty(server_elt, fname)
            else:
                self.assert_not_find_xml_elt(server_elt, fname)

        def _check_bool_elt(name, fname=None, false_exists=False):
            if fname is None:
                fname = name

            if server.get(name):
                self.assert_xml_elt_equal(server_elt, fname, 'yes')
            elif name in server and false_exists:
                self.assert_xml_elt_is_none_or_empty(server_elt, fname)
            else:
                self.assert_not_find_xml_elt(server_elt, fname)

        self.assert_xml_elt_equal(server_elt, 'id', str(server_id))

        _check_elt('mode', fname='status', default='active')
        _check_elt('forwardto')
        _check_elt('address')
        _check_elt('port')
        _check_elt('weight')
        _check_elt('verifyhost')
        _check_elt('ca', fname='ssl-server-ca', fvalue=self.caref)
        _check_elt('crl', fname='ssl-server-crl', fvalue=self.crlref)
        _check_elt('clientcert', fname='ssl-server-clientcert', fvalue=self.certref)
        _check_elt('cookie')
        _check_elt('maxconn')
        _check_elt('advanced')
        _check_elt('istemplate')

        _check_bool_elt('ssl')
        _check_bool_elt('checkssl')
        _check_bool_elt('sslserververify')

    ##############
    # tests
    #
    def test_haproxy_backend_server_create(self):
        """ test creation of a new backend server """
        server = dict(backend='test-backend', name='exchange', address='exchange.acme.org', port=443)
        command = "create haproxy_backend_server 'exchange' on 'test-backend', status='active', address='exchange.acme.org', port=443"
        self.do_module_test(server, command=command, server_id=103)

    def test_haproxy_backend_server_create2(self):
        """ test creation of a new backend server with some parameters"""
        server = dict(
            backend='test-backend', name='exchange', address='exchange.acme.org', port=443, ssl=True, ca='test ca', clientcert='test cert', crl='test crl'
        )
        command = (
            "create haproxy_backend_server 'exchange' on 'test-backend', status='active', address='exchange.acme.org', port=443, "
            "ssl=True, ca='test ca', crl='test crl', clientcert='test cert'"
        )
        self.do_module_test(server, command=command, server_id=103)

    def test_haproxy_backend_server_create_invalid_backend(self):
        """ test creation of a new backend server """
        server = dict(backend='test.backend', name='exchange', address='exchange.acme.org', port=443)
        msg = "The backend named 'test.backend' does not exist"
        self.do_module_test(server, msg=msg, failed=True)

    def test_haproxy_backend_server_create_invalid_name(self):
        """ test creation of a new backend server """
        server = dict(backend='test-backend', name='test exchange', address='exchange.acme.org', port=443)
        msg = "The field 'name' contains invalid characters"
        self.do_module_test(server, msg=msg, failed=True)

    def test_haproxy_backend_server_delete(self):
        """ test deletion of a backend server """
        server = dict(backend='test-backend', name='exchange.acme.org')
        command = "delete haproxy_backend_server 'exchange.acme.org' on 'test-backend'"
        self.do_module_test(server, delete=True, command=command)

    def test_haproxy_backend_server_update_noop(self):
        """ test not updating a backend server """
        server = dict(backend='test-backend', name='exchange.acme.org', address='exchange.acme.org', port=443)
        self.do_module_test(server, changed=False)

    def test_haproxy_backend_server_update_frontend(self):
        """ test updating a backend server """
        server = dict(backend='test-backend', name='exchange.acme.org', forwardto='test-frontend')
        command = "update haproxy_backend_server 'exchange.acme.org' on 'test-backend' set forwardto='test-frontend', address=none, port=none"
        self.do_module_test(server, changed=True, command=command, server_id=101)

    def test_haproxy_backend_server_update_certs(self):
        """ test updating certs """
        server = dict(
            backend='test-backend', name='exchange2.acme.org', address='exchange2.acme.org', port=443, ca='test ca2', clientcert='test cert2', crl='test crl2'
        )
        command = "update haproxy_backend_server 'exchange2.acme.org' on 'test-backend' set ca='test ca2', crl='test crl2', clientcert='test cert2'"
        self.do_module_test(server, changed=True, command=command, server_id=102)

    def test_haproxy_backend_server_update_certs2(self):
        """ test updating certs """
        server = dict(
            backend='test-backend', name='exchange2.acme.org', address='exchange2.acme.org', port=443
        )
        command = "update haproxy_backend_server 'exchange2.acme.org' on 'test-backend' set ca=none, crl=none, clientcert=none"
        self.do_module_test(server, changed=True, command=command, server_id=102)

    def test_haproxy_backend_server_update_certs3(self):
        """ test updating certs """
        server = dict(
            backend='test-backend', name='exchange.acme.org', address='exchange.acme.org', port=443, ca='test ca2', clientcert='test cert2', crl='test crl2'
        )
        command = "update haproxy_backend_server 'exchange.acme.org' on 'test-backend' set ca='test ca2', crl='test crl2', clientcert='test cert2'"
        self.do_module_test(server, changed=True, command=command, server_id=101)

    def test_haproxy_backend_server_invalid_ca(self):
        """ test updating certs """
        server = dict(backend='test-backend', name='exchange', address='exchange.acme.org', port=443, ca='test ca3')
        msg = "test ca3 is not a valid certificate authority"
        self.do_module_test(server, msg=msg, failed=True)

    def test_haproxy_backend_server_invalid_crl(self):
        """ test updating certs """
        server = dict(backend='test-backend', name='exchange', address='exchange.acme.org', port=443, crl='test crl3')
        msg = "test crl3 is not a valid certificate revocation list"
        self.do_module_test(server, msg=msg, failed=True)

    def test_haproxy_backend_server_invalid_cert(self):
        """ test updating certs """
        server = dict(backend='test-backend', name='exchange', address='exchange.acme.org', port=443, clientcert='test cert3')
        msg = "test cert3 is not a valid certificate"
        self.do_module_test(server, msg=msg, failed=True)

    def test_haproxy_backend_server_invalid_frontend(self):
        """ test updating certs """
        server = dict(backend='test-backend', name='exchange', forwardto='test frontend')
        msg = "The frontend named 'test frontend' does not exist"
        self.do_module_test(server, msg=msg, failed=True)
