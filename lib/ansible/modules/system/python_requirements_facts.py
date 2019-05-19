#!/usr/bin/python
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: python_requirements_facts
short_description: Show python path and assert dependency versions
description:
    - Get info about available Python requirements on the target host, including listing required libraries and gathering versions.
version_added: "2.7"
options:
  dependencies:
    description: >
      A list of version-likes or module names to check for installation.
      Supported operators: <, >, <=, >=, or ==. The bare module name like
      I(ansible), the module with a specific version like I(boto3==1.6.1), or a
      partial version like I(requests>2) are all valid specifications.
author:
- Will Thames (@willthames)
- Ryan Scott Brown (@ryan_sb)
'''

EXAMPLES = '''
- name: show python lib/site paths
  python_requirements_facts:
- name: check for modern boto3 and botocore versions
  python_requirements_facts:
    dependencies:
    - boto3>1.6
    - botocore<2
'''

RETURN = '''
python:
  description: path to python version used
  returned: always
  type: str
  sample: /usr/local/opt/python@2/bin/python2.7
python_version:
  description: version of python
  returned: always
  type: str
  sample: "2.7.15 (default, May  1 2018, 16:44:08)\n[GCC 4.2.1 Compatible Apple LLVM 9.1.0 (clang-902.0.39.1)]"
python_system_path:
  description: List of paths python is looking for modules in
  returned: always
  type: list
  sample:
  - /usr/local/opt/python@2/site-packages/
  - /usr/lib/python/site-packages/
  - /usr/lib/python/site-packages/
valid:
  description: A dictionary of dependencies that matched their desired versions. If no version was specified, then I(desired) will be null
  returned: always
  type: dict
  sample:
    boto3:
      desired: null
      installed: 1.7.60
    botocore:
      desired: botocore<2
      installed: 1.10.60
mismatched:
  description: A dictionary of dependencies that did not satisfy the desired version
  returned: always
  type: dict
  sample:
    botocore:
      desired: botocore>2
      installed: 1.10.60
not_found:
  description: A list of packages that could not be imported at all, and are not installed
  returned: always
  type: dict
  sample:
  - boto4
  - riquests
'''

import re
import sys
import operator

HAS_DISTUTILS = False
try:
    import pkg_resources
    from distutils.version import LooseVersion
    HAS_DISTUTILS = True
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule

operations = {
    '<=': operator.le,
    '>=': operator.ge,
    '<': operator.lt,
    '>': operator.gt,
    '==': operator.eq,
}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            dependencies=dict(type='list')
        ),
        supports_check_mode=True,
    )
    if not HAS_DISTUTILS:
        module.fail_json(
            msg='Could not import "distutils" and "pkg_resources" libraries to introspect python environment.',
            python=sys.executable,
            python_version=sys.version,
            python_system_path=sys.path,
        )
    pkg_dep_re = re.compile(r'(^[a-zA-Z][a-zA-Z0-9_-]+)(==|[><]=?)?([0-9.]+)?$')

    results = dict(
        not_found=[],
        mismatched={},
        valid={},
    )

    for dep in (module.params.get('dependencies') or []):
        match = pkg_dep_re.match(dep)
        if match is None:
            module.fail_json(msg="Failed to parse version requirement '{0}'. Must be formatted like 'ansible>2.6'".format(dep))
        pkg, op, version = match.groups()
        if op is not None and op not in operations:
            module.fail_json(msg="Failed to parse version requirement '{0}'. Operator must be one of >, <, <=, >=, or ==".format(dep))
        try:
            existing = pkg_resources.get_distribution(pkg).version
        except pkg_resources.DistributionNotFound:
            # not there
            results['not_found'].append(pkg)
            continue
        if op is None and version is None:
            results['valid'][pkg] = {
                'installed': existing,
                'desired': None,
            }
        elif operations[op](LooseVersion(existing), LooseVersion(version)):
            results['valid'][pkg] = {
                'installed': existing,
                'desired': dep,
            }
        else:
            results['mismatched'] = {
                'installed': existing,
                'desired': dep,
            }

    module.exit_json(
        python=sys.executable,
        python_version=sys.version,
        python_system_path=sys.path,
        **results
    )


if __name__ == '__main__':
    main()
