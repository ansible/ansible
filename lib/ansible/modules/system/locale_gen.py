#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: locale_gen
short_description: Creates or removes locales
description:
     - Manages locales by editing /etc/locale.gen and invoking locale-gen.
version_added: "1.6"
author:
- Augustus Kling (@AugustusKling)
options:
    name:
        description:
             - Name and encoding of the locale, such as "en_GB.UTF-8".
        required: true
    state:
      description:
           - Whether the locale shall be present.
      choices: [ absent, present ]
      default: present
'''

EXAMPLES = '''
- name: Ensure a locale exists
  locale_gen:
    name: de_CH.UTF-8
    state: present
'''

import os
import re
from subprocess import Popen, PIPE, call

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

LOCALE_NORMALIZATION = {
    ".utf8": ".UTF-8",
    ".eucjp": ".EUC-JP",
    ".iso885915": ".ISO-8859-15",
    ".cp1251": ".CP1251",
    ".koi8r": ".KOI8-R",
    ".armscii8": ".ARMSCII-8",
    ".euckr": ".EUC-KR",
    ".gbk": ".GBK",
    ".gb18030": ".GB18030",
    ".euctw": ".EUC-TW",
}


# ===========================================
# location module specific support methods.
#

def is_available(name, ubuntuMode):
    """Check if the given locale is available on the system. This is done by
    checking either :
    * if the locale is present in /etc/locales.gen
    * or if the locale is present in /usr/share/i18n/SUPPORTED"""
    if ubuntuMode:
        __regexp = r'^(?P<locale>\S+_\S+) (?P<charset>\S+)\s*$'
        __locales_available = '/usr/share/i18n/SUPPORTED'
    else:
        __regexp = r'^#{0,1}\s*(?P<locale>\S+_\S+) (?P<charset>\S+)\s*$'
        __locales_available = '/etc/locale.gen'

    re_compiled = re.compile(__regexp)
    fd = open(__locales_available, 'r')
    for line in fd:
        result = re_compiled.match(line)
        if result and result.group('locale') == name:
            return True
    fd.close()
    return False


def is_present(name):
    """Checks if the given locale is currently installed."""
    output = Popen(["locale", "-a"], stdout=PIPE).communicate()[0]
    output = to_native(output)
    return any(fix_case(name) == fix_case(line) for line in output.splitlines())


def fix_case(name):
    """locale -a might return the encoding in either lower or upper case.
    Passing through this function makes them uniform for comparisons."""
    for s, r in LOCALE_NORMALIZATION.items():
        name = name.replace(s, r)
    return name


def replace_line(existing_line, new_line):
    """Replaces lines in /etc/locale.gen"""
    try:
        f = open("/etc/locale.gen", "r")
        lines = [line.replace(existing_line, new_line) for line in f]
    finally:
        f.close()
    try:
        f = open("/etc/locale.gen", "w")
        f.write("".join(lines))
    finally:
        f.close()


def set_locale(name, enabled=True):
    """ Sets the state of the locale. Defaults to enabled. """
    search_string = r'#{0,1}\s*%s (?P<charset>.+)' % name
    if enabled:
        new_string = r'%s \g<charset>' % (name)
    else:
        new_string = r'# %s \g<charset>' % (name)
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


def apply_change(targetState, name):
    """Create or remove locale.

    Keyword arguments:
    targetState -- Desired state, either present or absent.
    name -- Name including encoding such as de_CH.UTF-8.
    """
    if targetState == "present":
        # Create locale.
        set_locale(name, enabled=True)
    else:
        # Delete locale.
        set_locale(name, enabled=False)

    localeGenExitValue = call("locale-gen")
    if localeGenExitValue != 0:
        raise EnvironmentError(localeGenExitValue, "locale.gen failed to execute, it returned " + str(localeGenExitValue))


def apply_change_ubuntu(targetState, name):
    """Create or remove locale.

    Keyword arguments:
    targetState -- Desired state, either present or absent.
    name -- Name including encoding such as de_CH.UTF-8.
    """
    if targetState == "present":
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

    if localeGenExitValue != 0:
        raise EnvironmentError(localeGenExitValue, "locale.gen failed to execute, it returned " + str(localeGenExitValue))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['absent', 'present']),
        ),
        supports_check_mode=True,
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

    if not is_available(name, ubuntuMode):
        module.fail_json(msg="The locale you've entered is not available "
                             "on your system.")

    if is_present(name):
        prev_state = "present"
    else:
        prev_state = "absent"
    changed = (prev_state != state)

    if module.check_mode:
        module.exit_json(changed=changed)
    else:
        if changed:
            try:
                if ubuntuMode is False:
                    apply_change(state, name)
                else:
                    apply_change_ubuntu(state, name)
            except EnvironmentError as e:
                module.fail_json(msg=to_native(e), exitValue=e.errno)

        module.exit_json(name=name, changed=changed, msg="OK")


if __name__ == '__main__':
    main()
