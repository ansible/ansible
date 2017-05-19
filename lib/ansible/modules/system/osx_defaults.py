#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, GeekChimp - Franck Nijhof <franck@geekchimp.com>
# (c) 2017, Etienne Desautels <etienne.desautels@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: osx_defaults
author: "Franck Nijhof (@frenck), Etienne Desautels (@etienned)"
short_description:
    Allows users to read, write, and delete macOS preferences from Ansible.
description:
  - osx_defaults allows users to read, write, and delete macOS preferences
    from Ansible scripts.
    macOS applications and other programs use the defaults system to record
    user preferences and other information that must be maintained when the
    applications aren't running (such as default font for new documents, or
    the position of an Info panel).
version_added: "2.0"
requirements:
  - Python 2.6+.
  - macOS installed Foundation and CoreFoundation python modules (or from PyObjC).
options:
  domain:
    description:
      - The I(domain) is a domain name of the form com.companyname.appname or
        I(NSGlobalDomain) for the Global Domain.
    default: NSGlobalDomain
  host:
    description:
      - The host on which the preference should apply. The special value "currentHost" corresponds to the
        "-currentHost" switch of the defaults commandline tool.
    version_added: "2.1"
  any_user:
    description:
      - Set the preference for any user or only the current user.
    type: bool
    default: 'no'
    version_added: "2.8"
  key:
    description:
      - The key of the preference. Nested values can be accessed by giving all
        keys and indexes separated by colons (:). Indexes are zero-based
        (see Notes for special cases).
    required: true
  type:
    description:
      - The type of the value to write. If unspecified, I(type) will be deduce mostly
        the same way YAML cast type (see Notes for special cases).
    choices: [ "array", "bool", "boolean", "data", "date", "dict", "float", "real", "int", "integer", "string" ]
  array_add:
    description:
      - Add new elements to the array for a key which has an array as its value.
    type: bool
    default: 'no'
  value:
    description:
      - The value to write. Only required when I(state = present).
  state:
    description:
      - The state of the preference.
    default: present
    choices: [ "present", "absent" ]
notes:
    - macOS caches preferences aggressively. This module should take care of
      updating caches but in some cases you may need to logout and login to
      apply the changes.
    - Check mode can be used with this module.
    - Nested keys must be quoted when specified in abbreviated form
      (e.g. C("DesktopViewSettings:IconViewSettings:arrangeBy")),
      since colons are treated as part of YAML syntax itself.
    - All dates need to be quoted.
    - Microseconds in dates are skipped because they are unsupported in CF.
    - First level (not nested) quoted boolean, integers and floats are
      converted to boolean, integer and float unless type is specified.
    - List and dict can't be given as value in key=argument form.
    - Binary data need to be encoded in base64.
'''

EXAMPLES = '''
# Show debug menu in Safari. Specifying the type.
- osx_defaults:
    domain: com.apple.Safari
    key: IncludeInternalDebugMenu
    type: bool
    value: true
    state: present
# Set Measurement unit to cm for all apps (NSGlobalDomain).
- osx_defaults:
    domain: NSGlobalDomain
    key: AppleMeasurementUnits
    type: str
    value: Centimeters
    state: present
# Set clock visibility on screensaver for all users on current host.
- osx_defaults:
    domain: com.apple.screensaver
    host: currentHost
    any_user: true
    key: showClock
    type: int
    value: 1
# Set Measurement unit to cm for all apps (NSGlobalDomain). No type specified.
- osx_defaults:
    key: AppleMeasurementUnits
    type: str
    value: Centimeters
# Set AppleLanguages to a list of languages.
- osx_defaults:
    key: AppleLanguages
    value: ["en", "nl"]
# Remove a key.
- osx_defaults:
    domain: com.geekchimp.macable
    key: ExampleKeyToRemove
    state: absent
# Set a date. Dates need to be quoted. Timezone can be omitted. Local timezone will be use in this case.
- osx_defaults:
    domain: com.geekchimp.macable
    key: SomeDate
    value: "2002-12-15 02:59:43Z"
# Set the nested key arrangeBy in abbreviated form (nested key need to be quoted).
- osx_defaults: { domain: com.apple.finder, key: 'DesktopViewSettings:IconViewSettings:arrangeBy', value: dateModified }
# Set ListViewSettings key to complex nested values.
- osx_defaults:
    domain: com.apple.finder
    key: ComputerViewSettings:ListViewSettings
    value:
        - iconSize: 16
        - sortColumn: name
        - textSize: 12
        - columns:
            - comments:
                - ascending: true
'''


from base64 import b64decode
import calendar
import contextlib
import datetime
import os
import re
import string

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types, binary_type, text_type
from ansible.module_utils.six import integer_types

try:
    import CoreFoundation
    import Foundation
    has_foundation = True
except ImportError:
    has_foundation = False


# Regular expression that match datetime formats. Should match mostly the
# same formats that YAML support. This regex is adapted from the one defined
# in the YAML specifications <http://yaml.org/type/timestamp.html>.
# It is also almost conforming to the ISO 8601 format
# <https://en.wikipedia.org/wiki/ISO_8601>.
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
                    offset *= -1

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
    Instance should be initialize with binary data encoded in base64 codec.
    """
    # List of all Base64 accepted characters.
    BASE64_CHARS = (
        string.ascii_letters + string.digits + '+/='
    ).encode('ascii')

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
        if isinstance(data, binary_type) and len(data) > 51 and not data.translate(None, cls.BASE64_CHARS):
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
        return len(data.translate(None, cls.TEXT_CHARS)) / float(len(data)) > 0.3

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

    def __init__(self, domain, any_user=False, host=None):
        """
        Domain should be the identifier of the application whose preferences to
        read or modify. Takes the form of a Java package name, com.foosoft.app
        or `NSGlobalDomain` for global domain. `any_user` control if the
        preference is for the current user only (default) or for any user.
        `host` control if the preference is for the current host only or for
        any host (default).
        """
        if any_user:
            self.user = Foundation.kCFPreferencesAnyUser
        else:
            self.user = Foundation.kCFPreferencesCurrentUser

        if host == 'currentHost':
            self.host = Foundation.kCFPreferencesCurrentHost
        elif host is None:
            self.host = Foundation.kCFPreferencesAnyHost
        else:
            # Keep it to be backward compatible, but that not look to be really
            # supported by the API. Behavior of defaults with host given as a
            # string look undefined anyway. Should probably be remove in the
            # future if nobody prove it's actually functional.
            self.host = host

        self.domain = domain

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

    def read(self, key):
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

        keys_n_idxs = self._split_keys_n_idxs(key)
        # Get value/structure of the first level key.
        if self._is_current_app_and_user():
            value = CoreFoundation.CFPreferencesCopyAppValue(
                keys_n_idxs[0], self.domain
            )
        else:
            value = CoreFoundation.CFPreferencesCopyValue(
                keys_n_idxs[0], self.domain, self.user, self.host
            )
        # If there's more then one key level, follow the structure until the
        # last level is reach or return None if some substructures are missing.
        for key_or_idx in keys_n_idxs[1:]:
            try:
                value = value[key_or_idx]
            except (KeyError, IndexError, TypeError, ValueError):
                return None

        value = self._normalize_to_python(value)
        return value

    def write(self, key, value, array_add=False):
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
        keys_n_idxs = self._split_keys_n_idxs(key)
        root = node = self._get_tree(keys_n_idxs)

        # Add list and dict that are missing.
        for key_or_idx, next_key_or_idx in zip(keys_n_idxs, keys_n_idxs[1:]):
            self._validate_key_node(key_or_idx, node)

            # Add missing list and dict.
            if isinstance(node, list):
                if key_or_idx > len(node):
                    raise IndexError(
                        'Index {0} in key `{1}` out of range.'
                        .format(key_or_idx, key)
                    )
                if key_or_idx == len(node):
                    node.append([] if isinstance(next_key_or_idx, int) else {})
            elif key_or_idx not in node:
                node[key_or_idx] = [] if isinstance(next_key_or_idx, int) else {}

            node = node[key_or_idx]

        # Set final value.
        last_key_or_idx = keys_n_idxs[-1]
        self._validate_key_node(last_key_or_idx, node)

        if array_add:
            if isinstance(node, list):
                # If index doesn't exist, raise error except if it's the next one.
                if last_key_or_idx > len(node):
                    raise IndexError(
                        'Index {0} in key `{1}` out of range.'
                        .format(last_key_or_idx, key)
                    )
                if last_key_or_idx == len(node):
                    node.append([])
            else:  # it's a dict.
                if last_key_or_idx not in node:
                    node[last_key_or_idx] = []

            if not isinstance(node[last_key_or_idx], list):
                raise TypeError(
                    "With array_add end node should be a list and it's not."
                )
            # Add only items that are not already present in the current list,
            # and preserve order.
            items_to_add = [
                item for item in value if item not in node[last_key_or_idx]
            ]
            node[last_key_or_idx].extend(items_to_add)

        elif isinstance(node, list):
            # If index doesn't exist, raise error except if it's the next one.
            if last_key_or_idx > len(node):
                raise IndexError(
                    'Index {0} in key `{1}` out of range.'
                    .format(last_key_or_idx, key)
                )
            if last_key_or_idx == len(node):
                node.append(value)
            elif equivalent_types(node[last_key_or_idx], value):
                node[last_key_or_idx] = value
            else:
                raise TypeError(
                    'New value type does not match current value type for key '
                    '{0} ({1!r} {2} -> {3!r} {4}).'
                    .format(
                        last_key_or_idx, value, type(value),
                        node[last_key_or_idx], type(node[last_key_or_idx])
                    )
                )

        else:  # it's a dict.
            if (last_key_or_idx in node and not
                    equivalent_types(node[last_key_or_idx], value)):
                raise TypeError(
                    'New value type does not match current value type for key '
                    '{0} ({1!r} {2} -> {3!r} {4}).'
                    .format(
                        last_key_or_idx, value, type(value),
                        node[last_key_or_idx], type(node[last_key_or_idx])
                    )
                )
            node[last_key_or_idx] = value

        # Update the plist.
        value = root[keys_n_idxs[0]]
        self._set_plist(keys_n_idxs[0], value)

    def delete(self, key):
        """
        Delete a preference value for the specified key. Nested values can be
        access by giving all keys and indexes, separated by colons (:).
        Indexes are zero-based.

        Example: 'NSToolbar Configuration Browser:TB Item Identifiers:1'

        Here we assume that the plist root is a dict, not an array. So first
        key's level should always be a key (string) not an index (int).

        If the key doesn't exist this function return None.
        """
        keys_n_idxs = self._split_keys_n_idxs(key)
        root = node = self._get_tree(keys_n_idxs)

        for key_or_idx in keys_n_idxs[:-1]:
            try:
                node = node[key_or_idx]
            except (IndexError, KeyError, TypeError, ValueError):
                # That means there's nothing to delete.
                return

        last_key_or_idx = keys_n_idxs[-1]
        key_or_idx_type = list if isinstance(last_key_or_idx, int) else dict
        if not isinstance(node, key_or_idx_type):
            # That means there's nothing to delete.
            return

        if isinstance(node, list):
            if last_key_or_idx < len(node):
                node.pop(last_key_or_idx)
        elif last_key_or_idx in node:
            del node[last_key_or_idx]

        # Update the plist.
        value = root.get(keys_n_idxs[0])
        self._set_plist(keys_n_idxs[0], value)

    def _normalize_to_python(self, value):
        """
        Return value with all Foundation types converted to their python
        equivalent.
        """
        if isinstance(value, (Foundation.NSMutableDictionary, dict)):
            value = dict(value)
            for key, item in value.items():
                value[key] = self._normalize_to_python(item)
        elif isinstance(value, (Foundation.NSMutableArray, list, tuple)):
            value = [self._normalize_to_python(item) for item in value]
        elif isinstance(value, Foundation.NSDate):
            value = string_to_datetime(text_type(value))
        elif isinstance(value, Foundation.NSMutableData):
            value = Data(value.base64Encoding())
        return value

    def _normalize_to_cf(self, value):
        """
        Return value with all python datetime and Data objects converted
        to their CoreFoundation equivalent. Python strings are converted
        to unicode.

        If value contains a type not supported by the .plist format,
        a TypeError will be raise.
        """
        if isinstance(value, dict):
            for key, item in value.items():
                value[key] = self._normalize_to_cf(item)
        elif isinstance(value, (list, tuple)):
            value = [self._normalize_to_cf(item) for item in value]
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
            gregorian_date, None, b"yMdHms",
            date_time.year, date_time.month, date_time.day,
            date_time.hour, date_time.minute, date_time.second
        )[1]
        cfdate = CoreFoundation.CFDateCreate(None, absolute_time)

        return cfdate

    def _split_keys_n_idxs(self, key_string):
        """ Split key string in a list of keys and indexes (as int). """
        if not isinstance(key_string, string_types):
            raise TypeError('Key should be a string. {0} {1}'.format(repr(key_string), type(key_string)))

        keys_n_idxs = [
            int(key_or_idx) if key_or_idx.isdigit() else key_or_idx
            for key_or_idx in key_string.strip(':').split(':')
        ]

        # Be sure first key is a string. If not, that can trigger
        # a "Trace/BPT trap" crash.
        if not isinstance(keys_n_idxs[0], string_types):
            raise TypeError('First key should be a string.')

        return keys_n_idxs

    def _is_current_app_and_user(self):
        return (self.domain != Foundation.kCFPreferencesAnyApplication and
                self.user != Foundation.kCFPreferencesAnyUser and
                self.host == Foundation.kCFPreferencesAnyHost)

    def _get_tree(self, keys_n_idxs):
        """
        Return the tree that contains all the keys and indexes from the .plist.
        """
        root = {}
        tree = self.read(keys_n_idxs[0])
        if tree is not None:
            root[keys_n_idxs[0]] = tree
        return root

    def _validate_key_node(self, key_or_idx, node):
        key_or_idx_type = list if isinstance(key_or_idx, int) else dict
        if not isinstance(node, key_or_idx_type):
            raise TypeError(
                'Type mismatch between the key `{0}` and the node `{1}` '
                '({2} -> {3}).'
                .format(key_or_idx, repr(node), key_or_idx_type, type(node))
            )

    def _set_plist(self, key, value):
        """ Save the value for the key to the .plist and update the cache. """
        value = self._normalize_to_cf(value)

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


class OSXDefaultsException(Exception):
    pass


class OSXDefaults(object):
    """
    Class to manage macOS user defaults.
    """

    def __init__(self, **kwargs):
        """ Prepare and validate the parameters. """

        self.current_value = None

        # Set all given parameters.
        for key, value in kwargs.items():
            setattr(self, key, value)

        # When state is present, we require a value.
        if self.state == 'present' and self.value is None:
            raise OSXDefaultsException('Missing value parameter.')

        if self.state == 'absent' and self.array_add:
            raise OSXDefaultsException('Cannot use `array_add` with `absent`.')

    def _auto_cast_type(self, value, first_level=True):
        """
        Cast booleans, integers and floats given as string on first level (not
        nested) to their proper type. It's currently useful to do this because
        Ansible convert integers and floats found in first level variables to
        string (but in nested structure, integers and floats keep their type).

        Date strings are always cast to datetime objects because dates are
        always given as string (Because JSON do not support datetime type).

        Binary data encoded in base64 is always converted to Data object.

        Strings are always converted to unicode objects.

        It's possible to keep all those cases as string by specifying their
        type: `type: string`.
        """
        if isinstance(value, (text_type, binary_type)):
            if first_level and isinstance(value, string_types):
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
                    raise OSXDefaultsException('String is not valid UTF-8.')
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
            raise OSXDefaultsException(
                'Unsupported type specified: <{0}>'.format(given_type)
            )
        if isinstance(value, binary_type):
            try:
                value = value.decode('utf-8')
            except UnicodeDecodeError:
                raise OSXDefaultsException('String is not valid UTF-8.')

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
                    raise OSXDefaultsException(
                        'Invalid date value: {0}. Required format '
                        'yyyy-mm-dd hh:mm:ss (or with Timezone).'.format(repr(value)))
            else:
                try:
                    return given_type(value)
                except ValueError:
                    # Let the final error raise.
                    pass

        raise OSXDefaultsException(
            "Can't convert value `{0}` of {1} to {2}."
            .format(repr(value), type(value), given_type)
        )

    def run(self):
        preferences = CFPreferences(self.domain, self.any_user, self.host)

        # Get the current value from defaults.
        self.current_value = preferences.read(self.key)

        # Handle absent state.
        if self.state == 'absent':
            if self.current_value is None:
                return False
            if self.module.check_mode:
                return True
            preferences.delete(self.key)
            return True

        # Cast value type before comparing and writing.
        if self.type:
            self.value = self._cast_type(self.value, self.type)
        else:
            self.value = self._auto_cast_type(self.value)

        # For array_add, convert single item to a list.
        if self.array_add and not isinstance(self.value, list):
            self.value = [self.value]

        # Check if there's a type mismatch.
        if (self.current_value is not None and
                not equivalent_types(self.current_value, self.value)):
            raise OSXDefaultsException(
                'New value type does not match current value type for key '
                '{0} ({1!r} {2} -> {3!r} {4}).'
                .format(
                    self.key, self.value, type(self.value),
                    self.current_value, type(self.current_value)
                )
            )

        # When array_add, check if all values to add are already there.
        if self.array_add:
            if self.current_value is not None:
                if not isinstance(self.current_value, list):
                    raise OSXDefaultsException(
                        "With array_add current value at key need to be an array "
                        "but it's {0}.".format(type(self.current_value))
                    )
                new_items = [
                    item for item in self.value
                    if item not in self.current_value
                ]
                if not new_items:
                    return False

        elif self.current_value == self.value:
            return False

        if self.module.check_mode:
            return True

        # Change/Create/Set given key/value for domain in defaults.
        preferences.write(self.key, self.value, self.array_add)
        return True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            domain=dict(
                default='NSGlobalDomain',
            ),
            any_user=dict(
                default=False,
                type='bool',
            ),
            host=dict(
                default=None,
                required=False,
            ),
            array_add=dict(
                default=False,
                type='bool',
            ),
            key=dict(
                required=True,
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
                default=None,
                type='raw',
            ),
            state=dict(
                default='present',
                choices=['absent', 'present'],
            ),
        ),
        supports_check_mode=True,
    )

    if not has_foundation:
        module.fail_json(msg='macOS Foundation and CoreFoundation modules are '
                             'required. Be sure to use the Apple provided '
                             'python on the remote Mac or have installed '
                             'the modules.')

    try:
        defaults = OSXDefaults(module=module, **module.params)
        changed = defaults.run()
        module.exit_json(changed=changed)
    except Exception as e:
        module.fail_json(msg=e.args[0])


if __name__ == '__main__':
    main()
