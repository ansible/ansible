# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
import re
from ansible.module_utils.network.pfsense.module_base import PFSenseModuleBase

HAPROXY_BACKEND_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    name=dict(required=True, type='str'),
    balance=dict(default='none', choices=['none', 'roundrobin', 'static-rr', 'leastconn', 'source', 'uri']),
    balance_urilen=dict(required=False, type='int'),
    balance_uridepth=dict(required=False, type='int'),
    balance_uriwhole=dict(required=False, type='bool'),
    connection_timeout=dict(required=False, type='int'),
    server_timeout=dict(required=False, type='int'),
    check_type=dict(default='none', choices=['none', 'Basic', 'HTTP', 'Agent', 'LDAP', 'MySQL', 'PostgreSQL', 'Redis', 'SMTP', 'ESMTP', 'SSL']),
    check_frequency=dict(required=False, type='int'),
    retries=dict(required=False, type='int'),
    log_checks=dict(required=False, type='bool'),
    httpcheck_method=dict(required=False, choices=['OPTIONS', 'HEAD', 'GET', 'POST', 'PUT', 'DELETE', 'TRACE']),
    monitor_uri=dict(required=False, type='str'),
    monitor_httpversion=dict(required=False, type='str'),
    monitor_username=dict(required=False, type='str'),
    monitor_domain=dict(required=False, type='str'),
)


class PFSenseHaproxyBackendModule(PFSenseModuleBase):
    """ module managing pfsense haproxy backends """

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseHaproxyBackendModule, self).__init__(module, pfsense)
        self.name = "pfsense_haproxy_backend"
        self.obj = dict()

        pkgs_elt = self.pfsense.get_element('installedpackages')
        self.haproxy = pkgs_elt.find('haproxy') if pkgs_elt is not None else None
        self.root_elt = self.haproxy.find('ha_pools') if self.haproxy is not None else None
        if self.root_elt is None:
            self.module.fail_json(msg='Unable to find backends XML configuration entry. Are you sure haproxy is installed ?')

    ##############################
    # params processing
    #
    def _params_to_obj(self):
        """ return a backend dict from module params """
        obj = dict()
        obj['name'] = self.params['name']
        if self.params['state'] == 'present':
            self._get_ansible_param(obj, 'balance', force=True)
            if obj['balance'] == 'none':
                obj['balance'] = None
            self._get_ansible_param(obj, 'balance_urilen', force=True)
            self._get_ansible_param(obj, 'balance_uridepth', force=True)
            self._get_ansible_param(obj, 'connection_timeout', force=True)
            self._get_ansible_param(obj, 'server_timeout', force=True)
            self._get_ansible_param(obj, 'check_type', force=True)
            self._get_ansible_param(obj, 'check_frequency', fname='checkinter', force=True)
            self._get_ansible_param(obj, 'retries', force=True)
            self._get_ansible_param_bool(obj, 'log_checks', fname='log-health-checks', force=True)
            self._get_ansible_param_bool(obj, 'balance_uriwhole', force=True)
            self._get_ansible_param(obj, 'httpcheck_method', force=True)
            self._get_ansible_param(obj, 'monitor_uri', force=True)
            self._get_ansible_param(obj, 'monitor_httpversion', force=True)
            self._get_ansible_param(obj, 'monitor_username', force=True)
            self._get_ansible_param(obj, 'monitor_domain', force=True)

        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        # check name
        if re.search(r'[^a-zA-Z0-9\.\-_]', self.params['name']) is not None:
            self.module.fail_json(msg="The field 'name' contains invalid characters.")

    ##############################
    # XML processing
    #
    def _create_target(self):
        """ create the XML target_elt """
        server_elt = self.pfsense.new_element('item')
        self.obj['id'] = self._get_next_id()
        return server_elt

    def _find_target(self):
        """ find the XML target_elt """
        for item_elt in self.root_elt:
            if item_elt.tag != 'item':
                continue
            name_elt = item_elt.find('name')
            if name_elt is not None and name_elt.text == self.obj['name']:
                return item_elt
        return None

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
        """ make the target pfsense reload haproxy """
        return self.pfsense.phpshell('''require_once("haproxy/haproxy.inc");
$result = haproxy_check_and_run($savemsg, true); if ($result) unlink_if_exists($d_haproxyconfdirty_path);''')

    ##############################
    # Logging
    #
    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        values = ''
        if before is None:
            values += self.format_cli_field(self.params, 'balance')
            values += self.format_cli_field(self.params, 'balance_urilen')
            values += self.format_cli_field(self.params, 'balance_uridepth')
            values += self.format_cli_field(self.params, 'balance_uriwhole', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.params, 'connection_timeout')
            values += self.format_cli_field(self.params, 'server_timeout')
            values += self.format_cli_field(self.params, 'check_type')
            values += self.format_cli_field(self.params, 'check_frequency')
            values += self.format_cli_field(self.params, 'retries')
            values += self.format_cli_field(self.params, 'log_checks', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.params, 'httpcheck_method')
            values += self.format_cli_field(self.params, 'monitor_uri')
            values += self.format_cli_field(self.params, 'monitor_httpversion')
            values += self.format_cli_field(self.params, 'monitor_username')
            values += self.format_cli_field(self.params, 'monitor_domain')
        else:
            for param in ['balance', 'log-health-checks', 'balance_uriwhole']:
                if param in before and before[param] == '':
                    before[param] = None
            values += self.format_updated_cli_field(self.obj, before, 'balance', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'balance_urilen', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'balance_uridepth', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'balance_uriwhole', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.obj, before, 'connection_timeout', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'server_timeout', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'check_type', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'checkinter', add_comma=(values), fname='check_frequency')
            values += self.format_updated_cli_field(self.obj, before, 'retries', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'log-health-checks', add_comma=(values), fname='log_checks', fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.obj, before, 'httpcheck_method', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'monitor_uri', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'monitor_httpversion', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'monitor_username', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'monitor_domain', add_comma=(values))
        return values

    def _get_obj_name(self):
        """ return obj's name """
        return "'{0}'".format(self.obj['name'])
