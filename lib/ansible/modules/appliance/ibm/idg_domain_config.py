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
module: idg_domain_config
short_description: Manages IBM DataPower Gateway(IDG) domains configurations actions.
description:
  - Manages IBM DataPower Gateway(IDG) domains configurations actions.
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

  state:
    description:
      - Specifies the current state of the domain.
        C(reseted) will delete all configured services within the domain.
        C(exported)
        C(imported)
        C(saved)
      - Be particularly careful about changing the status C(reseted).
        These Will affect all configured services within the domain.
        C(reseted) deletes all configuration data in the domain
    default: saved
    required: True
    type: str
    choices:
      - reseted
      - imported
      - exported
      - saved

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

notes:
  - This documentation was developed mostly from the content
    provided by IBM in its web administration interface.
  - For more information consult the official documentation.
    U(https://www.ibm.com/support/knowledgecenter/SS9H2Y_7.7.0/com.ibm.dp.doc/welcome.html)

author:
  - David Grau Merconchini (@dgraum)
'''

EXAMPLES = '''

'''

RETURN = '''

'''

import json
from time import sleep
# import pdb

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import open_url

# Common package of our implementation for IDG
try:
    from ansible.module_utils.appliance.ibm.idg_common import *
    HAS_IDG_UTILS = True
except ImportError:
    HAS_IDG_UTILS = False

def main():

    # Constants for domain management
    _URI_DOMAIN_LIST = "/mgmt/domains/config/"
    _URI_DOMAIN_STATUS = "/mgmt/status/default/DomainStatus"
    _URI_ACTION = "/mgmt/actionqueue/{0}"

    # Arguments/parameters that a user can pass to the module

    module_args = dict(
        state = dict(type = 'str', choices = ['exported', 'imported', 'reseted', 'saved'], default = 'saved'), # Domain's operational state
        idg_connection = dict(type = 'dict', options = idg_endpoint_spec, required = True), # IDG connection
        name = dict(type = 'str', required = True), # Domain to work
        # for Export
        user_summary = dict(type = 'str', required = False), # Backup comment
        all_files = dict(type = 'bool', default = False), # Include all files in the local: directory for the domain
        persisted = dict(type = 'bool', default = False), # Export from persisted or running configuration
        internal_files = dict(type = 'bool', default = True), # Export internal configuration file
        # for Import
        input_file = dict(type = 'str', required = False, no_log=True), # The base64-encoded BLOB to import
        overwrite_files = dict(type = 'bool', default = False), # Overwrite files that exist
        overwrite_objects = dict(type = 'bool', default = False), # Overwrite objects that exist
        dry_run = dict(type = 'bool', default = False), # Import package (on) or validate the import operation without importing (off).
        rewrite_local_ip = dict(type = 'bool', default = False) # The local address bindings of services in the import package are rewritten on import to their equivalent interfaces
        # TODO !!!
        # DeploymentPolicy
    )

    # AnsibleModule instantiation
    module = AnsibleModule(
        argument_spec = module_args,
        supports_check_mode = True
    )

    # Validates the dependence of the utility module
    if not HAS_IDG_UTILS:
        module.fail_json(msg="The IDG utils module is required")

    # Parse arguments to dict
    idg_data_spec = parse_to_dict(module.params['idg_connection'], 'IDGConnection', ANSIBLE_VERSION)

    # Status & domain
    state = module.params['state']
    domain_name = module.params['name']

    # Result
    result['name'] = domain_name

    # Init IDG API connect
    idg_mgmt = IDG_API(ansible_module = module,
                       idg_host = "https://{0}:{1}".format(idg_data_spec['server'], idg_data_spec['server_port']),
                       headers = BASIC_HEADERS,
                       http_agent = HTTP_AGENT_SPEC,
                       use_proxy = idg_data_spec['use_proxy'],
                       timeout = idg_data_spec['timeout'],
                       validate_certs = idg_data_spec['validate_certs'],
                       user = idg_data_spec['user'],
                       password = idg_data_spec['password'],
                       force_basic_auth = BASIC_AUTH_SPEC)

    # Variable to store the status of the action
    action_result = ''

    # Configuration template for the domain
    export_action_msg = { "Export": {
                            "Format": "ZIP",
                            "UserComment": module.params['user_summary'],
                            "AllFiles": on_off(module.params['all_files']),
                            "Persisted": on_off(module.params['persisted']),
                            "IncludeInternalFiles": on_off(module.params['internal_files'])
                            # TODO
                            # "DeploymentPolicy":""
                          }
                        }

    import_action_msg = { "Import": {
                            "Format": "ZIP",
                            "InputFile": module.params['input_file'],
                            "OverwriteFiles": on_off(module.params['overwrite_files']),
                            "OverwriteObjects": on_off(module.params['overwrite_objects']),
                            "DryRun": on_off(module.params['dry_run']),
                            "RewriteLocalIP": on_off(module.params['rewrite_local_ip'])
                            # TODO
                            # "DeploymentPolicy": "name",
                            # "DeploymentPolicyParams": "name",
                          }
                        }
    # Action messages
    # Reset
    reset_act_msg = { "ResetThisDomain": {} }

    # Save
    save_act_msg = { "SaveConfig": {} }

    ###
    ### Here the action begins
    ###

    # List of configured domains
    chk_code, chk_msg, chk_data = idg_mgmt.api_call(uri = _URI_DOMAIN_LIST, method = 'GET', data = None)

    if chk_code == 200 and chk_msg == 'OK': # If the answer is correct

        if isinstance(chk_data['domain'], dict): # if has only default domain
            configured_domains = [chk_data['domain']['name']]
        else:
            configured_domains = [d['name'] for d in chk_data['domain']]

        if domain_name in configured_domains: # Domain EXIST.

            # pdb.set_trace()
            if state == 'exported':

                # If the user is working in only check mode we do not want to make any changes
                if module.check_mode:
                    result['msg'] = CHECK_MODE_MESSAGE
                    module.exit_json(**result)

                # export and finish
                # pdb.set_trace()
                exp_code, exp_msg, exp_data = idg_mgmt.api_call(uri = _URI_ACTION.format(domain_name), method = 'POST',
                                                                data = json.dumps(export_action_msg))

                if exp_code == 202 and exp_msg == 'Accepted':
                    # Exported accepted
                    while action_result != 'completed':
                        # Wait to complete
                        eac_code, eac_msg, eac_data = idg_mgmt.api_call(uri = _URI_ACTION.format(domain_name) + '/pending',
                                                                        method = 'GET', data = None)

                        if eac_code == 200 and eac_msg == 'OK':
                            action_result = idg_mgmt.get_operation_status(eac_data['operations'], exp_data['_links']['location']['href'])
                            if action_result != 'completed': sleep(idg_mgmt.SHORT_DELAY)
                        else:
                            # Opps can't get export status
                            module.fail_json(msg = to_native(idg_mgmt.ERROR_RETRIEVING_STATUS % (state, domain_name)))

                    # Export completed. Get result
                    doex_code, doex_msg, doex_data = idg_mgmt.api_call(uri = exp_data['_links']['location']['href'], method = 'GET',
                                                                       data = None)

                    if doex_code == 200 and doex_msg == 'OK':
                        # Export ok
                        result['file'] = doex_data['result']['file']
                        result['msg'] = idg_mgmt.status_text(action_result)
                        result['changed'] = True
                    else:
                        # Can't retrieve the export
                        module.fail_json(msg = to_native(idg_mgmt.ERROR_RETRIEVING_RESULT % (state, domain_name)))
                else:
                    # Export not accepted
                    module.fail_json(msg = to_native(idg_mgmt.ERROR_ACCEPTING_ACTION % (state, domain_name)))

            elif state == 'reseted':

                # If the user is working in only check mode we do not want to make any changes
                if module.check_mode:
                    result['msg'] = CHECK_MODE_MESSAGE
                    module.exit_json(**result)

                # Reseted domain
                reset_code, reset_msg, reset_data = idg_mgmt.api_call(uri = _URI_ACTION.format(domain_name), method = 'POST',
                                                                      data = json.dumps(reset_act_msg))

                # pdb.set_trace()
                if reset_code == 202 and reset_msg == 'Accepted':
                    # Reseted accepted
                    while action_result != 'processed':
                        rac_code, rac_msg, rac_data = idg_mgmt.api_call(uri = _URI_ACTION.format(domain_name) + '/pending',
                                                                        method = 'GET', data = None)

                        if rac_code == 200 and rac_msg == 'OK':
                            action_result = idg_mgmt.get_operation_status(rac_data['operations'], reset_data['_links']['location']['href'])
                            if action_result != 'completed': sleep(idg_mgmt.SHORT_DELAY) # Time for complete
                        else:
                            # Can't get reset status
                            module.fail_json(msg = to_native(idg_mgmt.ERROR_RETRIEVING_STATUS % (state, domain_name)))

                    # Reseted completed
                    dore_code, dore_msg, dore_data = idg_mgmt.api_call(uri = reset_data['_links']['location']['href'], method = 'GET',
                                                                       data = None)

                    if dore_code == 200 and dore_msg == 'OK':
                        # Reseted successfully
                        result['msg'] = dore_data['status']
                        result['changed'] = True
                    else:
                        # Can't retrieve the reset result
                        module.fail_json(msg = to_native(idg_mgmt.ERROR_RETRIEVING_RESULT % (state, domain_name)))

                else:
                    # Reseted not accepted
                    module.fail_json(msg = to_native(idg_mgmt.ERROR_ACCEPTING_ACTION % (state, domain_name)))

            elif state == 'saved':

                qds_code, qds_msg, qds_data = idg_mgmt.api_call(uri = _URI_DOMAIN_STATUS, method = 'GET', data = None)

                # pdb.set_trace()
                if qds_code == 200 and qds_msg == 'OK':

                    if isinstance(qds_data['DomainStatus'], dict):
                        domain_save_needed = qds_data['DomainStatus']['SaveNeeded']
                    else:
                        domain_save_needed = [d['SaveNeeded'] for d in qds_data['DomainStatus'] if d['Domain'] == domain_name][0]

                    # Saved domain
                    if domain_save_needed != 'off':

                        # If the user is working in only check mode we do not want to make any changes
                        if module.check_mode:
                            result['msg'] = CHECK_MODE_MESSAGE
                            module.exit_json(**result)

                        save_code, save_msg, save_data = idg_mgmt.api_call(uri = _URI_ACTION.format(domain_name), method = 'POST',
                                                                           data = json.dumps(save_act_msg))

                        # pdb.set_trace()
                        if save_code == 200 and save_msg == 'OK':
                            # Saved successfully
                            result['msg'] = idg_mgmt.status_text(save_data['SaveConfig'])
                            result['changed'] = True
                        else:
                            # Can't saved
                            module.fail_json(msg = to_native(idg_mgmt.ERROR_RETRIEVING_RESULT % (state, domain_name)))
                    else:
                        # Domain is save
                        result['msg'] = IMMUTABLE_MESSAGE

            elif state == 'imported':

                # If the user is working in only check mode we do not want to make any changes
                if module.check_mode:
                    result['msg'] = CHECK_MODE_MESSAGE
                    module.exit_json(**result)

                # Import
                # pdb.set_trace()
                imp_code, imp_msg, imp_data = idg_mgmt.api_call(uri = _URI_ACTION.format(domain_name), method = 'POST',
                                                                data = json.dumps(import_action_msg))

                # pdb.set_trace()
                if imp_code == 202 and imp_msg == 'Accepted':
                    # Import accepted
                    while action_result != 'processed':
                        iac_code, iac_msg, iac_data = idg_mgmt.api_call(uri = _URI_ACTION.format(domain_name) + '/pending',
                                                                        method = 'GET', data = None)

                        if iac_code == 200 and iac_msg == 'OK':
                            # Export completed
                            action_result = idg_mgmt.get_operation_status(iac_data['operations'], imp_data['_links']['location']['href'])
                            if action_result != 'processed': sleep(idg_mgmt.SHORT_DELAY) # Time for complete
                        else:
                            # Can't get import status
                            module.fail_json(msg = to_native(idg_mgmt.ERROR_RETRIEVING_STATUS % (state, domain_name)))

                    # Import ready
                    doim_code, doim_msg, doim_data = idg_mgmt.api_call(uri = imp_data['_links']['location']['href'], method = 'GET',
                                                                       data = None)

                    if doim_code == 200 and doim_msg == 'OK':
                        # Export completed
                        if doim_data['result']['Import']['import-results']['detected-errors'] == 'true':
                            # pdb.set_trace()
                            result['msg'] = 'Error code:' + doim_data['result']['Import']['import-results']['detected-errors']['error']
                            result['changed'] = False
                            result['failed'] = True
                        else:
                            result['msg'] = doim_data['status']
                            result['changed'] = True
                    else:
                        # Can't retrieve the import result
                        module.fail_json(msg = to_native(idg_mgmt.ERROR_RETRIEVING_RESULT % (state, domain_name)))
                else:
                    # Imported not accepted
                    module.fail_json(msg = to_native(idg_mgmt.ERROR_ACCEPTING_ACTION % (state, domain_name)))

        else: # Domain NOT EXIST.
            # pdb.set_trace()
            # Opps can't work the configuration of non-existent domain
            module.fail_json(msg = idg_mgmt.ERROR_REACH_STATE + ' Domain not exist!' % (state, domain_name))

        # pdb.set_trace()
        # That's all folks!
        module.exit_json(**result)

    else: # The DP domains could not be extracted
        module.fail_json(msg = idg_mgmt.ERROR_GET_DOMAIN_LIST)

if __name__ == '__main__':
    main()
