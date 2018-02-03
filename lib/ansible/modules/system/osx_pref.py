#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2016 - John Calixto <john.calixto@nordstrom.com> and Nordstrom, Inc.
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

import collections
import copy
import sys

# Ensure that we have access to the pyobjc libraries that Apple shipped with
# the operating system (e.g. even when using brew-installed python)
sys.path.insert(0, '/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjc')
import CoreFoundation
from PyObjCTools.Conversion import pythonCollectionFromPropertyList


DOCUMENTATION = '''
---
module: osx_pref
author: "John Calixto, @nordjc"
version_added: "2.2"
short_description: Manipulates macOS preferences including complex data types
description:
- This module allows users to create, read, update, and delete system and application preferences on macOS including deeply nested dictionary values like those in the C(com.apple.finder) domain.
- It also provides a convenient C(merge) strategy for assignments in nested dictionaries so that users can very specifically target nested keys without having to assign unchanged peer or parent values.
requirements:
- Target machine should be running macOS
- PyObjC (preinstalled by Apple with the operating system)
options:
  domain:
    description:
    - The preference domain.  E.g. com.apple.finder, /path/to/some.plist, NSGlobalDomain
    required: false
    default: NSGlobalDomain
  key:
    description:
    - The preference key.
    required: true
  value:
    description:
    - The value that will be set for the specified key.
    - Required when C(action=set).
    required: false
  action:
    description:
    - Whether to I(get) or I(set) the specified preference.
    required: false
    default: get
    choices: ['get', 'set']
  dict_set_method:
    description:
    - When setting a value to a dictionary, either C(replace) any existing value with the contents of C(value), or perform a deep C(merge) of nested dictionaries.
    required: false
    default: replace
    choices: ['merge', 'replace']
notes:
- This module uses the Core Foundation Preferences API of macOS directly instead of manipulating plists or passing arguments to `defaults`.  This ensures that cfprefsd is in the loop when values change.  It also allows users to retrieve and assign all of the complex data structures supported by the preferences API (e.g. nested dicts).
- To retrieve the value of a key, use C(action=get) and register the result.  The value will be available in the C(value) attribute of the registered variable.
- To delete a key and its associated value, use C(action=set) with C(value=null).
'''


EXAMPLES = '''
# Get basic string value
- name: Discover finder view style
  osx_pref:
    key: FXPreferredViewStyle
    domain: com.apple.finder
    action: get
  register: finder_view_style
- name: Only accept icon view
  fail: msg="Only icons are acceptable!"
  when: "{{ finder_view_style.value != 'icnv' }}"


# Set basic boolean value
- name: Do not show connected servers on desktop
  osx_pref:
    key: ShowMountedServersOnDesktop
    value: false
    domain: com.apple.finder
    action: set


# Set basic string value
- name: Set Terminal default window settings
  osx_pref:
    key: Default Window Settings
    value: Pro
    domain: com.apple.Terminal
    action: set


# Perform deep merge of dictionary keys.  I.e. use any existing values unless
# they are specified in the task below:
- name: Configure finder kit standard view
  osx_pref:
    key: FK_StandardViewSettings
    value:
      IconViewSettings:
        arrangeBy: name
        gridSpacing: 43
        iconSize: 36
        showIconPreview: true
        showItemInfo: false
        labelOnBottom: true
        textSize: 12
    domain: com.apple.finder
    action: set
    dict_set_method: merge


# Read directly from a plist file (also works for writing)
- name: Read rumour from file
  osx_pref:
    key: Rumour
    domain: /tmp/rumours.plist
  register: rumour
'''


RETURN = '''
value:
  description: The value associated with the preference domain and key
  returned: when action=get
  type: Python object that maps closest to the data type of the OS X preference.  This can be an integer, float, string, dict, list, etc...
  sample: "{'CustomViewStyleVersion': 1}"
'''


class PrefActor(object):
    def __init__(self, module):
        self.module = module
        params = module.params
        self.key = params['key']
        self.domain = params['domain']
        self.dict_set_method = params['dict_set_method']
        self.value = params.get('value')
        self.act = getattr(self, params['action'])

    def get(self):
        value = get_pref(self.key, self.domain)
        self.module.exit_json(changed=False, value=value)

    def set(self):
        changed = False
        success = True
        current = get_pref(self.key, self.domain)
        if (isinstance(current, collections.MutableMapping)
                and self.dict_set_method == 'merge'):
            new = copy.deepcopy(current)
            deep_merge_dicts(new, self.value)
        else:
            new = self.value

        if new != current:
            changed = True
            if not self.module.check_mode:
                if not set_pref(self.key, new, self.domain):
                    success = False

        if success:
            self.module.exit_json(changed=changed)
        else:
            self.module.fail_json(changed=changed)


def deep_merge_dicts(base, incoming):
    """
    Performs an *in-place* deep-merge of key-values from :attr:`incoming`
    into :attr:`base`.  No attempt is made to preserve the original state of
    the objects passed in as arguments.

    :param dict base:  The target container for the merged values.  This will
        be modified *in-place*.
    :type base:  Any :class:`dict`-like object

    :param dict incoming:  The container from which incoming values will be
        copied.  Nested dicts in this will be modified.
    :type incoming:  Any :class:`dict`-like object

    :rtype:  None

    """
    for ki, vi in incoming.iteritems():
        if (ki in base
                and isinstance(vi, collections.MutableMapping)
                and isinstance(base[ki], collections.MutableMapping)
                ):
            deep_merge_dicts(base[ki], vi)
        else:
            base[ki] = vi


def get_pref(key, domain):
    return pythonCollectionFromPropertyList(
            CoreFoundation.CFPreferencesCopyAppValue(key, domain)
            )


def set_pref(key, value, domain):
    CoreFoundation.CFPreferencesSetAppValue(key, value, domain)
    return CoreFoundation.CFPreferencesAppSynchronize(domain)


ARG_SPEC = {
        'domain': {
            'default': 'NSGlobalDomain',
            'type': 'str',
            },
        'key': {
            'required': True,
            'type': 'str',
            },
        'value': {},
        'action': {
            'choices': ['get', 'set'],
            'default': 'get',
            },
        'dict_set_method': {
            'choices': ['merge', 'replace'],
            'default': 'replace',
            },
        }


def main():
    module = AnsibleModule(
            argument_spec=ARG_SPEC,
            supports_check_mode=True,
            )
    actor = PrefActor(module)
    actor.act()


from ansible.module_utils.basic import *  # noqa
if __name__ == '__main__':
    main()