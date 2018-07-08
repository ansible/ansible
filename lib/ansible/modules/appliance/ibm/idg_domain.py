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
      - A descriptive summary for the domain.
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
        C(restarted) all services will be stoped and started.
        C(quiesced) Transitions the operational state of a domain,
        and the services and handlers associated with the domain,
        to down in a controlled manner.
        C(unquiesced) Bring the operational state of the domain to up
      - Be particularly careful about changing the status to C(restarted).
        These Will affect all configured services within the domain.
        C(restarted) all the configuration that has not been saved will be lost.
    default: present
    required: True
    type: str
    choices:
      - present
      - absent
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

  - name: Restart domain
    idg_domain:
        name: "{{ domain_name }}"
        idg_connection: "{{ remote_idg }}"
        state: restarted
'''

RETURN = '''
name:
  description:
    - The name of the domain that is being worked on.
  returned: changed and success
  type: string
  sample:
    - core-security-wrap
    - DevWSOrchestration
msg:
  description:
    - Message returned by the device API.
  returned: always
  type: string
  sample:
    - Configuration was created.
    - Unknown error for (https://idg-host1:5554/mgmt/domains/config/). <urlopen error timed out>
'''

import json
# import pdb

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

# Common package of our implementation for IDG
try:
    from ansible.module_utils.appliance.ibm.idg_common import result, idg_endpoint_spec, IDG_Utils
    from ansible.module_utils.appliance.ibm.idg_rest_mgmt import IDG_API
    HAS_IDG_DEPS = True
except ImportError:
    HAS_IDG_DEPS = False

def main():

    # Define the available arguments/parameters that a user can pass to the module

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
        state = dict(type = 'str', choices = ['present', 'absent', 'restarted', 'quiesced', 'unquiesced'], default = 'present'), # Domain's operational state
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
        supports_check_mode = True,
        # Interaction between parameters
        required_if = [
                        ['state', 'quiesced', ['quiesce_conf']]
                      ]
    )

    # Validates the dependence of the utility module
    if not HAS_IDG_DEPS:
        module.fail_json(msg="The IDG utils module is required")

    # Parse arguments to dict
    idg_data_spec = IDG_Utils.parse_to_dict(module.params['idg_connection'], 'IDGConnection', IDG_Utils.ANSIBLE_VERSION)
    filemap_data_spec = IDG_Utils.parse_to_dict(module.params['file_map'], 'FileMap', IDG_Utils.ANSIBLE_VERSION)
    monitoringmap_data_spec = IDG_Utils.parse_to_dict(module.params['monitoring_map'], 'MonitoringMap', IDG_Utils.ANSIBLE_VERSION)
    quiesce_conf_data_spec = IDG_Utils.parse_to_dict(module.params['quiesce_conf'], 'QuiesceConf', IDG_Utils.ANSIBLE_VERSION)

    # Domain to work
    domain_name = module.params['name']

    # Status
    state = module.params['state']
    admin_state = module.params['admin_state']

    # Result
    result['name'] = domain_name

    # Init IDG API connect
    idg_mgmt = IDG_API(ansible_module = module,
                       idg_host = "https://{0}:{1}".format(idg_data_spec['server'], idg_data_spec['server_port']),
                       headers = IDG_Utils.BASIC_HEADERS,
                       http_agent = IDG_Utils.HTTP_AGENT_SPEC,
                       use_proxy = idg_data_spec['use_proxy'],
                       timeout = idg_data_spec['timeout'],
                       validate_certs = idg_data_spec['validate_certs'],
                       user = idg_data_spec['user'],
                       password = idg_data_spec['password'],
                       force_basic_auth = IDG_Utils.BASIC_AUTH_SPEC)

    # Variable to store the status of the action
    action_result = ''

    # Configuration template for the domain
    domain_obj_msg = { "Domain": {
                           "name": domain_name,
                           "mAdminState": admin_state,
                           "UserSummary": module.params['user_summary'],
                           "ConfigMode": module.params['config_mode'],
                           "ConfigPermissionsMode": module.params['config_permissions_mode'],
                           "ImportFormat": module.params['import_format'],
                           "LocalIPRewrite": IDG_Utils.on_off(module.params['local_ip_rewrite']),
                           "MaxChkpoints": module.params['max_chkpoints'],
                           "FileMap": {
                                "Display": IDG_Utils.on_off(filemap_data_spec['display']),
                                "Exec": IDG_Utils.on_off(filemap_data_spec['exec']),
                                "CopyFrom": IDG_Utils.on_off(filemap_data_spec['copyfrom']),
                                "CopyTo": IDG_Utils.on_off(filemap_data_spec['copyto']),
                                "Delete": IDG_Utils.on_off(filemap_data_spec['delete']),
                                "Subdir": IDG_Utils.on_off(filemap_data_spec['subdir'])
                           },
                           "MonitoringMap": {
                                "Audit": IDG_Utils.on_off(monitoringmap_data_spec['audit']),
                                "Log": IDG_Utils.on_off(monitoringmap_data_spec['log'])
                           }
                        }
                     }

    # List of properties that are managed
    domain_obj_items = [k for k, v in domain_obj_msg['Domain'].items()]

    # Action messages
    # Restart
    restart_act_msg = { "RestartThisDomain": {} }

    # Quiesce
    quiesce_act_msg = { "DomainQuiesce": {
                            "delay": quiesce_conf_data_spec['delay'], "name": domain_name,
                            "timeout": quiesce_conf_data_spec['timeout']
                      } }

    # Unquiesce
    unquiesce_act_msg = { "DomainUnquiesce": { "name": domain_name } }

    ###
    ### Here the action begins
    ###

    # List of configured domains
    chk_code, chk_msg, chk_data = idg_mgmt.api_call(uri = IDG_Utils.URI_DOMAIN_LIST, method = 'GET', data = None)

    if chk_code == 200 and chk_msg == 'OK': # If the answer is correct

        # List of existing domains
        if isinstance(chk_data['domain'], dict): # if has only default domain
            configured_domains = [chk_data['domain']['name']]
        else:
            configured_domains = [d['name'] for d in chk_data['domain']]

        if state in ('present', 'restarted', 'quiesced', 'unquiesced'): # They need for or do a domain

            if domain_name not in configured_domains: # Domain NOT EXIST.

                # pdb.set_trace()
                if state == 'present': # Create it

                    # If the user is working in only check mode we do not want to make any changes
                    if module.check_mode:
                        result['msg'] = IDG_Utils.CHECK_MODE_MESSAGE
                        module.exit_json(**result)

                    create_code, create_msg, create_data = idg_mgmt.api_call(uri = IDG_Utils.URI_DOMAIN_CONFIG.format(domain_name), method = 'PUT',
                                                                             data = json.dumps(domain_obj_msg))

                    if create_code == 201 and create_msg == 'Created': # Created successfully
                        result['msg'] = idg_mgmt.status_text(create_data[domain_name])
                        result['changed'] = True
                    elif create_code == 200 and create_msg == 'OK': # Updated successfully
                        result['msg'] = idg_mgmt.status_text(create_data[domain_name])
                        result['changed'] = True
                    else:
                        # Opps can't create
                        module.fail_json(msg = idg_mgmt.ERROR_REACH_STATE % (state, domain_name))

                elif state in ('restarted', 'quiesced', 'unquiesced'): # Can't do this actions
                    module.fail_json(msg = (idg_mgmt.ERROR_REACH_STATE + " Domain not exist!") % (state, domain_name))

            else: # Domain EXIST
                # Update, save or restart
                # pdb.set_trace()

                # Get current domain configuration
                dc_code, dc_msg, dc_data = idg_mgmt.api_call(uri = IDG_Utils.URI_DOMAIN_CONFIG.format(domain_name), method = 'GET', data = None)

                if dc_code == 200 and dc_msg == 'OK':

                    # We focus only on the properties we administer

                    del dc_data['_links']
                    for k, v in dc_data['Domain'].items():
                        if k not in domain_obj_items: del dc_data['Domain'][k]

                    if state == 'present' and (domain_obj_msg['Domain'] != dc_data['Domain']): # Need update

                        # If the user is working in only check mode we do not want to make any changes
                        if module.check_mode:
                            result['msg'] = IDG_Utils.CHECK_MODE_MESSAGE
                            module.exit_json(**result)

                        upd_code, upd_msg, upd_json = idg_mgmt.api_call(uri = IDG_Utils.URI_DOMAIN_CONFIG.format(domain_name), method = 'PUT',
                                                                        data = json.dumps(domain_obj_msg))

                        # pdb.set_trace()
                        if upd_code == 200 and upd_msg == 'OK':
                            # Updates successfully
                            result['msg'] = idg_mgmt.status_text(upd_json[domain_name])
                            result['changed'] = True
                        else:
                            # Opps can't update
                            module.fail_json(msg = to_native(upd_json['error']))

                    elif state == 'present' and (domain_obj_msg['Domain'] == dc_data['Domain']): # Identicals configurations
                        # The current configuration is identical to the new configuration, there is nothing to do
                        result['msg'] = IDG_Utils.IMMUTABLE_MESSAGE

                    elif state == 'restarted': # Restart domain

                        # If the user is working in only check mode we do not want to make any changes
                        if module.check_mode:
                            result['msg'] = IDG_Utils.CHECK_MODE_MESSAGE
                            module.exit_json(**result)

                        restart_code, restart_msg, restart_data = idg_mgmt.api_call(uri = IDG_Utils.URI_ACTION.format(domain_name), method = 'POST',
                                                                                    data = json.dumps(restart_act_msg))

                        if restart_code == 202 and restart_msg == 'Accepted':
                            # Asynchronous actions restart accepted. Wait for complete
                            action_result = idg_mgmt.wait_for_action_end(uri = IDG_Utils.URI_ACTION.format(domain_name), href = restart_data['_links']['location']['href'],
                                                                         state = state, domain = domain_name)

                            # Restart completed. Get result
                            acs_code, acs_msg, acs_data = idg_mgmt.api_call(uri = restart_data['_links']['location']['href'], method = 'GET',
                                                                            data = None)

                            if acs_code == 200 and acs_msg == 'OK':
                                # Restarted successfully
                                result['msg'] = action_result
                                result['changed'] = True
                            else:
                                # Can't retrieve the restart result
                                module.fail_json(msg = to_native(idg_mgmt.ERROR_RETRIEVING_RESULT % (state, domain_name)))

                        elif restart_code == 200 and restart_msg == 'OK':
                            # Successfully processed synchronized action
                            result['msg'] = idg_mgmt.status_text(restart_data['RestartThisDomain'])
                            result['changed'] = True

                        else:
                            # Can't restarted
                            module.fail_json(msg = to_native(idg_mgmt.ERROR_ACCEPTING_ACTION % (state, domain_name)))

                    elif state in ('quiesced', 'unquiesced'):

                        qds_code, qds_msg, qds_data = idg_mgmt.api_call(uri = IDG_Utils.URI_DOMAIN_STATUS, method = 'GET', data = None)

                        # pdb.set_trace()
                        if qds_code == 200 and qds_msg == 'OK':

                            if isinstance(qds_data['DomainStatus'], dict):
                                domain_quiesce_status = qds_data['DomainStatus']['QuiesceState']
                            else:
                                domain_quiesce_status = [d['QuiesceState'] for d in qds_data['DomainStatus'] if d['Domain'] == domain_name][0]

                            # pdb.set_trace()
                            if state == 'quiesced':
                                if domain_quiesce_status == '':

                                    # If the user is working in only check mode we do not want to make any changes
                                    if module.check_mode:
                                        result['msg'] = IDG_Utils.CHECK_MODE_MESSAGE
                                        module.exit_json(**result)

                                    # Quiesce domain
                                    qd_code, qd_msg, qd_data = idg_mgmt.api_call(uri = IDG_Utils.URI_ACTION.format(domain_name), method = 'POST',
                                                                                 data = json.dumps(quiesce_act_msg))

                                    # pdb.set_trace()
                                    if qd_code == 202 and qd_msg == 'Accepted':
                                        # Asynchronous actions quiesce accepted. Wait for complete
                                        action_result = idg_mgmt.wait_for_action_end(uri = IDG_Utils.URI_ACTION.format(domain_name), href = qd_data['_links']['location']['href'],
                                                                                     state = state, domain = domain_name)

                                        # Quiesced completed. Get result
                                        acs_code, acs_msg, acs_data = idg_mgmt.api_call(uri = qd_data['_links']['location']['href'], method = 'GET',
                                                                                        data = None)

                                        if acs_code == 200 and acs_msg == 'OK':
                                            # Quiesced successfully
                                            result['msg'] = action_result
                                            result['changed'] = True
                                        else:
                                            # Can't get the quiesced action result
                                            module.fail_json(msg = to_native(idg_mgmt.ERROR_RETRIEVING_RESULT % (state, domain_name)))

                                    elif qd_code == 200 and qd_msg == 'OK':
                                        # Successfully processed synchronized action
                                        result['msg'] = idg_mgmt.status_text(qd_data['DomainQuiesce'])
                                        result['changed'] = True

                                    else:
                                        # Can't quiesced
                                        module.fail_json(msg = to_native(idg_mgmt.ERROR_ACCEPTING_ACTION % (state, domain_name)))
                                else:
                                    # Domain is quiesced
                                    result['msg'] = IDG_Utils.IMMUTABLE_MESSAGE

                            elif state == 'unquiesced':
                                if domain_quiesce_status == 'quiesced':

                                    # If the user is working in only check mode we do not want to make any changes
                                    if module.check_mode:
                                        result['msg'] = IDG_Utils.CHECK_MODE_MESSAGE
                                        module.exit_json(**result)

                                    # Unquiesce domain
                                    uqd_code, uqd_msg, uqd_data = idg_mgmt.api_call(uri = IDG_Utils.URI_ACTION.format(domain_name), method = 'POST',
                                                                                    data = json.dumps(unquiesce_act_msg))

                                    # pdb.set_trace()
                                    if uqd_code == 202 and uqd_msg == 'Accepted':
                                        # Asynchronous actions unquiesce accepted. Wait for complete
                                        action_result = idg_mgmt.wait_for_action_end(uri = IDG_Utils.URI_ACTION.format(domain_name), href = uqd_data['_links']['location']['href'],
                                                                                     state = state, domain = domain_name)

                                        # Unquiesced completed. Get result
                                        acs_code, acs_msg, acs_data = idg_mgmt.api_call(uri = uqd_data['_links']['location']['href'],
                                                                                        method = 'GET', data = None)

                                        if acs_code == 200 and acs_msg == 'OK':
                                            # Unquiesce successfully
                                            result['msg'] = action_result
                                            result['changed'] = True
                                        else:
                                            # Can't get unquiesce final result
                                            module.fail_json(msg = to_native(idg_mgmt.ERROR_RETRIEVING_RESULT % (state, domain_name)))

                                    elif uqd_code == 200 and uqd_msg == 'OK':
                                        # Successfully processed synchronized action
                                        result['msg'] = idg_mgmt.status_text(uqd_data['DomainUnquiesce'])
                                        result['changed'] = True

                                    else:
                                        # Can't accept unquiesce
                                        module.fail_json(msg = to_native(idg_mgmt.ERROR_ACCEPTING_ACTION % (state, domain_name)))

                                else:
                                    # Domain is unquiesced
                                    result['msg'] = IDG_Utils.IMMUTABLE_MESSAGE

                        else:
                            # Can't get domain status
                            module.fail_json(msg = "Unable to get status from domain %s." % (domain_name))

                else:
                    # Can't read domain configuration
                    module.fail_json(msg = "Unable to get configuration from domain %s." % (domain_name))

        elif state == 'absent': # Remove domain

            if domain_name in configured_domains: # Domain EXIST.

                # If the user is working in only check mode we do not want to make any changes
                if module.check_mode:
                    result['msg'] = IDG_Utils.CHECK_MODE_MESSAGE
                    module.exit_json(**result)

                # Remove
                del_code, del_msg, del_data = idg_mgmt.api_call(uri = IDG_Utils.URI_DOMAIN_CONFIG.format(domain_name),
                                                                method = 'DELETE', data = None)

                # pdb.set_trace()
                if del_code == 200 and del_msg == 'OK':
                    # Remove successfully
                    result['msg'] = idg_mgmt.status_text(del_data[domain_name])
                    result['changed'] = True
                else:
                    # Can't remove
                    module.fail_json(msg = 'Error deleting domain "%s".' % (domain_name))

            else: # Domain NOT EXIST.
                result['msg'] = IDG_Utils.IMMUTABLE_MESSAGE

        # pdb.set_trace()
        # That's all folks!
        module.exit_json(**result)

    else: # Can't read domain's lists
        module.fail_json(msg = idg_mgmt.ERROR_GET_DOMAIN_LIST)

if __name__ == '__main__':
    main()
