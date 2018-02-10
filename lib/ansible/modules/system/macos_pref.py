#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 - Matthias Hollerbach <mail@matthias-hollerbach.de>
# Copyright (c) 2016 - John Calixto <john.calixto@nordstrom.com> and Nordstrom, Inc.
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
module: macos_pref
author:
    - Matthias Hollerbach (@kinglouie)
    - John Calixto (@nordjc)
short_description: Manipulates macOS preferences including complex data types
version_added: "2.6"
description:
    - This module allows users to create, read, update, and delete system and application preferences on macOS
      including deeply nested dictionary values like those in the C(com.apple.finder) domain.
    - It also provides a convenient C(merge) strategy for assignments in nested dictionaries so that users can very
      specifically target nested keys without having to assign unchanged peer or parent values.
requirements:
    - Target machine should be running macOS
    - PyObjC (preinstalled by Apple with the operating system since macOS 10.5 Leopard)
options:
    domain:
        description:
            - The preference domain. E.g. C(com.apple.finder), C(/path/to/some.plist), C(NSGlobalDomain).
        required: false
        default: NSGlobalDomain
    user:
        description:
            - The user on which the preference should apply.
        required: false
        default: currentUser
        choices: ["anyUser", "currentUser"]
    host:
        description:
            - The host on which the preference should apply. Most Apple preferences live in the C(anyHost) domain.
            - See U(https://developer.apple.com/library/content/documentation/CoreFoundation/Conceptual/CFPreferences/Concepts/PreferenceDomains.html)
              for further information.
        required: false
        default: anyHost
        choices: ["anyHost", "currentHost"]
    key:
        description:
            - The preference key.
        required: true
    value:
        description:
            - The value that will be set for the specified key. If value is omitted the preference value of C(key) will be returned.
        required: false
    state:
        description:
            - The state of the preference key, C(replace) replaces any existing value with the contents
              of C(value), C(merge) performs a deep merge of nested dictionaries and C(absent) deletes the key if present.
        required: false
        default: replace
        choices: ["replace", "merge", "absent"]
notes:
    - This module uses the Core Foundation Preferences API of macOS directly instead of manipulating plists or passing arguments to `defaults`.
      This ensures that cfprefsd is in the loop when values change.
      It also allows users to retrieve and assign all of the complex data structures supported by the preferences API (e.g. nested dicts).
      The value will be available in the C(value) attribute of the registered variable.
    - To delete a key and its associated value, use C(state=absent).
'''

EXAMPLES = '''
# Set a string key
- name: Set preferred view style
  macos_pref:
    domain: com.apple.finder
    key: FXPreferredViewStyle
    value: Nlsv


# Read a string key
- name: Read preferred view style
  macos_pref:
    domain: com.apple.finder
    key: FXPreferredViewStyle
  register: finder_view_style

- name: Check preferred view style
  fail: msg="Only list view is acceptable!"
  when: finder_view_style.value != 'Nlnv'


# Set a boolean key
- name: Show all files
  macos_pref:
    domain: com.apple.finder
    key: AppleShowAllFiles
    value: true


# Read a boolean key
- name: Show all files
  macos_pref:
    domain: com.apple.finder
    key: AppleShowAllFiles
  register: show_all_files

- name: Check show all files
  fail: msg="Only show all files is acceptable!"
  when: not show_all_files.value


# Set (replace) a dictionary key
- name: Set desktop and finder icon view settings
  macos_pref:
    domain: com.apple.finder
    key: FK_StandardViewSettings
    value:
      IconViewSettings:
        arrangeBy: name
        gridSpacing: 44
        iconSize: 36
        showIconPreview: true
        showItemInfo: false
        labelOnBottom: true
        textSize: 12


# Set (merge) a dictionary key
- name: Set desktop and finder icon size
  macos_pref:
    domain: com.apple.finder
    key: FK_StandardViewSettings
    value:
      IconViewSettings:
        iconSize: 50
    state: merge


# Read a dictionary key
- name: Show all files
  macos_pref:
    domain: com.apple.finder
    key: FK_StandardViewSettings
  register: finder_view_settings

- name: Check show all files
  fail: msg="Only iconSize=50 is acceptable!"
  when: finder_view_settings.value.IconViewSettings.iconSize != 50


# Delete a key
- name: Set Terminal default window settings
  macos_pref:
    domain: com.apple.Terminal
    key: Default Window Settings
    state: absent


# Read directly from a plist file (also works for writing)
- name: Read rumour from file
  macos_pref:
    domain: /tmp/rumours.plist
    key: Rumour
  register: rumour


# Set a dict on currentHost
- name: Set screensaver
  macos_pref:
    domain: com.apple.screensaver
    host: currentHost
    key: moduleDict
    value:
      moduleName: Flurry
      displayName: Flurry
      path: /System/Library/Screen Savers/Flurry.saver
      type: 0
'''

RETURN = '''
value:
    description: The value associated with the preference domain and key.
                 Return type is a python object that maps closest to the data type of the macOS preference.
                 This can be an integer, float, string, dict, list, etc...
                 In case the preference was changed, the new value of C(key) will be returned.
    type: string
    returned: on success
    sample: "{'CustomViewStyleVersion': 1}"
'''

import collections
import copy
import sys
from ansible.module_utils.basic import AnsibleModule

# Ensure that we have access to the pyobjc libraries that Apple ships with
# macOS (e.g. even when using brew-installed python)
try:
    sys.path.insert(0, '/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjc')
    import CoreFoundation
    import Foundation
    from PyObjCTools.Conversion import pythonCollectionFromPropertyList
except ImportError:
    pyobjc_found = False
else:
    pyobjc_found = True


class CFPreferencesException(Exception):
    pass


class CFPreferences(object):

    global pyobjc_found

    def __init__(self, domain, user, host):

        if not pyobjc_found:
            raise CFPreferencesException("The PyObjC python module was not found.")

        self.domain = domain

        if user == "currentUser":
            self.user = Foundation.kCFPreferencesCurrentUser
        elif user == "anyUser":
            self.user = Foundation.kCFPreferencesAnyUser

        if host == "anyHost":
            self.host = Foundation.kCFPreferencesAnyHost
        elif host == "currentHost":
            self.host = Foundation.kCFPreferencesCurrentHost

    def read(self, key):
        if self._is_current_app_and_user():
            value = pythonCollectionFromPropertyList(
                CoreFoundation.CFPreferencesCopyAppValue(key, self.domain)
            )
        else:
            value = pythonCollectionFromPropertyList(
                CoreFoundation.CFPreferencesCopyValue(key, self.domain, self.user, self.host)
            )
        return value

    def delete(self, key):
        self.write(key, None)

    def write(self, key, value, method=None):
        if method == "merge":
            current_value = self.read(key)
            if isinstance(current_value, collections.MutableMapping):
                new = copy.deepcopy(current_value)
                self._deep_merge_dicts(new, value)
        else:
            new = value

        if self._is_current_app_and_user():
            CoreFoundation.CFPreferencesSetAppValue(key, new, self.domain)
            CoreFoundation.CFPreferencesAppSynchronize(self.domain)
        else:
            CoreFoundation.CFPreferencesSetValue(
                key, new, self.domain, self.user, self.host
            )
            CoreFoundation.CFPreferencesSynchronize(
                self.domain, self.user, self.host
            )

    def _is_current_app_and_user(self):
        return (self.domain != Foundation.kCFPreferencesAnyApplication and
                self.user != Foundation.kCFPreferencesAnyUser and
                self.host == Foundation.kCFPreferencesAnyHost)

    def _deep_merge_dicts(self, base, incoming):
        """
        Performs an *in-place* deep-merge of key-values from :attr:`incoming`
        into :attr:`base`. No attempt is made to preserve the original state of
        the objects passed in as arguments.

        :param dict base:  The target container for the merged values. This will
            be modified *in-place*.
        :type base:  Any :class:`dict`-like object

        :param dict incoming:  The container from which incoming values will be
            copied. Nested dicts in this will be modified.
        :type incoming:  Any :class:`dict`-like object

        :rtype:  None

        """
        for ki, vi in incoming.items():
            if (
                ki in base
                and isinstance(vi, collections.MutableMapping)
                and isinstance(base[ki], collections.MutableMapping)
            ):
                self._deep_merge_dicts(base[ki], vi)
            else:
                base[ki] = vi


class MacOSPrefException(Exception):
    pass


class MacOSPref(object):
    def __init__(self, domain, user, host, key, value, state, check_mode):

        try:
            self.prefs = CFPreferences(domain=domain, user=user, host=host)
        except CFPreferencesException as e:
            raise MacOSPrefException(e.message)

        self.key = key
        self.value = value
        self.state = state
        self.check_mode = check_mode

        # Set initial var values
        self.current_value = None
        self.changed = False
        self.success = True
        self.return_value = None

    def run(self):

        self.current_value = self.return_value = self.prefs.read(self.key)

        if self.state == "absent":
            if self.current_value is None:
                return

            self.changed = True
            self.return_value = None

            if self.check_mode:
                return

            self.prefs.delete(self.key)

        elif self.value is not None:
            if self.current_value == self.value:
                return

            self.changed = True
            self.return_value = self.value

            if self.check_mode:
                return

            self.prefs.write(self.key, self.value, self.state)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            domain=dict(
                default="NSGlobalDomain",
                type='str',
                required=False
            ),
            user=dict(
                choices=[
                    "anyUser",
                    "currentUser"
                ],
                default="currentUser",
                required=False
            ),
            host=dict(
                choices=[
                    "anyHost",
                    "currentHost"
                ],
                default="anyHost",
                required=False
            ),
            key=dict(
                type='str',
                required=True
            ),
            value=dict(
                required=False,
                type='raw'
            ),
            state=dict(
                choices=[
                    "replace",
                    "merge",
                    "absent"
                ],
                default="replace",
                required=False
            ),
        ),
        supports_check_mode=True
    )

    try:
        macospref = MacOSPref(
            domain=module.params['domain'],
            user=module.params['user'],
            host=module.params['host'],
            key=module.params['key'],
            value=module.params.get('value'),
            state=module.params['state'],
            check_mode=module.check_mode
        )
        macospref.run()
        module.exit_json(changed=macospref.changed, value=macospref.return_value)
    except MacOSPrefException as e:
        module.fail_json(msg=e.message)

if __name__ == '__main__':
    main()
