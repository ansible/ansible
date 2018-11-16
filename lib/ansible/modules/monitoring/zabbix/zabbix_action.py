#!/usr/bin/python


from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: zabbix_action

short_description: Create/Delete/Update Zabbix actions

version_added: "2.4"

description:
    - This module allows you to create, modify and delete Zabbix actions.

options:
    name:
        description:
            - Name of the action
        required: true
    event_source:
        description:
            - Type of events that the action will handle.
        required: true
        choices: ['triggers', 'discovery', 'auto_registration', 'internal']
    state:
        description:
            - State of the action.
            - On C(present), it will create an action if it does not exist or update the action if the associated data is different.
            - On C(absent), it will remove the action if it exists.
        choices: ['present', 'absent']
        default: 'present'
    status:
        description:
            - Monitoring status of the action.
        choices: ['enabled', 'disabled']
        default: 'enabled'
    conditions:
        type: list
        description:
            - List of dictionaries of conditions to evaluate.
        suboptions:
            type:
                description: Type (label) of the condition
                choices:
                    # trigger
                    - host_group
                    - host
                    - trigger
                    - trigger_name
                    - trigger_severity
                    - time_period
                    - host_template
                    - application
                    - maintenance_status
                    - event_tag
                    - event_tag_value
                    # discovery
                    - host_IP
                    - discovered_service_type
                    - discovered_service_port
                    - discovery_status
                    - uptime_or_downtime_duration
                    - received_value
                    - discovery_rule
                    - discovery_check
                    - proxy
                    - discovery_object
                    # auto_registration
                    - proxy
                    - host_name
                    - host_metadata
                    # internal
                    - host_group
                    - host
                    - host_template
                    - application
                    - event_type
            value:
                description:
                    - Value to compare with.
            operator:
                description:
                    - Condition operator.
                choices:
                    - '='
                    - '<>'
                    - 'like'
                    - 'not like'
                    - 'in'
                    - '>='
                    - '<='
                    - 'not in'
            formulaid:
                description:
                    - Arbitrary unique ID that is used to reference the condition from a custom expression. 
                    - Can only contain capital-case letters.
    formula:
        description:
            - User-defined expression to be used for evaluating conditions of filters with a custom expression.
            - The expression must contain IDs that reference specific filter conditions by its formulaid. 
            - The IDs used in the expression must exactly match the ones defined in the filter conditions: no condition can remain unused or omitted.
            - Required for custom expression filters. 
    operations:
        type: list
        description:
            - List of action operations
        suboptions:
            type:
                description:
                    - Type of operation.
                choices:
                    - send_message
                    - remote_command
                    - add_host
                    - remove_host
                    - add_to_host_group
                    - remove_from_host_group
                    - link_to_template
                    - unlink_from_template
                    - enable_host
                    - disable_host
                    - set_host_inventory_mode
            esc_period:
                description:
                    - Duration of an escalation step in seconds. 
                    - Must be greater than 60 seconds. 
                    - Accepts seconds, time unit with suffix and user macro. 
                    - If set to 0 or 0s, the default action escalation period will be used.
                default: 0s
            esc_step_from:
                description:
                    - Step to start escalation from.
                default: 1
            esc_step_to:
                description:
                    - Step to end escalation at.
                default: 1
            send_to_groups:
                type: list
                description:
                    - User groups to send messages to.
            send_to_users:
                type: list
                description:
                    - Users to send messages to.
            message:
                description:
                    - Operation message text.
            subject:
                description:
                    - Operation message subject.
            media_type:
                description:
                    - Media type that will be used to send the message.
            command_type:
                description:
                    - Type of operation command.
                    - Required when I(type=remote_command).
                choices:
                    - custom_script
                    - ipmi
                    - ssh
                    - telnet
                    - global_script
            command:
                description:
                    - Command to run.
                    - Required when I(type=remote_command) and I(command_type!=global_script).
            execute_on:
                description:
                    - Target on which the custom script operation command will be executed.
                    - Required when I(type=remote_command) and I(command_type=custom_script)
                choices:
                    - agent
                    - server
                    - proxy
            run_on_groups:
                description:
                    - Host groups to run remote commands on
                    - Required when I(type=remote_command) if I(run_on_hosts) is not set
            run_on_hosts:
                description:
                    - Hosts to run remote commands on
                    - Required when I(type=remote_command) if I(run_on_groups) is not set
            ssh_auth_type:
                description:
                    - Authentication method used for SSH commands.
                    - Required when I(type=remote_command) and I(command_type=ssh)
                choices:
                    - password
                    - public_key
            ssh_privatekey_file:
                description:
                    - Name of the private key file used for SSH commands with public key authentication.
                    - Required when I(type=remote_command) and I(command_type=ssh)
            ssh_publickey_file:
                description:
                    - Name of the public key file used for SSH commands with public key authentication.
                    - Required when I(type=remote_command) and I(command_type=ssh)
            username:
                description:
                    - User name used for authentication.
                    - Required when I(type=remote_command) and I(command_type in [ssh, telnet])
            password:
                description:
                    - Password used for authentication.
                    - Required when I(type=remote_command) and I(command_type in [ssh, telnet])
            port:
                description:
                    - Port number used for authentication.
                    - Required when I(type=remote_command) and I(command_type in [ssh, telnet])
            script_name:
                description:
                    - The name of script used for global script commands.
                    - Required when I(type=remote_command) and I(command_type=global_script)
    recovery_operations:
        type: list
        description:
            - List of recovery operations
        suboptions:
            - Same as I(operations)
    acknowledge_operations:
        type: list
        description:
            - List of acknowledge operations
        suboptions:
            - Same as I(operations)



extends_documentation_fragment:
    - zabbix

author:
    - Ruben Tsirunyan (@rubentsirunyan)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_new_test_module:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

try:
    from zabbix_api import ZabbixAPI, ZabbixAPISubClass

    # Extend the ZabbixAPI
    # Since the zabbix-api python module too old (version 1.0, no higher version so far),
    # it does not support the 'hostinterface' api calls,
    # so we have to inherit the ZabbixAPI class to add 'hostinterface' support.
    class ZabbixAPIExtends(ZabbixAPI):
        hostinterface = None

        def __init__(self, server, timeout, user, passwd, validate_certs, **kwargs):
            ZabbixAPI.__init__(self, server, timeout=timeout, user=user, passwd=passwd, validate_certs=validate_certs)
            self.hostinterface = ZabbixAPISubClass(self, dict({"prefix": "hostinterface"}, **kwargs))

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False

from ansible.module_utils.basic import AnsibleModule


class Action(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    def check_if_action_exists(self, name):
        result = self._zapi.action.get({'filter': {'name': name}})
        return result

    def get_action_by_name(self, name):
        action_list = self._zapi.action.get({'output': 'extend', 'selectInventory': 'extend', 'filter': {'name': [name]}})
        if len(action_list) < 1:
            self._module.fail_json(msg="Action not found: " % name)
        else:
            return action_list[0]

    def add_action(self, **kwargs):
        try:
            parameters = {
                    'name': kwargs['name'],
                    'eventsource': kwargs['event_source'],
                    'esc_period': kwargs['esc_period'],
                    'operations': kwargs['operations'],
                    'status': kwargs['status'],
                    }
            action_list = self._zapi.action.create(parameters)
            return action_list['actionids'][0]
        except Exception as e:
            self._module.fail_json(msg="Failed to create action '%s': %s" % (kwargs['name'], e))


class Operations(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    # get host by host name
    def get_host_by_host_name(self, host_name):
        host_list = self._zapi.host.get({'output': 'extend', 'selectInventory': 'extend', 'filter': {'host': [host_name]}})
        if len(host_list) < 1:
            self._module.fail_json(msg="Host not found: %s" % host_name)
        else:
            return host_list[0]

    def _construct_operationtype(self, operation):
        operation['type'] = map_to_int([
                "send_message",
                "remote_command",
                "add_host",
                "remove_host",
                "add_to_host_group",
                "remove_from_host_group",
                "link_to_template",
                "unlink_from_template",
                "enable_host",
                "disable_host",
                "set_host_inventory_mode"], operation['type'])
        operation['operationtype'] = operation.pop('type')

    # Convert to opcommand
    def _construct_opcommand(self, operation):
        self.command_keys = {
            'command_type',
            'command',
            'execute_on',
            'global_script',
            'ssh_auth_type',
            'ssh_privatekey_file',
            'ssh_publickey_file',
            'username',
            'password',
            'port'
        }

        operation['opcommand'] = {
                'type': map_to_int([
                    'custom_script',
                    'ipmi',
                    'ssh',
                    'telnet',
                    'global_script'], operation.get('command_type','custom_script')),
                'command': operation.get('command',None),
                'execute_on': map_to_int([
                    'agent',
                    'server',
                    'proxy'],operation.get('execute_on','server')),
                'scriptid': operation.get('global_script',None),
                'authtype': map_to_int([
                    'password',
                    'private_key'
                    ], operation.get('ssh_auth_type', 'password')),
                'privatekey': operation.get('ssh_privatekey_file',None),
                'publickey': operation.get('ssh_publickey_file',None),
                'username': operation.get('username',None),
                'password': operation.get('password',None),
                'port': operation.get('port',None)
        }

        for _key in self.command_keys:
            if _key in operation:
                operation.pop(_key)

    def _construct_opcommand_targets(self, operation):
        operation['opcommand_hst'] = [{'hostid': self.get_host_by_host_name(_host)} if _host != 0 else {'hostid': 0} for _host in operation.get('run_on_host',[])]
        operation['opcommand_grp'] = [{'groupid': self.get_group_by_group_name(_group)} for _group in operation.get('run_on_group',[])]
        operation.pop('run_on_host',None)
        operation.pop('run_on_group', None)


    def construct_the_data(self, operations):
        for op in operations:
            self._construct_operationtype(op)
            # Send Command type
            if op['operationtype'] == 1:
                self._construct_opcommand(op)
                self._construct_opcommand_targets(op)
            op = cleanup_data(op)
        return operations



def map_to_int(strs, value):
    """ Convert string values to integers"""
    tmp_dict = dict(zip(strs, list(range(len(strs)))))
    return tmp_dict[value]


def cleanup_data(obj):
    if isinstance(obj, (list, tuple, set)):
        return type(obj)(cleanup_data(x) for x in obj if x is not None)
    elif isinstance(obj, dict):
        return type(obj)((cleanup_data(k), cleanup_data(v))
            for k, v in obj.items() if k is not None and v is not None)
    else:
        return obj

def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            timeout=dict(type='int', default=10),
            name=dict(type='str', required=True),
            event_source=dict(type='str', required=True),
            state=dict(type='str', required=False, default='present'),
            status=dict(type='str', required=False, default='enabled'),
            conditions=dict(type='list', required=False, default=None),
            formula=dict(type='str', required=False, default=None),
            operations=dict(type='list', required=False, default=None),
            recovery_operations=dict(type='list', required=False, default=None),
            acknowledge_operations=dict(type='list', required=False, default=None)
        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing required zabbix-api module (check docs or install with: pip install zabbix-api)")

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    timeout = module.params['timeout']
    name = module.params['name']
    event_source = module.params['event_source']
    state = module.params['state']
    status = module.params['status']
    conditions = module.params['conditions']
    formula = module.params['formula']
    operations = module.params['operations']
    recovery_operations = module.params['recovery_operations']
    acknowledge_operations = module.params['acknowledge_operations']


    # Convert strings to integers
    status = map_to_int(['enabled', 'disabled'], status)
    event_source = map_to_int(['trigger', 'discovery', 'auto_registration', 'internal'], event_source)
    esc_period = "1h"
    try:
        zbx = ZabbixAPIExtends(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                               validate_certs=validate_certs)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    action = Action(module, zbx)

    action_exists = action.check_if_action_exists(name)

    ops = Operations(module, zbx)

    if action_exists:
        pass
    #    zabbix_action_obj = action.get_action_by_name(name)
    #    action_id = zabbix_action_obj['actionid']
    #    module.exit_json(changed=False, result="Action already exists: %s" %action_id)
    else:
        action_id = action.add_action(
                name=name,
                event_source=event_source,
                esc_period=esc_period,
                status=status,
                operations=ops.construct_the_data(operations)
                )
        module.exit_json(changed=True, result="Action created: %s, ID: %s" %(name, action_id) )

if __name__ == '__main__':
    main()
