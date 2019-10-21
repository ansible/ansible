#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


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

version_added: "2.8"

description:
    - This module allows you to create, modify and delete Zabbix actions.

author:
    - Ruben Tsirunyan (@rubentsirunyan)
    - Ruben Harutyunov (@K-DOT)

requirements:
    - zabbix-api

options:
    name:
        description:
            - Name of the action
        required: true
    event_source:
        description:
            - Type of events that the action will handle.
        required: true
        choices: ['trigger', 'discovery', 'auto_registration', 'internal']
    state:
        description:
            - State of the action.
            - On C(present), it will create an action if it does not exist or update the action if the associated data is different.
            - On C(absent), it will remove the action if it exists.
        choices: ['present', 'absent']
        default: 'present'
    status:
        description:
            - Status of the action.
        choices: ['enabled', 'disabled']
        default: 'enabled'
    pause_in_maintenance:
        description:
            - Whether to pause escalation during maintenance periods or not.
            - Can be used when I(event_source=trigger).
        type: 'bool'
        default: true
    esc_period:
        description:
            - Default operation step duration. Must be greater than 60 seconds. Accepts seconds, time unit with suffix and user macro.
        required: true
    conditions:
        type: list
        description:
            - List of dictionaries of conditions to evaluate.
            - For more information about suboptions of this option please
              check out Zabbix API documentation U(https://www.zabbix.com/documentation/3.4/manual/api/reference/action/object#action_filter_condition)
        suboptions:
            type:
                description: Type (label) of the condition.
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
                    - When I(type) is set to C(discovery_status), the choices
                      are C(up), C(down), C(discovered), C(lost).
                    - When I(type) is set to C(discovery_object), the choices
                      are C(host), C(service).
                    - When I(type) is set to C(event_type), the choices
                      are C(item in not supported state), C(item in normal state),
                      C(LLD rule in not supported state),
                      C(LLD rule in normal state), C(trigger in unknown state), C(trigger in normal state).
                    - When I(type) is set to C(trigger_severity), the choices
                      are (case-insensitive) C(not classified), C(information), C(warning), C(average), C(high), C(disaster)
                      irrespective of user-visible names being changed in Zabbix. Defaults to C(not classified) if omitted.
                    - Besides the above options, this is usually either the name
                      of the object or a string to compare with.
            operator:
                description:
                    - Condition operator.
                    - When I(type) is set to C(time_period), the choices are C(in), C(not in).
                    - C(matches), C(does not match), C(Yes) and C(No) condition operators work only with >= Zabbix 4.0
                choices:
                    - '='
                    - '<>'
                    - 'like'
                    - 'not like'
                    - 'in'
                    - '>='
                    - '<='
                    - 'not in'
                    - 'matches'
                    - 'does not match'
                    - 'Yes'
                    - 'No'
            formulaid:
                description:
                    - Arbitrary unique ID that is used to reference the condition from a custom expression.
                    - Can only contain upper-case letters.
                    - Required for custom expression filters.
    eval_type:
        description:
            - Filter condition evaluation method.
            - Defaults to C(andor) if conditions are less then 2 or if
              I(formula) is not specified.
            - Defaults to C(custom_expression) when formula is specified.
        choices:
            - 'andor'
            - 'and'
            - 'or'
            - 'custom_expression'
    formula:
        description:
            - User-defined expression to be used for evaluating conditions of filters with a custom expression.
            - The expression must contain IDs that reference specific filter conditions by its formulaid.
            - The IDs used in the expression must exactly match the ones
              defined in the filter conditions. No condition can remain unused or omitted.
            - Required for custom expression filters.
            - Use sequential IDs that start at "A". If non-sequential IDs are used, Zabbix re-indexes them.
              This makes each module run notice the difference in IDs and update the action.
    default_message:
        description:
            - Problem message default text.
    default_subject:
        description:
            - Problem message default subject.
    recovery_default_message:
        description:
            - Recovery message text.
            - Works only with >= Zabbix 3.2
    recovery_default_subject:
        description:
            - Recovery message subject.
            - Works only with >= Zabbix 3.2
    acknowledge_default_message:
        description:
            - Update operation (known as "Acknowledge operation" before Zabbix 4.0) message text.
            - Works only with >= Zabbix 3.4
    acknowledge_default_subject:
        description:
            - Update operation (known as "Acknowledge operation" before Zabbix 4.0) message subject.
            - Works only with >= Zabbix 3.4
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
                    - Users (usernames or aliases) to send messages to.
            message:
                description:
                    - Operation message text.
                    - Will check the 'default message' and use the text from I(default_message) if this and I(default_subject) are not specified
            subject:
                description:
                    - Operation message subject.
                    - Will check the 'default message' and use the text from I(default_subject) if this and I(default_subject) are not specified
            media_type:
                description:
                    - Media type that will be used to send the message.
                    - Set to C(all) for all media types
                default: 'all'
            operation_condition:
                type: 'str'
                description:
                    - The action operation condition object defines a condition that must be met to perform the current operation.
                choices:
                    - acknowledged
                    - not_acknowledged
            host_groups:
                type: list
                description:
                    - List of host groups host should be added to.
                    - Required when I(type=add_to_host_group) or I(type=remove_from_host_group).
            templates:
                type: list
                description:
                    - List of templates host should be linked to.
                    - Required when I(type=link_to_template) or I(type=unlink_from_template).
            inventory:
                description:
                    - Host inventory mode.
                    - Required when I(type=set_host_inventory_mode).
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
                    - Required when I(type=remote_command) and I(command_type=custom_script).
                choices:
                    - agent
                    - server
                    - proxy
            run_on_groups:
                description:
                    - Host groups to run remote commands on.
                    - Required when I(type=remote_command) if I(run_on_hosts) is not set.
            run_on_hosts:
                description:
                    - Hosts to run remote commands on.
                    - Required when I(type=remote_command) if I(run_on_groups) is not set.
                    - If set to 0 the command will be run on the current host.
            ssh_auth_type:
                description:
                    - Authentication method used for SSH commands.
                    - Required when I(type=remote_command) and I(command_type=ssh).
                choices:
                    - password
                    - public_key
            ssh_privatekey_file:
                description:
                    - Name of the private key file used for SSH commands with public key authentication.
                    - Required when I(type=remote_command) and I(command_type=ssh).
            ssh_publickey_file:
                description:
                    - Name of the public key file used for SSH commands with public key authentication.
                    - Required when I(type=remote_command) and I(command_type=ssh).
            username:
                description:
                    - User name used for authentication.
                    - Required when I(type=remote_command) and I(command_type in [ssh, telnet]).
            password:
                description:
                    - Password used for authentication.
                    - Required when I(type=remote_command) and I(command_type in [ssh, telnet]).
            port:
                description:
                    - Port number used for authentication.
                    - Required when I(type=remote_command) and I(command_type in [ssh, telnet]).
            script_name:
                description:
                    - The name of script used for global script commands.
                    - Required when I(type=remote_command) and I(command_type=global_script).
    recovery_operations:
        type: list
        description:
            - List of recovery operations.
            - C(Suboptions) are the same as for I(operations).
            - Works only with >= Zabbix 3.2
    acknowledge_operations:
        type: list
        description:
            - List of acknowledge operations.
            - C(Suboptions) are the same as for I(operations).
            - Works only with >= Zabbix 3.4

notes:
    - Only Zabbix >= 3.0 is supported.


extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = '''
# Trigger action with only one condition
- name: Deploy trigger action
  zabbix_action:
    server_url: "http://zabbix.example.com/zabbix/"
    login_user: Admin
    login_password: secret
    name: "Send alerts to Admin"
    event_source: 'trigger'
    state: present
    status: enabled
    esc_period: 60
    conditions:
      - type: 'trigger_severity'
        operator: '>='
        value: 'Information'
    operations:
      - type: send_message
        subject: "Something bad is happening"
        message: "Come on, guys do something"
        media_type: 'Email'
        send_to_users:
          - 'Admin'

# Trigger action with multiple conditions and operations
- name: Deploy trigger action
  zabbix_action:
    server_url: "http://zabbix.example.com/zabbix/"
    login_user: Admin
    login_password: secret
    name: "Send alerts to Admin"
    event_source: 'trigger'
    state: present
    status: enabled
    esc_period: 60
    conditions:
      - type: 'trigger_name'
        operator: 'like'
        value: 'Zabbix agent is unreachable'
        formulaid: A
      - type: 'trigger_severity'
        operator: '>='
        value: 'disaster'
        formulaid: B
    formula: A or B
    operations:
      - type: send_message
        media_type: 'Email'
        send_to_users:
          - 'Admin'
      - type: remote_command
        command: 'systemctl restart zabbix-agent'
        command_type: custom_script
        execute_on: server
        run_on_hosts:
          - 0

# Trigger action with recovery and acknowledge operations
- name: Deploy trigger action
  zabbix_action:
    server_url: "http://zabbix.example.com/zabbix/"
    login_user: Admin
    login_password: secret
    name: "Send alerts to Admin"
    event_source: 'trigger'
    state: present
    status: enabled
    esc_period: 60
    conditions:
      - type: 'trigger_severity'
        operator: '>='
        value: 'Information'
    operations:
      - type: send_message
        subject: "Something bad is happening"
        message: "Come on, guys do something"
        media_type: 'Email'
        send_to_users:
          - 'Admin'
    recovery_operations:
      - type: send_message
        subject: "Host is down"
        message: "Come on, guys do something"
        media_type: 'Email'
        send_to_users:
          - 'Admin'
    acknowledge_operations:
      - type: send_message
        media_type: 'Email'
        send_to_users:
          - 'Admin'
'''

RETURN = '''
msg:
    description: The result of the operation
    returned: success
    type: str
    sample: 'Action Deleted: Register webservers, ID: 0001'
'''


import atexit
import traceback

try:
    from zabbix_api import ZabbixAPI
    HAS_ZABBIX_API = True
except ImportError:
    ZBX_IMP_ERR = traceback.format_exc()
    HAS_ZABBIX_API = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


class Zapi(object):
    """
    A simple wrapper over the Zabbix API
    """
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    def check_if_action_exists(self, name):
        """Check if action exists.

        Args:
            name: Name of the action.

        Returns:
            The return value. True for success, False otherwise.

        """
        try:
            _action = self._zapi.action.get({
                "selectOperations": "extend",
                "selectRecoveryOperations": "extend",
                "selectAcknowledgeOperations": "extend",
                "selectFilter": "extend",
                'selectInventory': 'extend',
                'filter': {'name': [name]}
            })
            if len(_action) > 0:
                _action[0]['recovery_operations'] = _action[0].pop('recoveryOperations', [])
                _action[0]['acknowledge_operations'] = _action[0].pop('acknowledgeOperations', [])
            return _action
        except Exception as e:
            self._module.fail_json(msg="Failed to check if action '%s' exists: %s" % (name, e))

    def get_action_by_name(self, name):
        """Get action by name

        Args:
            name: Name of the action.

        Returns:
            dict: Zabbix action

        """
        try:
            action_list = self._zapi.action.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'name': [name]}
            })
            if len(action_list) < 1:
                self._module.fail_json(msg="Action not found: " % name)
            else:
                return action_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get ID of '%s': %s" % (name, e))

    def get_host_by_host_name(self, host_name):
        """Get host by host name

        Args:
            host_name: host name.

        Returns:
            host matching host name

        """
        try:
            host_list = self._zapi.host.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'host': [host_name]}
            })
            if len(host_list) < 1:
                self._module.fail_json(msg="Host not found: %s" % host_name)
            else:
                return host_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get host '%s': %s" % (host_name, e))

    def get_hostgroup_by_hostgroup_name(self, hostgroup_name):
        """Get host group by host group name

        Args:
            hostgroup_name: host group name.

        Returns:
            host group matching host group name

        """
        try:
            hostgroup_list = self._zapi.hostgroup.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'name': [hostgroup_name]}
            })
            if len(hostgroup_list) < 1:
                self._module.fail_json(msg="Host group not found: %s" % hostgroup_name)
            else:
                return hostgroup_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get host group '%s': %s" % (hostgroup_name, e))

    def get_template_by_template_name(self, template_name):
        """Get template by template name

        Args:
            template_name: template name.

        Returns:
            template matching template name

        """
        try:
            template_list = self._zapi.template.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'host': [template_name]}
            })
            if len(template_list) < 1:
                self._module.fail_json(msg="Template not found: %s" % template_name)
            else:
                return template_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get template '%s': %s" % (template_name, e))

    def get_trigger_by_trigger_name(self, trigger_name):
        """Get trigger by trigger name

        Args:
            trigger_name: trigger name.

        Returns:
            trigger matching trigger name

        """
        try:
            trigger_list = self._zapi.trigger.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'description': [trigger_name]}
            })
            if len(trigger_list) < 1:
                self._module.fail_json(msg="Trigger not found: %s" % trigger_name)
            else:
                return trigger_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get trigger '%s': %s" % (trigger_name, e))

    def get_discovery_rule_by_discovery_rule_name(self, discovery_rule_name):
        """Get discovery rule by discovery rule name

        Args:
            discovery_rule_name: discovery rule name.

        Returns:
            discovery rule matching discovery rule name

        """
        try:
            discovery_rule_list = self._zapi.drule.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'name': [discovery_rule_name]}
            })
            if len(discovery_rule_list) < 1:
                self._module.fail_json(msg="Discovery rule not found: %s" % discovery_rule_name)
            else:
                return discovery_rule_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get discovery rule '%s': %s" % (discovery_rule_name, e))

    def get_discovery_check_by_discovery_check_name(self, discovery_check_name):
        """Get discovery check  by discovery check name

        Args:
            discovery_check_name: discovery check name.

        Returns:
            discovery check matching discovery check name

        """
        try:
            discovery_check_list = self._zapi.dcheck.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'name': [discovery_check_name]}
            })
            if len(discovery_check_list) < 1:
                self._module.fail_json(msg="Discovery check not found: %s" % discovery_check_name)
            else:
                return discovery_check_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get discovery check '%s': %s" % (discovery_check_name, e))

    def get_proxy_by_proxy_name(self, proxy_name):
        """Get proxy by proxy name

        Args:
            proxy_name: proxy name.

        Returns:
            proxy matching proxy name

        """
        try:
            proxy_list = self._zapi.proxy.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'host': [proxy_name]}
            })
            if len(proxy_list) < 1:
                self._module.fail_json(msg="Proxy not found: %s" % proxy_name)
            else:
                return proxy_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get proxy '%s': %s" % (proxy_name, e))

    def get_mediatype_by_mediatype_name(self, mediatype_name):
        """Get mediatype by mediatype name

        Args:
            mediatype_name: mediatype name

        Returns:
            mediatype matching mediatype name

        """
        try:
            if str(mediatype_name).lower() == 'all':
                return '0'
            mediatype_list = self._zapi.mediatype.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'description': [mediatype_name]}
            })
            if len(mediatype_list) < 1:
                self._module.fail_json(msg="Media type not found: %s" % mediatype_name)
            else:
                return mediatype_list[0]['mediatypeid']
        except Exception as e:
            self._module.fail_json(msg="Failed to get mediatype '%s': %s" % (mediatype_name, e))

    def get_user_by_user_name(self, user_name):
        """Get user by user name

        Args:
            user_name: user name

        Returns:
            user matching user name

        """
        try:
            user_list = self._zapi.user.get({
                'output': 'extend',
                'selectInventory':
                'extend', 'filter': {'alias': [user_name]}
            })
            if len(user_list) < 1:
                self._module.fail_json(msg="User not found: %s" % user_name)
            else:
                return user_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get user '%s': %s" % (user_name, e))

    def get_usergroup_by_usergroup_name(self, usergroup_name):
        """Get usergroup by usergroup name

        Args:
            usergroup_name: usergroup name

        Returns:
            usergroup matching usergroup name

        """
        try:
            usergroup_list = self._zapi.usergroup.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'name': [usergroup_name]}
            })
            if len(usergroup_list) < 1:
                self._module.fail_json(msg="User group not found: %s" % usergroup_name)
            else:
                return usergroup_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get user group '%s': %s" % (usergroup_name, e))

    # get script by script name
    def get_script_by_script_name(self, script_name):
        """Get script by script name

        Args:
            script_name: script name

        Returns:
            script matching script name

        """
        try:
            if script_name is None:
                return {}
            script_list = self._zapi.script.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'name': [script_name]}
            })
            if len(script_list) < 1:
                self._module.fail_json(msg="Script not found: %s" % script_name)
            else:
                return script_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get script '%s': %s" % (script_name, e))


class Action(object):
    """
    Restructures the user defined action data to fit the Zabbix API requirements
    """
    def __init__(self, module, zbx, zapi_wrapper):
        self._module = module
        self._zapi = zbx
        self._zapi_wrapper = zapi_wrapper

    def _construct_parameters(self, **kwargs):
        """Construct parameters.

        Args:
            **kwargs: Arbitrary keyword parameters.

        Returns:
            dict: dictionary of specified parameters
        """

        _params = {
            'name': kwargs['name'],
            'eventsource': to_numeric_value([
                'trigger',
                'discovery',
                'auto_registration',
                'internal'], kwargs['event_source']),
            'esc_period': kwargs.get('esc_period'),
            'filter': kwargs['conditions'],
            'def_longdata': kwargs['default_message'],
            'def_shortdata': kwargs['default_subject'],
            'r_longdata': kwargs['recovery_default_message'],
            'r_shortdata': kwargs['recovery_default_subject'],
            'ack_longdata': kwargs['acknowledge_default_message'],
            'ack_shortdata': kwargs['acknowledge_default_subject'],
            'operations': kwargs['operations'],
            'recovery_operations': kwargs.get('recovery_operations'),
            'acknowledge_operations': kwargs.get('acknowledge_operations'),
            'status': to_numeric_value([
                'enabled',
                'disabled'], kwargs['status'])
        }
        if kwargs['event_source'] == 'trigger':
            if float(self._zapi.api_version().rsplit('.', 1)[0]) >= 4.0:
                _params['pause_suppressed'] = '1' if kwargs['pause_in_maintenance'] else '0'
            else:
                _params['maintenance_mode'] = '1' if kwargs['pause_in_maintenance'] else '0'

        return _params

    def check_difference(self, **kwargs):
        """Check difference between action and user specified parameters.

        Args:
            **kwargs: Arbitrary keyword parameters.

        Returns:
            dict: dictionary of differences
        """
        existing_action = convert_unicode_to_str(self._zapi_wrapper.check_if_action_exists(kwargs['name'])[0])
        parameters = convert_unicode_to_str(self._construct_parameters(**kwargs))
        change_parameters = {}
        _diff = cleanup_data(compare_dictionaries(parameters, existing_action, change_parameters))
        return _diff

    def update_action(self, **kwargs):
        """Update action.

        Args:
            **kwargs: Arbitrary keyword parameters.

        Returns:
            action: updated action
        """
        try:
            if self._module.check_mode:
                self._module.exit_json(msg="Action would be updated if check mode was not specified: %s" % kwargs, changed=True)
            kwargs['actionid'] = kwargs.pop('action_id')
            return self._zapi.action.update(kwargs)
        except Exception as e:
            self._module.fail_json(msg="Failed to update action '%s': %s" % (kwargs['actionid'], e))

    def add_action(self, **kwargs):
        """Add action.

        Args:
            **kwargs: Arbitrary keyword parameters.

        Returns:
            action: added action
        """
        try:
            if self._module.check_mode:
                self._module.exit_json(msg="Action would be added if check mode was not specified", changed=True)
            parameters = self._construct_parameters(**kwargs)
            action_list = self._zapi.action.create(parameters)
            return action_list['actionids'][0]
        except Exception as e:
            self._module.fail_json(msg="Failed to create action '%s': %s" % (kwargs['name'], e))

    def delete_action(self, action_id):
        """Delete action.

        Args:
            action_id: Action id

        Returns:
            action: deleted action
        """
        try:
            if self._module.check_mode:
                self._module.exit_json(msg="Action would be deleted if check mode was not specified", changed=True)
            return self._zapi.action.delete([action_id])
        except Exception as e:
            self._module.fail_json(msg="Failed to delete action '%s': %s" % (action_id, e))


class Operations(object):
    """
    Restructures the user defined operation data to fit the Zabbix API requirements
    """
    def __init__(self, module, zbx, zapi_wrapper):
        self._module = module
        # self._zapi = zbx
        self._zapi_wrapper = zapi_wrapper

    def _construct_operationtype(self, operation):
        """Construct operation type.

        Args:
            operation: operation to construct

        Returns:
            str: constructed operation
        """
        try:
            return to_numeric_value([
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
                "set_host_inventory_mode"], operation['type']
            )
        except Exception as e:
            self._module.fail_json(msg="Unsupported value '%s' for operation type." % operation['type'])

    def _construct_opmessage(self, operation):
        """Construct operation message.

        Args:
            operation: operation to construct the message

        Returns:
            dict: constructed operation message
        """
        try:
            return {
                'default_msg': '0' if operation.get('message') is not None or operation.get('subject')is not None else '1',
                'mediatypeid': self._zapi_wrapper.get_mediatype_by_mediatype_name(
                    operation.get('media_type')
                ) if operation.get('media_type') is not None else '0',
                'message': operation.get('message'),
                'subject': operation.get('subject'),
            }
        except Exception as e:
            self._module.fail_json(msg="Failed to construct operation message. The error was: %s" % e)

    def _construct_opmessage_usr(self, operation):
        """Construct operation message user.

        Args:
            operation: operation to construct the message user

        Returns:
            list: constructed operation message user or None if operation not found
        """
        if operation.get('send_to_users') is None:
            return None
        return [{
            'userid': self._zapi_wrapper.get_user_by_user_name(_user)['userid']
        } for _user in operation.get('send_to_users')]

    def _construct_opmessage_grp(self, operation):
        """Construct operation message group.

        Args:
            operation: operation to construct the message group

        Returns:
            list: constructed operation message group or None if operation not found
        """
        if operation.get('send_to_groups') is None:
            return None
        return [{
            'usrgrpid': self._zapi_wrapper.get_usergroup_by_usergroup_name(_group)['usrgrpid']
        } for _group in operation.get('send_to_groups')]

    def _construct_opcommand(self, operation):
        """Construct operation command.

        Args:
            operation: operation to construct command

        Returns:
            list: constructed operation command
        """
        try:
            return {
                'type': to_numeric_value([
                    'custom_script',
                    'ipmi',
                    'ssh',
                    'telnet',
                    'global_script'], operation.get('command_type', 'custom_script')),
                'command': operation.get('command'),
                'execute_on': to_numeric_value([
                    'agent',
                    'server',
                    'proxy'], operation.get('execute_on', 'server')),
                'scriptid': self._zapi_wrapper.get_script_by_script_name(
                    operation.get('script_name')
                ).get('scriptid'),
                'authtype': to_numeric_value([
                    'password',
                    'private_key'
                ], operation.get('ssh_auth_type', 'password')),
                'privatekey': operation.get('ssh_privatekey_file'),
                'publickey': operation.get('ssh_publickey_file'),
                'username': operation.get('username'),
                'password': operation.get('password'),
                'port': operation.get('port')
            }
        except Exception as e:
            self._module.fail_json(msg="Failed to construct operation command. The error was: %s" % e)

    def _construct_opcommand_hst(self, operation):
        """Construct operation command host.

        Args:
            operation: operation to construct command host

        Returns:
            list: constructed operation command host
        """
        if operation.get('run_on_hosts') is None:
            return None
        return [{
            'hostid': self._zapi_wrapper.get_host_by_host_name(_host)['hostid']
        } if str(_host) != '0' else {'hostid': '0'} for _host in operation.get('run_on_hosts')]

    def _construct_opcommand_grp(self, operation):
        """Construct operation command group.

        Args:
            operation: operation to construct command group

        Returns:
            list: constructed operation command group
        """
        if operation.get('run_on_groups') is None:
            return None
        return [{
            'groupid': self._zapi_wrapper.get_hostgroup_by_hostgroup_name(_group)['hostid']
        } for _group in operation.get('run_on_groups')]

    def _construct_opgroup(self, operation):
        """Construct operation group.

        Args:
            operation: operation to construct group

        Returns:
            list: constructed operation group
        """
        return [{
            'groupid': self._zapi_wrapper.get_hostgroup_by_hostgroup_name(_group)['groupid']
        } for _group in operation.get('host_groups', [])]

    def _construct_optemplate(self, operation):
        """Construct operation template.

        Args:
            operation: operation to construct template

        Returns:
            list: constructed operation template
        """
        return [{
            'templateid': self._zapi_wrapper.get_template_by_template_name(_template)['templateid']
        } for _template in operation.get('templates', [])]

    def _construct_opinventory(self, operation):
        """Construct operation inventory.

        Args:
            operation: operation to construct inventory

        Returns:
            dict: constructed operation inventory
        """
        return {'inventory_mode': operation.get('inventory')}

    def _construct_opconditions(self, operation):
        """Construct operation conditions.

        Args:
            operation: operation to construct the conditions

        Returns:
            list: constructed operation conditions
        """
        _opcond = operation.get('operation_condition')
        if _opcond is not None:
            if _opcond == 'acknowledged':
                _value = '1'
            elif _opcond == 'not_acknowledged':
                _value = '0'
            return [{
                'conditiontype': '14',
                'operator': '0',
                'value': _value
            }]
        return []

    def construct_the_data(self, operations):
        """Construct the operation data using helper methods.

        Args:
            operation: operation to construct

        Returns:
            list: constructed operation data
        """
        constructed_data = []
        for op in operations:
            operation_type = self._construct_operationtype(op)
            constructed_operation = {
                'operationtype': operation_type,
                'esc_period': op.get('esc_period'),
                'esc_step_from': op.get('esc_step_from'),
                'esc_step_to': op.get('esc_step_to')
            }
            # Send Message type
            if constructed_operation['operationtype'] == '0':
                constructed_operation['opmessage'] = self._construct_opmessage(op)
                constructed_operation['opmessage_usr'] = self._construct_opmessage_usr(op)
                constructed_operation['opmessage_grp'] = self._construct_opmessage_grp(op)
                constructed_operation['opconditions'] = self._construct_opconditions(op)

            # Send Command type
            if constructed_operation['operationtype'] == '1':
                constructed_operation['opcommand'] = self._construct_opcommand(op)
                constructed_operation['opcommand_hst'] = self._construct_opcommand_hst(op)
                constructed_operation['opcommand_grp'] = self._construct_opcommand_grp(op)
                constructed_operation['opconditions'] = self._construct_opconditions(op)

            # Add to/Remove from host group
            if constructed_operation['operationtype'] in ('4', '5'):
                constructed_operation['opgroup'] = self._construct_opgroup(op)

            # Link/Unlink template
            if constructed_operation['operationtype'] in ('6', '7'):
                constructed_operation['optemplate'] = self._construct_optemplate(op)

            # Set inventory mode
            if constructed_operation['operationtype'] == '10':
                constructed_operation['opinventory'] = self._construct_opinventory(op)

            constructed_data.append(constructed_operation)

        return cleanup_data(constructed_data)


class RecoveryOperations(Operations):
    """
    Restructures the user defined recovery operations data to fit the Zabbix API requirements
    """
    def _construct_operationtype(self, operation):
        """Construct operation type.

        Args:
            operation: operation to construct type

        Returns:
            str: constructed operation type
        """
        try:
            return to_numeric_value([
                "send_message",
                "remote_command",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                "notify_all_involved"], operation['type']
            )
        except Exception as e:
            self._module.fail_json(msg="Unsupported value '%s' for recovery operation type." % operation['type'])

    def construct_the_data(self, operations):
        """Construct the recovery operations data using helper methods.

        Args:
            operation: operation to construct

        Returns:
            list: constructed recovery operations data
        """
        constructed_data = []
        for op in operations:
            operation_type = self._construct_operationtype(op)
            constructed_operation = {
                'operationtype': operation_type,
            }

            # Send Message type
            if constructed_operation['operationtype'] in ('0', '11'):
                constructed_operation['opmessage'] = self._construct_opmessage(op)
                constructed_operation['opmessage_usr'] = self._construct_opmessage_usr(op)
                constructed_operation['opmessage_grp'] = self._construct_opmessage_grp(op)

            # Send Command type
            if constructed_operation['operationtype'] == '1':
                constructed_operation['opcommand'] = self._construct_opcommand(op)
                constructed_operation['opcommand_hst'] = self._construct_opcommand_hst(op)
                constructed_operation['opcommand_grp'] = self._construct_opcommand_grp(op)

            constructed_data.append(constructed_operation)

        return cleanup_data(constructed_data)


class AcknowledgeOperations(Operations):
    """
    Restructures the user defined acknowledge operations data to fit the Zabbix API requirements
    """
    def _construct_operationtype(self, operation):
        """Construct operation type.

        Args:
            operation: operation to construct type

        Returns:
            str: constructed operation type
        """
        try:
            return to_numeric_value([
                "send_message",
                "remote_command",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                "notify_all_involved"], operation['type']
            )
        except Exception as e:
            self._module.fail_json(msg="Unsupported value '%s' for acknowledge operation type." % operation['type'])

    def construct_the_data(self, operations):
        """Construct the acknowledge operations data using helper methods.

        Args:
            operation: operation to construct

        Returns:
            list: constructed acknowledge operations data
        """
        constructed_data = []
        for op in operations:
            operation_type = self._construct_operationtype(op)
            constructed_operation = {
                'operationtype': operation_type,
            }

            # Send Message type
            if constructed_operation['operationtype'] in ('0', '11'):
                constructed_operation['opmessage'] = self._construct_opmessage(op)
                constructed_operation['opmessage_usr'] = self._construct_opmessage_usr(op)
                constructed_operation['opmessage_grp'] = self._construct_opmessage_grp(op)

            # Send Command type
            if constructed_operation['operationtype'] == '1':
                constructed_operation['opcommand'] = self._construct_opcommand(op)
                constructed_operation['opcommand_hst'] = self._construct_opcommand_hst(op)
                constructed_operation['opcommand_grp'] = self._construct_opcommand_grp(op)

            constructed_data.append(constructed_operation)

        return cleanup_data(constructed_data)


class Filter(object):
    """
    Restructures the user defined filter conditions to fit the Zabbix API requirements
    """
    def __init__(self, module, zbx, zapi_wrapper):
        self._module = module
        self._zapi = zbx
        self._zapi_wrapper = zapi_wrapper

    def _construct_evaltype(self, _eval_type, _formula, _conditions):
        """Construct the eval type

        Args:
            _formula: zabbix condition evaluation formula
            _conditions: list of conditions to check

        Returns:
            dict: constructed acknowledge operations data
        """
        if len(_conditions) <= 1:
            return {
                'evaltype': '0',
                'formula': None
            }
        if _eval_type == 'andor':
            return {
                'evaltype': '0',
                'formula': None
            }
        if _eval_type == 'and':
            return {
                'evaltype': '1',
                'formula': None
            }
        if _eval_type == 'or':
            return {
                'evaltype': '2',
                'formula': None
            }
        if _eval_type == 'custom_expression':
            if _formula is not None:
                return {
                    'evaltype': '3',
                    'formula': _formula
                }
            else:
                self._module.fail_json(msg="'formula' is required when 'eval_type' is set to 'custom_expression'")
        if _formula is not None:
            return {
                'evaltype': '3',
                'formula': _formula
            }
        return {
            'evaltype': '0',
            'formula': None
        }

    def _construct_conditiontype(self, _condition):
        """Construct the condition type

        Args:
            _condition: condition to check

        Returns:
            str: constructed condition type data
        """
        try:
            return to_numeric_value([
                "host_group",
                "host",
                "trigger",
                "trigger_name",
                "trigger_severity",
                "trigger_value",
                "time_period",
                "host_ip",
                "discovered_service_type",
                "discovered_service_port",
                "discovery_status",
                "uptime_or_downtime_duration",
                "received_value",
                "host_template",
                None,
                "application",
                "maintenance_status",
                None,
                "discovery_rule",
                "discovery_check",
                "proxy",
                "discovery_object",
                "host_name",
                "event_type",
                "host_metadata",
                "event_tag",
                "event_tag_value"], _condition['type']
            )
        except Exception as e:
            self._module.fail_json(msg="Unsupported value '%s' for condition type." % _condition['type'])

    def _construct_operator(self, _condition):
        """Construct operator

        Args:
            _condition: condition to construct

        Returns:
            str: constructed operator
        """
        try:
            return to_numeric_value([
                "=",
                "<>",
                "like",
                "not like",
                "in",
                ">=",
                "<=",
                "not in",
                "matches",
                "does not match",
                "Yes",
                "No"], _condition['operator']
            )
        except Exception as e:
            self._module.fail_json(msg="Unsupported value '%s' for operator." % _condition['operator'])

    def _construct_value(self, conditiontype, value):
        """Construct operator

        Args:
            conditiontype: type of condition to construct
            value: value to construct

        Returns:
            str: constructed value
        """
        try:
            # Host group
            if conditiontype == '0':
                return self._zapi_wrapper.get_hostgroup_by_hostgroup_name(value)['groupid']
            # Host
            if conditiontype == '1':
                return self._zapi_wrapper.get_host_by_host_name(value)['hostid']
            # Trigger
            if conditiontype == '2':
                return self._zapi_wrapper.get_trigger_by_trigger_name(value)['triggerid']
            # Trigger name: return as is
            # Trigger severity
            if conditiontype == '4':
                return to_numeric_value([
                    "not classified",
                    "information",
                    "warning",
                    "average",
                    "high",
                    "disaster"], value or "not classified"
                )

            # Trigger value
            if conditiontype == '5':
                return to_numeric_value([
                    "ok",
                    "problem"], value or "ok"
                )
            # Time period: return as is
            # Host IP: return as is
            # Discovered service type
            if conditiontype == '8':
                return to_numeric_value([
                    "SSH",
                    "LDAP",
                    "SMTP",
                    "FTP",
                    "HTTP",
                    "POP",
                    "NNTP",
                    "IMAP",
                    "TCP",
                    "Zabbix agent",
                    "SNMPv1 agent",
                    "SNMPv2 agent",
                    "ICMP ping",
                    "SNMPv3 agent",
                    "HTTPS",
                    "Telnet"], value
                )
            # Discovered service port: return as is
            # Discovery status
            if conditiontype == '10':
                return to_numeric_value([
                    "up",
                    "down",
                    "discovered",
                    "lost"], value
                )
            if conditiontype == '13':
                return self._zapi_wrapper.get_template_by_template_name(value)['templateid']
            if conditiontype == '18':
                return self._zapi_wrapper.get_discovery_rule_by_discovery_rule_name(value)['druleid']
            if conditiontype == '19':
                return self._zapi_wrapper.get_discovery_check_by_discovery_check_name(value)['dcheckid']
            if conditiontype == '20':
                return self._zapi_wrapper.get_proxy_by_proxy_name(value)['proxyid']
            if conditiontype == '21':
                return to_numeric_value([
                    "pchldrfor0",
                    "host",
                    "service"], value
                )
            if conditiontype == '23':
                return to_numeric_value([
                    "item in not supported state",
                    "item in normal state",
                    "LLD rule in not supported state",
                    "LLD rule in normal state",
                    "trigger in unknown state",
                    "trigger in normal state"], value
                )
            return value
        except Exception as e:
            self._module.fail_json(
                msg="""Unsupported value '%s' for specified condition type.
                       Check out Zabbix API documentation for supported values for
                       condition type '%s' at
                       https://www.zabbix.com/documentation/3.4/manual/api/reference/action/object#action_filter_condition""" % (value, conditiontype)
            )

    def construct_the_data(self, _eval_type, _formula, _conditions):
        """Construct the user defined filter conditions to fit the Zabbix API
        requirements operations data using helper methods.

        Args:
            _formula:  zabbix condition evaluation formula
            _conditions: conditions to construct

        Returns:
            dict: user defined filter conditions
        """
        if _conditions is None:
            return None
        constructed_data = {}
        constructed_data['conditions'] = []
        for cond in _conditions:
            condition_type = self._construct_conditiontype(cond)
            constructed_data['conditions'].append({
                "conditiontype": condition_type,
                "value": self._construct_value(condition_type, cond.get("value")),
                "value2": cond.get("value2"),
                "formulaid": cond.get("formulaid"),
                "operator": self._construct_operator(cond)
            })
        _constructed_evaltype = self._construct_evaltype(
            _eval_type,
            _formula,
            constructed_data['conditions']
        )
        constructed_data['evaltype'] = _constructed_evaltype['evaltype']
        constructed_data['formula'] = _constructed_evaltype['formula']
        return cleanup_data(constructed_data)


def convert_unicode_to_str(data):
    """Converts unicode objects to strings in dictionary
    args:
        data: unicode object

    Returns:
        dict: strings in dictionary
    """
    if isinstance(data, dict):
        return dict(map(convert_unicode_to_str, data.items()))
    elif isinstance(data, (list, tuple, set)):
        return type(data)(map(convert_unicode_to_str, data))
    elif data is None:
        return data
    else:
        return str(data)


def to_numeric_value(strs, value):
    """Converts string values to integers
    Args:
        value: string value

    Returns:
        int: converted integer
    """
    strs = [s.lower() if isinstance(s, str) else s for s in strs]
    value = value.lower()
    tmp_dict = dict(zip(strs, list(range(len(strs)))))
    return str(tmp_dict[value])


def compare_lists(l1, l2, diff_dict):
    """
    Compares l1 and l2 lists and adds the items that are different
    to the diff_dict dictionary.
    Used in recursion with compare_dictionaries() function.
    Args:
        l1: first list to compare
        l2: second list to compare
        diff_dict: dictionary to store the difference

    Returns:
        dict: items that are different
    """
    if len(l1) != len(l2):
        diff_dict.append(l1)
        return diff_dict
    for i, item in enumerate(l1):
        if isinstance(item, dict):
            diff_dict.insert(i, {})
            diff_dict[i] = compare_dictionaries(item, l2[i], diff_dict[i])
        else:
            if item != l2[i]:
                diff_dict.append(item)
    while {} in diff_dict:
        diff_dict.remove({})
    return diff_dict


def compare_dictionaries(d1, d2, diff_dict):
    """
    Compares d1 and d2 dictionaries and adds the items that are different
    to the diff_dict dictionary.
    Used in recursion with compare_lists() function.
    Args:
        d1: first dictionary to compare
        d2: second dictionary to compare
        diff_dict: dictionary to store the difference

    Returns:
        dict: items that are different
    """
    for k, v in d1.items():
        if k not in d2:
            diff_dict[k] = v
            continue
        if isinstance(v, dict):
            diff_dict[k] = {}
            compare_dictionaries(v, d2[k], diff_dict[k])
            if diff_dict[k] == {}:
                del diff_dict[k]
            else:
                diff_dict[k] = v
        elif isinstance(v, list):
            diff_dict[k] = []
            compare_lists(v, d2[k], diff_dict[k])
            if diff_dict[k] == []:
                del diff_dict[k]
            else:
                diff_dict[k] = v
        else:
            if v != d2[k]:
                diff_dict[k] = v
    return diff_dict


def cleanup_data(obj):
    """Removes the None values from the object and returns the object
    Args:
        obj: object to cleanup

    Returns:
       object: cleaned object
    """
    if isinstance(obj, (list, tuple, set)):
        return type(obj)(cleanup_data(x) for x in obj if x is not None)
    elif isinstance(obj, dict):
        return type(obj)((cleanup_data(k), cleanup_data(v))
                         for k, v in obj.items() if k is not None and v is not None)
    else:
        return obj


def main():
    """Main ansible module function
    """

    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            esc_period=dict(type='int', required=True),
            timeout=dict(type='int', default=10),
            name=dict(type='str', required=True),
            event_source=dict(type='str', required=True, choices=['trigger', 'discovery', 'auto_registration', 'internal']),
            state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
            status=dict(type='str', required=False, default='enabled', choices=['enabled', 'disabled']),
            pause_in_maintenance=dict(type='bool', required=False, default=True),
            default_message=dict(type='str', required=False, default=''),
            default_subject=dict(type='str', required=False, default=''),
            recovery_default_message=dict(type='str', required=False, default=''),
            recovery_default_subject=dict(type='str', required=False, default=''),
            acknowledge_default_message=dict(type='str', required=False, default=''),
            acknowledge_default_subject=dict(type='str', required=False, default=''),
            conditions=dict(
                type='list',
                required=False,
                default=[],
                elements='dict',
                options=dict(
                    formulaid=dict(type='str', required=False),
                    operator=dict(type='str', required=True),
                    type=dict(type='str', required=True),
                    value=dict(type='str', required=True),
                    value2=dict(type='str', required=False)
                )
            ),
            formula=dict(type='str', required=False, default=None),
            eval_type=dict(type='str', required=False, default=None, choices=['andor', 'and', 'or', 'custom_expression']),
            operations=dict(
                type='list',
                required=False,
                default=[],
                elements='dict',
                options=dict(
                    type=dict(
                        type='str',
                        required=True,
                        choices=[
                            'send_message',
                            'remote_command',
                            'add_host',
                            'remove_host',
                            'add_to_host_group',
                            'remove_from_host_group',
                            'link_to_template',
                            'unlink_from_template',
                            'enable_host',
                            'disable_host',
                            'set_host_inventory_mode',
                        ]
                    ),
                    esc_period=dict(type='int', required=False),
                    esc_step_from=dict(type='int', required=False, default=1),
                    esc_step_to=dict(type='int', required=False, default=1),
                    operation_condition=dict(
                        type='str',
                        required=False,
                        default=None,
                        choices=['acknowledged', 'not_acknowledged']
                    ),
                    # when type is remote_command
                    command_type=dict(
                        type='str',
                        required=False,
                        choices=[
                            'custom_script',
                            'ipmi',
                            'ssh',
                            'telnet',
                            'global_script'
                        ]
                    ),
                    command=dict(type='str', required=False),
                    execute_on=dict(
                        type='str',
                        required=False,
                        choices=['agent', 'server', 'proxy']
                    ),
                    password=dict(type='str', required=False),
                    port=dict(type='int', required=False),
                    run_on_groups=dict(type='list', required=False),
                    run_on_hosts=dict(type='list', required=False),
                    script_name=dict(type='str', required=False),
                    ssh_auth_type=dict(
                        type='str',
                        required=False,
                        default='password',
                        choices=['password', 'public_key']
                    ),
                    ssh_privatekey_file=dict(type='str', required=False),
                    ssh_publickey_file=dict(type='str', required=False),
                    username=dict(type='str', required=False),
                    # when type is send_message
                    media_type=dict(type='str', required=False),
                    subject=dict(type='str', required=False),
                    message=dict(type='str', required=False),
                    send_to_groups=dict(type='list', required=False),
                    send_to_users=dict(type='list', required=False),
                    # when type is add_to_host_group or remove_from_host_group
                    host_groups=dict(type='list', required=False),
                    # when type is set_host_inventory_mode
                    inventory=dict(type='str', required=False),
                    # when type is link_to_template or unlink_from_template
                    templates=dict(type='list', required=False)
                ),
                required_if=[
                    ['type', 'remote_command', ['command_type']],
                    ['type', 'remote_command', ['run_on_groups', 'run_on_hosts'], True],
                    ['command_type', 'custom_script', [
                        'command',
                        'execute_on'
                    ]],
                    ['command_type', 'ipmi', ['command']],
                    ['command_type', 'ssh', [
                        'command',
                        'password',
                        'username',
                        'port',
                        'ssh_auth_type',
                        'ssh_privatekey_file',
                        'ssh_publickey_file'
                    ]],
                    ['command_type', 'telnet', [
                        'command',
                        'password',
                        'username',
                        'port'
                    ]],
                    ['command_type', 'global_script', ['script_name']],
                    ['type', 'add_to_host_group', ['host_groups']],
                    ['type', 'remove_from_host_group', ['host_groups']],
                    ['type', 'link_to_template', ['templates']],
                    ['type', 'unlink_from_template', ['templates']],
                    ['type', 'set_host_inventory_mode', ['inventory']],
                    ['type', 'send_message', ['send_to_users', 'send_to_groups'], True]
                ]
            ),
            recovery_operations=dict(
                type='list',
                required=False,
                default=[],
                elements='dict',
                options=dict(
                    type=dict(
                        type='str',
                        required=True,
                        choices=[
                            'send_message',
                            'remote_command',
                            'notify_all_involved'
                        ]
                    ),
                    # when type is remote_command
                    command_type=dict(
                        type='str',
                        required=False,
                        choices=[
                            'custom_script',
                            'ipmi',
                            'ssh',
                            'telnet',
                            'global_script'
                        ]
                    ),
                    command=dict(type='str', required=False),
                    execute_on=dict(
                        type='str',
                        required=False,
                        choices=['agent', 'server', 'proxy']
                    ),
                    password=dict(type='str', required=False),
                    port=dict(type='int', required=False),
                    run_on_groups=dict(type='list', required=False),
                    run_on_hosts=dict(type='list', required=False),
                    script_name=dict(type='str', required=False),
                    ssh_auth_type=dict(
                        type='str',
                        required=False,
                        default='password',
                        choices=['password', 'public_key']
                    ),
                    ssh_privatekey_file=dict(type='str', required=False),
                    ssh_publickey_file=dict(type='str', required=False),
                    username=dict(type='str', required=False),
                    # when type is send_message
                    media_type=dict(type='str', required=False),
                    subject=dict(type='str', required=False),
                    message=dict(type='str', required=False),
                    send_to_groups=dict(type='list', required=False),
                    send_to_users=dict(type='list', required=False),
                ),
                required_if=[
                    ['type', 'remote_command', ['command_type']],
                    ['type', 'remote_command', [
                        'run_on_groups',
                        'run_on_hosts'
                    ], True],
                    ['command_type', 'custom_script', [
                        'command',
                        'execute_on'
                    ]],
                    ['command_type', 'ipmi', ['command']],
                    ['command_type', 'ssh', [
                        'command',
                        'password',
                        'username',
                        'port',
                        'ssh_auth_type',
                        'ssh_privatekey_file',
                        'ssh_publickey_file'
                    ]],
                    ['command_type', 'telnet', [
                        'command',
                        'password',
                        'username',
                        'port'
                    ]],
                    ['command_type', 'global_script', ['script_name']],
                    ['type', 'send_message', ['send_to_users', 'send_to_groups'], True]
                ]
            ),
            acknowledge_operations=dict(
                type='list',
                required=False,
                default=[],
                elements='dict',
                options=dict(
                    type=dict(
                        type='str',
                        required=True,
                        choices=[
                            'send_message',
                            'remote_command',
                            'notify_all_involved'
                        ]
                    ),
                    # when type is remote_command
                    command_type=dict(
                        type='str',
                        required=False,
                        choices=[
                            'custom_script',
                            'ipmi',
                            'ssh',
                            'telnet',
                            'global_script'
                        ]
                    ),
                    command=dict(type='str', required=False),
                    execute_on=dict(
                        type='str',
                        required=False,
                        choices=['agent', 'server', 'proxy']
                    ),
                    password=dict(type='str', required=False),
                    port=dict(type='int', required=False),
                    run_on_groups=dict(type='list', required=False),
                    run_on_hosts=dict(type='list', required=False),
                    script_name=dict(type='str', required=False),
                    ssh_auth_type=dict(
                        type='str',
                        required=False,
                        default='password',
                        choices=['password', 'public_key']
                    ),
                    ssh_privatekey_file=dict(type='str', required=False),
                    ssh_publickey_file=dict(type='str', required=False),
                    username=dict(type='str', required=False),
                    # when type is send_message
                    media_type=dict(type='str', required=False),
                    subject=dict(type='str', required=False),
                    message=dict(type='str', required=False),
                    send_to_groups=dict(type='list', required=False),
                    send_to_users=dict(type='list', required=False),
                ),
                required_if=[
                    ['type', 'remote_command', ['command_type']],
                    ['type', 'remote_command', [
                        'run_on_groups',
                        'run_on_hosts'
                    ], True],
                    ['command_type', 'custom_script', [
                        'command',
                        'execute_on'
                    ]],
                    ['command_type', 'ipmi', ['command']],
                    ['command_type', 'ssh', [
                        'command',
                        'password',
                        'username',
                        'port',
                        'ssh_auth_type',
                        'ssh_privatekey_file',
                        'ssh_publickey_file'
                    ]],
                    ['command_type', 'telnet', [
                        'command',
                        'password',
                        'username',
                        'port'
                    ]],
                    ['command_type', 'global_script', ['script_name']],
                    ['type', 'send_message', ['send_to_users', 'send_to_groups'], True]
                ]
            )
        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg=missing_required_lib('zabbix-api', url='https://pypi.org/project/zabbix-api/'), exception=ZBX_IMP_ERR)

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    timeout = module.params['timeout']
    name = module.params['name']
    esc_period = module.params['esc_period']
    event_source = module.params['event_source']
    state = module.params['state']
    status = module.params['status']
    pause_in_maintenance = module.params['pause_in_maintenance']
    default_message = module.params['default_message']
    default_subject = module.params['default_subject']
    recovery_default_message = module.params['recovery_default_message']
    recovery_default_subject = module.params['recovery_default_subject']
    acknowledge_default_message = module.params['acknowledge_default_message']
    acknowledge_default_subject = module.params['acknowledge_default_subject']
    conditions = module.params['conditions']
    formula = module.params['formula']
    eval_type = module.params['eval_type']
    operations = module.params['operations']
    recovery_operations = module.params['recovery_operations']
    acknowledge_operations = module.params['acknowledge_operations']

    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user,
                        passwd=http_login_password, validate_certs=validate_certs)
        zbx.login(login_user, login_password)
        atexit.register(zbx.logout)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    zapi_wrapper = Zapi(module, zbx)

    action = Action(module, zbx, zapi_wrapper)

    action_exists = zapi_wrapper.check_if_action_exists(name)
    ops = Operations(module, zbx, zapi_wrapper)
    recovery_ops = RecoveryOperations(module, zbx, zapi_wrapper)
    acknowledge_ops = AcknowledgeOperations(module, zbx, zapi_wrapper)
    fltr = Filter(module, zbx, zapi_wrapper)

    if action_exists:
        action_id = zapi_wrapper.get_action_by_name(name)['actionid']
        if state == "absent":
            result = action.delete_action(action_id)
            module.exit_json(changed=True, msg="Action Deleted: %s, ID: %s" % (name, result))
        else:
            difference = action.check_difference(
                action_id=action_id,
                name=name,
                event_source=event_source,
                esc_period=esc_period,
                status=status,
                pause_in_maintenance=pause_in_maintenance,
                default_message=default_message,
                default_subject=default_subject,
                recovery_default_message=recovery_default_message,
                recovery_default_subject=recovery_default_subject,
                acknowledge_default_message=acknowledge_default_message,
                acknowledge_default_subject=acknowledge_default_subject,
                operations=ops.construct_the_data(operations),
                recovery_operations=recovery_ops.construct_the_data(recovery_operations),
                acknowledge_operations=acknowledge_ops.construct_the_data(acknowledge_operations),
                conditions=fltr.construct_the_data(eval_type, formula, conditions)
            )

            if difference == {}:
                module.exit_json(changed=False, msg="Action is up to date: %s" % (name))
            else:
                result = action.update_action(
                    action_id=action_id,
                    **difference
                )
                module.exit_json(changed=True, msg="Action Updated: %s, ID: %s" % (name, result))
    else:
        if state == "absent":
            module.exit_json(changed=False)
        else:
            action_id = action.add_action(
                name=name,
                event_source=event_source,
                esc_period=esc_period,
                status=status,
                pause_in_maintenance=pause_in_maintenance,
                default_message=default_message,
                default_subject=default_subject,
                recovery_default_message=recovery_default_message,
                recovery_default_subject=recovery_default_subject,
                acknowledge_default_message=acknowledge_default_message,
                acknowledge_default_subject=acknowledge_default_subject,
                operations=ops.construct_the_data(operations),
                recovery_operations=recovery_ops.construct_the_data(recovery_operations),
                acknowledge_operations=acknowledge_ops.construct_the_data(acknowledge_operations),
                conditions=fltr.construct_the_data(eval_type, formula, conditions)
            )
            module.exit_json(changed=True, msg="Action created: %s, ID: %s" % (name, action_id))


if __name__ == '__main__':
    main()
