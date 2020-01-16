# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
import re
from ansible.module_utils.network.pfsense.module_base import PFSenseModuleBase

HAPROXY_BACKEND_SERVER_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    backend=dict(required=True, type='str'),
    name=dict(required=True, type='str'),
    mode=dict(default='active', choices=['active', 'backup', 'disabled', 'inactive']),
    forwardto=dict(required=False, type='str'),
    address=dict(required=False, type='str'),
    port=dict(required=False, type='int'),
    ssl=dict(required=False, type='bool'),
    checkssl=dict(required=False, type='bool'),
    weight=dict(required=False, type='int'),
    sslserververify=dict(required=False, type='bool'),
    verifyhost=dict(required=False, type='str'),
    ca=dict(required=False, type='str'),
    crl=dict(required=False, type='str'),
    clientcert=dict(required=False, type='str'),
    cookie=dict(required=False, type='str'),
    maxconn=dict(required=False, type='int'),
    advanced=dict(required=False, type='str'),
    istemplate=dict(required=False, type='str'),
)

HAPROXY_BACKEND_SERVER_MUTUALLY_EXCLUSIVE = [
    ['forwardto', 'address'],
    ['forwardto', 'port'],
]


class PFSenseHaproxyBackendServerModule(PFSenseModuleBase):
    """ module managing pfsense haproxy backend servers """

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseHaproxyBackendServerModule, self).__init__(module, pfsense)
        self.name = "pfsense_haproxy_backend_server"
        self.root_elt = None
        self.obj = dict()

        pkgs_elt = self.pfsense.get_element('installedpackages')
        self.haproxy = pkgs_elt.find('haproxy') if pkgs_elt is not None else None
        self.backends = self.haproxy.find('ha_pools') if self.haproxy is not None else None
        if self.backends is None:
            self.module.fail_json(msg='Unable to find backends XML configuration entry. Are you sure haproxy is installed ?')

        self.backend = None
        self.servers = None

    ##############################
    # params processing
    #
    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()
        obj['name'] = params['name']
        if params['state'] == 'present':
            obj['status'] = params['mode']

            for param in ['ssl', 'checkssl', 'sslserververify']:
                self._get_ansible_param_bool(obj, param)

            self._get_ansible_param(obj, 'forwardto')
            self._get_ansible_param(obj, 'address')
            self._get_ansible_param(obj, 'port')
            self._get_ansible_param(obj, 'weight')
            self._get_ansible_param(obj, 'verifyhost')

            if 'ca' in params and params['ca'] is not None and params['ca'] != '':
                ca_elt = self.pfsense.find_ca_elt(params['ca'])
                if ca_elt is None:
                    self.module.fail_json(msg='%s is not a valid certificate authority' % (params['ca']))
                obj['ssl-server-ca'] = ca_elt.find('refid').text

            if 'crl' in params and params['crl'] is not None and params['crl'] != '':
                crl_elt = self.pfsense.find_crl_elt(params['crl'])
                if crl_elt is None:
                    self.module.fail_json(msg='%s is not a valid certificate revocation list' % (params['crl']))
                obj['ssl-server-crl'] = crl_elt.find('refid').text

            if 'clientcert' in params and params['clientcert'] is not None and params['clientcert'] != '':
                cert = self.pfsense.find_cert_elt(params['clientcert'])
                if cert is None:
                    self.module.fail_json(msg='%s is not a valid certificate' % (params['clientcert']))
                obj['ssl-server-clientcert'] = cert.find('refid').text

            self._get_ansible_param(obj, 'cookie')
            self._get_ansible_param(obj, 'maxconn')
            self._get_ansible_param(obj, 'advanced')
            self._get_ansible_param(obj, 'istemplate')

        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params
        # check name
        if re.search(r'[^a-zA-Z0-9\.\-_]', params['name']) is not None:
            self.module.fail_json(msg="The field 'name' contains invalid characters")

        if len(params['name']) < 2:
            self.module.fail_json(msg="The field 'name' must be at least 2 characters")

        self.backend = self._find_backend(params['backend'])
        if self.backend is None:
            self.module.fail_json(msg="The backend named '{0}' does not exist".format(params['backend']))

        self.root_elt = self.backend.find('ha_servers')
        if self.root_elt is None:
            self.root_elt = self.pfsense.new_element('ha_servers')
            self.backend.append(self.root_elt)

        if 'forwardto' in params and params['forwardto'] is not None:
            frontend_elt = None
            frontends = self.haproxy.find('ha_backends')
            for item_elt in frontends:
                if item_elt.tag != 'item':
                    continue
                name_elt = item_elt.find('name')
                if name_elt is not None and name_elt.text == params['forwardto']:
                    frontend_elt = item_elt
                    break
            if frontend_elt is None:
                self.module.fail_json(msg="The frontend named '{0}' does not exist".format(params['forwardto']))

    ##############################
    # XML processing
    #
    def _create_target(self):
        """ create the XML target_elt """
        server_elt = self.pfsense.new_element('item')
        self.obj['id'] = self._get_next_id()
        return server_elt

    def _find_backend(self, name):
        """ return the target backend_elt if found """
        for item_elt in self.backends:
            if item_elt.tag != 'item':
                continue
            name_elt = item_elt.find('name')
            if name_elt is not None and name_elt.text == name:
                return item_elt
        return None

    def _find_target(self):
        """ find the XML target_elt """
        for item_elt in self.root_elt:
            if item_elt.tag != 'item':
                continue
            name_elt = item_elt.find('name')
            if name_elt is not None and name_elt.text == self.obj['name']:
                return item_elt
        return None

    @staticmethod
    def _get_params_to_remove():
        """ returns the list of params to remove if they are not set """
        params = ['ssl', 'checkssl', 'sslserververify', 'forwardto', 'address', 'port', 'weight', 'istemplate', 'verifyhost']
        params += ['ssl-server-crl', 'ssl-server-ca', 'ssl-server-clientcert', 'cookie', 'maxconn', 'advanced']
        return params

    def _get_next_id(self):
        """ get next free haproxy id  """
        max_id = 99
        id_elts = self.haproxy.findall('.//id')
        for id_elt in id_elts:
            if id_elt.text is None:
                continue
            ha_id = int(id_elt.text)
            if ha_id > max_id:
                max_id = ha_id
        return str(max_id + 1)

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload """
        return self.pfsense.phpshell('''require_once("haproxy/haproxy.inc");
$result = haproxy_check_and_run($savemsg, true); if ($result) unlink_if_exists($d_haproxyconfdirty_path);''')

    ##############################
    # Logging
    #
    def _get_ref_names(self, before):
        """ get cert and ca names """
        if 'ssl-server-ca' in before and before['ssl-server-ca'] is not None and before['ssl-server-ca'] != '':
            elt = self.pfsense.find_ca_elt(before['ssl-server-ca'], 'refid')
            if elt is not None:
                before['ca'] = elt.find('descr').text
        if 'ca' not in before:
            before['ca'] = None

        if 'ssl-server-crl' in before and before['ssl-server-crl'] is not None and before['ssl-server-crl'] != '':
            elt = self.pfsense.find_crl_elt(before['ssl-server-crl'], 'refid')
            if elt is not None:
                before['crl'] = elt.find('descr').text
        if 'crl' not in before:
            before['crl'] = None

        if 'ssl-server-clientcert' in before and before['ssl-server-clientcert'] is not None and before['ssl-server-clientcert'] != '':
            elt = self.pfsense.find_cert_elt(before['ssl-server-clientcert'], 'refid')
            if elt is not None:
                before['clientcert'] = elt.find('descr').text
        if 'clientcert' not in before:
            before['clientcert'] = None

    def _get_obj_name(self):
        """ return obj's name """
        return "'{0}' on '{1}'".format(self.obj['name'], self.params['backend'])

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        values = ''
        if before is None:
            values += self.format_cli_field(self.params, 'mode', fname='status')
            values += self.format_cli_field(self.params, 'forwardto')
            values += self.format_cli_field(self.params, 'address')
            values += self.format_cli_field(self.params, 'port')
            values += self.format_cli_field(self.params, 'ssl', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.params, 'checkssl', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.params, 'weight')
            values += self.format_cli_field(self.params, 'sslserververify', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.params, 'ca')
            values += self.format_cli_field(self.params, 'crl')
            values += self.format_cli_field(self.params, 'clientcert')
            values += self.format_cli_field(self.params, 'cookie')
            values += self.format_cli_field(self.params, 'maxconn')
            values += self.format_cli_field(self.params, 'advanced')
            values += self.format_cli_field(self.params, 'istemplate')
        else:
            for param in ['ssl', 'checkssl', 'sslserververify']:
                if param in before and before[param] == '':
                    before[param] = None
            self._get_ref_names(before)
            values += self.format_updated_cli_field(self.obj, before, 'status', add_comma=(values), fname='mode')
            values += self.format_updated_cli_field(self.obj, before, 'forwardto', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'address', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'port', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'ssl', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.obj, before, 'checkssl', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.obj, before, 'weight', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'sslserververify', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.obj, before, 'verifyhost', add_comma=(values))
            values += self.format_updated_cli_field(self.params, before, 'ca', add_comma=(values))
            values += self.format_updated_cli_field(self.params, before, 'crl', add_comma=(values))
            values += self.format_updated_cli_field(self.params, before, 'clientcert', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'cookie', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'maxconn', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'advanced', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'istemplate', add_comma=(values))
        return values
