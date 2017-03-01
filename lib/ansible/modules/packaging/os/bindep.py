#!/usr/bin/python
# Copyright 2017 Red Hat, Inc.
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
module: bindep
short_description: Get lists of missing distro packages to be installed
author: Monty Taylor (@mordred)
version_added: "2.4"
description:
  - Retreive a list of packages that are not already installed based on a
    list of requirements in bindep format. For more information on bindep,
    please see https://docs.openstack.org/infra/bindep/.
requirements:
  - "python >= 2.7"
  - "bindep >= 2.2.0"
options:
  path:
    description:
      - Path to a bindep.txt file or to a directory that contains either
        a bindep.txt file or an other-requirements.txt file that should
        be used as input. Mutually exclusive with I(requirements).
    required: false
    default: None
  requirements:
    description:
      - A list of bindep requirements strings. Mutually exclusive with I(path).
    required: false
    default: None
  profiles:
    description:
      - An explicit list of profiles to filter by.
    required: false
    default: [default]
'''

EXAMPLES = '''
- name: Get the list of packages to install on a given host from a file
  bindep:
    path: /home/example/bindep.txt

- name: Get the list of test packages to install from current directory
  bindep:
    profiles:
    - test
  register: ret
- name: Install the missing packages
  package:
    name: "{{ item }}"
    state: present
  with_items: "{{ ret.bindep_packages.missing }}"

- name: Get the list of packages to install from an explicit list
  bindep:
    requirements:
    - "build-essential [platform:dpkg test]"
    - "gcc [platform:rpm test]"
    - "language-pack-en [platform:ubuntu]"
    - "libffi-dev [platform:dpkg test]"
    - "libffi-devel [platform:rpm test]"

- name: Get the list of packages to install for the test profile
  bindep:
    requirements:
    - "build-essential [platform:dpkg test]"
    - "gcc [platform:rpm test]"
    - "language-pack-en [platform:ubuntu]"
    - "libffi-dev [platform:dpkg test]"
    - "libffi-devel [platform:rpm test]"
    profiles:
    - test
'''


RETURN = '''
bindep_packages:
  description: Dictionary containing information about the requirements.
  returned: On success.
  type: complex
  contains:
    missing:
      description: Packages that are missing from the system
      returned: success
      type: list
      sample:
      - libmysqlclient-dev
      - libxml2-dev
    badversion:
      description: Packages that are installed but at bad versions.
      returned: success
      type: list
      sample:
      - package: libxml2-dev
        version: 2.9.4+dfsg1-2
        constraint: ">= 3.0"
    up_to_date:
      description: Flag indicating all packages are up to date
      returned: success
      type: bool
'''

import os

from ansible.module_utils.basic import AnsibleModule

try:
    import bindep.depends
    import ometa.runtime
    HAS_BINDEP = True
except ImportError:
    HAS_BINDEP = False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(),
            requirements=dict(required=False, type="list"),
            profiles=dict(required=False, default=['default'], type='list'),
        ),
        mutually_exclusive=[['path', 'requirements']],
        required_one_of=[['path', 'requirements']],
        supports_check_mode=True
    )

    if not HAS_BINDEP:
        module.fail_json(msg='bindep is required for this module')
    if not hasattr(bindep.depends, 'get_depends'):
        module.fail_json(
            msg='bindep is required at version >= 2.2 for this module')

    path = module.params['path']
    requirements = module.params['requirements']
    profiles = module.params['profiles']

    if requirements:
        req_string = '\n'.join(requirements) + '\n'
        try:
            depends = bindep.depends.Depends(req_string)
        except ometa.runtime.ParseError as e:
            module.fail_json(msg='bindep parse error: %s' % str(e))
    else:
        if path and os.path.isdir(path):
            os.chdir(path)
            try:
                depends = bindep.depends.get_depends()
            except ometa.runtime.ParseError as e:
                module.fail_json(msg='bindep parse error: %s' % str(e))
            if not depends:
                module.fail_json(msg="no bindep.txt file found at %s" % path)
        elif path and not os.path.isdir(path):
            module.fail_json(msg="path %s was given but does not exist" % path)
        else:
            try:
                depends = bindep.depends.get_depends(filename=path)
            except ometa.runtime.ParseError as e:
                module.fail_json(msg='bindep parse error: %s' % str(e))
            if not depends:
                module.fail_json(msg="bindep file %s not found" % path)

    profiles = profiles + depends.platform_profiles()
    rules = depends.active_rules(profiles)
    results = depends.check_rules(rules)

    ret = {
        'up_to_date': True,
        'missing': [],
        'badversion': []
    }

    if results:
        ret['up_to_date'] = False
    for result in results:
        if result[0] == 'missing':
            ret['missing'].append(result[1])
        if result[0] == 'badversion':
            for pkg, constraint, version in result[1]:
                ret['badversion'].append({
                    'package': pkg,
                    'version': version,
                    'constraint': constraint,
                })

    module.exit_json(changed=False, bindep_packages=ret)

if __name__ == '__main__':
    main()
