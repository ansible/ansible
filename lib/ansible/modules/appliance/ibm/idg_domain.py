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
version_added: "2.8"
options:

  name:
    description:
      - Domain identifier.
    required: True

  user_summary:
    description:
      - Description for the domain.

  admin_state:
    description:
      - Define the administrative state of the domain.
      - C(enabled), To make active.
      - C(disabled), To make inactive.
    default: enabled
    choices:
      - enabled
      - disabled

  config_mode:
    description:
      - Whether the configuration file is local or remote.
      - NOT YET IMPLEMENTED, its value are fixed so as not to affect the immutability
    default: local

  config_permissions_mode:
    description:
      - Specifies the the security context for the configuration
        files that are run in the domain.
      - NOT YET IMPLEMENTED, its value are fixed so as not to affect the immutability
    default: scope-domain

  import_format:
    description:
      - The format of the remote configuration file.
      - NOT YET IMPLEMENTED, its value are fixed so as not to affect the immutability
    default: ZIP

  visible:
    description:
        - Set which application domains have their C(local:/) directory visible to this application domain.
    default:
        - default
    required: False

  local_ip_rewrite:
    description:
      - Whether to rewrite local IP addresses during import.
      - NOT YET IMPLEMENTED, its value are fixed so as not to affect the immutability
    default: True
    type: bool

  max_chkpoints:
    description:
      - The maximum number of configuration checkpoints to support.
    default: 3

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
        These will affect all configured services within the domain.
        C(restarted) all the configuration that has not been saved will be lost.
    default: present
    required: True
    choices:
      - present
      - absent
      - restarted
      - quiesced
      - unquiesced

  quiesce_conf:
    description:
      - Only necessary when the I(state=quiesced)
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
            all transactions to complete. The minimum is C(60).

  monitoring_map:
    description:
      - Which types of events to generate when files are added to or deleted from the C(local://) directory.
    default:
      audit: False
      log: False
    suboptions:
      audit:
        description:
          - Generate audit events.
        type: bool
      log:
        description:
          - Generate log events.
        type: bool

  file_map:
    description:
      - Which file permissions to apply to the C(local://) directory.
    default:
      display: True
      exec: True
      copyfrom: True
      copyto: True
      delete: True
      subdir: True
    suboptions:
      display:
        description:
          - File content can be displayed.
        type: bool
      exec:
        description:
          - Files can be run as scripts.
        type: bool
      copyfrom:
        description:
          - Files can be copied from directory.
        type: bool
      copyto:
        description:
          - Files can be copied to the directory.
        type: bool
      delete:
        description:
          - Files can be deleted.
        type: bool
      subdir:
        description:
          - Can be created subdirectories.
        type: bool

extends_documentation_fragment: idg

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
  returned: always
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
    - Unknown error for (https://idg-host1:5554/mgmt/domains/config/). <open_url error timed out>
'''

import json
# import pdb

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

# Common package of our implementation for IDG
HAS_IDG_DEPS = False
try:
    from ansible.module_utils.appliance.ibm.idg_common import result, idg_endpoint_spec, IDGUtils
    from ansible.module_utils.appliance.ibm.idg_rest_mgmt import IDGApi, ErrorHandler
    HAS_IDG_DEPS = True
except ImportError:
    try:
        from library.module_utils.idg_common import result, idg_endpoint_spec, IDGUtils
        from library.module_utils.idg_rest_mgmt import IDGApi, ErrorHandler
        HAS_IDG_DEPS = True
    except ImportError:
        pass

# Version control
__MODULE_NAME = "idg_domain"
__MODULE_VERSION = "1.0"
__MODULE_FULLNAME = __MODULE_NAME + '-' + __MODULE_VERSION


def main():
    # Define the available arguments/parameters that a user can pass to the module
    # File permission to the local: directory
    filemap_spec = {
        'display': dict(type='bool'),  # File content can be displayed for the local: directory.
        'exec': dict(type='bool'),  # Files in the local: directory can be run as scripts.
        'copyfrom': dict(type='bool'),  # Files can be copied FROM the local: directory.
        'copyto': dict(type='bool'),  # Files can be copied TO the local: directory.
        'delete': dict(type='bool'),  # Files can be DELETED from the local: directory.
        'subdir': dict(type='bool')  # Subdirectories can be created in the local: directory.
    }

    # Which types of events to generate when files are added to or deleted from the local: directory.
    monitoringmap_spec = {
        'audit': dict(type='bool'),  # Generate audit events.
        'log': dict(type='bool')  # Generate log events.
    }

    # Quiesce configuration
    quiescemap_spec = {
        'delay': dict(type='int', default=0),  # Specifies the interval of time in seconds to wait before initiating the quiesce action.
        'timeout': dict(type='int', default=60)  # Specifies the length of time in seconds to wait for all transactions to complete.
    }

    # Validates the dependence of the utility module
    if HAS_IDG_DEPS:
        module_args = dict(
            name=dict(type='str', required=True),  # Domain name
            user_summary=dict(type='str', required=False),  # Domain description
            admin_state=dict(type='str', choices=['enabled', 'disabled'], default='enabled'),  # Domain's administrative state
            state=dict(type='str', choices=['present', 'absent', 'restarted', 'quiesced', 'unquiesced'], default='present'),  # Domain's operational state
            quiesce_conf=dict(type='dict', options=quiescemap_spec, default=dict({'delay': 0, 'timeout': 60})),  # Transitions the operational state to down
            idg_connection=dict(type='dict', options=idg_endpoint_spec, required=True),  # IDG connection
            file_map=dict(type='dict', options=filemap_spec, default=dict({'display': True, 'exec': True, 'copyfrom': True,
                                                                           'copyto': True, 'delete': True, 'subdir': True})),  # File permission
            monitoring_map=dict(type='dict', options=monitoringmap_spec, default=dict({'audit': False,
                                                                                       'log': False})),  # Events  when work whith files
            max_chkpoints=dict(type='int', default=3),  # The maximum number of configuration checkpoints to support.
            visible=dict(type='list', default=['default']),  # Which application domains have visible to this domain
            # TODO !!!
            # It is better to guarantee immutability while waiting.
            config_mode=dict(type='str', default='local'),
            config_permissions_mode=dict(type='str', default='scope-domain'),
            import_format=dict(type='str', default='ZIP'),
            local_ip_rewrite=dict(type='bool', default=True)
        )

        # AnsibleModule instantiation
        module = AnsibleModule(
            argument_spec=module_args,
            supports_check_mode=True,
            # Interaction between parameters
            required_if=[['state', 'quiesced', ['quiesce_conf']]]
        )

    else:
        # Failure AnsibleModule instance
        module = AnsibleModule(
            argument_spec={},
            check_invalid_arguments=False
        )
        module.fail_json(msg="The IDG utils modules is required")

    # Parse arguments to dict
    idg_data_spec = IDGUtils.parse_to_dict(module, module.params['idg_connection'], 'IDGConnection', IDGUtils.ANSIBLE_VERSION)
    filemap_data_spec = IDGUtils.parse_to_dict(module, module.params['file_map'], 'FileMap', IDGUtils.ANSIBLE_VERSION)
    monitoringmap_data_spec = IDGUtils.parse_to_dict(module, module.params['monitoring_map'], 'MonitoringMap', IDGUtils.ANSIBLE_VERSION)
    quiesce_conf_data_spec = IDGUtils.parse_to_dict(module, module.params['quiesce_conf'], 'QuiesceConf', IDGUtils.ANSIBLE_VERSION)

    if len(module.params['visible']) == 1:
        visible_domain = {"value": module.params['visible'][0]}
    else:
        visible_domain = []
        for d in module.params['visible']:
            visible_domain.append({"value": d})

    # Domain to work
    domain_name = module.params['name']

    # Status
    state = module.params['state']
    admin_state = module.params['admin_state']

    # Init IDG API connect
    idg_mgmt = IDGApi(ansible_module=module,
                      idg_host="https://{0}:{1}".format(idg_data_spec['server'], idg_data_spec['server_port']),
                      headers=IDGUtils.BASIC_HEADERS,
                      http_agent=IDGUtils.HTTP_AGENT_SPEC,
                      use_proxy=idg_data_spec['use_proxy'],
                      timeout=idg_data_spec['timeout'],
                      validate_certs=idg_data_spec['validate_certs'],
                      user=idg_data_spec['user'],
                      password=idg_data_spec['password'],
                      force_basic_auth=IDGUtils.BASIC_AUTH_SPEC)

    # Variable to store the status of the action
    action_result = ''

    # Configuration template for the domain
    domain_obj_msg = {"Domain": {
        "name": domain_name,
        "mAdminState": admin_state,
        "ConfigMode": module.params['config_mode'],
        "ConfigPermissionsMode": module.params['config_permissions_mode'],
        "ImportFormat": module.params['import_format'],
        "LocalIPRewrite": IDGUtils.str_on_off(module.params['local_ip_rewrite']),
        "MaxChkpoints": module.params['max_chkpoints'],
        "FileMap": {
            "Display": IDGUtils.str_on_off(filemap_data_spec['display']),
            "Exec": IDGUtils.str_on_off(filemap_data_spec['exec']),
            "CopyFrom": IDGUtils.str_on_off(filemap_data_spec['copyfrom']),
            "CopyTo": IDGUtils.str_on_off(filemap_data_spec['copyto']),
            "Delete": IDGUtils.str_on_off(filemap_data_spec['delete']),
            "Subdir": IDGUtils.str_on_off(filemap_data_spec['subdir'])
        },
        "MonitoringMap": {
            "Audit": IDGUtils.str_on_off(monitoringmap_data_spec['audit']),
            "Log": IDGUtils.str_on_off(monitoringmap_data_spec['log'])
        },
        "NeighborDomain": visible_domain
    }}
    # Add description
    if module.params['user_summary'] is not None:
        domain_obj_msg["Domain"].update({"UserSummary": module.params['user_summary']})

    # List of properties that are managed
    domain_obj_items = [k for k, v in domain_obj_msg['Domain'].items()]

    # Action messages
    # Restart
    restart_act_msg = {"RestartThisDomain": {}}

    # Quiesce
    quiesce_act_msg = {"DomainQuiesce": {
        "delay": quiesce_conf_data_spec['delay'], "name": domain_name,
        "timeout": quiesce_conf_data_spec['timeout']
    }}

    # Unquiesce
    unquiesce_act_msg = {"DomainUnquiesce": {"name": domain_name}}

    # Intermediate values ​​for result
    tmp_result = {"msg": None, "name": domain_name, "changed": None}

    #
    # Here the action begins
    #
    # pdb.set_trace()

    try:
        # List of configured domains
        idg_mgmt.api_call(IDGApi.URI_DOMAIN_LIST, method='GET', id="list_domains")

        if idg_mgmt.is_ok(idg_mgmt.last_call()):  # If the answer is correct

            # List of existing domains
            configured_domains = IDGUtils.domains_list(idg_mgmt.last_call()["data"]['domain'])

            if state in ('present', 'restarted', 'quiesced', 'unquiesced'):  # They need for or do a domain

                if domain_name not in configured_domains:  # Domain NOT EXIST.

                    if state == 'present':  # Create it

                        # If the user is working in only check mode we do not want to make any changes
                        IDGUtils.implement_check_mode(module)

                        idg_mgmt.api_call(IDGApi.URI_DOMAIN_CONFIG.format(domain_name), method='PUT', data=json.dumps(domain_obj_msg), id="create_domain")

                        if idg_mgmt.is_created(idg_mgmt.last_call()):  # Created successfully
                            tmp_result['msg'] = idg_mgmt.status_text(idg_mgmt.last_call()["data"][domain_name])
                            tmp_result['changed'] = True
                        else:
                            # Opps can't create
                            module.fail_json(msg=IDGApi.ERROR_REACH_STATE.format(state, domain_name))

                    elif state in ('restarted', 'quiesced', 'unquiesced'):  # Can't do this actions
                        module.fail_json(msg=(IDGApi.ERROR_REACH_STATE + " " + IDGApi.ERROR_NOT_DOMAIN).format(state, domain_name))

                else:  # Domain EXIST
                    # Update, save or restart
                    # Get current domain configuration
                    idg_mgmt.api_call(IDGApi.URI_DOMAIN_CONFIG.format(domain_name), method='GET', id="exist_domain_config")

                    if idg_mgmt.is_ok(idg_mgmt.last_call()):
                        if state == 'present':
                            # We focus only on the properties we administer
                            dc_data = idg_mgmt.last_call()["data"]  # Save domain configuration
                            del dc_data['_links']
                            for k, v in dc_data['Domain'].items():
                                if k not in domain_obj_items:
                                    del dc_data['Domain'][k]
                                elif k == 'NeighborDomain':
                                    if isinstance(dc_data['Domain'][k], dict):
                                        del dc_data['Domain'][k]['href']
                                    elif isinstance(dc_data['Domain'][k], list):
                                        dc_data['Domain'][k] = [{'value': dv['value']} for dv in dc_data['Domain'][k]]

                            if domain_obj_msg['Domain'] != dc_data['Domain']:  # Need update
                                # If the user is working in only check mode we do not want to make any changes
                                IDGUtils.implement_check_mode(module)

                                idg_mgmt.api_call(IDGApi.URI_DOMAIN_CONFIG.format(domain_name), method='PUT', data=json.dumps(domain_obj_msg),
                                                  id="update_domain")

                                if idg_mgmt.is_ok(idg_mgmt.last_call()):
                                    # Updates successfully
                                    tmp_result['msg'] = idg_mgmt.status_text(idg_mgmt.last_call()["data"][domain_name])
                                    tmp_result['changed'] = True
                                else:
                                    # Opps can't update
                                    module.fail_json(msg=IDGApi.GENERAL_ERROR.format(__MODULE_FULLNAME, state, domain_name) +
                                                     str(ErrorHandler(idg_mgmt.last_call()["data"]['error'])))

                            else:  # Identicals configurations
                                # The current configuration is identical to the new configuration, there is nothing to do
                                tmp_result['msg'] = IDGUtils.IMMUTABLE_MESSAGE

                        elif state == 'restarted':  # Restart domain
                            # If the user is working in only check mode we do not want to make any changes
                            IDGUtils.implement_check_mode(module)

                            idg_mgmt.api_call(IDGApi.URI_ACTION.format(domain_name), method='POST', data=json.dumps(restart_act_msg), id="restart_domain")

                            if idg_mgmt.is_accepted(idg_mgmt.last_call()):
                                # Asynchronous actions restart accepted. Wait for complete
                                idg_mgmt.api_event_sink(IDGApi.URI_ACTION.format(domain_name),
                                                        href=idg_mgmt.call_by_id("restart_domain")["data"]['_links']['location']['href'], state=state)

                                if idg_mgmt.is_ok(idg_mgmt.last_call()):
                                    # Restarted successfully
                                    tmp_result['msg'] = idg_mgmt.last_call()["data"]["status"].capitalize()
                                    tmp_result['changed'] = True
                                else:
                                    # Can't retrieve the restart result
                                    module.fail_json(msg=IDGApi.ERROR_RETRIEVING_RESULT.format(state, domain_name))

                            else:
                                # Can't restarted
                                module.fail_json(msg=IDGApi.ERROR_ACCEPTING_ACTION.format(state, domain_name))

                        elif state in ('quiesced', 'unquiesced'):

                            idg_mgmt.api_call(IDGApi.URI_DOMAIN_STATUS, method='GET', id="domain_status")

                            if idg_mgmt.is_ok(idg_mgmt.last_call()):

                                if isinstance(idg_mgmt.last_call()["data"]['DomainStatus'], dict):
                                    domain_quiesce_status = idg_mgmt.last_call()["data"]['DomainStatus']['QuiesceState']
                                else:
                                    domain_quiesce_status = [d['QuiesceState'] for d in idg_mgmt.last_call()["data"]['DomainStatus'] if
                                                             d['Domain'] == domain_name][0]

                                if state == 'quiesced':
                                    if domain_quiesce_status == '':
                                        # If the user is working in only check mode we do not want to make any changes
                                        IDGUtils.implement_check_mode(module)

                                        # Quiesce domain
                                        idg_mgmt.api_call(IDGApi.URI_ACTION.format(domain_name), method='POST', data=json.dumps(quiesce_act_msg),
                                                          id="quiesce_domain")

                                        if idg_mgmt.is_accepted(idg_mgmt.last_call()):
                                            # Asynchronous actions quiesce accepted. Wait for complete
                                            idg_mgmt.api_event_sink(IDGApi.URI_ACTION.format(domain_name),
                                                                    href=idg_mgmt.call_by_id("quiesce_domain")["data"]['_links']['location']['href'],
                                                                    state=state)

                                            if idg_mgmt.is_ok(idg_mgmt.last_call()):
                                                # Quiesced successfully
                                                tmp_result['msg'] = idg_mgmt.last_call()["data"]["status"].capitalize()
                                                tmp_result['changed'] = True
                                            else:
                                                # Can't get the quiesced action result
                                                module.fail_json(msg=IDGApi.ERROR_RETRIEVING_RESULT.format(state, domain_name))

                                        else:
                                            # Can't quiesced
                                            module.fail_json(msg=IDGApi.ERROR_ACCEPTING_ACTION.format(state, domain_name))
                                    else:
                                        # Domain is quiesced
                                        tmp_result['msg'] = IDGUtils.IMMUTABLE_MESSAGE

                                elif state == 'unquiesced':
                                    if domain_quiesce_status == 'quiesced':
                                        # If the user is working in only check mode we do not want to make any changes
                                        IDGUtils.implement_check_mode(module)

                                        # Unquiesce domain
                                        idg_mgmt.api_call(IDGApi.URI_ACTION.format(domain_name), method='POST', data=json.dumps(unquiesce_act_msg),
                                                          id="unquiesce_domain")

                                        if idg_mgmt.is_accepted(idg_mgmt.last_call()):
                                            # Asynchronous actions unquiesce accepted. Wait for complete
                                            idg_mgmt.api_event_sink(IDGApi.URI_ACTION.format(domain_name),
                                                                    href=idg_mgmt.call_by_id("unquiesce_domain")["data"]['_links']['location']['href'],
                                                                    state=state)

                                            if idg_mgmt.is_ok(idg_mgmt.last_call()):
                                                # Unquiesce successfully
                                                tmp_result['msg'] = idg_mgmt.last_call()["data"]["status"].capitalize()
                                                tmp_result['changed'] = True
                                            else:
                                                # Can't get unquiesce final result
                                                module.fail_json(msg=IDGApi.ERROR_RETRIEVING_RESULT.format(state, domain_name))

                                        elif idg_mgmt.is_ok(idg_mgmt.call_by_id("unquiesce_domain")):
                                            # Successfully processed synchronized action
                                            tmp_result['msg'] = idg_mgmt.status_text(idg_mgmt.call_by_id("unquiesce_domain")['DomainUnquiesce'])
                                            tmp_result['changed'] = True

                                        else:
                                            # Can't accept unquiesce
                                            module.fail_json(msg=IDGApi.ERROR_ACCEPTING_ACTION.format(state, domain_name))
                                    else:
                                        # Domain is unquiesced
                                        tmp_result['msg'] = IDGUtils.IMMUTABLE_MESSAGE
                            else:
                                # Can't get domain status
                                module.fail_json(msg="Unable to get status from domain {0}.".format(domain_name))
                    else:
                        # Can't read domain configuration
                        module.fail_json(msg="Unable to get configuration from domain {0}.".format(domain_name))

            elif state == 'absent':  # Remove domain

                if domain_name in configured_domains:  # Domain EXIST.
                    # If the user is working in only check mode we do not want to make any changes
                    IDGUtils.implement_check_mode(module)

                    # Remove
                    idg_mgmt.api_call(IDGApi.URI_DOMAIN_CONFIG.format(domain_name), method='DELETE', id="delete_domain")

                    if idg_mgmt.is_ok(idg_mgmt.last_call()):
                        # Remove successfully
                        tmp_result['msg'] = idg_mgmt.status_text(idg_mgmt.last_call()["data"][domain_name])
                        tmp_result['changed'] = True
                    else:
                        # Can't remove
                        module.fail_json(msg='Error deleting domain "{0}".'.format(domain_name))

                else:  # Domain NOT EXIST.
                    tmp_result['msg'] = IDGUtils.IMMUTABLE_MESSAGE

        else:  # Can't read domain's lists
            module.fail_json(msg=IDGApi.ERROR_GET_DOMAIN_LIST)

        #
        # Finish
        #
        # Update
        for k, v in tmp_result.items():
            if v is not None:
                result[k] = v

    except Exception as e:
        # Uncontrolled exception
        module.fail_json(msg=(IDGUtils.UNCONTROLLED_EXCEPTION + '. {0}').format(to_native(e)))
    else:
        # That's all folks!
        module.exit_json(**result)


if __name__ == '__main__':
    main()
