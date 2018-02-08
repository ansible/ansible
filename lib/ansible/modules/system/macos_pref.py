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
short_description: Manipulates macOS preferences including complex data types.
version_added: "2.6"
description:
    - This module allows users to create, read, update, and delete system and application preferences on macOS
      including deeply nested dictionary values like those in the C(com.apple.finder) domain.
    - It also provides a convenient C(merge) strategy for assignments in nested dictionaries so that users can very
      specifically target nested keys without having to assign unchanged peer or parent values.
requirements:
    - Target machine should be running macOS
    - PyObjC (preinstalled by Apple with the operating system)
options:
    domain:
        description:
            - The preference domain. E.g. C(com.apple.finder), C(/path/to/some.plist), C(NSGlobalDomain).
        required: false
        default: NSGlobalDomain
    host:
        description:
            - The host on which the preference should apply.
        required: false
        default: anyHost
        choices: ["anyHost", "currentHost"]
    key:
        description:
            - The preference key.
        required: true
    value:
        description:
            - The value that will be set for the specified key.
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
    from Foundation import kCFPreferencesCurrentUser, kCFPreferencesAnyUser, kCFPreferencesCurrentHost, kCFPreferencesAnyHost
    from PyObjCTools.Conversion import pythonCollectionFromPropertyList
except ImportError:
    pyobjc_found = False
else:
    pyobjc_found = True


class MacOSPrefException(Exception):
    pass


class MacOSPref(object):

    global pyobjc_found

    def __init__(self, **kwargs):
        # Exit if PyObjC module is not available
        if not pyobjc_found:
            raise MacOSPrefException("The PyObjC python module is required.")

        # Set all given parameters
        for key, val in kwargs.items():
            setattr(self, key, val)

        # Set initial var values
        self.current_value = None
        self.changed = False
        self.success = True
        self.return_value = None

    def _host_arg(self):
        if self.host == 'currentHost':
            return kCFPreferencesCurrentHost
        else:
            return kCFPreferencesAnyHost

    def read(self):
        self.current_value = get_pref(self.key, self.domain, kCFPreferencesCurrentUser, self._host_arg())
        self.return_value = self.current_value

    def delete(self):
        if self.current_value is None:
            return

        self.changed = True
        self.return_value = None

        if self.module.check_mode:
            return

        set_pref(self.key, None, self.domain)

    def write(self):
        if (isinstance(self.current_value, collections.MutableMapping)
                and self.state == 'merge'):
            new = copy.deepcopy(self.current_value)
            deep_merge_dicts(new, self.value)
        else:
            new = self.value

        if self.current_value == new:
            return

        self.changed = True
        self.return_value = new

        if self.module.check_mode:
            return

        if not set_pref(self.key, new, self.domain, kCFPreferencesCurrentUser, self._host_arg()):
            self.success = False        
    
    def run(self):

        self.read()

        if self.state == "absent":
            self.delete()

        elif self.value is not None:
            self.write()


def deep_merge_dicts(base, incoming):
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
            deep_merge_dicts(base[ki], vi)
        else:
            base[ki] = vi


def get_pref(key, domain, username, hostname):
    return pythonCollectionFromPropertyList(
        CoreFoundation.CFPreferencesCopyValue(key, domain, username, hostname)
    )


def set_pref(key, value, domain, username, hostname):
    CoreFoundation.CFPreferencesSetValue(key, value, domain, username, hostname)
    return CoreFoundation.CFPreferencesAppSynchronize(domain)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            domain=dict(
                default="NSGlobalDomain",
                type='str',
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

    domain = module.params['domain']
    host = module.params['host']
    key = module.params['key']
    value = module.params.get('value')
    state = module.params['state']
    
    try:
        macospref = MacOSPref(module=module, domain=domain,host=host, key=key, value=value, state=state)
        macospref.run()
        module.exit_json(changed=macospref.changed, value=macospref.return_value)
    except MacOSPrefException as e:
        module.fail_json(msg=e.message)

if __name__ == '__main__':
    main()
