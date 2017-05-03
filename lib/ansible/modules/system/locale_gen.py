#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, modified by Pierre-Louis Bonicoli
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
    distribution:
        description:
            - The service module actually uses system specific commands, normally through auto detection, this setting can force a specific distribution.
            - Normally it uses the value of the 'ansible_distribution' fact.
        required: false
        choices: ['auto', Debian', 'Raspbian', 'Ubuntu']
        default: 'auto'
        version_added: 2.4
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
from ansible.module_utils.facts import Distribution
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.six import with_metaclass
from ansible.module_utils._text import to_native


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


class Debian(Distrib):
    LOCALES_AVAILABLE = ['/usr/share/i18n/SUPPORTED', '/usr/local/share/i18n/SUPPORTED']

    def __init__(self, module):
        super(Debian, self).__init__(module)
        self._default_codeset = None

    def is_available(self, locale):
        """Check if the given locale is available on the system. This is done by
        checking if the locale is present in /usr/{local/,}share/i18n/SUPPORTED"""

        if not os.path.exists("/etc/locale.gen"):
            self.module.warn(msg="/etc/locale.gen is missing. Is the package \"locales\" installed?")
            return False

        if locale.modifier and locale.codeset:
            search = '{0.lang}@{0.modifier}'.format(locale)
            search_with_codeset = '{0.lang}.{0.codeset}@{0.modifier}'.format(locale)
        elif locale.modifier:
            search = '{0.lang}@{0.modifier} '.format(locale)
            search_with_codeset = None
        elif locale.codeset:
            search = '%s ' % locale.lang
            search_with_codeset = '{0.lang}.{0.codeset} '.format(locale)
        else:
            search = '%s ' % locale.lang
            search_with_codeset = None

        for supported_path in self.LOCALES_AVAILABLE:
            if not os.path.exists(supported_path):
                continue

            with open(supported_path, 'r') as supported:
                for line in supported:
                    line = line.strip()

                    # match 'iu_CA UTF-8' or 'aa_ER@saaho UTF-8'
                    if line.startswith(search):
                        if not locale.codeset:
                            # Store the value in order to avoid to parse again
                            # SUPPORTED files while searching for a default_codeset
                            locale.codeset = line.replace(search, '')
                            return locale.codeset
                        elif line.endswith(' %s' % locale.codeset):
                            return True
                    # match 'ja_JP.UTF-8 UTF-8' or 'ca_ES.UTF-8@valencia UTF-8'
                    elif search_with_codeset and line.startswith(search_with_codeset):
                        return True
        return False

    def get_default_codeset(self, locale):
        super(Debian, self).get_default_codeset(locale)
        default = self.is_available(locale)
        if default:
            return default

    def generate(self, locale):
        # Create locale.
        self._set_locale(locale, enabled=True)

    def delete(self, locale):
        # Delete locale.
        self._set_locale(locale, enabled=False)

    def _set_locale(self, locale, enabled=True):
        """ Sets the state of the locale. Defaults to enabled. """

        if locale.modifier:
            lang = '{0.lang}@{0.modifier}'.format(locale)
        else:
            lang = locale.lang

        search = r'{0}\s*{1}\s+{2.codeset}'.format('#' if enabled else '', lang, locale)
        search_with_enc = r'{0}\s*{1}.{2.codeset}\s+{2.codeset}'.format('#' if enabled else '', lang, locale)

        with open('/etc/locale.gen', 'r') as locale_gen:
            lines = []
            found = False
            for line in locale_gen:
                if re.search(search, line) or re.search(search_with_enc, line):
                    found = True
                    if enabled:
                        #remove comment
                        line = line[1:]
                    else:
                        line = '#%s' % line
                lines.append(line)

        if found:
            with open('/etc/locale.gen', 'w') as locale_gen:
                locale_gen.write(''.join(lines))
        elif enabled:
            with open('/etc/locale.gen', 'a') as locale_gen:
                locale_gen.write('%s %s\n' % (lang, locale.codeset))

        localeGenExitValue = call("locale-gen")
        if localeGenExitValue!=0:
            raise EnvironmentError(localeGenExitValue, "locale.gen failed to execute, it returned "+str(localeGenExitValue))


class Ubuntu(Debian):
    REGEXP = '^(?P<locale>\S+_\S+) (?P<charset>\S+)\s*$'
    LOCALES_AVAILABLE = '/usr/share/i18n/SUPPORTED'


    def generate(self, name, lang, charset, modifier):
        # Ubuntu's patched locale-gen automatically adds the new locale to /var/lib/locales/supported.d/local
        localeGenExitValue = call(["locale-gen", name])

        if localeGenExitValue != 0:
            raise EnvironmentError(localeGenExitValue, "locale.gen failed to execute, it returned "+str(localeGenExitValue))

    def delete(self, name, lang, charset, modifier):
        # Delete locale involves discarding the locale from /var/lib/locales/supported.d/local and regenerating all locales.
        try:
            f = open("/var/lib/locales/supported.d/local", "r")
            content = f.readlines()
        finally:
            f.close()
        try:
            f = open("/var/lib/locales/supported.d/local", "w")
            for line in content:
                lang, charset = line.split(' ')
                if  lang != name:
                    f.write(line)
        finally:
            f.close()
        # Purge locales and regenerate.
        # Please provide a patch if you know how to avoid regenerating the locales to keep!
        localeGenExitValue = call(["locale-gen", "--purge"])

        if localeGenExitValue != 0:
            raise EnvironmentError(localeGenExitValue, "locale.gen failed to execute, it returned "+str(localeGenExitValue))


# ==============================================================
# main

DISTRIBUTIONS = {}

FAMILIES = dict(
    Debian = Debian,
)

SUPPORTED = [d for d in set([distrib for distrib, family in Distribution.OS_FAMILY.items() if family in FAMILIES] + DISTRIBUTIONS.keys())]
SUPPORTED.append('auto')


def main():

    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            state = dict(choices=['present','absent'], default='present'),
            distribution = dict(choices=SUPPORTED, default='auto'),
        ),
        supports_check_mode=True
    )

    name = module.params['name']
    state = module.params['state']
    distribution = module.params['distribution']

    klass = DISTRIBUTIONS.get(distribution)
    if klass is None and distribution in Distribution.OS_FAMILY:
        klass = FAMILIES.get(Distribution.OS_FAMILY.get(distribution))

    if klass is None:
        module.fail_json(msg="Unsupported distribution '{0}'".format(distribution))

    locale = Locale(name)
    distrib = klass(module)

    if distrib.is_present(locale):
        prev_state = "present"
    else:
        prev_state = "absent"
    changed = (prev_state!=state)

    if module.check_mode:
        module.exit_json(changed=changed)
    else:
        if changed:
            try:
                distrib.apply_change(state, locale)
            except EnvironmentError:
                e = get_exception()
                module.fail_json(msg=e.strerror, exitValue=e.errno)

        module.exit_json(name=name, changed=changed, msg="OK")


if __name__ == '__main__':
    main()
