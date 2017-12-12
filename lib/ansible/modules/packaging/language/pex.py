#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Matt Martz <matt@sivel.net>
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
module: pex
author: "Matt Martz (@sivel)"
short_description: Builds and optionally executes PEX files
description:
    - Builds and optionally executes PEX files
version_added: "2.4"
options:
    always_write_cache:
        default: false
        description:
            - Always write the internally cached distributions to
              disk prior to invoking the pex source code.  This can
              use less memory in RAM constrained environments.
        type: bool
    args:
        default: []
        description:
            - A list of arguments to pass to the I(entry_point) or I(script).
              Only used when not specifying I(pex_name)
    cache_dir:
        default: ~/.pex/build
        description:
            - The local cache directory to use for speeding up
              requirement lookups.
    cache_ttl:
        default: 3600
        description:
            - The cache TTL to use for inexact requirement
              specifications.
    constraint_files:
        default: []
        description:
            - Add constraints from the given constraints file.  This
              option can be used multiple times.
    entry_point:
        default: null
        description:
            - Set the entry point to module or module:symbol.  If
              just specifying module, pex behaves like python -m,
              e.g. python -m SimpleHTTPServer.  If specifying
              module:symbol, pex imports that symbol and invokes it
              as if it were main.
    ignore_errors:
        default: false
        description:
            - Ignore run-time requirement resolution errors when
              invoking the pex.
        type: bool
    inherit_path:
        default: false
        description:
            - Inherit the contents of sys.path (including site-packages) running the pex.
        type: bool
    interpreter_cache_dir:
        default: ~/.pex/interpreters
        description:
            - The interpreter cache to use for keeping track of
              interpreter dependencies for the pex tool.
    interpreter_constraint:
        default: null
        description:
            - A list of constraints that determines the interpreter compatibility for
              this pex, using the Requirement-style format, e.g. C(CPython>=3), or
              C(>=2.7) for requirements agnostic to interpreter class.
    packages:
        default: []
        description:
            - Python package names to install
    pex_name:
        aliases:
            - name
        description:
            - >
              The path to save the generated .pex file: Omiting this will
              run PEX immediately and not save it to a file.
    pex_path:
        default: None
        description:
            - A list of other pex files to merge into the runtime environment.
    pex_root:
        default: ~/.pex
        description:
            - Specify the pex root used in this invocation of pex.
    platform:
        default: null
        description:
            - >
              The platform for which to build the PEX.
              Defaults: Auto determine on the target machine.
    preamble_file:
        default: null
        description:
            - The name of a file to be included as the preamble for
              the generated .pex file
    prereleases_allowed:
        aliases:
            - pre
        default: False
        description:
            - Whether to include pre-release and development versions of
              requirements if not explicitly requested.
        type: bool
    python:
        default: null
        description:
            - >
              The Python interpreter to use to build the pex.
              Either specify an explicit path to an interpreter, or
              specify a binary accessible on C($PATH). Default: Use
              current interpreter.
    python_shebang:
        default: null
        description:
            - The exact shebang C(#!...) line to add at the top of
              the PEX file minus the C(#!).  This overrides the default
              behavior, which picks an environment python
              interpreter compatible with the one used to build the
              PEX file.
    repos:
        default: []
        description:
            - Additional repository path (directory or URL) to look
              for requirements.
    requirement_files:
        default: []
        description:
            - Add requirements from the given requirements files.
    script:
        default: null
        description:
            - >
              Set the entry point as to the script or console_script
              as defined by a any of the distributions in the pex.
              For example: C(pex -c fab fabric) or
              C(pex -c mturk boto).
    use_pypi:
        default: true
        description:
            - Whether to use pypi to resolve dependencies
        type: bool
    use_wheel:
        default: true
        description:
            - Whether to allow wheel distributions
        type: bool
    verbosity:
        default: 0
        description:
            - Turn on logging verbosity, the higher the value the
              higher the verbosity
    zip_safe:
        default: true
        description:
            - Whether or not the sources in the pex file are zip
              safe.  If they are not zip safe, they will be written
              to disk prior to execution
        type: bool
requirements:
    - pex
notes:
    - When not supplying I(pex_name) the module will always report a change,
      as the pex will be built and destroyed in a single execution. Supplying
      I(pex_name) is idempotent.
    - Tested up to C(pex==1.2.15)
'''

EXAMPLES = '''
- name: Build a pex file containing pex, that executes pex on build with -h
  pex:
    packages:
      - pex
      - requests
    args:
      - '-h'
    script: pex

- name: Build a pex file for docker
  pex:
    pex_name: /tmp/docker.pex
    packages:
      - docker
'''

RETURN = '''
pex_name:
    description: The path of the generated .pex file
    returned: when successful and pex_name initially supplied
    type: str
    sample: /tmp/docker.pex
platform:
    description: The platform the PEX was built for
    returned: always
    type: str
    sample: macosx-10.12-x86_64
python:
    description: Python interpreter used to build the PEX
    returned: always
    type: str
    sample: /usr/bin/python
python_shebang:
    description: Shebang used in the PEX
    returned: always
    type: str
    sample: #!/usr/bin/env python3.6
build_log:
    description: Verbose log output
    returned: always
    type: str
build_log_lines:
    description: List of verbose log output lines
    returned: always
    type: list
'''

import copy
import json
import traceback

from ansible.module_utils.basic import AnsibleModule

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from pex.bin.pex import build_pex
    from pex.fetcher import Fetcher, PyPIFetcher
    from pex.pex_info import PexInfo
    from pex.platforms import Platform
    from pex.pex import PEX
    from pex.resolver_options import ResolverOptionsBuilder
    from pex.tracer import TRACER
    from pex.variables import ENV
    HAS_PEX = True
except ImportError:
    HAS_PEX = False


class Options(dict):
    def __init__(self, *args, **kwargs):
        super(Options, self).__init__(*args, **kwargs)
        self.__dict__ = self


def setup_options(params):
    options = Options(copy.deepcopy(params))

    if options.platform is None:
        options.platform = Platform.current()

    packages = options.pop('packages')
    use_pypi = options.pop('use_pypi')
    allow_prereleases = options.pop('pre')
    args = options.pop('args')

    builder = ResolverOptionsBuilder()

    for i, repo in enumerate(options.repos):
        options.repos[i] = Fetcher([repo])

    if not use_pypi:
        builder.clear_indices()
    else:
        builder.add_index(PyPIFetcher.PYPI_BASE)
        options.repos.append(PyPIFetcher())

    builder.allow_prereleases(allow_prereleases)

    return options, packages, args, builder


def pex_info_dict(pex_info):
    pex_info_copy = json.loads(pex_info.dump())
    pex_info_copy['requirements'] = sorted(list(pex_info.requirements))
    pex_info_copy['distributions'] = dict(
        sorted(pex_info.distributions.copy().items(), key=lambda t: t[0])
    )
    pex_info_copy.pop('code_hash', None)
    return pex_info_copy


def are_pex_equal(old, new):
    return pex_info_dict(old) == pex_info_dict(new)


def main():
    module = AnsibleModule(
        argument_spec={
            'python': {
                'type': 'str',
                'default': None,
            },
            'zip_safe': {
                'type': 'bool',
                'default': True,
            },
            'always_write_cache': {
                'type': 'bool',
                'default': False,
            },
            'ignore_errors': {
                'type': 'bool',
                'default': False,
            },
            'inherit_path': {
                'type': 'bool',
                'default': False,
            },
            'requirement_files': {
                'type': 'list',
                'default': [],
            },
            'constraint_files': {
                'type': 'list',
                'default': [],
            },
            'platform': {
                'type': 'str',
                'default': None,
            },
            'cache_dir': {
                'type': 'path',
                'default': '~/.pex/build',
            },
            'pex_root': {
                'type': 'path',
                'default': '~/.pex',
            },
            'cache_ttl': {
                'type': 'int',
                'default': 3600
            },
            'entry_point': {
                'type': 'str',
                'default': None,
            },
            'script': {
                'type': 'str',
                'default': None,
            },
            'python_shebang': {
                'type': 'str',
                'default': None
            },
            'packages': {
                'type': 'list',
                'default': [],
            },
            'pex_name': {
                'type': 'path',
                'aliases': [
                    'name'
                ]
            },
            'interpreter_cache_dir': {
                'type': 'path',
                'default': '~/.pex/interpreters',
            },
            'interpreter_constraint': {
                'type': 'list',
                'default': [],
            },
            'use_pypi': {
                'type': 'bool',
                'default': True,
            },
            'use_wheel': {
                'type': 'bool',
                'default': True,
            },
            'repos': {
                'type': 'list',
                'default': [],
            },
            'args': {
                'type': 'list',
                'default': [],
            },
            'verbosity': {
                'type': 'int',
                'default': 0,
            },
            'preamble_file': {
                'type': 'path',
                'default': None,
            },
            'pex_path': {
                'type': 'list',
                'default': None,
            },
            'pre': {
                'aliases': ['prereleases_allowed'],
                'type': 'bool',
                'default': False,
            },
        },
        mutually_exclusive=[
            ['entry_point', 'script'],
        ],
        required_one_of=[
            ['packages', 'requirement_files']
        ],
        supports_check_mode=True,
    )

    if not HAS_PEX:
        module.fail_json(msg="The pex python package is required for this module")

    options, packages, args, resolver_option_builder = setup_options(module.params)

    build_log = StringIO()
    TRACER._output = build_log
    ENV.set('PEX_VERBOSE', str(options.verbosity))

    try:
        pex_builder = build_pex(packages, options, resolver_option_builder)
    except AttributeError as e:
        module.fail_json(
            msg='Module not compatible with the installed version of pex: %s' % e,
            exception=traceback.format_exc()
        )

    if options.python_shebang:
        shebang = '#!%s' % options.python_shebang
    else:
        shebang = pex_builder.interpreter.identity.hashbang()

    response = {
        'pex_name': options.pex_name,
        'platform': options.platform,
        'python': pex_builder.interpreter.binary,
        'python_shebang': shebang,
        'stdout': '',
        'stderr': '',
        'rc': 0,
        'build_log': '',
        'build_log_lines': [],
    }

    changed = False
    try:
        current_info = PexInfo.from_pex(options.pex_name)
    except (IOError, TypeError):
        changed = True
    else:
        if are_pex_equal(current_info, pex_builder.info):
            module.exit_json(changed=False, **response)
        else:
            changed = True

    if module.check_mode:
        module.exit_json(changed=changed, **response)

    rc = 0
    stdout = ''
    stderr = ''
    if options.pex_name is not None:
        tmp_name = options.pex_name + '~'
        try:
            module.cleanup(tmp_name)
            module.cleanup(pex_builder.path())
            pex_builder.build(tmp_name)
            module.atomic_move(tmp_name, options.pex_name)
        except Exception:
            module.cleanup(tmp_name)
            module.cleanup(pex_builder.path())
            module.fail_json(
                msg='Failed to build pex file at %s' % options.pex_name,
                exception=traceback.format_exc(),
                rc=1
            )
    else:
        try:
            pex_builder.freeze()
            pex = PEX(pex_builder.path(), interpreter=pex_builder.interpreter)
            pex.clean_environment()
            rc, stdout, stderr = module.run_command(
                pex.cmdline(args=args)
            )
        except Exception:
            module.fail_json(
                msg='Failed to execute pex file',
                exception=traceback.format_exc(),
                rc=1
            )
        finally:
            module.cleanup(pex_builder.path())

    build_log_out = build_log.getvalue()

    response.update({
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
        'build_log': build_log_out,
        'build_log_lines': build_log_out.splitlines(),
    })

    module.exit_json(changed=changed, **response)


if __name__ == '__main__':
    main()
