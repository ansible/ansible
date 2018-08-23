# Copyright: (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import bisect
import json
import pkgutil
import re

from ansible import constants as C
from ansible.module_utils._text import to_text
from ansible.module_utils.distro import LinuxDistribution
from ansible.utils.display import Display
from ansible.utils.plugin_docs import get_versioned_doclink
from distutils.version import LooseVersion
from traceback import format_exc

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
    # target OS types, we'll dispatch a Python script that calls plaform.dist() (for older platforms, where available)
    # and brings back /etc/os-release (if present). The proper Python path is looked up in a table of known
    # distros/versions with included Pythons; if nothing is found, depending on the discovery mode, either the
    # default fallback of /usr/bin/python is used (if we know it's there), or discovery fails.

    # FUTURE: add logical equivalence for "python3" in the case of py3-only modules?
    if interpreter_name != 'python':
        raise ValueError('Interpreter discovery not supported for {0}'.format(interpreter_name))

    host = task_vars.get('inventory_hostname', 'unknown')
    res = None
    platform_type = 'unknown'
    found_interpreters = ['/usr/bin/python']  # fallback value
    is_auto_legacy = discovery_mode.startswith('auto_legacy')
    is_silent = discovery_mode.endswith('_silent')

    try:
        platform_python_map = C.config.get_config_value('INTERPRETER_PYTHON_DISTRO_MAP', variables=task_vars)
        bootstrap_python_list = C.config.get_config_value('INTERPRETER_PYTHON_FALLBACK', variables=task_vars)

        display.vvv(msg="Attempting {0} interpreter discovery".format(interpreter_name), host=host)

        # not all command -v impls accept a list of commands, so we have to call it once per python
        command_list = ["command -v '%s'" % py for py in bootstrap_python_list]
        shell_bootstrap = "echo PLATFORM; uname; echo FOUND; {0}; echo ENDFOUND".format('; '.join(command_list))

        # FUTURE: in most cases we probably don't want to use become, but maybe sometimes we do?
        res = action._low_level_execute_command(shell_bootstrap, sudoable=False)

        raw_stdout = res.get('stdout', '')

        match = foundre.match(raw_stdout)

        if not match:
            display.debug('raw interpreter discovery output: {0}'.format(raw_stdout), host=host)
            raise ValueError('unexpected output from Python interpreter discovery')

        platform_type = match.groups()[0].lower().strip()

        found_interpreters = [interp.strip() for interp in match.groups()[1].splitlines() if interp.startswith('/')]

        display.debug("found interpreters: {0}".format(found_interpreters), host=host)

        if not found_interpreters:
            action._discovery_warnings.append('No python interpreters found for host {0} (tried {1})'.format(host, bootstrap_python_list))
            # this is lame, but returning None or throwing an exception is uglier
            return '/usr/bin/python'

        if platform_type != 'linux':
            raise NotImplementedError('unsupported platform for extended discovery: {0}'.format(platform_type))

        platform_script = pkgutil.get_data('ansible.executor.discovery', 'python_target.py')

        # FUTURE: respect pipelining setting instead of just if the connection supports it?
        if action._connection.has_pipelining:
            res = action._low_level_execute_command(found_interpreters[0], sudoable=False, in_data=platform_script)
        else:
            # FIXME: implement on-disk case (via script action or ?)
            raise NotImplementedError('pipelining support required for extended interpreter discovery')

        platform_info = json.loads(res.get('stdout'))

        distro, version = _get_linux_distro(platform_info)

        if not distro or not version:
            raise NotImplementedError('unable to get Linux distribution/version info')

        version_map = platform_python_map.get(distro.lower().strip())
        if not version_map:
            raise NotImplementedError('unsupported Linux distribution: {0}'.format(distro))

        platform_interpreter = _version_fuzzy_match(version, version_map)

        # provide a transition period for hosts that were using /usr/bin/python previously (but shouldn't have been)
        if is_auto_legacy:
            if platform_interpreter != '/usr/bin/python' and '/usr/bin/python' in found_interpreters:
                # FIXME: support comments in sivel's deprecation scanner so we can get reminded on this
                if not is_silent:
                    action._discovery_deprecation_warnings.append(dict(
                        msg="Distribution {0} {1} should use {2}, but is using "
                            "/usr/bin/python for backward compatibility with prior Ansible releases. "
                            "A future Ansible release will default to using the discovered platform "
                            "python for this host. See {3} for more information"
                            .format(distro, version, platform_interpreter,
                                    get_versioned_doclink('reference_appendices/interpreter_discovery.html')),
                        version='2.12'))
                return '/usr/bin/python'

        if platform_interpreter not in found_interpreters:
            if platform_interpreter not in bootstrap_python_list:
                # sanity check to make sure we looked for it
                if not is_silent:
                    action._discovery_warnings \
                        .append("Platform interpreter {0} is missing from bootstrap list"
                                .format(platform_interpreter))

            if not is_silent:
                action._discovery_warnings \
                    .append("Distribution {0} {1} should use {2}, but is using {3}, since the "
                            "discovered platform python interpreter was not present. See {4} "
                            "for more information."
                            .format(distro, version, platform_interpreter, found_interpreters[0],
                                    get_versioned_doclink('reference_appendices/interpreter_discovery.html')))
            return found_interpreters[0]

        return platform_interpreter
    except NotImplementedError as ex:
        display.vvv(msg='Python interpreter discovery fallback ({0})'.format(to_text(ex)), host=host)
    except Exception as ex:
        if not is_silent:
            display.warning(msg='Unhandled error in Python interpreter discovery for host {0}: {1}'.format(host, to_text(ex)))
            display.debug(msg='Interpreter discovery traceback:\n{0}'.format(to_text(format_exc())), host=host)
            if res and res.get('stderr'):
                display.vvv(msg='Interpreter discovery remote stderr:\n{0}'.format(to_text(res.get('stderr'))), host=host)

    if not is_silent:
        action._discovery_warnings \
            .append("Platform {0} is using the discovered Python interpreter at {1}, but future installation of "
                    "another Python interpreter could change this. See {2} "
                    "for more information."
                    .format(platform_type, found_interpreters[0],
                            get_versioned_doclink('reference_appendices/interpreter_discovery.html')))
    return found_interpreters[0]


def _get_linux_distro(platform_info):
    dist_result = platform_info.get('platform_dist_result', [])

    if len(dist_result) == 3 and any(dist_result):
        return dist_result[0], dist_result[1]

    osrelease_content = platform_info.get('osrelease_content')

    if not osrelease_content:
        return '', ''

    osr = LinuxDistribution._parse_os_release_content(osrelease_content)

    return osr.get('id', ''), osr.get('version_id', '')


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
