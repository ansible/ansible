#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, [David Grau Merconchini <david@gallorojo.com.mx>]
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: idg_domain
short_description: Manages IBM DataPower Gateway(IDG) domains
description:
  - Manages IBM DataPower Gateway(IDG) domains.
version_added: "2.7"
options:
  name:
    description:
      - Domain identifier.
    required: True
    type: str

  user_summary:
    description:
      - A descriptive summary for the configuration.
    required: False
    type: str

  admin_state:
    description:
      - Define the administrative state of the domain.
      - C(enabled), To make active.
      - C(disabled), To make inactive.
    default: enabled
    required: False
    type: str
    choices:
      - enabled
      - disabled

  config_mode:
    description:
      - Whether the configuration file is local or remote.
      - NOT YET IMPLEMENTED, its value are fixed so as not to affect the immutability
    default: local
    required: False
    type: str

  config_permissions_mode:
    description:
      - Specifies the the security context for the configuration
        files that are run in the domain.
      - NOT YET IMPLEMENTED, its value are fixed so as not to affect the immutability
    default: scope-domain
    required: False
    type: str

  import_format:
    description:
      - The format of the remote configuration file.
      - NOT YET IMPLEMENTED, its value are fixed so as not to affect the immutability
    default: ZIP
    required: False
    type: str

  local_ip_rewrite:
    description:
      - Whether to rewrite local IP addresses during import.
      - NOT YET IMPLEMENTED, its value are fixed so as not to affect the immutability
    default: True
    required: False
    type: bool

  max_chkpoints:
    description:
      - The maximum number of configuration checkpoints to support.
    default: 3
    required: False
    type: int

  state:
    description:
      - Specifies the current state of the domain.
      - C(present), C(absent). Create or remove a domain.
      - To make active set to C(enabled), inactive, set to C(disabled).
        C(reseted) will delete all configured services within the domain.
        C(restarted) all services will be stoped and started.
        C(quiesced) Transitions the operational state of a domain,
        and the services and handlers associated with the domain,
        to down in a controlled manner.
        C(unquiesced) Bring the operational state of the domain to up
      - Be particularly careful about changing the status to C(restarted) or C(reseted).
        These Will affect all configured services within the domain.
        C(restarted) all the configuration that has not been saved will be lost.
        C(reseted) deletes all configuration data in the domain
    default: present
    required: True
    type: str
    choices:
      - present
      - absent
      - reseted
      - restarted
      - quiesced
      - unquiesced

  quiesce_conf:
    description:
      - Only necessary when the I(state)=C(quiesced)
    type: dict
    default:
      delay: 0
      timeout: 60
    suboptions:
      delay:
        description:
          - Specifies the interval of time in seconds to wait
            before initiating the quiesce action.
      timeout:
        description:
          - Specifies the length of time in seconds to wait for
            all transactions to complete. The minimum is 60.

  idg_connection:
    description:
      - A dict object containing connection details.
    type: dict
    required: True
    suboptions:
      password:
        description:
          - The password for the user account used to connect to the
            REST management interface.
        aliases:
            - url_password
        type: str
        required: True
      server:
        description:
          - The DataPower® Gateway host.
        type: str
        required: True
      server_port:
        description:
          - The DataPower® Gateway port.
        type: int
        default: 5554
        required: False
      timeout:
        description:
          - Specifies the timeout in seconds for communicating with the device.
        default: 10
        type: int
      use_proxy:
        description:
          - Control if the lookup will observe HTTP proxy environment variables when present.
        default: False
        type: bool
        required: False
      user:
        description:
          - The username to connect to the REST management interface with.
            This user must have administrative privileges.
        aliases:
            - url_username
        type: str
        required: True
      validate_certs:
        description:
          - Control SSL handshake validation.
        default: True
        type: bool

  monitoring_map:
    description:
      - Which types of events to generate when files
        are added to or deleted from the U(local://) directory.
    type: dict
    required: False
    suboptions:
      audit:
        description:
          - Generate audit events.
        default: False
        type: bool
        required: False
      log:
        description:
          - Generate log events.
        default: False
        type: bool
        required: False

  file_map:
    description:
      - Which file permissions to apply to the U(local://) directory.
    type: dict
    required: False
    suboptions:
      display:
        description:
          - File content can be displayed for the U(local://) directory.
        default: True
        type: bool
        required: False
      exec:
        description:
          - Files in the U(local://) directory can be run as scripts.
        default: True
        type: bool
        required: False
      copyfrom:
        description:
          - Files can be copied from the U(local://) directory.
        default: True
        type: bool
        required: False
      copyto:
        description:
          - Files can be copied to the U(local://) directory.
        default: True
        type: bool
        required: False
      delete:
        description:
          - Files can be deleted from the U(local://) directory.
        default: True
        type: bool
        required: False
      subdir:
        description:
          - Subdirectories can be created in the U(local://) directory.
        default: True
        type: bool
        required: False

notes:
  - This documentation was developed mostly from the content
    provided by IBM in its web administration interface.
  - For more information consult the official documentation.
    U(https://www.ibm.com/support/knowledgecenter/SS9H2Y_7.7.0/com.ibm.dp.doc/welcome.html)

author:
  - David Grau Merconchini (@dgraum)
'''

EXAMPLES = '''
- name: Test DataPower domain module
  connection: local
  hosts: localhost
  vars:
    domain_name: test
    summary: Made with Ansible!!!
    remote_idg:
        server: idghosts
        server_port: 5554
        user: admin
        password: admin
        validate_certs: false
        timeout: 15

  tasks:

  - name: Create domain
    idg_domain:
        name: "{{ domain_name }}"
        idg_connection: "{{ remote_idg }}"
        user_summary: "{{ summary }}"
        state: present

  - name: Save default domain
    idg_domain:
        name: default
        idg_connection: "{{ remote_idg }}"
        state: saved

  - name: Update domain
    idg_domain:
        name: "{{ domain_name }}"
        idg_connection: "{{ remote_idg }}"
        file_map: "{{ file_definition }}"
        user_summary: "{{ summary }}"
        state: present
    vars:
        file_definition:
            display: false
            exec: true
            copyfrom: true
            copyto: true
            delete: false
            subdir: true

  - name: Save domain
    idg_domain:
        name: "{{ domain_name }}"
        idg_connection: "{{ remote_idg }}"
        state: saved

  - name: Restart domain
    idg_domain:
        name: "{{ domain_name }}"
        idg_connection: "{{ remote_idg }}"
        state: restarted
'''

RETURN = '''
monitor_type:
  description:
    - Changed value for the monitor_type of the node.
  returned: changed and success
  type: string
  sample: m_of_n
quorum:
  description:
    - Changed value for the quorum of the node.
  returned: changed and success
  type: int
  sample: 1
'''

import json
# import pdb

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import open_url

# Common package of our implementation for IDG
from ansible.module_utils.appliance.ibm.idg_common import *

def main():

    # Constants for domain management
    _URI_DOMAIN_LIST = "/mgmt/domains/config/"
    _URI_DOMAIN_CONFIG = "/mgmt/config/default/Domain/{0}"
    _URI_DOMAIN_STATUS = "/mgmt/status/default/DomainStatus"

    _URI_ACTION = "/mgmt/actionqueue/{0}"
    _URI_SAVE_ACTION = "/mgmt/actionqueue/{0}/operations/SaveConfig"

    # Define the available arguments/parameters that a user can pass to
    # the module

    # File permission to the local: directory
    filemap_spec = {
        'display': dict(type = 'bool'), # File content can be displayed for the local: directory.
        'exec': dict(type = 'bool'), # Files in the local: directory can be run as scripts.
        'copyfrom': dict(type = 'bool'), # Files can be copied FROM the local: directory.
        'copyto': dict(type = 'bool'), # Files can be copied TO the local: directory.
        'delete': dict(type = 'bool'), # Files can be DELETED from the local: directory.
        'subdir': dict(type = 'bool') # Subdirectories can be created in the local: directory.
    }

    # Which types of events to generate when files are added to or deleted from the local: directory.
    monitoringmap_spec = {
        'audit': dict(type = 'bool'), # Generate audit events.
        'log': dict(type = 'bool') # Generate log events.
    }

    # Quiesce configuration
    quiescemap_spec = {
        'delay': dict(type = 'int'), # Specifies the interval of time in seconds to wait before initiating the quiesce action.
        'timeout': dict(type = 'int') # Specifies the length of time in seconds to wait for all transactions to complete.
    }

    module_args = dict(
        name = dict(type = 'str', required = True), # Domain name
        user_summary =  dict(type = 'str', required = False), # Domain description
        admin_state = dict(type = 'str', choices = ['enabled', 'disabled'], default = 'enabled'), # Domain's administrative state
        state = dict(type = 'str', choices = ['present', 'absent', 'restarted', 'reseted', 'saved', 'quiesced', 'unquiesced'], default = 'present'), # Domain's operational state
        quiesce_conf = dict(type = 'dict', options = quiescemap_spec, default = dict({ 'delay': 0, 'timeout': 60 })), # Transitions the operational state of a domain to down in a controlled manner.
        idg_connection = dict(type = 'dict', options = idg_endpoint_spec, required = True), # IDG connection
        file_map = dict(type = 'dict', options = filemap_spec, default = dict({ 'display': True, 'exec': True, 'copyfrom': True,
                                                                               'copyto': True, 'delete': True, 'subdir': True })), # File permission in local:
        monitoring_map = dict(type = 'dict', options = monitoringmap_spec, default = dict({ 'audit': False,
                                                                                           'log': False })), # Events  when work whith files
        max_chkpoints = dict(type = 'int', default = 3), # The maximum number of configuration checkpoints to support.
        # TODO !!!
        # It is better to guarantee immutability while waiting.
        config_mode = dict(type = 'str', choices = ['local'], default = 'local'),
        config_permissions_mode = dict(type = 'str', choices = ['scope-domain'], default = 'scope-domain'),
        import_format = dict(type = 'str', choices = ['ZIP'], default = 'ZIP'),
        local_ip_rewrite = dict(type = 'bool', default = True)
    )

    # AnsibleModule instantiation
    module = AnsibleModule(
        argument_spec = module_args,
        supports_check_mode = True
    )

    # Parse arguments to dict
    idg_data_spec = parse_to_dict(module.params['idg_connection'], 'IDGConnection', ANSIBLE_VERSION)
    filemap_data_spec = parse_to_dict(module.params['file_map'], 'FileMap', ANSIBLE_VERSION)
    monitoringmap_data_spec = parse_to_dict(module.params['monitoring_map'], 'MonitoringMap', ANSIBLE_VERSION)
    quiesce_conf_data_spec = parse_to_dict(module.params['quiesce_conf'], 'QuiesceConf', ANSIBLE_VERSION)

    # Domain to work
    domain_name = module.params['name']

    # Status
    state = module.params['state']
    admin_state = module.params['admin_state']

    # Connection
    socket_connection = "https://{0}:{1}".format(idg_data_spec['server'], idg_data_spec['server_port'])
    url = socket_connection + _URI_DOMAIN_CONFIG.format(domain_name)
    user = idg_data_spec['user']
    password = idg_data_spec['password']
    validate_certs = idg_data_spec['validate_certs']
    timeout = idg_data_spec['timeout']
    use_proxy = idg_data_spec['use_proxy']

    # Configuration template for the domain
    domain_obj_msg = { "Domain": {
                           "name": domain_name,
                           "mAdminState": admin_state,
                           "UserSummary": module.params['user_summary'],
                           "ConfigMode": module.params['config_mode'],
                           "ConfigPermissionsMode": module.params['config_permissions_mode'],
                           "ImportFormat": module.params['import_format'],
                           "LocalIPRewrite": on_off(module.params['local_ip_rewrite']),
                           "MaxChkpoints": module.params['max_chkpoints'],
                           "FileMap": {
                                "Display": on_off(filemap_data_spec['display']),
                                "Exec": on_off(filemap_data_spec['exec']),
                                "CopyFrom": on_off(filemap_data_spec['copyfrom']),
                                "CopyTo": on_off(filemap_data_spec['copyto']),
                                "Delete": on_off(filemap_data_spec['delete']),
                                "Subdir": on_off(filemap_data_spec['subdir'])
                           },
                           "MonitoringMap": {
                                "Audit": on_off(monitoringmap_data_spec['audit']),
                                "Log": on_off(monitoringmap_data_spec['log'])
                           }
                        }
                     }

    # List of properties that are managed
    domain_obj_items = [k for k, v in domain_obj_msg['Domain'].items()]

    # Action messages
    # Restart
    restart_act_msg = { "RestartThisDomain": {} }
    # Reset
    reset_act_msg = { "ResetThisDomain": {} }
    # Save
    save_act_msg = { "SaveConfig": {} }
    # Quiesce
    quiesce_act_msg = { "DomainQuiesce": {
                            "delay": quiesce_conf_data_spec['delay'], "name": domain_name,
                            "timeout": quiesce_conf_data_spec['timeout']
                      } }
    # Unquiesce
    unquiesce_act_msg = { "DomainUnquiesce": { "name": domain_name } }

    # Seed the result
    result = dict(
        changed = False,
        name = domain_name,
        msg = 'No change was made'
    )

    # If the user is working in only check mode we do not
    # want to make any changes
    if module.check_mode:
        module.exit_json(**result)

    # List of configured domains
    chk_code, chk_msg, chk_data = do_open_url(module, socket_connection + _URI_DOMAIN_LIST,
                                             method = 'GET', headers = BASIC_HEADERS, timeout = timeout, user = user,
                                             password = password, use_proxy = use_proxy,
                                             force_basic_auth = BASIC_AUTH_SPEC, validate_certs = validate_certs,
                                             http_agent = HTTP_AGENT_SPEC, data = None)

    if chk_code == 200 and chk_msg == 'OK': # If the answer is correct

        configured_domains = [] # List of existing domains
        if isinstance(chk_data['domain'], dict): # if has only default domain
            configured_domains = [chk_data['domain']['name']]
        else:
            configured_domains = [d['name'] for d in chk_data['domain']]

        if state in ('present', 'saved', 'restarted', 'reseted', 'quiesced', 'unquiesced'): # They need for or do a domain

            if domain_name not in configured_domains: # Domain NOT EXIST.

                # pdb.set_trace()

                if state == 'present': # Create it
                    create_code, create_msg, create_json = do_open_url(module, url, method = 'PUT', headers = BASIC_HEADERS,
                                                                       timeout = timeout, user = user, password = password,
                                                                       use_proxy = use_proxy, force_basic_auth = BASIC_AUTH_SPEC, validate_certs = validate_certs,
                                                                       http_agent = HTTP_AGENT_SPEC, data = json.dumps(domain_obj_msg))

                    # pdb.set_trace()
                    if create_code == 201 and create_msg == 'Created': # Created successfully
                        result['msg'] = create_json[domain_name]
                        result['changed'] = True
                    elif create_code == 200 and create_msg == 'OK': # Updated successfully
                        result['msg'] = create_json[domain_name]
                        result['changed'] = True
                    else:
                        # Opps can't create
                        module.fail_json(msg = "Unable to reach state %s in domain %s." % (state, domain_name))

                elif state in ('saved', 'restarted', 'reseted', 'quiesced', 'unquiesced'): # Can't do this actions
                    module.fail_json(msg = 'Unable to reach state "%s" in domain %s. Domain not exist!' % (state, domain_name))

            else: # Domain EXIST
                # Update, save or restart
                # pdb.set_trace()

                # Get current domain configuration
                dc_code, dc_msg, dc_data = do_open_url(module, url, method = 'GET', headers = BASIC_HEADERS,
                                                       timeout = timeout, user = user, password = password,
                                                       use_proxy = use_proxy, force_basic_auth = BASIC_AUTH_SPEC, validate_certs = validate_certs,
                                                       http_agent = HTTP_AGENT_SPEC, data = None)

                if dc_code == 200 and dc_msg == 'OK':

                    # We focus only on the properties we administer

                    del dc_data['_links']
                    for k, v in dc_data['Domain'].items():
                        if k not in domain_obj_items: del dc_data['Domain'][k]

                    if state == 'present' and (domain_obj_msg['Domain'] != dc_data['Domain']): # Need update

                        upd_code, upd_msg, upd_json = do_open_url(module, url, method = 'PUT', headers = BASIC_HEADERS,
                                                                  timeout = timeout, user = user, password = password, use_proxy = use_proxy,
                                                                  force_basic_auth = BASIC_AUTH_SPEC, validate_certs = validate_certs,
                                                                  http_agent = HTTP_AGENT_SPEC, data = json.dumps(domain_obj_msg))

                        if upd_code == 200 and upd_msg == 'OK':
                            # Updates successfully
                            result['msg'] = upd_json[domain_name]
                            result['changed'] = True
                        else:
                            # Opps can't update
                            module.fail_json(msg = to_native(upd_json['error']))

                    elif state == 'present' and (domain_obj_msg['Domain'] == dc_data['Domain']): # Identicals configurations
                        # The current configuration is identical to the new configuration, there is nothing to do
                        result['msg'] = IMMUTABLE_MESSAGE

                    elif state == 'restarted': # Restart domain
                        restart_code, restart_msg, restart_data = do_open_url(module, socket_connection + _URI_ACTION.format(domain_name),
                                                                              method = 'POST', headers = BASIC_HEADERS, timeout = timeout,
                                                                              user = user, password = password, use_proxy = use_proxy,
                                                                              force_basic_auth = BASIC_AUTH_SPEC, validate_certs = validate_certs,
                                                                              http_agent = HTTP_AGENT_SPEC, data = json.dumps(restart_act_msg))

                        if restart_code == 202 and restart_msg == 'Accepted':
                            # Restarted successfully
                            result['msg'] = restart_data['RestartThisDomain']['status']
                            result['changed'] = True
                        else:
                            # Opps can't restarted OJO(No se ha replicado)
                            module.fail_json(msg = to_native(restart_data['error']))

                    elif state == 'reseted':
                        # Reseted domain
                        reset_code, reset_msg, reset_json = do_open_url(module, socket_connection + _URI_ACTION.format(domain_name),
                                                                        method = 'POST', headers = BASIC_HEADERS, timeout = timeout,
                                                                        user = user, password = password, use_proxy = use_proxy,
                                                                        force_basic_auth = BASIC_AUTH_SPEC, validate_certs = validate_certs,
                                                                        http_agent = HTTP_AGENT_SPEC, data = json.dumps(reset_act_msg))

                        if reset_code == 202 and reset_msg == 'Accepted':
                            # Reseted successfully
                            result['msg'] = reset_json['ResetThisDomain']['status']
                            result['changed'] = True
                        else:
                            # Opps can't reseted OJO(No se ha replicado)
                            module.fail_json(msg = to_native(reset_json['error']))

                    elif state in ('quiesced', 'unquiesced', 'saved'):

                        qds_code, qds_msg, qds_data = do_open_url(module, socket_connection + _URI_DOMAIN_STATUS,
                                                                  method = 'GET', headers = BASIC_HEADERS, timeout = timeout,
                                                                  user = user, password = password, use_proxy = use_proxy,
                                                                  force_basic_auth = BASIC_AUTH_SPEC, validate_certs = validate_certs,
                                                                  http_agent = HTTP_AGENT_SPEC, data = None)

                        # pdb.set_trace()

                        if qds_code == 200 and qds_msg == 'OK':

                            if isinstance(qds_data['DomainStatus'], dict):
                                domain_quiesce_status = qds_data['DomainStatus']['QuiesceState']
                                domain_save_needed = qds_data['DomainStatus']['SaveNeeded']
                            else:
                                domain_quiesce_status = [d['QuiesceState'] for d in qds_data['DomainStatus'] if d['Domain'] == domain_name][0]
                                domain_save_needed = [d['SaveNeeded'] for d in qds_data['DomainStatus'] if d['Domain'] == domain_name][0]


                            # pdb.set_trace()
                            if state == 'saved':
                                # Saved domain
                                if domain_save_needed != 'off':

                                    save_code, save_msg, save_json = do_open_url(module, socket_connection + _URI_ACTION.format(domain_name),
                                                                                 method = 'POST', headers = BASIC_HEADERS, timeout = timeout,
                                                                                 user = user, password = password, use_proxy = use_proxy,
                                                                                 force_basic_auth = BASIC_AUTH_SPEC, validate_certs = validate_certs,
                                                                                 http_agent = HTTP_AGENT_SPEC, data = json.dumps(save_act_msg))

                                    # pdb.set_trace()
                                    if save_code == 200 and save_msg == 'OK':
                                        # Reseted successfully
                                        result['msg'] = save_json['SaveConfig']
                                        result['changed'] = True
                                    else:
                                        # Opps can't saved OJO(No se ha replicado)
                                        module.fail_json(msg = to_native(save_json['error']))
                                else:
                                    # Domain is save
                                    result['msg'] = IMMUTABLE_MESSAGE

                            elif state == 'quiesced':
                                if domain_quiesce_status == '':
                                    # Quiesce domain
                                    qd_code, qd_msg, qd_data = do_open_url(module, socket_connection + _URI_ACTION.format(domain_name),
                                                                           method = 'POST', headers = BASIC_HEADERS, timeout = timeout,
                                                                           user = user, password = password, use_proxy = use_proxy,
                                                                           force_basic_auth = BASIC_AUTH_SPEC, validate_certs = validate_certs,
                                                                           http_agent = HTTP_AGENT_SPEC, data = json.dumps(quiesce_act_msg))

                                    if qd_code == 202 and qd_msg == 'Accepted':
                                        # Quiesced successfully
                                        result['msg'] = qd_data['DomainQuiesce']
                                        result['changed'] = True
                                    else:
                                        # Opps can't quiesced OJO(No se ha replicado)
                                        module.fail_json(msg = to_native(qd_data['error']))
                                else:
                                    # Domain is quiesced
                                    result['msg'] = IMMUTABLE_MESSAGE

                            elif state == 'unquiesced':
                                if domain_quiesce_status == 'quiesced':
                                    # Unquiesce domain
                                    uqd_code, uqd_msg, uqd_data = do_open_url(module, socket_connection + _URI_ACTION.format(domain_name),
                                                                              method = 'POST', headers = BASIC_HEADERS, timeout = timeout,
                                                                              user = user, password = password, use_proxy = use_proxy,
                                                                              force_basic_auth = BASIC_AUTH_SPEC, validate_certs = validate_certs,
                                                                              http_agent = HTTP_AGENT_SPEC, data = json.dumps(unquiesce_act_msg))

                                    if uqd_code == 202 and uqd_msg == 'Accepted':
                                        # Unquiesce successfully
                                        result['msg'] = uqd_data['DomainUnquiesce']
                                        result['changed'] = True
                                    else:
                                        # Opps can't unquiesce
                                        module.fail_json(msg = to_native(uqd_data['error']))

                                else:
                                    # Domain is unquiesced
                                    result['msg'] = IMMUTABLE_MESSAGE

                        else:
                            # Opps can't get domain status
                            module.fail_json(msg = "Unable to get status from domain %s." % (domain_name))

                else:
                    # Opps can't read domain configuration
                    module.fail_json(msg = to_native(dc_data['error']))

        elif state == 'absent': # Remove domain

            if domain_name in configured_domains: # Domain EXIST.
                # Remove
                del_code, del_msg, del_data = do_open_url(module, url, method = 'DELETE', headers = BASIC_HEADERS,
                                                          timeout = timeout, user = user, password = password, use_proxy = use_proxy,
                                                          force_basic_auth = BASIC_AUTH_SPEC, validate_certs = validate_certs,
                                                          http_agent = HTTP_AGENT_SPEC, data = None)

                if del_code == 200 and del_msg == 'OK':
                    # Remove successfully
                    result['msg'] = del_data[domain_name]
                    result['changed'] = True
                else:
                    # Opps can't remove
                    module.fail_json(msg = to_native(del_data['error']))

            else: # Domain NOT EXIST.
                result['msg'] = IMMUTABLE_MESSAGE

        # pdb.set_trace()
        # That's all folks!
        module.exit_json(**result)

    else: # The DP domains could not be extracted
        # Opps can't read domain's lists
        # That's all folks!
        module.fail_json(msg = to_native(chk_data['error']))

if __name__ == '__main__':
    main()
