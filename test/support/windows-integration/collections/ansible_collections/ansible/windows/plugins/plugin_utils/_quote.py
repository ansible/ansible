# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Quoting helpers for Windows

This contains code to help with quoting values for use in the variable Windows
shell. Right now it should only be used in ansible.windows as the interface is
not final and could be subject to change.
"""

# FOR INTERNAL COLLECTION USE ONLY
# The interfaces in this file are meant for use within the ansible.windows collection
# and may not remain stable to outside uses. Changes may be made in ANY release, even a bugfix release.
# See also: https://github.com/ansible/community/issues/539#issuecomment-780839686
# Please open an issue if you have questions about this.

from __future__ import annotations

import re

from ansible.module_utils.six import text_type


_UNSAFE_C = re.compile(u'[\\s\t"]')
_UNSAFE_CMD = re.compile(u'[\\s\\(\\)\\^\\|%!"<>&]')

# PowerShell has 5 characters it uses as a single quote, we need to double up on all of them.
# https://github.com/PowerShell/PowerShell/blob/b7cb335f03fe2992d0cbd61699de9d9aafa1d7c1/src/System.Management.Automation/engine/parser/CharTraits.cs#L265-L272
# https://github.com/PowerShell/PowerShell/blob/b7cb335f03fe2992d0cbd61699de9d9aafa1d7c1/src/System.Management.Automation/engine/parser/CharTraits.cs#L18-L21
_UNSAFE_PWSH = re.compile(u"(['\u2018\u2019\u201a\u201b])")


def quote_c(s):  # type: (text_type) -> text_type
    """Quotes a value for the raw Win32 process command line.

    Quotes a value to be safely used by anything that calls the Win32
    CreateProcess API.

    Args:
        s: The string to quote.

    Returns:
        (text_type): The quoted string value.
    """
    # https://docs.microsoft.com/en-us/archive/blogs/twistylittlepassagesallalike/everyone-quotes-command-line-arguments-the-wrong-way
    if not s:
        return u'""'

    if not _UNSAFE_C.search(s):
        return s

    # Replace any double quotes in an argument with '\"'.
    s = s.replace('"', '\\"')

    # We need to double up on any '\' chars that preceded a double quote (now '\"').
    s = re.sub(r'(\\+)\\"', r'\1\1\"', s)

    # Double up '\' at the end of the argument so it doesn't escape out end quote.
    s = re.sub(r'(\\+)$', r'\1\1', s)

    # Finally wrap the entire argument in double quotes now we've escaped the double quotes within.
    return u'"{0}"'.format(s)


def quote_cmd(s):  # type: (text_type) -> text_type
    """Quotes a value for cmd.

    Quotes a value to be safely used by a command prompt call.

    Args:
        s: The string to quote.

    Returns:
        (text_type): The quoted string value.
    """
    # https://docs.microsoft.com/en-us/archive/blogs/twistylittlepassagesallalike/everyone-quotes-command-line-arguments-the-wrong-way#a-better-method-of-quoting
    if not s:
        return u'""'

    if not _UNSAFE_CMD.search(s):
        return s

    # Escape the metachars as we are quoting the string to stop cmd from interpreting that metachar. For example
    # 'file &whoami.exe' would result in 'whoami.exe' being executed and then that output being used as the argument
    # instead of the literal string.
    # https://stackoverflow.com/questions/3411771/multiple-character-replace-with-python
    for c in u'^()%!"<>&|':  # '^' must be the first char that we scan and replace
        if c in s:
            # I can't find any docs that explicitly say this but to escape ", it needs to be prefixed with \^.
            s = s.replace(c, (u"\\^" if c == u'"' else u"^") + c)

    return u'^"{0}^"'.format(s)


def quote_pwsh(s):  # type: (text_type) -> text_type
    """Quotes a value for PowerShell.

    Quotes a value to be safely used by a PowerShell expression. The input
    string because something that is safely wrapped in single quotes.

    Args:
        s: The string to quote.

    Returns:
        (text_type): The quoted string value.
    """
    # https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_quoting_rules?view=powershell-5.1
    if not s:
        return u"''"

    # We should always quote values in PowerShell as it has conflicting rules where strings can and can't be quoted.
    # This means we quote the entire arg with single quotes and just double up on the single quote equivalent chars.
    return u"'{0}'".format(_UNSAFE_PWSH.sub(u'\\1\\1', s))
