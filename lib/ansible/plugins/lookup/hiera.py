# (c) 2017, Juan Manuel Parrilla <jparrill@redhat.com>
# (c) 2012-17 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    author:
      - Juan Manuel Parrilla (@jparrill)
    lookup: hiera
    version_added: "2.4"
    short_description: get info from hiera data
    requirements:
      - hiera (command line utility)
    description:
        - Retrieves data from an Puppetmaster node using Hiera as ENC
    options:
      _hiera_key:
            description:
                - The list of keys to lookup on the Puppetmaster
            type: list
            element_type: string
            required: True
      _bin_file:
            description:
                - Binary file to execute Hiera
            default: '/usr/bin/hiera'
            env:
                - name: ANSIBLE_HIERA_BIN
      _hierarchy_file:
            description:
                - File that describes the hierarchy of Hiera
            default: '/etc/hiera.yaml'
            env:
                - name: ANSIBLE_HIERA_CFG
# FIXME: incomplete options .. _terms? environment/fqdn?
'''

EXAMPLES = """
# All this examples depends on hiera.yml  that describes the hierarchy

- name: "a value from Hiera 'DB'"
  debug: msg={{ lookup('hiera', 'foo') }}

- name: "a value from a Hiera 'DB' on other environment"
  debug: msg={{ lookup('hiera', 'foo environment=production') }}

- name: "a value from a Hiera 'DB' for a concrete node"
  debug: msg={{ lookup('hiera', 'foo fqdn=puppet01.localdomain') }}
"""

RETURN = """
    _raw:
        description:
            - a value associated with input key
        type: strings
"""

import os

from ansible.plugins.lookup import LookupBase
from ansible.utils.cmd_functions import run_cmd

ANSIBLE_HIERA_CFG = os.getenv('ANSIBLE_HIERA_CFG', '/etc/hiera.yaml')
ANSIBLE_HIERA_BIN = os.getenv('ANSIBLE_HIERA_BIN', '/usr/bin/hiera')


class Hiera(object):
    def get(self, hiera_key):
        pargs = [ANSIBLE_HIERA_BIN]
        pargs.extend(['-c', ANSIBLE_HIERA_CFG])

        pargs.extend(hiera_key)

        rc, output, err = run_cmd("{0} -c {1} {2}".format(
            ANSIBLE_HIERA_BIN, ANSIBLE_HIERA_CFG, hiera_key[0]))

        return output.strip()


class LookupModule(LookupBase):
    def run(self, terms, variables=''):
        hiera = Hiera()
        ret = []

        ret.append(hiera.get(terms))
        return ret
