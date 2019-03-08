#!/usr/bin/python
# (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# started out with AWX's scan_packages module

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: pip_package_info
short_description: pip package information
description:
  - Return information about installed pip packages
version_added: "2.8"
options:
  clients:
    description:
      - A list of the pip executables that will be used to get the packages.
        They can be supplied with the full path or just the executable name, i.e `pip3.7`.
    default: ['pip']
    required: False
    type: list
requirements:
    - The requested pip executables must be installed on the target.
author:
  - Matthew Jones (@matburt)
  - Brian Coca (@bcoca)
  - Adam Miller (@maxamillion)
'''

EXAMPLES = '''
- name: Just get the list from default pip
  pip_package_info:

- name: get the facts for default pip, pip2 and pip3.6
  pip_package_info:
    clients: ['pip', 'pip2', 'pip3.6']

- name: get from specific paths (virtualenvs?)
  pip_package_info:
    clients: '/home/me/projec42/python/pip3.5'
'''

RETURN = '''
packages:
  description: a dictionary of installed package data
  returned: always
  type: dict
  contains:
    python:
      description: A dictionary with each pip client which then contains a list of dicts with python package information
      returned: always
      type: dict
      sample:
        "packages": {
            "pip": {
                "Babel": [
                    {
                        "name": "Babel",
                        "source": "pip",
                        "version": "2.6.0"
                    }
                ],
                "Flask": [
                    {
                        "name": "Flask",
                        "source": "pip",
                        "version": "1.0.2"
                    }
                ],
                "Flask-SQLAlchemy": [
                    {
                        "name": "Flask-SQLAlchemy",
                        "source": "pip",
                        "version": "2.3.2"
                    }
                ],
                "Jinja2": [
                    {
                        "name": "Jinja2",
                        "source": "pip",
                        "version": "2.10"
                    }
                ],
            },
        }
'''
import json
import os

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.facts.packages import CLIMgr


class PIP(CLIMgr):

    def __init__(self, pip):

        self.CLI = pip

    def list_installed(self):
        global module
        rc, out, err = module.run_command([self._cli, 'list', '-l', '--format=json'])
        if rc != 0:
            raise Exception("Unable to list packages rc=%s : %s" % (rc, err))
        return json.loads(out)

    def get_package_details(self, package):
        package['source'] = self.CLI
        return package


def main():

    # start work
    global module
    module = AnsibleModule(argument_spec=dict(clients={'type': 'list', 'default': ['pip']},), supports_check_mode=True)
    packages = {}
    results = {'packages': {}}
    clients = module.params['clients']

    found = 0
    for pip in clients:

        if not os.path.basename(pip).startswith('pip'):
            module.warn('Skipping invalid pip client: %s' % (pip))
            continue
        try:
            pip_mgr = PIP(pip)
            if pip_mgr.is_available():
                found += 1
                packages[pip] = pip_mgr.get_packages()
        except Exception as e:
            module.warn('Failed to retrieve packages with %s: %s' % (pip, to_text(e)))
            continue

    if found == 0:
        module.fail_json(msg='Unable to use any of the supplied pip clients: %s' % clients)

    # return info
    results['packages'] = packages
    module.exit_json(**results)


if __name__ == '__main__':
    main()
