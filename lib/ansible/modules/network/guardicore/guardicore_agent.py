#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Guardicore Agents (c) 2019
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: guardicore_agent
short_description: Manages Guardicore Agents
description:
  - Manage Guardicore Agents over different linux operation system.
  - Please check the Agent Installation Instructions screen in the Guardicore Centra UI to make sure the OSs and versions are supported.
version_added: "2.10"
author: "Lior Bar-Oz (@liorBaroz)"
options:
  installation_password:
    description:
      - Agent installation password (as shown the the Centra UI). required if state set as C(present).
    required: False
    type: str
  ssl_address:
    description:
      - the ssl address to install the agent in front of.
      - C(ssl_address) or C(ssl_address_cluster) are required if state set as C(present).
    required: False
    type: str
  ssl_port:
    description:
      - the ssl port to install the agent in front of. default is C(443).
    required: False
    type: str
    default: 443
  ssl_addresses_cluster:
    description:
      - List of cluster ssl address must be in form of "C(<ssl_address>):C(<ssl_port>)". see example.
      - In case this parameter is given, ssl_address and ssl_port will not be in use
      - C(ssl_address) or C(ssl_address_cluster) are required if state set as C(present).
    required: False
    type: str
  state:
    description:
      - present, absent or service. Defaults to present.
      - if C('service') is selected, all the agent modules will be enabled unless the values of the
        C('disable_reveal')/C('disable_deception')/C('disable_detection')/C('disable_enforcement') 
        parameters will be set to disable. see example.
    type: str
    default: present
  labels:
    description:
      - Set a list of labels in the form of C('key1:value1,key2:value2') for labeling the Agent instance.
      - See examples below
    type: str
    required: False
  force:
    description:
      - Force the agent installation in case of any existing agent, from any versions.
    type: bool
    default: False
  display_name:
    description:
      - Set an alternative display name for the Agent in the Centra UI.
    type: str
  disable_reveal:
    description:
      - Disable the Reveal module by default.
      - Can be used with both C('present')/C('service') for C('state') parameter
      - It can be enabled manually through Agent configuration or by using C('service') for C('state') parameter afterwards.
    type: bool
    default: False
  disable_deception:
    description:
      - Disable the Deception module by default. 
      - Can be used with both C('present')/C('service') for C('state') parameter
      - It can be enabled manually through Agent configuration or by using C('service') for C('state') parameter afterwards.
    type: bool
    default: False
  disable_detection:
    description:
      - Disable the Detection module by default.
      - Can be used with both C('present')/C('service') for C('state') parameter.
      - It can be enabled manually through Agent configuration or by using C('service') for C('state') parameter afterwards.
    type: bool
    default: False
  disable_enforcement:
    description:
      - Disable the Enforcement module by default.
      - Can be used with both C('present')/C('service') for C('state') parameter
      - It can be enabled manually through Agent configuration or by using C('service') for C('state') parameter afterwards.
    type: bool
    default: False
  monitoring_enforcement:
    description:
      - Install the Enforcement module with monitoring operating mode.
    type: bool
    default: False
  disable_implicit_dns_rules:
    description:
      - Avoid creating default implicit ALLOW rules for the system configured DNS servers
    type: bool
    default: False
  custom_gc_root:
    description:
      - Install the agent and logs in a custom path instead of C(/var/lib/guardicore). For RPM based OS only.
    type: str
    default: /var/lib/guardicore
  debug:
    description:
      - Log extra debugging information.
    type: bool
    default: no
'''

EXAMPLES = r'''
- name: Install Guardicore Agent
  guardicore_agent:
    installation_password: "AgentInstallationPassword"
    state: present
    ssl_address: 192.168.1.100
    labels: "environment:production,app:web"

- name: Install Guardicore Agent without deception service using specific port
  guardicore_agent:
    installation_password: "AgentInstallationPassword"
    state: present
    ssl_address: 192.168.1.101
    ssl_port: 1443
    disable_deception: "no"

- name: Enable all Guardicore Agent modules except for deception, after it was installed
  guardicore_agent:
    state: service
    disable_deception: "yes"

- name: Install Guardicore Agent using cluster of ssl addresses
  guardicore_agent:
    installation_password: "AgentInstallationPassword"
    state: present
    ssl_addresses_cluster: "192.168.1.100:443,192.168.1.101:1443"

- name: Remove Guardicore Agent
  guardicore_agent:
    state: absent
'''

RETURN = r'''
installation_result:
    description: the Guardicore agent installation result
    returned: always
    type: dict
    sample: None
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url

AGENT_CERTIFICATE_TMP_PATH = "/tmp/guardicore_cas_chain_file.pem"
TEMP_INSTALLATION_FILE_PATH = "/tmp/agent_installation.sh"


def verify_params(params):
    """ verifying params before triggering the guardicore agent installation"""
    boolean_flag_params = ["debug", "force", "disable_reveal", "disable_deception", "disable_detection",
                           "disable_enforcement", "monitoring_enforcement", "disable_implicit_dns_rules"]
    wrong_params = []
    for flag_param in boolean_flag_params:
        if flag_param in params:
            if not isinstance(params[flag_param], bool):
                wrong_params.append(flag_param)
    return wrong_params


def set_env_vars(params):
    """setting the required environment variables to install the Guardicore agent on the machine"""
    os_environ = {}
    if params['installation_password']:
        os_environ['UI_UM_PASSWORD'] = params['installation_password']
    if params['ssl_addresses_cluster']:
        os_environ['SSL_ADDRESSES'] = params['ssl_addresses_cluster']
    elif params['ssl_address'] is not None and params['ssl_port']:
        os_environ['SSL_ADDRESSES'] = "{ssl_address}:{ssl_port}".format(ssl_address=params['ssl_address'],
                                                                        ssl_port=int(params['ssl_port']))
    if params['disable_enforcement']:
        os_environ['DISABLE_ENFORCEMENT'] = "true"
    if params['monitoring_enforcement']:
        os_environ['MONITORING_ENFORCEMENT'] = "true"
    if params['disable_deception']:
        os_environ['DISABLE_DECEPTION'] = "true"
    if params['disable_implicit_dns_rules']:
        os_environ['ENFORCEMENT_DAEMON_ARGS'] = "--verbose --disable-implicit-dns-rules"
    if params['debug']:
        os_environ['DAEMON_ARGS'] = "--verbose"
    if params['custom_gc_root'] != "/var/lib/guardicore":
        if params['custom_gc_root'][-1] == "/":
            params['custom_gc_root'] = params['custom_gc_root'][:-1]
        os_environ['CUSTOM_GC_ROOT'] = params['custom_gc_root']
    controller_daemon_args = ""
    if "display_name" in params:
        if params['display_name']:
            controller_daemon_args = "{controller_daemon_args} --display-name {display_name}".format(
                controller_daemon_args=controller_daemon_args, display_name=params['display_name'])
    if "labels" in params:
        if params['labels']:
            controller_daemon_args = "%s --labels %s" % (controller_daemon_args, params['labels'])
    if params['debug']:
        controller_daemon_args = "{controller_daemon_args} --verbose".format(
            controller_daemon_args=controller_daemon_args)
    if controller_daemon_args:
        os_environ['CONTROLLER_DAEMON_ARGS'] = controller_daemon_args
    return os_environ


def is_agent_exist(module, os_environ):
    """:return true if guardicore agent installed on the destination machine"""
    rc, stdout, stderr = module.run_command(args="ls /usr/bin/gc-agent", environ_update=os_environ)
    if stderr:
        if "No such file or directory:" in stderr:
            return False
    if stdout:
        return True


def _get_ssl_address(params):
    """ :return the ssl address based on the parameters """
    ssl_addresses = []

    if params['ssl_addresses_cluster']:
        ssl_addresses = params['ssl_addresses_cluster'].split(",")

    elif params['ssl_address'] is not None and params['ssl_port']:
        ssl_addresses.append("{ssl_address}:{ssl_port}".format(ssl_address=params['ssl_address'], ssl_port=params['ssl_port']))

    return ssl_addresses


def _download_cert(params):
    """downloading the certificate from the guardicore aggregator to install the agent with"""
    datatowrite = None
    ssl_addresses = _get_ssl_address(params)

    for ssl_address in ssl_addresses:
        if not datatowrite:
            url = 'https://{ssl_address}/guardicore-cas-chain-file.pem'.format(ssl_address=ssl_address)

            response = open_url(url=url, validate_certs=False, force_basic_auth=True)
            datatowrite = response.read()

    with open(AGENT_CERTIFICATE_TMP_PATH, 'wb') as f:
        f.write(datatowrite)


def _download_installation_file(module, params):
    """download the installation file"""
    datatowrite = None
    ssl_addresses = _get_ssl_address(params)

    for ssl_address in ssl_addresses:
        if not datatowrite:
            url = 'https://{ssl_address}/install.sh'.format(ssl_address=ssl_address)

            response = open_url(url=url, ca_path=AGENT_CERTIFICATE_TMP_PATH, validate_certs=False)
            datatowrite = response.read()

    with open(TEMP_INSTALLATION_FILE_PATH, 'wb') as f:
        f.write(datatowrite)

    module.run_command(
        "chmod +x {temp_installation_file_path}".format(temp_installation_file_path=TEMP_INSTALLATION_FILE_PATH))


def install_guardicore_agent(module, params, os_environ):
    """installing the guardicore agent on the machine"""
    try:
        output = ""

        _download_cert(params=params)

        _download_installation_file(module=module, params=params)

        rc, stdout, stderr = module.run_command("/tmp/agent_installation.sh", environ_update=os_environ)

        if rc == 0:
            output = stdout

        else:
            output += stderr

        if not output:
            output = " failed to get installation response "
        return output

    except Exception as e:
        return e


def uninstall_guardicore_agent(module):
    """remove gc-agent package form the destination machine"""
    try:
        rc, stdout, stderr = module.run_command("gc-agent uninstall")

        if stdout:
            return "Guardicore agent was removed successfully: {stdout}".format(stdout=stdout)
        elif stderr:
            return "Something went wrong with uninstalling Guardicore agent: {stderr}".format(stderr=stderr)

    except Exception as e:
        return e


def enable_guardicore_agent_services(params, module):
    """ enable the Guardicore Agent service except for those who is disabled by the params"""
    try:
        output = ""
        guardicore_agent_modules_to_disable = []
        services_list = ['reveal', 'deception', 'detection', 'enforcement']

        for service in services_list:

            if service == 'reveal':
                guardicore_agents_modules = ['reveal', 'reveal-channel']
            elif service == 'deception':
                guardicore_agents_modules = ['deception']
            elif service == 'detection':
                guardicore_agents_modules = ['detection']
            elif service == 'enforcement':
                guardicore_agents_modules = ['enforcement', 'enforcement-channel']

            if params['disable_{service}'.format(service=service)]:
                action = "module-stop"
                guardicore_agent_modules_to_disable.append(service)

            else:
                action = "module-start"

            for guardicore_agents_module in guardicore_agents_modules:
                rc, stdout, stderr = module.run_command("gc-agent {action} {guardicore_agents_module}".format(
                    action=action, guardicore_agents_module=guardicore_agents_module))
                if rc == 0:
                    output += stdout
                else:
                    output += stderr

        if guardicore_agent_modules_to_disable is []:
            output += "All Guardicore Agent services set to be enabled"

        return output

    except Exception as e:

        if not output:
            output = "Failed to change the Guardicore Agent services:\n{e}".format(e=e)
        return output


def main():
    argument_spec = dict(
        installation_password=dict(type='str', required=False),
        ssl_address=dict(type='str', required=False),
        ssl_port=dict(type='str', required=False, default='443'),
        ssl_addresses_cluster=dict(type='str', required=False),
        display_name=dict(type='str', required=False),
        labels=dict(type='str', required=False),
        state=dict(type='str', default='present'),
        force=dict(type='bool', default=False),
        debug=dict(type='bool', default=False),
        disable_reveal=dict(type='bool', default=False),
        disable_deception=dict(type='bool', default=False),
        disable_detection=dict(type='bool', default=False),
        disable_enforcement=dict(type='bool', default=False),
        monitoring_enforcement=dict(type='bool', default=False),
        disable_implicit_dns_rules=dict(type='bool', default=False),
        custom_gc_root=dict(type='str', default='/var/lib/guardicore')
    )

    required_if = [('state', 'present', ['installation_password'])]
    module = AnsibleModule(argument_spec=argument_spec, required_if=required_if)
    params = module.params
    result = {}

    try:
        unverified_params = verify_params(params)
        if not unverified_params:
            os_environ = set_env_vars(params=params)

            if params['state'] == 'present':

                if (not is_agent_exist(module=module, os_environ=os_environ)) or params['force']:
                    result['installation_result'] = install_guardicore_agent(module=module,
                                                                             params=params,
                                                                             os_environ=os_environ)
                else:
                    result['installation_result'] = "Guardicore agent already exist on destination"

            elif params['state'] == 'absent' or params['state'] == 'service':
                if is_agent_exist(module=module, os_environ=os_environ):

                    if params['state'] == 'absent':
                        result['installation_result'] = uninstall_guardicore_agent(module=module)

                    elif params['state'] == 'service':
                        result['installation_result'] = enable_guardicore_agent_services(params=params, module=module)

                else:
                    result['installation_result'] = "Guardicore agent was not exist on destination"

            module.exit_json(changed=True, msg="Done with: {result}".format(result=result))
        else:
            module.fail_json(msg="Some parameters are not valid: {unverified_params}\n{params}".format(
                unverified_params=unverified_params, params=params))
    except Exception as e:
        module.fail_json(msg="Something fatal happened: {exception}".format(exception=e))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
