#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 - Matthias Hollerbach <mail@matthias-hollerbach.de>
# Copyright (c) 2018 - Etienne Desautels <etienne.desautels@gmail.com>
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
    - Etienne Desautels (@etienned)
short_description: Manipulates macOS preferences including complex data types
version_added: "2.6"
description:
    - This module allows users to create, read, update, and delete system
      and application preferences on macOS including deeply nested dictionary
      values like those in the C(com.apple.finder) domain.
    - It also provides a convenient C(merge) strategy for assignments in
      nested dictionaries so that users can very specifically target nested
      keys without having to assign unchanged peer or parent values.
requirements:
    - Target machine should be running macOS
    - PyObjc python module (preinstalled when using system python since macOS 10.5 Leopard).
      When using python 3 you have to install PyObjc manually.
options:
    domain:
        description:
            - The preference domain. E.g. C(com.apple.finder), C(/path/to/some.plist), C(NSGlobalDomain).
        required: false
        default: NSGlobalDomain
    user:
        description:
            - The user on which the preference will be applied.
              C(anyUser) will set the preference for all users on the machine.
            - See U(https://developer.apple.com/library/content/documentation/CoreFoundation/Conceptual/CFPreferences/Concepts/PreferenceDomains.html)
              for further information.
        required: false
        default: currentUser
        choices: ["anyUser", "currentUser"]
    host:
        description:
            - The host on which the preference should apply. Most Apple preferences
              live in the C(anyHost) domain.
            - See U(https://developer.apple.com/library/content/documentation/CoreFoundation/Conceptual/CFPreferences/Concepts/PreferenceDomains.html)
              for further information.
        required: false
        default: anyHost
        choices: ["anyHost", "currentHost"]
    key:
        description:
            - The key of the preference. Nested values can be accessed by giving all
              keys and indexes separated by colons (:). Indexes are zero-based
              (see Notes for special cases).
        required: false
    type:
        description:
            - The type of the value to write. If unspecified, I(type) will
              be deduced mostly the same way YAML casts types (see Notes for special cases).
        default: null
        choices: ["array", "bool", "boolean", "data", "date", "dict", "float", "real", "int", "integer", "string"]
    value:
        description:
            - The value that will be set for the specified key.
              If C(value) is omitted and C(state) is not C(absent), the preference value of C(key) will be returned.
        required: false
    state:
        description:
            - The state of the preference.
              c(merge) performs a deep merge of dictionaries and arrays.
        default: repace
        choices: ["replace", "merge", "absent"]
notes:
    - macOS caches preferences aggressively. This module should take care of
      updating caches but in some cases you may need to logout and login to
      apply the changes.
    - Check mode can be use with this module.
    - Nested keys need to be quoted when use in abbreviated form
      (because they contains colons and that messes with the syntax).
    - Dates need to be quoted.
    - First level (not nested) quoted boolean, integers and floats are
      converted to boolean, integer and float unless C(type) is specified.
    - Lists and dicts can't be given as C(value) in C(key=argument) form.
    - Binary data needs to be encoded in base64.
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
    key: FK_StandardViewSettings:IconViewSettings
    value:
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


# Set the nested key arrangeBy in abbreviated form (nested keys need to be quoted).
- macos_pref: { domain: com.apple.finder, key: 'DesktopViewSettings:IconViewSettings:arrangeBy', value: dateModified }


# Set ListViewSettings key to complex nested values.
- macos_pref:
    domain: com.apple.finder
    key: ComputerViewSettings:ListViewSettings
    value:
      iconSize: 16
      sortColumn: name
        - textSize: 12
        - columns:
            - comments:
                - ascending: true
'''

RETURN = '''
value:
    description: The value associated with the preference domain and key.
                 Return type is a python object that maps closest to the data type of the macOS preference.
                 This can be an integer, float, string, dict, list, etc...
    type: string
    returned: when C(state) is not C(absent) and C(value) is not given
    sample: "{'CustomViewStyleVersion': 1}"
'''

from base64 import b64decode
import collections
import copy
import calendar
import contextlib
import datetime
import os
import re
import string

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import integer_types, string_types, binary_type, text_type

try:
    import CoreFoundation
    import Foundation
except ImportError:
    pyobjc_found = False
else:
    pyobjc_found = True


# Regular expression that match datetime formats. Should match mostly the
# same formats that YAML supports.
RE_DATETIME = re.compile(r"""
    # year-month-day
    (?P<year>\d{4})-(?P<month>[0-1]?[0-9])-(?P<day>[0-3]?[0-9])
    # start of optional time section
    (?:
        # time separator
        (?:\ +|[Tt])
        # hour-minute-second
        (?P<hour>[0-2]?[0-9]):(?P<minute>[0-5][0-9]):(?P<second>[0-5][0-9])
        # optional microsecond
        (?:\.(?P<microsecond>\d*))?
        # optional timezone info
        (?P<timezone>\ *Z|\ *[-+][0-2]?[0-9](?::?[0-5][0-9])?)?
    )?$
""", re.VERBOSE)


def string_to_datetime(value):
    """
    Convert a date and time string to a datetime object.
    String need to be similar to the Combined date and time ISO 8601 form
    (YYYY-MM-DDThh:mm:ss+00:00).
    Local timezone offset will be added to dates without timezone.
    """
    if not isinstance(value, string_types):
        raise ValueError('Value need to be a string.')

    match = RE_DATETIME.match(value)
    if match:
        timezone = match.group('timezone')
        offset = None

        if timezone:
            timezone = timezone.lstrip()
            if timezone == 'Z':
                offset = 0
            else:
                if ':' in timezone:
                    hour, minute = timezone.split(':')
                elif len(timezone) > 3:
                    hour, minute = timezone[0:3], timezone[3:5]
                else:
                    hour, minute = timezone, 0
                sign, hour = hour[0], hour[1:]
                offset = ((int(hour) * 60) + int(minute)) * 60
                if sign == '-':
                    offset = -offset

        local_datetime = datetime.datetime(
            int(match.group('year')),
            int(match.group('month')),
            int(match.group('day')),
            int(match.group('hour')) if match.group('hour') else 0,
            int(match.group('minute')) if match.group('minute') else 0,
            int(match.group('second')) if match.group('second') else 0,
            # Skip microsecond because they are unsupported in CF.
            0,
        )

        class Offset(datetime.tzinfo):
            def __init__(self, local_datetime, offset=None):
                if offset is None:
                    # Get local timezone offset for the specified date.
                    timestamp = calendar.timegm(local_datetime.timetuple())
                    local_datetime = datetime.datetime.fromtimestamp(timestamp)
                    utc_datetime = datetime.datetime.utcfromtimestamp(timestamp)
                    self.__offset = local_datetime - utc_datetime
                else:
                    self.__offset = datetime.timedelta(0, offset)

            def utcoffset(self, dt=None):
                return self.__offset

        timezone = Offset(local_datetime, offset)

        return local_datetime.replace(tzinfo=timezone)

    raise ValueError(
        'Invalid string format for datetime: `{0}`'.format(value)
    )


def equivalent_types(value1, value2):
    """
    Compare type of two values and return if they are equivalent or not.

    Objective-C types are considered equivalent to their corresponding
    python types.
    For example, `objc.pyobjc_unicode` is equivalent to `unicode`.
    """
    supported_types = (
        bool,
        integer_types,
        float,
        (text_type, binary_type),
        datetime.datetime,
        Data,
        list,
        dict,
    )
    for value_type in supported_types:
        if isinstance(value1, value_type) and isinstance(value2, value_type):
            return True
    return False


class Data(binary_type):
    """
    Object representing binary data.
    Instance should be initialized with binary data encoded in base64 codec.
    """
    # List of all base64 characters.
    BASE64_CHARS = string.ascii_letters + string.digits + '+/='

    # List of all text characters.
    TEXT_CHARS = bytearray(set([7, 8, 9, 10, 12, 13, 27]) | set(range(0x20, 0x100)) - set([0x7f]))

    def __new__(cls, data):
        if isinstance(data, cls):
            return data

        # Try to convert unicode to ascii string.
        if isinstance(data, text_type):
            try:
                data = data.encode('ascii')
            except UnicodeEncodeError:
                pass

        # Check if data is a valid base64 string. Short strings are not
        # considered as binary.
        if isinstance(data, binary_type) and len(data) > 51 and not data.decode().translate({ord(c): None for c in cls.BASE64_CHARS}):
            try:
                binary_data = b64decode(data)
            except TypeError:
                pass
            else:
                if cls.is_binary(binary_data):
                    return super(Data, cls).__new__(cls, data)

        raise ValueError('Unsupported data type.')

    @classmethod
    def is_binary(cls, data):
        """ Check if data looks like binary data and not textual data. """
        if b'\x00' in data:
            return True
        # Check only first 512 characters.
        data = data[:512]
        # If more than 30% are non-text characters, then this is considered
        # binary data.
        return len(data.translate({ord(c): None for c in cls.TEXT_CHARS})) / float(len(data)) > .3

    @property
    def binary(self):
        return b64decode(self)


class CFPreferences(object):
    """
    Read, write and delete value for specified keys and indexes from macOS
    Preferences files (.plist). It's possible to access nested values and to
    write complex nested values. All types in written nested values should be
    supported by the .plist format: bool, int, float, unicode, datetime,
    binary data (as base64 string), list and dict.

    This class uses CoreFoundation python binding to access .plist.
    """
    global pyobjc_found

    def __init__(self, domain, user=None, host=None):

        if not pyobjc_found:
            raise ImportError("The PyObjC python module was not found.")

        self.domain = domain

        if user == "currentUser" or user is None:
            self.user = Foundation.kCFPreferencesCurrentUser
        elif user == "anyUser":
            self.user = Foundation.kCFPreferencesAnyUser

        if host == "anyHost" or host is None:
            self.host = Foundation.kCFPreferencesAnyHost
        elif host == "currentHost":
            self.host = Foundation.kCFPreferencesCurrentHost

    @property
    def domain(self):
        return self._domain

    @domain.setter
    def domain(self, domain):
        # Be sure domain is a string/unicode. If not, that will trigger
        # a "Trace/BPT trap" crash.
        if not isinstance(domain, string_types):
            raise TypeError('Domain should be a string or unicode.')
        if domain == 'NSGlobalDomain':
            domain = Foundation.kCFPreferencesAnyApplication
        self._domain = domain

    def read(self, key_string):
        """
        Read a preference value for the specified key. Nested values can be
        access by giving all keys and indexes, separated by colons (:).
        Indexes are zero-based.

        Example: 'NSToolbar Configuration Browser:TB Item Identifiers:1'

        Here we assume that the plist root is a dict, not an array. So first
        key's level should always be a key (string) not an index (int).
        """
        # Can't pass an array index to CFPreferencesCopyAppValue,
        # we could probably read the entire plist in this case.

        keys = self._split_keys(key_string)
        # Get value/structure of the first level key.
        if self._is_current_app_and_user():
            value = CoreFoundation.CFPreferencesCopyAppValue(
                keys[0], self.domain
            )
        else:
            value = CoreFoundation.CFPreferencesCopyValue(
                keys[0], self.domain, self.user, self.host
            )
        # If there's more then one key level, follow the structure until the
        # last level is reach or return None if some substructures are missing.
        for key in keys[1:]:
            try:
                value = value[key]
            except (KeyError, IndexError, TypeError, ValueError):
                return None

        value = self._cf_to_py(value)
        return value

    def write(self, key_string, value, merge=False):
        """
        Write a preference value for the specified key. Nested values can be
        written by giving all keys and indexes separated by colons (:).
        Indexes are zero-based.

        Example: 'NSToolbar Configuration Browser:TB Item Identifiers:1'

        It's possible to write complex nested values. All types in written
        nested values should be supported by the .plist format: bool, int,
        float, unicode, datetime, binary data (as base64 string), list
        and dict.

        With array_add argument as True value can be an item or a list.
        Item will be appended to the current array and list will extend
        current array.
        """
        keys = self._split_keys(key_string)
        last_key = keys[-1]
        root = node = self._get_tree(keys)

        # Add lists and dicts that are missing.
        for key, next_key in zip(keys, keys[1:]):
            self._validate_key_node(key, node)

            # Add missing list and dict.
            if isinstance(node, list):
                if key > len(node):
                    raise IndexError(
                        'Index {0} in key `{1}` out of range.'
                        .format(key, key)
                    )
                if key == len(node):
                    node.append([] if isinstance(next_key, int) else {})
            elif key not in node:
                node[key] = [] if isinstance(next_key, int) else {}

            node = node[key]
        self._validate_key_node(last_key, node)

        # If index doesn't exist, raise error except if it's the next one.
        if isinstance(node, list) and last_key > len(node):
            raise IndexError(
                'Index {0} in key `{1}` out of range.'
                .format(last_key, key)
            )
        # Value is present.
        if (
            (isinstance(node, list) and last_key < len(node))
            or (not isinstance(node, list) and last_key in node)
        ):
            if not equivalent_types(node[last_key], value):
                raise TypeError(
                    'New value type does not match current value type for key '
                    '{0} ({1!r} {2} -> {3!r} {4}).'
                    .format(
                        last_key, value, type(value),
                        node[last_key], type(node[last_key])
                    )
                )
            if merge:
                self._deep_merge(node[last_key], value)
            else:
                node[last_key] = value
        # Value not present.
        else:
            # Handle array.
            if isinstance(node, list):
                node.append(value)
            # Handle dict.
            else:
                node[last_key] = value

        # Update the plist.
        value = root[keys[0]]
        self._set_plist(keys[0], value)

    def delete(self, key):
        """
        Delete a preference value for the specified key. Nested values can be
        access by giving all keys and indexes, separated by colons (:).
        Indexes are zero-based.

        Example: 'NSToolbar Configuration Browser:TB Item Identifiers:1'

        Here we assume that the plist root is a dict, not an array. So first
        key's level should always be a key (string) not an index (int).

        If the key doesn't exists this function return None.
        """
        keys = self._split_keys(key)
        root = node = self._get_tree(keys)

        for key in keys[:-1]:
            try:
                node = node[key]
            except (IndexError, KeyError, TypeError, ValueError):
                # That means there's nothing to delete.
                return

        last_key = keys[-1]
        key_type = list if isinstance(last_key, int) else dict
        if not isinstance(node, key_type):
            # That means there's nothing to delete.
            return

        if isinstance(node, list):
            if last_key < len(node):
                node.pop(last_key)
        elif last_key in node:
            del node[last_key]

        # Update the plist.
        value = root.get(keys[0])
        self._set_plist(keys[0], value)

    def _deep_merge(self, base, incoming):
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
        # Merge array.
        if isinstance(base, list):
            items_to_add = [
                item for item in incoming if item not in base
            ]
            base.extend(items_to_add)
        # Merge dict.
        else:
            for key, val in incoming.items():
                if (
                    key in base
                    and ((isinstance(val, collections.MutableMapping)
                            and isinstance(base[key], collections.MutableMapping))
                        or (isinstance(val, list)
                            and isinstance(base[key], list)))
                ):
                    self._deep_merge(base[key], val)
                else:
                    base[key] = val

    def _cf_to_py(self, value):
        """
        Return value with all CoreFoundation types converted to their python
        equivalent.
        """
        if isinstance(value, (Foundation.NSMutableDictionary, dict)):
            value = dict(value)
            for key, item in value.items():
                value[key] = self._cf_to_py(item)
        elif isinstance(value, (Foundation.NSMutableArray, list, tuple)):
            value = [self._cf_to_py(item) for item in value]
        elif isinstance(value, Foundation.NSDate):
            value = string_to_datetime(text_type(value))
        elif isinstance(value, Foundation.NSMutableData):
            value = Data(value.base64Encoding())
        return value

    def _py_to_cf(self, value):
        """
        Return value with all python datetime and Data objects converted
        to their CoreFoundation equivalent. Python strings are converted
        to unicode.

        If value contains a type not supported by the .plist format,
        a TypeError will be raised.
        """
        if isinstance(value, dict):
            for key, item in value.items():
                value[key] = self._py_to_cf(item)
        elif isinstance(value, (list, tuple)):
            value = [self._py_to_cf(item) for item in value]
        elif isinstance(value, datetime.datetime):
            value = self._datetime_to_cfdate(value)
        elif isinstance(value, Data):
            value = value.binary
            value = CoreFoundation.CFDataCreate(None, value, len(value))
        elif isinstance(value, binary_type):
            try:
                value = text_type(value, 'utf-8')
            except UnicodeDecodeError:
                raise TypeError(
                    'Invalid string {0} of value `{1}` is unsupported.'
                    .format(type(value), repr(value))
                )
        elif (value is not None and
                not isinstance(value, integer_types) and
                not isinstance(value, (bool, float, text_type))):
            raise TypeError('{0} of value `{1}` is unsupported.'.format(
                type(value), repr(value)
            ))
        return value

    def _datetime_to_cfdate(self, date_time):
        """
        Convert python datetime object to a Core Foundation CFDate object.
        """
        offset = date_time.utcoffset()
        if offset is None:
            # Get local timezone offset when datetime have no timezone.
            timestamp = calendar.timegm(date_time.timetuple())
            local_date_time = datetime.datetime.fromtimestamp(timestamp)
            utc_date_time = datetime.datetime.utcfromtimestamp(timestamp)
            offset = local_date_time - utc_date_time

        # Get timezone offset from datetime object.
        offset = (offset.days * 60 * 60 * 24) + offset.seconds

        # Need to redirect PyObjC errors that are not errors.
        with silence_stderr():
            gregorian_date = CoreFoundation.CFCalendarCreateWithIdentifier(
                None, CoreFoundation.kCFGregorianCalendar
            )
            timezone = CoreFoundation.CFTimeZoneCreateWithTimeIntervalFromGMT(
                None, offset
            )

        CoreFoundation.CFCalendarSetTimeZone(gregorian_date, timezone)
        absolute_time = CoreFoundation.CFCalendarComposeAbsoluteTime(
            gregorian_date, None, "yMdHms",
            date_time.year, date_time.month, date_time.day,
            date_time.hour, date_time.minute, date_time.second
        )[1]
        cfdate = CoreFoundation.CFDateCreate(None, absolute_time)

        return cfdate

    def _split_keys(self, key_string):
        """ Split key string in a list of keys and indexes (as int). """
        if not isinstance(key_string, string_types):
            raise TypeError('Key should be a string. {0} {1}'.format(repr(key_string), type(key_string)))

        keys = [
            int(key) if key.isdigit() else key
            for key in key_string.strip(':').split(':')
        ]

        # Be sure first key is a string. If not, that can trigger
        # a "Trace/BPT trap" crash.
        if not isinstance(keys[0], string_types):
            raise TypeError('First key should be a string.')

        return keys

    def _is_current_app_and_user(self):
        return (self.domain != Foundation.kCFPreferencesAnyApplication and
                self.user != Foundation.kCFPreferencesAnyUser and
                self.host == Foundation.kCFPreferencesAnyHost)

    def _get_tree(self, keys):
        """
        Return the tree that contains all the keys and indexes from the .plist.
        """
        root = {}
        tree = self.read(keys[0])
        if tree is not None:
            root[keys[0]] = tree
        return root

    def _validate_key_node(self, key, node):
        key_type = list if isinstance(key, int) else dict
        if not isinstance(node, key_type):
            raise TypeError(
                'Type mismatch between the key `{0}` and the node `{1}` '
                '({2} -> {3}).'
                .format(key, repr(node), key_type, type(node))
            )

    def _set_plist(self, key, value):
        """ Save the value for the key to the .plist and update the cache. """
        value = self._py_to_cf(value)

        if self._is_current_app_and_user():
            CoreFoundation.CFPreferencesSetAppValue(key, value, self.domain)
            CoreFoundation.CFPreferencesAppSynchronize(self.domain)
        else:
            CoreFoundation.CFPreferencesSetValue(
                key, value, self.domain, self.user, self.host
            )
            CoreFoundation.CFPreferencesSynchronize(
                self.domain, self.user, self.host
            )


@contextlib.contextmanager
def silence_stderr():
    """ Prevent standard error from the PyObjC bridge to show up. """
    dev_null = os.open(os.devnull, os.O_RDWR)
    save_stderr = os.dup(2)
    os.dup2(dev_null, 2)
    yield
    os.dup2(save_stderr, 2)
    os.close(dev_null)


class MacOSPrefException(Exception):
    pass


class MacOSPref(object):
    def __init__(self, domain, user, host, key, type, value, state, check_mode):

        try:
            self.prefs = CFPreferences(domain=domain, user=user, host=host)
        except Exception as e:
            raise MacOSPrefException(e.args[0])

        self.key = key
        self.type = type
        self.value = value
        self.state = state
        self.check_mode = check_mode
        if state == 'merge':
            self.merge = True
        else:
            self.merge = False

        # Set initial var values
        self.current_value = None
        self.changed = False
        self.success = True
        self.return_value = None
        self.should_return_value = True

    def _auto_cast_type(self, value, first_level=True):
        """
        Cast booleans, integers and floats given as string on first level (not
        nested) to their proper type. It's currently useful to do this because
        Ansible convert integers and floats found in first level variables to
        string (but in nested structure, integers and floats keep their type).

        Date strings are always cast to datetime objects because dates are
        always given as string (Because JSON does not support datetime type).

        Binary data encoded in base64 is always converted to Data object.

        Strings are always converted to unicode objects.

        It's possible to keep all those cases as string by specifying their
        type: `type: string`.
        """
        if isinstance(value, string_types):
            if first_level:
                if '.' in value:
                    try:
                        return float(value)
                    except ValueError:
                        pass
                else:
                    try:
                        return int(value)
                    except ValueError:
                        pass
                if value.lower() in ('on', 'true', 'yes'):
                    return True
                if value.lower() in ('off', 'false', 'no'):
                    return False

            try:
                return string_to_datetime(value)
            except ValueError:
                pass
            try:
                return Data(value)
            except ValueError:
                pass
            if isinstance(value, binary_type):
                try:
                    return value.decode('utf-8')
                except UnicodeDecodeError:
                    raise MacOSPrefException('String is not valid UTF-8.')
        elif isinstance(value, list):
            return [self._auto_cast_type(item, False) for item in value]
        elif isinstance(value, dict):
            return dict([(key, self._auto_cast_type(item, False)) for key, item in value.items()])

        return value

    def _cast_type(self, value, given_type):
        """
        Try to cast the specified value to the given type.
        """
        supported_types = {
            'array': list,
            'list': list,
            'bool': bool,
            'boolean': bool,
            'data': Data,
            'date': datetime.datetime,
            'dict': dict,
            'float': float,
            'real': float,
            'int': int,
            'integer': int,
            'string': text_type,
            'str': text_type,
        }

        possible_casting = {
            bool: (int, text_type),
            int: (bool, float, text_type),
            float: (bool, int, text_type),
            text_type: (bool, int, float),
            Data: (text_type,),
            datetime.datetime: (text_type,),
        }

        try:
            given_type = supported_types[given_type]
        except KeyError:
            raise MacOSPrefException(
                'Unsupported type specified: <{0}>'.format(given_type)
            )
        if isinstance(value, binary_type):
            try:
                value = value.decode('utf-8')
            except UnicodeDecodeError:
                raise MacOSPrefException('String is not valid UTF-8.')

        if isinstance(value, given_type):
            if given_type in (list, dict):
                return self._auto_cast_type(value)
            return value

        if (value is not None and
                isinstance(value, possible_casting.get(given_type, given_type))):
            if given_type == bool:
                if text_type(value).lower() in ('1', 'on', 'true', 'yes'):
                    return True
                if text_type(value).lower() in ('0', 'off', 'false', 'no'):
                    return False
            elif given_type == datetime.datetime:
                try:
                    return string_to_datetime(value)
                except ValueError:
                    raise MacOSPrefException(
                        'Invalid date value: {0}. Required format '
                        'yyyy-mm-dd hh:mm:ss (or with Timezone).'.format(repr(value)))
            else:
                try:
                    return given_type(value)
                except ValueError:
                    # Let the final error raise.
                    pass

        raise MacOSPrefException(
            "Can't convert value `{0}` of {1} to {2}."
            .format(repr(value), type(value), given_type)
        )

    def run(self):

        # Read the current value
        self.current_value = self.return_value = self.prefs.read(self.key)

        # Delete the key if state is "absent"
        if self.state == "absent":
            self.should_return_value = False
            if self.current_value is None:
                return

            self.changed = True
            self.return_value = None

            if self.check_mode:
                return

            self.prefs.delete(self.key)

        # Write if value is present
        if self.value:
            self.should_return_value = False
            # Cast value type before comparing and writing.
            if self.type:
                self.value = self._cast_type(self.value, self.type)
            else:
                self.value = self._auto_cast_type(self.value)

            # For state=merge, when base is array convert single item to a list.
            if self.merge and isinstance(self.current_value, list) and not isinstance(self.value, list):
                self.value = [self.value]

            # Check if there's a type mismatch.
            if (self.current_value is not None and
                    not equivalent_types(self.current_value, self.value)):
                raise MacOSPrefException(
                    'New value type does not match current value type for key '
                    '{0} ({1!r} {2} -> {3!r} {4}).'
                    .format(
                        self.key, self.value, type(self.value),
                        self.current_value, type(self.current_value)
                    )
                )

            # Check for changes and abort if ther are none
            if self.merge:
                if self.current_value is not None:
                    # compare arrays
                    if isinstance(self.current_value, list):
                        new_items = [
                            item for item in self.value
                            if item not in self.current_value
                        ]
                        if not new_items:
                            return
                    # compare dicts
                    else:
                        new_items = [
                            key for key, val in self.value.items()
                            if key not in self.current_value
                        ]
                        if not new_items:
                            return
            elif self.current_value == self.value:
                return

            self.changed = True

            if self.check_mode:
                return

            # Change/Create/Set given key/value for domain in defaults.
            self.prefs.write(self.key, self.value, self.merge)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            domain=dict(
                default='NSGlobalDomain',
                type='str',
                required=False
            ),
            user=dict(
                default='currentUser',
                choices=[
                    'anyUser',
                    'currentUser'
                ],
                required=False
            ),
            host=dict(
                default='anyHost',
                choices=[
                    'anyHost',
                    'currentHost'
                ],
                required=False
            ),
            key=dict(
                type='str',
                required=True
            ),
            type=dict(
                default=None,
                choices=[
                    'array',
                    'bool',
                    'boolean',
                    'data',
                    'date',
                    'dict',
                    'float',
                    'real',
                    'int',
                    'integer',
                    'string',
                ],
            ),
            value=dict(
                type='raw',
                required=False
            ),
            state=dict(
                default='replace',
                choices=[
                    'replace',
                    'merge',
                    'absent'
                ],
                required=False
            ),
        ),
        supports_check_mode=True
    )

    try:
        macospref = MacOSPref(check_mode=module.check_mode, **module.params)
        macospref.run()
        if macospref.should_return_value:
            module.exit_json(changed=macospref.changed, value=macospref.return_value)
        else:
            module.exit_json(changed=macospref.changed)
    except Exception as e:
        module.fail_json(msg=e.args[0])

if __name__ == '__main__':
    main()
