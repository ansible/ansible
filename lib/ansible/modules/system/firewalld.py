#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Adam Miller (maxamillion@fedoraproject.org)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: firewalld
short_description: Manage arbitrary ports/services with firewalld
description:
  - This module allows for addition or deletion of services and ports either tcp or udp in either running or permanent firewalld rules.
version_added: "1.4"
options:
  service:
    description:
      - "Name of a service to add/remove to/from firewalld - service must be listed in output of firewall-cmd --get-services."
    required: false
    default: null
  port:
    description:
      - "Name of a port or port range to add/remove to/from firewalld. Must be in the form PORT/PROTOCOL or PORT-PORT/PROTOCOL for port ranges."
    required: false
    default: null
  rich_rule:
    description:
      - "Rich rule to add/remove to/from firewalld."
    required: false
    default: null
  source:
    description:
      - 'The source/network you would like to add/remove to/from firewalld'
    required: false
    default: null
    version_added: "2.0"
  interface:
    description:
      - 'The interface you would like to add/remove to/from a zone in firewalld'
    required: false
    default: null
    version_added: "2.1"
  zone:
    description:
      - >
        The firewalld zone to add/remove to/from (NOTE: default zone can be configured per system but "public" is default from upstream. Available choices
        can be extended based on per-system configs, listed here are "out of the box" defaults).
    required: false
    default: system-default(public)
    choices: [ "work", "drop", "internal", "external", "trusted", "home", "dmz", "public", "block" ]
  permanent:
    description:
      - >
        Should this configuration be in the running firewalld configuration or persist across reboots. As of Ansible version 2.3, permanent operations can
        operate on firewalld configs when it's not running (requires firewalld >= 3.0.9). (NOTE: If this is false, immediate is assumed true.)
    required: false
    default: null
  immediate:
    description:
      - "Should this configuration be applied immediately, if set as permanent"
    required: false
    default: false
    version_added: "1.9"
  state:
    description:
      - >
        Enable or disable a setting.
        For ports: Should this port accept(enabled) or reject(disabled) connections.
        The states "present" and "absent" can only be used in zone level operations (i.e. when no other parameters but zone and state are set).
    required: true
    choices: [ "enabled", "disabled", "present", "absent" ]
  timeout:
    description:
      - "The amount of time the rule should be in effect for when non-permanent."
    required: false
    default: 0
  masquerade:
    description:
      - 'The masquerade setting you would like to enable/disable to/from zones within firewalld'
    required: false
    default: null
    version_added: "2.1"
notes:
  - Not tested on any Debian based system.
  - Requires the python2 bindings of firewalld, which may not be installed by default if the distribution switched to python 3
  - Zone transactions (creating, deleting) can be performed by using only the zone and state parameters "present" or "absent".
    Note that zone transactions must explicitly be permanent. This is a limitation in firewalld.
    This also means that you will have to reload firewalld after adding a zone that you wish to perfom immediate actions on.
    The module will not take care of this for you implicitly because that would undo any previously performed immediate actions which were not
    permanent. Therefor, if you require immediate access to a newly created zone it is recommended you reload firewalld immediately after the zone
    creation returns with a changed state and before you perform any other immediate, non-permanent actions on that zone.
requirements: [ 'firewalld >= 0.2.11' ]
author: "Adam Miller (@maxamillion)"
'''

EXAMPLES = '''
- firewalld:
    service: https
    permanent: true
    state: enabled

- firewalld:
    port: 8081/tcp
    permanent: true
    state: disabled

- firewalld:
    port: 161-162/udp
    permanent: true
    state: enabled

- firewalld:
    zone: dmz
    service: http
    permanent: true
    state: enabled

- firewalld:
    rich_rule: 'rule service name="ftp" audit limit value="1/m" accept'
    permanent: true
    state: enabled

- firewalld:
    source: 192.0.2.0/24
    zone: internal
    state: enabled

- firewalld:
    zone: trusted
    interface: eth2
    permanent: true
    state: enabled

- firewalld:
    masquerade: yes
    state: enabled
    permanent: true
    zone: dmz

- firewalld:
    zone: custom
    state: present
    permanent: true
'''

from ansible.module_utils.basic import AnsibleModule

# globals
module = None

# Imports
try:
    import firewall.config
    FW_VERSION = firewall.config.VERSION

    from firewall.client import Rich_Rule
    from firewall.client import FirewallClient
    from firewall.client import FirewallClientZoneSettings
    fw = None
    fw_offline = False
    import_failure = False

    try:
        fw = FirewallClient()
        fw.getDefaultZone()
    except AttributeError:
        # Firewalld is not currently running, permanent-only operations
        fw_offline = True

        # Import other required parts of the firewalld API
        #
        # NOTE:
        #  online and offline operations do not share a common firewalld API
        from firewall.core.fw_test import Firewall_test
        fw = Firewall_test()
        fw.start()

except ImportError:
    import_failure = True


class FirewallTransaction(object):
    """
    FirewallTransaction

    This is the base class for all firewalld transactions we might want to have
    """

    global module

    def __init__(self, fw, action_args=(), zone=None, desired_state=None,
                 permanent=False, immediate=False, fw_offline=False,
                 enabled_values=None, disabled_values=None):
        # type: (firewall.client, tuple, str, bool, bool, bool)
        """
        initializer the transaction

        :fw:              firewall client instance
        :action_args:     tuple, args to pass for the action to take place
        :zone:            str,  firewall zone
        :desired_state:   str,  the desired state (enabled, disabled, etc)
        :permanent:       bool, action should be permanent
        :immediate:       bool, action should take place immediately
        :fw_offline:      bool, action takes place as if the firewall were offline
        :enabled_values:  str[], acceptable values for enabling something (default: enabled)
        :disabled_values: str[], acceptable values for disabling something (default: disabled)
        """

        self.fw = fw
        self.action_args = action_args
        self.zone = zone
        self.desired_state = desired_state
        self.permanent = permanent
        self.immediate = immediate
        self.fw_offline = fw_offline
        self.enabled_values = enabled_values or ["enabled"]
        self.disabled_values = disabled_values or ["disabled"]

        # List of messages that we'll call module.fail_json or module.exit_json
        # with.
        self.msgs = []

        # Allow for custom messages to be added for certain subclass transaction
        # types
        self.enabled_msg = None
        self.disabled_msg = None

    #####################
    # exception handling
    #
    def action_handler(self, action_func, action_func_args):
        """
        Function to wrap calls to make actions on firewalld in try/except
        logic and emit (hopefully) useful error messages
        """

        try:
            return action_func(*action_func_args)
        except Exception as e:

            # If there are any commonly known errors that we should provide more
            # context for to help the users diagnose what's wrong. Handle that here
            if "INVALID_SERVICE" in "%s" % e:
                self.msgs.append("Services are defined by port/tcp relationship and named as they are in /etc/services (on most systems)")

            if len(self.msgs) > 0:
                module.fail_json(
                    msg='ERROR: Exception caught: %s %s' % (e, ', '.join(self.msgs))
                )
            else:
                module.fail_json(msg='ERROR: Exception caught: %s' % e)

    def get_fw_zone_settings(self):
        if self.fw_offline:
            fw_zone = self.fw.config.get_zone(self.zone)
            fw_settings = FirewallClientZoneSettings(
                list(self.fw.config.get_zone_config(fw_zone))
            )
        else:
            fw_zone = self.fw.config().getZoneByName(self.zone)
            fw_settings = fw_zone.getSettings()

        return (fw_zone, fw_settings)

    def update_fw_settings(self, fw_zone, fw_settings):
        if self.fw_offline:
            self.fw.config.set_zone_config(fw_zone, fw_settings.settings)
        else:
            fw_zone.update(fw_settings)

    def get_enabled_immediate(self):
        raise NotImplementedError

    def get_enabled_permanent(self):
        raise NotImplementedError

    def set_enabled_immediate(self):
        raise NotImplementedError

    def set_enabled_permanent(self):
        raise NotImplementedError

    def set_disabled_immediate(self):
        raise NotImplementedError

    def set_disabled_permanent(self):
        raise NotImplementedError

    def run(self):
        """
        run

        This fuction contains the "transaction logic" where as all operations
        follow a similar pattern in order to perform their action but simply
        call different functions to carry that action out.
        """

        self.changed = False

        if self.immediate and self.permanent:
            is_enabled_permanent = self.action_handler(
                self.get_enabled_permanent,
                self.action_args
            )
            is_enabled_immediate = self.action_handler(
                self.get_enabled_immediate,
                self.action_args
            )
            self.msgs.append('Permanent and Non-Permanent(immediate) operation')

            if self.desired_state in self.enabled_values:
                if not is_enabled_permanent or not is_enabled_immediate:
                    if module.check_mode:
                        module.exit_json(changed=True)
                if not is_enabled_permanent:
                    self.action_handler(
                        self.set_enabled_permanent,
                        self.action_args
                    )
                    self.changed = True
                if not is_enabled_immediate:
                    self.action_handler(
                        self.set_enabled_immediate,
                        self.action_args
                    )
                    self.changed = True
                if self.changed and self.enabled_msg:
                    self.msgs.append(self.enabled_msg)

            elif self.desired_state in self.disabled_values:
                if is_enabled_permanent or is_enabled_immediate:
                    if module.check_mode:
                        module.exit_json(changed=True)
                if is_enabled_permanent:
                    self.action_handler(
                        self.set_disabled_permanent,
                        self.action_args
                    )
                    self.changed = True
                if is_enabled_immediate:
                    self.action_handler(
                        self.set_disabled_immediate,
                        self.action_args
                    )
                    self.changed = True
                if self.changed and self.disabled_msg:
                    self.msgs.append(self.disabled_msg)

        elif self.permanent and not self.immediate:
            is_enabled = self.action_handler(
                self.get_enabled_permanent,
                self.action_args
            )
            self.msgs.append('Permanent operation')

            if self.desired_state in self.enabled_values:
                if not is_enabled:
                    if module.check_mode:
                        module.exit_json(changed=True)

                    self.action_handler(
                        self.set_enabled_permanent,
                        self.action_args
                    )
                    self.changed = True
                if self.changed and self.enabled_msg:
                    self.msgs.append(self.enabled_msg)

            elif self.desired_state in self.disabled_values:
                if is_enabled:
                    if module.check_mode:
                        module.exit_json(changed=True)

                    self.action_handler(
                        self.set_disabled_permanent,
                        self.action_args
                    )
                    self.changed = True
                if self.changed and self.disabled_msg:
                    self.msgs.append(self.disabled_msg)

        elif self.immediate and not self.permanent:
            is_enabled = self.action_handler(
                self.get_enabled_immediate,
                self.action_args
            )
            self.msgs.append('Non-permanent operation')

            if self.desired_state in self.enabled_values:
                if not is_enabled:
                    if module.check_mode:
                        module.exit_json(changed=True)

                    self.action_handler(
                        self.set_enabled_immediate,
                        self.action_args
                    )
                    self.changed = True
                if self.changed and self.enabled_msg:
                    self.msgs.append(self.enabled_msg)

            elif self.desired_state in self.disabled_values:
                if is_enabled:
                    if module.check_mode:
                        module.exit_json(changed=True)

                    self.action_handler(
                        self.set_disabled_immediate,
                        self.action_args
                    )
                    self.changed = True
                if self.changed and self.disabled_msg:
                    self.msgs.append(self.disabled_msg)

        return (self.changed, self.msgs)


class ServiceTransaction(FirewallTransaction):
    """
    ServiceTransaction
    """

    def __init__(self, fw, action_args=None, zone=None, desired_state=None,
                 permanent=False, immediate=False, fw_offline=False):
        super(ServiceTransaction, self).__init__(
            fw, action_args=action_args, desired_state=desired_state, zone=zone,
            permanent=permanent, immediate=immediate, fw_offline=fw_offline)

    def get_enabled_immediate(self, service, timeout):
        if service in self.fw.getServices(self.zone):
            return True
        else:
            return False

    def get_enabled_permanent(self, service, timeout):
        fw_zone, fw_settings = self.get_fw_zone_settings()

        if service in fw_settings.getServices():
            return True
        else:
            return False

    def set_enabled_immediate(self, service, timeout):
        self.fw.addService(self.zone, service, timeout)

    def set_enabled_permanent(self, service, timeout):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        fw_settings.addService(service)
        self.update_fw_settings(fw_zone, fw_settings)

    def set_disabled_immediate(self, service, timeout):
        self.fw.removeService(self.zone, service)

    def set_disabled_permanent(self, service, timeout):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        fw_settings.removeService(service)
        self.update_fw_settings(fw_zone, fw_settings)


class MasqueradeTransaction(FirewallTransaction):
    """
    MasqueradeTransaction
    """

    def __init__(self, fw, action_args=None, zone=None, desired_state=None,
                 permanent=False, immediate=False, fw_offline=False):
        super(MasqueradeTransaction, self).__init__(
            fw, action_args=action_args, desired_state=desired_state, zone=zone,
            permanent=permanent, immediate=immediate, fw_offline=fw_offline)

        self.enabled_msg = "Added masquerade to zone %s" % self.zone
        self.disabled_msg = "Removed masquerade from zone %s" % self.zone

    def get_enabled_immediate(self):
        if self.fw.queryMasquerade(self.zone) is True:
            return True
        else:
            return False

    def get_enabled_permanent(self):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        if fw_settings.getMasquerade() is True:
            return True
        else:
            return False

    def set_enabled_immediate(self):
        self.fw.addMasquerade(self.zone)

    def set_enabled_permanent(self):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        fw_settings.setMasquerade(True)
        self.update_fw_settings(fw_zone, fw_settings)

    def set_disabled_immediate(self):
        self.fw.removeMasquerade(self.zone)

    def set_disabled_permanent(self):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        fw_settings.setMasquerade(False)
        self.update_fw_settings(fw_zone, fw_settings)


class PortTransaction(FirewallTransaction):
    """
    PortTransaction
    """

    def __init__(self, fw, action_args=None, zone=None, desired_state=None,
                 permanent=False, immediate=False, fw_offline=False):
        super(PortTransaction, self).__init__(
            fw, action_args=action_args, desired_state=desired_state, zone=zone,
            permanent=permanent, immediate=immediate, fw_offline=fw_offline)

    def get_enabled_immediate(self, port, protocol, timeout):
        port_proto = [port, protocol]
        if self.fw_offline:
            fw_zone, fw_settings = self.get_fw_zone_settings()
            ports_list = fw_settings.getPorts()
        else:
            ports_list = self.fw.getPorts(self.zone)

        if port_proto in ports_list:
            return True
        else:
            return False

    def get_enabled_permanent(self, port, protocol, timeout):
        port_proto = (port, protocol)
        fw_zone, fw_settings = self.get_fw_zone_settings()

        if port_proto in fw_settings.getPorts():
            return True
        else:
            return False

    def set_enabled_immediate(self, port, protocol, timeout):
        self.fw.addPort(self.zone, port, protocol, timeout)

    def set_enabled_permanent(self, port, protocol, timeout):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        fw_settings.addPort(port, protocol)
        self.update_fw_settings(fw_zone, fw_settings)

    def set_disabled_immediate(self, port, protocol, timeout):
        self.fw.removePort(self.zone, port, protocol)

    def set_disabled_permanent(self, port, protocol, timeout):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        fw_settings.removePort(port, protocol)
        self.update_fw_settings(fw_zone, fw_settings)


class InterfaceTransaction(FirewallTransaction):
    """
    InterfaceTransaction
    """

    def __init__(self, fw, action_args=None, zone=None, desired_state=None,
                 permanent=False, immediate=False, fw_offline=False):
        super(InterfaceTransaction, self).__init__(
            fw, action_args=action_args, desired_state=desired_state, zone=zone,
            permanent=permanent, immediate=immediate, fw_offline=fw_offline)

        self.enabled_msg = "Changed %s to zone %s" % \
            (self.action_args[0], self.zone)

        self.disabled_msg = "Removed %s from zone %s" % \
            (self.action_args[0], self.zone)

    def get_enabled_immediate(self, interface):
        if self.fw_offline:
            fw_zone, fw_settings = self.get_fw_zone_settings()
            interface_list = fw_settings.getInterfaces()
        else:
            interface_list = self.fw.getInterfaces(self.zone)
        if interface in interface_list:
            return True
        else:
            return False

    def get_enabled_permanent(self, interface):
        fw_zone, fw_settings = self.get_fw_zone_settings()

        if interface in fw_settings.getInterfaces():
            return True
        else:
            return False

    def set_enabled_immediate(self, interface):
        self.fw.changeZoneOfInterface(self.zone, interface)

    def set_enabled_permanent(self, interface):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        if self.fw_offline:
            iface_zone_objs = []
            for zone in self.fw.config.get_zones():
                old_zone_obj = self.fw.config.get_zone(zone)
                if interface in old_zone_obj.interfaces:
                    iface_zone_objs.append(old_zone_obj)
            if len(iface_zone_objs) > 1:
                # Even it shouldn't happen, it's actually possible that
                # the same interface is in several zone XML files
                module.fail_json(
                    msg='ERROR: interface {} is in {} zone XML file, can only be in one'.format(
                        interface,
                        len(iface_zone_objs)
                    )
                )
            old_zone_obj = iface_zone_objs[0]
            if old_zone_obj.name != self.zone:
                old_zone_settings = FirewallClientZoneSettings(
                    self.fw.config.get_zone_config(old_zone_obj)
                )
                old_zone_settings.removeInterface(interface)    # remove from old
                self.fw.config.set_zone_config(
                    old_zone_obj,
                    old_zone_settings.settings
                )
                fw_settings.addInterface(interface)             # add to new
                self.fw.config.set_zone_config(fw_zone, fw_settings.settings)
        else:
            old_zone_name = self.fw.config().getZoneOfInterface(interface)
            if old_zone_name != self.zone:
                if old_zone_name:
                    old_zone_obj = self.fw.config().getZoneByName(old_zone_name)
                    old_zone_settings = old_zone_obj.getSettings()
                    old_zone_settings.removeInterface(interface)  # remove from old
                    old_zone_obj.update(old_zone_settings)
                fw_settings.addInterface(interface)              # add to new
                fw_zone.update(fw_settings)

    def set_disabled_immediate(self, interface):
        self.fw.removeInterface(self.zone, interface)

    def set_disabled_permanent(self, interface):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        fw_settings.removeInterface(interface)
        self.update_fw_settings(fw_zone, fw_settings)


class RichRuleTransaction(FirewallTransaction):
    """
    RichRuleTransaction
    """

    def __init__(self, fw, action_args=None, zone=None, desired_state=None,
                 permanent=False, immediate=False, fw_offline=False):
        super(RichRuleTransaction, self).__init__(
            fw, action_args=action_args, desired_state=desired_state, zone=zone,
            permanent=permanent, immediate=immediate, fw_offline=fw_offline)

    def get_enabled_immediate(self, rule, timeout):
        # Convert the rule string to standard format
        # before checking whether it is present
        rule = str(Rich_Rule(rule_str=rule))
        if rule in self.fw.getRichRules(self.zone):
            return True
        else:
            return False

    def get_enabled_permanent(self, rule, timeout):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        # Convert the rule string to standard format
        # before checking whether it is present
        rule = str(Rich_Rule(rule_str=rule))
        if rule in fw_settings.getRichRules():
            return True
        else:
            return False

    def set_enabled_immediate(self, rule, timeout):
        self.fw.addRichRule(self.zone, rule, timeout)

    def set_enabled_permanent(self, rule, timeout):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        fw_settings.addRichRule(rule)
        self.update_fw_settings(fw_zone, fw_settings)

    def set_disabled_immediate(self, rule, timeout):
        fw.removeRichRule(self.zone, rule)

    def set_disabled_permanent(self, rule, timeout):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        fw_settings.removeRichRule(rule)
        self.update_fw_settings(fw_zone, fw_settings)


class SourceTransaction(FirewallTransaction):
    """
    SourceTransaction
    """

    def __init__(self, fw, action_args=None, zone=None, desired_state=None,
                 permanent=False, immediate=False, fw_offline=False):
        super(SourceTransaction, self).__init__(
            fw, action_args=action_args, desired_state=desired_state, zone=zone,
            permanent=permanent, immediate=immediate, fw_offline=fw_offline)

        self.enabled_msg = "Added %s to zone %s" % \
            (self.action_args[0], self.zone)

        self.disabled_msg = "Removed %s from zone %s" % \
            (self.action_args[0], self.zone)

    def get_enabled_immediate(self, source):
        if source in self.fw.getSources(self.zone):
            return True
        else:
            return False

    def get_enabled_permanent(self, source):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        if source in fw_settings.getSources():
            return True
        else:
            return False

    def set_enabled_immediate(self, source):
        self.fw.addSource(self.zone, source)

    def set_enabled_permanent(self, source):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        fw_settings.addSource(source)
        self.update_fw_settings(fw_zone, fw_settings)

    def set_disabled_immediate(self, source):
        self.fw.removeSource(self.zone, source)

    def set_disabled_permanent(self, source):
        fw_zone, fw_settings = self.get_fw_zone_settings()
        fw_settings.removeSource(source)
        self.update_fw_settings(fw_zone, fw_settings)


class ZoneTransaction(FirewallTransaction):
    """
    ZoneTransaction
    """

    def __init__(self, fw, action_args=None, zone=None, desired_state=None,
                 permanent=True, immediate=False, fw_offline=False,
                 enabled_values=None, disabled_values=None):
        super(ZoneTransaction, self).__init__(
            fw, action_args=action_args, desired_state=desired_state, zone=zone,
            permanent=permanent, immediate=immediate, fw_offline=fw_offline,
            enabled_values=enabled_values or ["present"],
            disabled_values=disabled_values or ["absent"])

        self.enabled_msg = "Added zone %s" % \
            (self.zone)

        self.disabled_msg = "Removed zone %s" % \
            (self.zone)

        self.tx_not_permanent_error_msg = "Zone operations must be permanent. " \
            "Make sure you didn't set the 'permanent' flag to 'false' or the 'immediate' flag to 'true'."

    def get_enabled_immediate(self):
        module.fail_json(msg=self.tx_not_permanent_error_msg)

    def get_enabled_permanent(self):
        if self.zone in fw.config().getZoneNames():
            return True
        else:
            return False

    def set_enabled_immediate(self):
        module.fail_json(msg=self.tx_not_permanent_error_msg)

    def set_enabled_permanent(self):
        fw.config().addZone(self.zone, FirewallClientZoneSettings())

    def set_disabled_immediate(self):
        module.fail_json(msg=self.tx_not_permanent_error_msg)

    def set_disabled_permanent(self):
        zone_obj = self.fw.config().getZoneByName(self.zone)
        zone_obj.remove()


def main():

    global module
    module = AnsibleModule(
        argument_spec=dict(
            service=dict(required=False, default=None),
            port=dict(required=False, default=None),
            rich_rule=dict(required=False, default=None),
            zone=dict(required=False, default=None),
            immediate=dict(type='bool', default=False),
            source=dict(required=False, default=None),
            permanent=dict(type='bool', required=False, default=None),
            state=dict(choices=['enabled', 'disabled', 'present', 'absent'], required=True),
            timeout=dict(type='int', required=False, default=0),
            interface=dict(required=False, default=None),
            masquerade=dict(required=False, default=None),
            offline=dict(type='bool', required=False, default=None),
        ),
        supports_check_mode=True
    )

    if fw_offline:
        # Pre-run version checking
        if FW_VERSION < "0.3.9":
            module.fail_json(msg='unsupported version of firewalld, offline operations require >= 0.3.9')
    else:
        # Pre-run version checking
        if FW_VERSION < "0.2.11":
            module.fail_json(msg='unsupported version of firewalld, requires >= 0.2.11')

        # Check for firewalld running
        try:
            if fw.connected is False:
                module.fail_json(msg='firewalld service must be running, or try with offline=true')
        except AttributeError:
            module.fail_json(msg="firewalld connection can't be established,\
                    installed version (%s) likely too old. Requires firewalld >= 0.2.11" % FW_VERSION)

    if import_failure:
        module.fail_json(
            msg='firewalld and its python module are required for this module, version 0.2.11 or newer required (0.3.9 or newer for offline operations)'
        )

    permanent = module.params['permanent']
    desired_state = module.params['state']
    immediate = module.params['immediate']
    timeout = module.params['timeout']
    interface = module.params['interface']
    masquerade = module.params['masquerade']

    # If neither permanent or immediate is provided, assume immediate (as
    # written in the module's docs)
    if not permanent and not immediate:
        immediate = True

    # Verify required params are provided
    if immediate and fw_offline:
        module.fail(msg='firewall is not currently running, unable to perform immediate actions without a running firewall daemon')

    changed = False
    msgs = []
    service = module.params['service']
    rich_rule = module.params['rich_rule']
    source = module.params['source']

    if module.params['port'] is not None:
        port, protocol = module.params['port'].strip().split('/')
        if protocol is None:
            module.fail_json(msg='improper port format (missing protocol?)')
    else:
        port = None

    # If we weren't provided a zone, then just use the system default
    if module.params['zone'] is not None:
        zone = module.params['zone']
    else:
        if fw_offline:
            zone = fw.get_default_zone()
        else:
            zone = fw.getDefaultZone()

    modification_count = 0
    if service is not None:
        modification_count += 1
    if port is not None:
        modification_count += 1
    if rich_rule is not None:
        modification_count += 1
    if interface is not None:
        modification_count += 1
    if masquerade is not None:
        modification_count += 1

    if modification_count > 1:
        module.fail_json(
            msg='can only operate on port, service, rich_rule, or interface at once'
        )
    elif modification_count > 0 and desired_state in ['absent', 'present']:
        module.fail_json(
            msg='absent and present state can only be used in zone level operations'
        )

    if service is not None:

        transaction = ServiceTransaction(
            fw,
            action_args=(service, timeout),
            zone=zone,
            desired_state=desired_state,
            permanent=permanent,
            immediate=immediate,
            fw_offline=fw_offline
        )

        changed, transaction_msgs = transaction.run()
        msgs = msgs + transaction_msgs
        if changed is True:
            msgs.append("Changed service %s to %s" % (service, desired_state))

    if source is not None:

        transaction = SourceTransaction(
            fw,
            action_args=(source,),
            zone=zone,
            desired_state=desired_state,
            permanent=permanent,
            immediate=immediate,
            fw_offline=fw_offline
        )

        changed, transaction_msgs = transaction.run()
        msgs = msgs + transaction_msgs

    if port is not None:

        transaction = PortTransaction(
            fw,
            action_args=(port, protocol, timeout),
            zone=zone,
            desired_state=desired_state,
            permanent=permanent,
            immediate=immediate,
            fw_offline=fw_offline
        )

        changed, transaction_msgs = transaction.run()
        msgs = msgs + transaction_msgs
        if changed is True:
            msgs.append(
                "Changed port %s to %s" % (
                    "%s/%s" % (port, protocol), desired_state
                )
            )

    if rich_rule is not None:

        transaction = RichRuleTransaction(
            fw,
            action_args=(rich_rule, timeout),
            zone=zone,
            desired_state=desired_state,
            permanent=permanent,
            immediate=immediate,
            fw_offline=fw_offline
        )

        changed, transaction_msgs = transaction.run()
        msgs = msgs + transaction_msgs
        if changed is True:
            msgs.append("Changed rich_rule %s to %s" % (rich_rule, desired_state))

    if interface is not None:

        transaction = InterfaceTransaction(
            fw,
            action_args=(interface,),
            zone=zone,
            desired_state=desired_state,
            permanent=permanent,
            immediate=immediate,
            fw_offline=fw_offline
        )

        changed, transaction_msgs = transaction.run()
        msgs = msgs + transaction_msgs

    if masquerade is not None:

        transaction = MasqueradeTransaction(
            fw,
            action_args=(),
            zone=zone,
            desired_state=desired_state,
            permanent=permanent,
            immediate=immediate,
            fw_offline=fw_offline
        )

        changed, transaction_msgs = transaction.run()
        msgs = msgs + transaction_msgs

    ''' If there are no changes within the zone we are operating on the zone itself '''
    if modification_count == 0 and desired_state in ['absent', 'present']:

        transaction = ZoneTransaction(
            fw,
            action_args=(),
            zone=zone,
            desired_state=desired_state,
            permanent=permanent,
            immediate=immediate,
            fw_offline=fw_offline
        )

        changed, transaction_msgs = transaction.run()
        msgs = msgs + transaction_msgs
        if changed is True:
            msgs.append("Changed zone %s to %s" % (zone, desired_state))

    if fw_offline:
        msgs.append("(offline operation: only on-disk configs were altered)")

    module.exit_json(changed=changed, msg=', '.join(msgs))


if __name__ == '__main__':
    main()
