#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of Ansible
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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: locale_gen
short_description: Creates or removes locales.
description:
     - Manages locales by editing /etc/locale.gen and invoking locale-gen.
version_added: "1.6"
author: "Augustus Kling (@AugustusKling)"
options:
    name:
        description:
             - Name and encoding of the locale, such as "en_GB.UTF-8".
        required: true
        default: null
        aliases: []
    state:
      description:
           - Whether the locale shall be present.
      required: false
      choices: ["present", "absent"]
      default: "present"
'''

EXAMPLES = '''
# Ensure a locale exists.
- locale_gen:
    name: de_CH.UTF-8
    state: present
'''

from abc import ABCMeta, abstractmethod
import os
import os.path
import re
from subprocess import Popen, PIPE, call

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.six import with_metaclass
from ansible.module_utils._text import to_native


# ===========================================
# location module specific support methods.
#

def is_available_debian(name, ubuntuMode):
    """Check if the given locale is available on the system. This is done by
    checking either :
    * if the locale is present in /etc/locales.gen
    * or if the locale is present in /usr/share/i18n/SUPPORTED"""
    if ubuntuMode:
        __regexp = '^(?P<locale>\S+_\S+) (?P<charset>\S+)\s*$'
        __locales_available = '/usr/share/i18n/SUPPORTED'
    else:
        __regexp = '^#{0,1}\s*(?P<locale>\S+_\S+) (?P<charset>\S+)\s*$'
        __locales_available = '/etc/locale.gen'

    re_compiled = re.compile(__regexp)
    fd = open(__locales_available, 'r')
    for line in fd:
        result = re_compiled.match(line)
        if result and result.group('locale') == name:
            return True
    fd.close()
    return False

def is_present_debian(name):
    """Checks if the given locale is currently installed."""
    output = Popen(["locale", "-a"], stdout=PIPE).communicate()[0]
    output = to_native(output)
    return any(fix_case(name) == fix_case(line) for line in output.splitlines())

def fix_case(name):
    """locale --all might return the encoding in either lower or upper case.
    Passing through this function makes them uniform for comparisons."""
    for s, r in LOCALE_NORMALIZATION.items():
        name = name.replace(s, r)
    return name

def set_locale(name, enabled=True):
    """ Sets the state of the locale. Defaults to enabled. """
    search_string = '#{0,1}\s*%s (?P<charset>.+)' % name
    if enabled:
        new_string = '%s \g<charset>' % (name)
    else:
        new_string = '# %s \g<charset>' % (name)
    try:
        f = open("/etc/locale.gen", "r")
        lines = [re.sub(search_string, new_string, line) for line in f]
    finally:
        f.close()
    try:
        f = open("/etc/locale.gen", "w")
        f.write("".join(lines))
    finally:
        f.close()

def apply_change_debian(targetState, name):
    """Create or remove locale.

    Keyword arguments:
    targetState -- Desired state, either present or absent.
    name -- Name including encoding such as de_CH.UTF-8.
    """
    if targetState=="present":
        # Create locale.
        set_locale(name, enabled=True)
    else:
        # Delete locale.
        set_locale(name, enabled=False)

    localeGenExitValue = call("locale-gen")
    if localeGenExitValue!=0:
        raise EnvironmentError(localeGenExitValue, "locale.gen failed to execute, it returned "+str(localeGenExitValue))

def apply_change_ubuntu(targetState, name):
    """Create or remove locale.

    Keyword arguments:
    targetState -- Desired state, either present or absent.
    name -- Name including encoding such as de_CH.UTF-8.
    """
    if targetState=="present":
        # Create locale.
        # Ubuntu's patched locale-gen automatically adds the new locale to /var/lib/locales/supported.d/local
        localeGenExitValue = call(["locale-gen", name])
    else:
        # Delete locale involves discarding the locale from /var/lib/locales/supported.d/local and regenerating all locales.
        try:
            f = open("/var/lib/locales/supported.d/local", "r")
            content = f.readlines()
        finally:
            f.close()
        try:
            f = open("/var/lib/locales/supported.d/local", "w")
            for line in content:
                locale, charset = line.split(' ')
                if locale != name:
                    f.write(line)
        finally:
            f.close()
        # Purge locales and regenerate.
        # Please provide a patch if you know how to avoid regenerating the locales to keep!
        localeGenExitValue = call(["locale-gen", "--purge"])

    if localeGenExitValue!=0:
        raise EnvironmentError(localeGenExitValue, "locale.gen failed to execute, it returned "+str(localeGenExitValue))


class Locale(object):
    def __init__(self, name):
        self.lang = None
        self.codeset = None
        self.modifier = None
        self.name = name
        self._normalized_codeset = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        self.lang, self.codeset, self.modifier = self.split(name)

    @property
    def normalized_codeset(self):
        if not self._normalized_codeset:
            if self.codeset:
                self._normalized_codeset = self.normalize_codeset(self.codeset)

        return self._normalized_codeset

    @property
    def normalized(self):
        normalized = self.lang

        if self.codeset:
            normalized = '%s.%s' % (self.lang, self.normalized_codeset)

        if self.modifier:
            normalized = '%s@%s' % (normalized, self.modifier)

        return normalized

    @staticmethod
    def split(name):
        """Analyse name and return lang, codeset, modifier"""
        if '.' not in name:
            lang = name
            codeset = None
        else:
            lang, codeset = name.split('.')

        if '@' in lang:
            # name was sv_FI@euro
            lang, modifier = lang.split('@')
        elif codeset and '@' in codeset:
            # name was sv_FI.ISO-8859-15@euro
            codeset, modifier = codeset.split('@')
        else:
            modifier = None

        return lang, codeset, modifier

    @staticmethod
    def normalize_codeset(codeset):
        """Same as 'normalize_codeset' in localedef.c from glibc"""
        if codeset.isdigit():
            codeset = 'iso%s' % codeset
        else:
            codeset = codeset.lower()
            codeset = ''.join(car for car in codeset if car.isalnum())

        return codeset


class Distrib(with_metaclass(ABCMeta, object)):

    def __init__(self, module):
        self.module = module

    @abstractmethod
    def is_available(self, locale):
        """Return a boolean indicating if the given locale could be generated."""

    @abstractmethod
    def generate(self, locale):
        """Create locale."""

    @abstractmethod
    def delete(self, locale):
        """Create locale."""

    def is_present(self, locale):
        """Check if the given locale is currently installed."""

        output = Popen(['locale', '--all'], stdout=PIPE).communicate()[0]
        output = to_native(output)

        return locale.normalized in output.splitlines()

    @abstractmethod
    def get_default_codeset(self, locale):
        """Return default codeset for locale"""
        if '.' in locale.name:
            raise ValueError('locale {0.name!r} already contains a codeset: {0.codeset!r}'.format(locale))

    def apply_change(self, targetState, locale):
        """Create or remove locale.

        Keyword arguments:
        targetState -- Desired state, either present or absent.
        name -- Locale potentially including codeset such as de_CH.UTF-8.
        """
        if not locale.codeset:
            locale.codeset = self.get_default_codeset(locale)

        if targetState == 'present':

            if not self.is_available(locale):
                self.module.fail_json(msg='The locale (%r) is not available.' % locale.name)

            self.generate(locale)
        else:
            self.delete(locale)

# ==============================================================
# main

def main():

    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            state = dict(choices=['present','absent'], default='present'),
        ),
        supports_check_mode=True
    )

    name = module.params['name']
    state = module.params['state']

    if not os.path.exists("/etc/locale.gen"):
        if os.path.exists("/var/lib/locales/supported.d/"):
            # Ubuntu created its own system to manage locales.
            ubuntuMode = True
        else:
            module.fail_json(msg="/etc/locale.gen and /var/lib/locales/supported.d/local are missing. Is the package \"locales\" installed?")
    else:
        # We found the common way to manage locales.
        ubuntuMode = False

    if not is_available_debian(name, ubuntuMode):
        module.fail_json(msg="The locales you've entered is not available "
                             "on your system.")

    if is_present_debian(name):
        prev_state = "present"
    else:
        prev_state = "absent"
    changed = (prev_state!=state)

    if module.check_mode:
        module.exit_json(changed=changed)
    else:
        if changed:
            try:
                if ubuntuMode is False:
                    apply_change_debian(state, name)
                else:
                    apply_change_ubuntu(state, name)
            except EnvironmentError:
                e = get_exception()
                module.fail_json(msg=e.strerror, exitValue=e.errno)

        module.exit_json(name=name, changed=changed, msg="OK")


if __name__ == '__main__':
    main()
