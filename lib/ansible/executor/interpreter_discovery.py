# Copyright: (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import bisect
import json
import pkgutil
import re

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.module_utils.distro import LinuxDistribution
from ansible.utils.display import Display
from ansible.utils.plugin_docs import get_versioned_doclink
from ansible.module_utils.compat.version import LooseVersion
from ansible.module_utils.facts.system.distribution import Distribution

OS_FAMILY_LOWER = {k.lower(): v.lower() for k, v in Distribution.OS_FAMILY.items()}

_FALLBACK_INTERPRETER = '/usr/bin/python3'

display = Display()
foundre = re.compile(r'(?s)PLATFORM[\r\n]+(.*)FOUND(.*)ENDFOUND')


class InterpreterDiscoveryRequiredError(Exception):
    def __init__(self, message, interpreter_name, discovery_mode):
        super(InterpreterDiscoveryRequiredError, self).__init__(message)
        self.interpreter_name = interpreter_name
        self.discovery_mode = discovery_mode

    def __str__(self):
        return self.message

    def __repr__(self):
        # TODO: proper repr impl
        return self.message


def discover_interpreter(action, interpreter_name, discovery_mode, task_vars):
    # interpreter discovery is a 2-step process with the target. First, we use a simple shell-agnostic bootstrap to
    # get the system type from uname, and find any random Python that can get us the info we need. For supported
    # target OS types, we'll dispatch a Python script that calls platform.dist() (for older platforms, where available)
    # and brings back /etc/os-release (if present). The proper Python path is looked up in a table of known
    # distros/versions with included Pythons; if nothing is found, depending on the discovery mode, either the
    # default fallback of /usr/bin/python is used (if we know it's there), or discovery fails.

    # FUTURE: add logical equivalence for "python3" in the case of py3-only modules?
    if interpreter_name != 'python':
        raise ValueError('Interpreter discovery not supported for {0}'.format(interpreter_name))

    host = task_vars.get('inventory_hostname', 'unknown')
    res = None
    platform_type = 'unknown'
    found_interpreters = [_FALLBACK_INTERPRETER]  # fallback value
    is_auto_legacy = discovery_mode.startswith('auto_legacy')
    is_silent = discovery_mode.endswith('_silent')

    try:
        platform_python_map = C.config.get_config_value('_INTERPRETER_PYTHON_DISTRO_MAP', variables=task_vars)
        bootstrap_python_list = C.config.get_config_value('INTERPRETER_PYTHON_FALLBACK', variables=task_vars)

        display.vvv(msg=u"Attempting {0} interpreter discovery".format(interpreter_name), host=host)

        # not all command -v impls accept a list of commands, so we have to call it once per python
        command_list = ["command -v '%s'" % py for py in bootstrap_python_list]
        shell_bootstrap = "echo PLATFORM; uname; echo FOUND; {0}; echo ENDFOUND".format('; '.join(command_list))

        # FUTURE: in most cases we probably don't want to use become, but maybe sometimes we do?
        res = action._low_level_execute_command(shell_bootstrap, sudoable=False)

        raw_stdout = res.get('stdout', u'')

        match = foundre.match(raw_stdout)

        if not match:
            display.debug(u'raw interpreter discovery output: {0}'.format(raw_stdout), host=host)
            raise ValueError('unexpected output from Python interpreter discovery')

        platform_type = match.groups()[0].lower().strip()

        found_interpreters = [interp.strip() for interp in match.groups()[1].splitlines() if interp.startswith('/')]

        display.debug(u"found interpreters: {0}".format(found_interpreters), host=host)

        if not found_interpreters:
            if not is_silent:
                display.warning(msg=f'No python interpreters found for host {host!r} (tried {bootstrap_python_list!r}).')
            # this is lame, but returning None or throwing an exception is uglier
            return _FALLBACK_INTERPRETER

        if platform_type != 'linux':
            raise NotImplementedError('unsupported platform for extended discovery: {0}'.format(to_native(platform_type)))

        platform_script = pkgutil.get_data('ansible.executor.discovery', 'python_target.py')

        # FUTURE: respect pipelining setting instead of just if the connection supports it?
        if action._connection.has_pipelining:
            res = action._low_level_execute_command(found_interpreters[0], sudoable=False, in_data=platform_script)
        else:
            # FUTURE: implement on-disk case (via script action or ?)
            raise NotImplementedError('pipelining support required for extended interpreter discovery')

        platform_info = json.loads(res.get('stdout'))

        distro, version = _get_linux_distro(platform_info)
        if not distro or not version:
            raise NotImplementedError('unable to get Linux distribution/version info')

        family = OS_FAMILY_LOWER.get(distro.lower().strip())

        version_map = platform_python_map.get(distro.lower().strip()) or platform_python_map.get(family)
        if not version_map:
            raise NotImplementedError('unsupported Linux distribution: {0}'.format(distro))

        platform_interpreter = to_text(_version_fuzzy_match(version, version_map), errors='surrogate_or_strict')

        # provide a transition period for hosts that were using /usr/bin/python previously (but shouldn't have been)
        if is_auto_legacy:
            if platform_interpreter != _FALLBACK_INTERPRETER and _FALLBACK_INTERPRETER in found_interpreters:
                if not is_silent:
                    display.warning(
                        msg=(
                            f"Distribution {distro!r} {version!r} on host {host!r} should use {platform_interpreter!r}, "
                            f"but is using {_FALLBACK_INTERPRETER!r} for backward compatibility with prior Ansible releases."
                        ),
                        help_text=f"See {get_versioned_doclink('reference_appendices/interpreter_discovery.html')} for more information.",
                    )
                return _FALLBACK_INTERPRETER

        if platform_interpreter not in found_interpreters:
            if platform_interpreter not in bootstrap_python_list:
                # sanity check to make sure we looked for it
                if not is_silent:
                    display.warning(msg=f"Platform interpreter {platform_interpreter!r} on host {host!r} is missing from bootstrap list.")

            if not is_silent:
                display.warning(
                    msg=(
                        f"Distribution {distro!r} {version!r} on host {host!r} should use {platform_interpreter!r}, but is using {found_interpreters[0]!r}, "
                        "since the discovered platform python interpreter was not present."
                    ),
                    help_text=f"See {get_versioned_doclink('reference_appendices/interpreter_discovery.html')} for more information.",
                )

            return found_interpreters[0]

        return platform_interpreter
    except NotImplementedError as ex:
        display.vvv(msg=u'Python interpreter discovery fallback ({0})'.format(to_text(ex)), host=host)
    except AnsibleError:
        raise
    except Exception as ex:
        if not is_silent:
            display.error_as_warning(msg=f'Unhandled error in Python interpreter discovery for host {host!r}.', exception=ex)

            if res and res.get('stderr'):
                display.vvv(msg=u'Interpreter discovery remote stderr:\n{0}'.format(to_text(res.get('stderr'))), host=host)

    if not is_silent:
        display.warning(
            msg=(
                f"Platform {platform_type!r} on host {host!r} is using the discovered Python interpreter at {found_interpreters[0]!r}, "
                "but future installation of another Python interpreter could cause a different interpreter to be discovered."
            ),
            help_text=f"See {get_versioned_doclink('reference_appendices/interpreter_discovery.html')} for more information.",
        )
    return found_interpreters[0]


def _get_linux_distro(platform_info):
    dist_result = platform_info.get('platform_dist_result', [])

    if len(dist_result) == 3 and any(dist_result):
        return dist_result[0], dist_result[1]

    osrelease_content = platform_info.get('osrelease_content')

    if not osrelease_content:
        return u'', u''

    osr = LinuxDistribution._parse_os_release_content(osrelease_content)

    return osr.get('id', u''), osr.get('version_id', u'')


def _version_fuzzy_match(version, version_map):
    # try exact match first
    res = version_map.get(version)
    if res:
        return res

    sorted_looseversions = sorted([LooseVersion(v) for v in version_map.keys()])

    find_looseversion = LooseVersion(version)

    # slot match; return nearest previous version we're newer than
    kpos = bisect.bisect(sorted_looseversions, find_looseversion)

    if kpos == 0:
        # older than everything in the list, return the oldest version
        # TODO: warning-worthy?
        return version_map.get(sorted_looseversions[0].vstring)

    # TODO: is "past the end of the list" warning-worthy too (at least if it's not a major version match)?

    # return the next-oldest entry that we're newer than...
    return version_map.get(sorted_looseversions[kpos - 1].vstring)
