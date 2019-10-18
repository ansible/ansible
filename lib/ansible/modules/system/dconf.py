#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Pedro Costa <dev@iampfac.com>
# (c) 2017, Branko Majic <branko@majic.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: dconf
author:
    - "Branko Majic (@azaghal)"
    - "Pedro Costa (@pfac)"
short_description: Modify and read dconf database
description:
  - This module allows modifications and reading of dconf database. The module
    is implemented as a wrapper around dconf tool. Please see the dconf(1) man
    page for more details.
  - Since C(dconf) requires a running D-Bus session to change values, the module
    will try to detect an existing session and reuse it, or run the tool via
    C(dbus-run-session).
notes:
  - This module depends on C(psutil) Python library (version 4.0.0 and upwards),
    C(dconf), C(dbus-send), and C(dbus-run-session) binaries. Depending on
    distribution you are using, you may need to install additional packages to
    have these available.
  - Detection of existing, running D-Bus session, required to change settings
    via C(dconf), is not 100% reliable due to implementation details of D-Bus
    daemon itself. This might lead to running applications not picking-up
    changes on the fly if options are changed via Ansible and
    C(dbus-run-session).
  - Keep in mind that the C(dconf) CLI tool, which this module wraps around,
    utilises an unusual syntax for the values (GVariant). For example, if you
    wanted to provide a string value, the correct syntax would be
    C(value="'myvalue'") - with single quotes as part of the Ansible parameter
    value.
  - When using loops in combination with a value like
    :code:`"[('xkb', 'us'), ('xkb', 'se')]"`, you need to be aware of possible
    type conversions. Applying a filter :code:`"{{ item.value | string }}"`
    to the parameter variable can avoid potential conversion problems.
  - The easiest way to figure out exact syntax/value you need to provide for a
    key is by making the configuration change in application affected by the
    key, and then having a look at value set via commands C(dconf dump
    /path/to/dir/) or C(dconf read /path/to/key).
version_added: "2.4"
options:
  key:
    required: true
    description:
      - A dconf key to modify or read from the dconf database.
  value:
    required: false
    description:
      - Value to set for the specified dconf key. Value should be specified in
        GVariant format. Due to complexity of this format, it is best to have a
        look at existing values in the dconf database. Required for
        C(state=present).
  content:
    required: false
    description:
      - Value to set for the specified dconf key. Value should be specified in
        GVariant format. Due to complexity of this format, it is best to have a
        look at existing values in the dconf database. Required for
        C(state=present) when C(key) ends with `/`.
    version_added: "2.10"
  state:
    required: false
    default: present
    choices:
      - read
      - present
      - absent
    description:
      - The action to take upon the key/value.
"""

RETURN = """
value:
    description: value associated with the requested key
    returned: success, state was "read"
    type: str
    sample: "'Default'"
"""

EXAMPLES = """
- name: Configure available keyboard layouts in Gnome
  dconf:
    key: "/org/gnome/desktop/input-sources/sources"
    value: "[('xkb', 'us'), ('xkb', 'se')]"
    state: present

- name: Read currently available keyboard layouts in Gnome
  dconf:
    key: "/org/gnome/desktop/input-sources/sources"
    state: read
  register: keyboard_layouts

- name: Reset the available keyboard layouts in Gnome
  dconf:
    key: "/org/gnome/desktop/input-sources/sources"
    state: absent

- name: Configure available keyboard layouts in Cinnamon
  dconf:
    key: "/org/gnome/libgnomekbd/keyboard/layouts"
    value: "['us', 'se']"
    state: present

- name: Read currently available keyboard layouts in Cinnamon
  dconf:
    key: "/org/gnome/libgnomekbd/keyboard/layouts"
    state: read
  register: keyboard_layouts

- name: Reset the available keyboard layouts in Cinnamon
  dconf:
    key: "/org/gnome/libgnomekbd/keyboard/layouts"
    state: absent

- name: Disable desktop effects in Cinnamon
  dconf:
    key: "/org/cinnamon/desktop-effects"
    value: "false"
    state: present

- name: Load multiple configs under a specific dconf key
  dconf:
    key: "/com/gexperts/Tilix/"
    content: |
      [/]
      quake-specific-monitor=0
"""


import os
import traceback

PSUTIL_IMP_ERR = None
try:
    import psutil
    psutil_found = True
except ImportError:
    PSUTIL_IMP_ERR = traceback.format_exc()
    psutil_found = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


class DBusWrapper(object):
    """
    Helper class that can be used for running a command with a working D-Bus
    session.

    If possible, command will be run against an existing D-Bus session,
    otherwise the session will be spawned via dbus-run-session.

    Example usage:

    dbus_wrapper = DBusWrapper(ansible_module)
    dbus_wrapper.run_command(["printenv", "DBUS_SESSION_BUS_ADDRESS"])
    """

    def __init__(self, module):
        """
        Initialises an instance of the class.

        :param module: Ansible module instance used to signal failures and run commands.
        :type module: AnsibleModule
        """

        # Store passed-in arguments and set-up some defaults.
        self.module = module

        # Try to extract existing D-Bus session address.
        self.dbus_session_bus_address = self._get_existing_dbus_session()

        # If no existing D-Bus session was detected, check if dbus-run-session
        # is available.
        if self.dbus_session_bus_address is None:
            self.module.get_bin_path('dbus-run-session', required=True)

    def _get_existing_dbus_session(self):
        """
        Detects and returns an existing D-Bus session bus address.

        :returns: string -- D-Bus session bus address. If a running D-Bus session was not detected, returns None.
        """

        # We'll be checking the processes of current user only.
        uid = os.getuid()

        # Go through all the pids for this user, try to extract the D-Bus
        # session bus address from environment, and ensure it is possible to
        # connect to it.
        self.module.debug("Trying to detect existing D-Bus user session for user: %d" % uid)

        for pid in psutil.pids():
            process = psutil.Process(pid)
            process_real_uid, _, _ = process.uids()
            try:
                if process_real_uid == uid and 'DBUS_SESSION_BUS_ADDRESS' in process.environ():
                    dbus_session_bus_address_candidate = process.environ()['DBUS_SESSION_BUS_ADDRESS']
                    self.module.debug("Found D-Bus user session candidate at address: %s" % dbus_session_bus_address_candidate)
                    command = ['dbus-send', '--address=%s' % dbus_session_bus_address_candidate, '--type=signal', '/', 'com.example.test']
                    rc, _, _ = self.module.run_command(command)

                    if rc == 0:
                        self.module.debug("Verified D-Bus user session candidate as usable at address: %s" % dbus_session_bus_address_candidate)

                        return dbus_session_bus_address_candidate

            # This can happen with things like SSH sessions etc.
            except psutil.AccessDenied:
                pass

        self.module.debug("Failed to find running D-Bus user session, will use dbus-run-session")

        return None

    def run_command(self, command, data=None):
        """
        Runs the specified command within a functional D-Bus session. Command is
        effectively passed-on to AnsibleModule.run_command() method, with
        modification for using dbus-run-session if necessary.

        :param command: Command to run, including parameters. Each element of the list should be a string.
        :type module: list

        :returns: tuple(result_code, standard_output, standard_error) -- Result code, standard output, and standard error from running the command.
        """

        if self.dbus_session_bus_address is None:
            self.module.debug("Using dbus-run-session wrapper for running commands.")
            command = ['dbus-run-session'] + command
            rc, out, err = self.module.run_command(command, data=data)

            if self.dbus_session_bus_address is None and rc == 127:
                self.module.fail_json(msg="Failed to run passed-in command, dbus-run-session faced an internal error: %s" % err)
        else:
            extra_environment = {'DBUS_SESSION_BUS_ADDRESS': self.dbus_session_bus_address}
            rc, out, err = self.module.run_command(command, data=data, environ_update=extra_environment)

        return rc, out, err


class DconfPreference(object):

    def __init__(self, module, check_mode=False):
        """
        Initialises instance of the class.

        :param module: Ansible module instance used to signal failures and run commands.
        :type module: AnsibleModule

        :param check_mode: Specify whether to only check if a change should be made or if to actually make a change.
        :type check_mode: bool
        """

        self.module = module
        self.check_mode = check_mode

    def normalize_value(self, value):
        if value == '':
            return None

        return value.rstrip('\n')

    def read(self, key, include_defaults=False):
        """
        Retrieves current value associated with the dconf key.

        If an error occurs, a call will be made to AnsibleModule.fail_json.

        :param key: dconf key to read. Must not end with `/`.
        :type key: str

        :returns: string -- Value assigned to the provided key. If the value is not set for specified key, returns None.
        """

        # Set up command to run
        command = ["dconf", "read"]

        if include_defaults:
            command.append("-d")

        command.append(key)

        # Run DConf read command (no need for DBus wrapping)
        rc, out, err = self.module.run_command(command)

        if rc != 0:
            self.module.fail_json(msg='dconf failed while reading the value with error: %s' % err)

        return self.normalize_value(out)

    def dump(self, key):
        """
        Dumps all the values under the dconf key.

        If an error occurs, a call will be made to AnsibleModule.fail_json.

        :param key: dconf key to dump. Must end with `/`.
        :type key: str

        :returns: string -- Values under the provided key. If there are no values under the specified key, returns None.
        """

        # Set up command to run
        command = ["dconf", "dump", key]

        # Run DConf read command (no need for DBus wrapping)
        rc, out, err = self.module.run_command(command)

        # Handle command failure
        if rc != 0:
            self.module.fail_json(msg='dconf failed while dumping values with error: %s' % err)
            return None

        return self.normalize_value(out)

    def write(self, key, value):
        """
        Writes the value for specified key.

        If an error occurs, a call will be made to AnsibleModule.fail_json.

        :param key: dconf key for which the value should be set. Should be a full path.
        :type key: str

        :param value: Value to set for the specified dconf key. Should be specified in GVariant format.
        :type value: str

        :returns: bool -- True if a change was made, False if no change was required.
        """

        # If no change is needed, exit early
        if self.read(key) == self.normalize_value(value):
            return False

        # If running in check mode, just notify user
        if self.check_mode:
            return True

        # Set up command to run
        command = ["dconf", "write", key, value]

        # Run the command wrapped in dbus-launch
        dbus_wrapper = DBusWrapper(self.module)
        rc, out, err = dbus_wrapper.run_command(command)

        # Handle command failure
        if rc != 0:
            self.module.fail_json(msg='dconf failed while write the value with error: %s' % err)

        # Value was changed.
        return True

    def reset(self, key):
        """
        Returns value for the specified key (removes it from user configuration).

        If an error occurs, a call will be made to AnsibleModule.fail_json.

        :param key: dconf key to reset. Should be a full path.
        :type key: str

        :returns: bool -- True if a change was made, False if no change was required.
        """

        # Check whether key is a directory
        is_directory = key.endswith('/')

        # Read the current value first.
        if is_directory:
            current_value = self.dump(key)
        else:
            current_value = self.read(key)

        # Key is not set, so no change is needed
        if current_value is None:
            return False

        # If we are in check mode, just notify the user
        if self.check_mode:
            return True

        # Set up command to run
        command = ["dconf", "reset"]

        if is_directory:
            command.append("-f")

        command.append(key)

        # Run the command wrapped in dbus-launch
        dbus_wrapper = DBusWrapper(self.module)
        rc, out, err = dbus_wrapper.run_command(command)

        # Handle command failure
        if rc != 0:
            self.module.fail_json(msg='dconf failed while reseting the value with error: %s' % err)

        # Value was changed.
        return True

    def load(self, key, content):
        """
        Loads all the values from content under the dconf key.

        Ignores any locked non-writable keys.

        If there are any current values under the provided keys, and those are
        different, the key is initially reset to assume defaults for unspecified
        keys.

        If an error occurs, a call will be made to AnsibleModule.fail_json.

        :param key: dconf key to load content under. Must end with `/`.
        :type key: str

        :param content: values to load under the provided key. Must be in the correct dconf format.
        :type key: str

        :returns: bool -- True if a change was made, False if no change was required.
        """
        # Get current values first
        current_values = self.dump(key)

        # Exit early if no change is needed
        if current_values == self.normalize_value(content):
            return False

        # If in check mode, just notify user a change will be performed
        if self.check_mode:
            return True

        # First reset the key to assume defaults for unspecified sub-keys
        if current_values:
            self.reset(key)

        # Set up the command to run
        command = ["dconf", "load", "-f", key]

        # Run the command wrapped in dbus-launch
        dbus_wrapper = DBusWrapper(self.module)
        rc, out, err = dbus_wrapper.run_command(command, data=content)

        # Handle command failure
        if rc != 0:
            fail_msg_lines = []
            fail_msg_lines.append('dconf failed to load values under %(key)s with error: %(error)s' % {"key": key, "error": err})

            # Attempt to restore old values
            rc, _, err = dbus_wrapper.run_command(command, data=current_values)

            # Handle recovery failure
            if rc != 0:
                fail_msg_lines.append('dconf failed to restore values under %(key)s with error: %(error)s' % {"key": key, "error": err})

                # Attempt to back up old values into a regular file
                try:
                    with open('recovery.dconf') as file:
                        file.write(current_values)

                    fail_msg_lines.append('saved previous values under %(key)s in file: %(path)s' % {"key": key, "path": os.path.realpath(file.name)})
                except OSError:
                    fail_msg_lines.append('dconf failed to restore values under %(key)s with error: %(error)s' % {"key": key, "error": err})
                    fail_msg_lines.append('previous values under %(key)s:' % {"key": key})
                    fail_msg_lines.append(current_values)

            # Print error messages
            fail_msg = os.linesep.join(fail_msg_lines)
            self.module.fail_json(msg=fail_msg)

            return None

        return True


def main():
    # Setup the Ansible module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent', 'read']),
            key=dict(required=True, type='str'),
            value=dict(required=False, default=None, type='str'),
            content=dict(required=False, default=None, type='str'),
        ),
        supports_check_mode=True
    )

    # Fail quickly if psutil is not available
    if not psutil_found:
        module.fail_json(msg=missing_required_lib("psutil"), exception=PSUTIL_IMP_ERR)

    # Extract params
    state = module.params['state']
    key = module.params['key']
    value = module.params['value']
    content = module.params['content']

    is_directory = key.endswith('/')

    # If present state was specified, and key does not end in `/`, value must be provided.
    if state == 'present' and not is_directory and value is None:
        module.fail_json(msg='State "present" with key not ending in "/" requires "value" to be set.')

    # If present state was specified, and key ends in `/`, content must be provided.
    if state == 'present' and is_directory and content is None:
        module.fail_json(msg='State "present" with key ending in "/" requires "content" to be set.')

    # Create wrapper instance.
    dconf = DconfPreference(module, module.check_mode)

    # Process based on different states.
    if state == 'read' and not is_directory:
        value = dconf.read(key)
        module.exit_json(changed=False, value=value)
    elif state == 'read' and is_directory:
        value = dconf.dump(key)
        module.exit_json(changed=False, value=value)
    elif state == 'present' and not is_directory:
        changed = dconf.write(key, value)
        module.exit_json(changed=changed)
    elif state == 'present' and is_directory:
        changed = dconf.load(key, content)
        module.exit_json(changed=changed)
    elif state == 'absent':
        changed = dconf.reset(key)
        module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
