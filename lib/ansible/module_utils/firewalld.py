# -*- coding: utf-8 -*-
#
# (c) 2013-2018, Adam Miller (maxamillion@fedoraproject.org)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Imports and info for sanity checking
from distutils.version import LooseVersion

FW_VERSION = None
fw = None
fw_offline = False
import_failure = True
try:
    import firewall.config
    FW_VERSION = firewall.config.VERSION

    from firewall.client import FirewallClient
    from firewall.client import FirewallClientZoneSettings
    from firewall.errors import FirewallError
    import_failure = False

    try:
        fw = FirewallClient()
        fw.getDefaultZone()

    except (AttributeError, FirewallError):
        # Firewalld is not currently running, permanent-only operations
        fw_offline = True

        # Import other required parts of the firewalld API
        #
        # NOTE:
        #  online and offline operations do not share a common firewalld API
        try:
            from firewall.core.fw_test import Firewall_test
            fw = Firewall_test()
        except (ModuleNotFoundError):
            # In firewalld version 0.7.0 this behavior changed
            from firewall.core.fw import Firewall
            fw = Firewall(offline=True)

        fw.start()
except ImportError:
    pass


class FirewallTransaction(object):
    """
    FirewallTransaction

    This is the base class for all firewalld transactions we might want to have
    """

    def __init__(self, module, action_args=(), zone=None, desired_state=None,
                 permanent=False, immediate=False, enabled_values=None, disabled_values=None):
        # type: (firewall.client, tuple, str, bool, bool, bool)
        """
        initializer the transaction

        :module:          AnsibleModule, instance of AnsibleModule
        :action_args:     tuple, args to pass for the action to take place
        :zone:            str,  firewall zone
        :desired_state:   str,  the desired state (enabled, disabled, etc)
        :permanent:       bool, action should be permanent
        :immediate:       bool, action should take place immediately
        :enabled_values:  str[], acceptable values for enabling something (default: enabled)
        :disabled_values: str[], acceptable values for disabling something (default: disabled)
        """

        self.module = module
        self.fw = fw
        self.action_args = action_args

        if zone:
            self.zone = zone
        else:
            if fw_offline:
                self.zone = fw.get_default_zone()
            else:
                self.zone = fw.getDefaultZone()

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
                self.module.fail_json(
                    msg='ERROR: Exception caught: %s %s' % (e, ', '.join(self.msgs))
                )
            else:
                self.module.fail_json(msg='ERROR: Exception caught: %s' % e)

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

        This function contains the "transaction logic" where as all operations
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
                    if self.module.check_mode:
                        self.module.exit_json(changed=True)
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
                    if self.module.check_mode:
                        self.module.exit_json(changed=True)
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
                    if self.module.check_mode:
                        self.module.exit_json(changed=True)

                    self.action_handler(
                        self.set_enabled_permanent,
                        self.action_args
                    )
                    self.changed = True
                if self.changed and self.enabled_msg:
                    self.msgs.append(self.enabled_msg)

            elif self.desired_state in self.disabled_values:
                if is_enabled:
                    if self.module.check_mode:
                        self.module.exit_json(changed=True)

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
                    if self.module.check_mode:
                        self.module.exit_json(changed=True)

                    self.action_handler(
                        self.set_enabled_immediate,
                        self.action_args
                    )
                    self.changed = True
                if self.changed and self.enabled_msg:
                    self.msgs.append(self.enabled_msg)

            elif self.desired_state in self.disabled_values:
                if is_enabled:
                    if self.module.check_mode:
                        self.module.exit_json(changed=True)

                    self.action_handler(
                        self.set_disabled_immediate,
                        self.action_args
                    )
                    self.changed = True
                if self.changed and self.disabled_msg:
                    self.msgs.append(self.disabled_msg)

        return (self.changed, self.msgs)

    @staticmethod
    def sanity_check(module):
        """
        Perform sanity checking, version checks, etc

        :module:    AnsibleModule instance
        """

        if FW_VERSION and fw_offline:
            # Pre-run version checking
            if LooseVersion(FW_VERSION) < LooseVersion("0.3.9"):
                module.fail_json(msg='unsupported version of firewalld, offline operations require >= 0.3.9 - found: {0}'.format(FW_VERSION))
        elif FW_VERSION and not fw_offline:
            # Pre-run version checking
            if LooseVersion(FW_VERSION) < LooseVersion("0.2.11"):
                module.fail_json(msg='unsupported version of firewalld, requires >= 0.2.11 - found: {0}'.format(FW_VERSION))

            # Check for firewalld running
            try:
                if fw.connected is False:
                    module.fail_json(msg='firewalld service must be running, or try with offline=true')
            except AttributeError:
                module.fail_json(msg="firewalld connection can't be established,\
                        installed version (%s) likely too old. Requires firewalld >= 0.2.11" % FW_VERSION)

        if import_failure:
            module.fail_json(
                msg='Python Module not found: firewalld and its python module are required for this module, \
                        version 0.2.11 or newer required (0.3.9 or newer for offline operations)'
            )
