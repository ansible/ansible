# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Markus Bergholz <markuman@gmail.com>
# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase

try:
    from lesspass.password import generate_password
except ImportError:
    raise AnsibleError("Please install lesspass library.")

import json
import yaml

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
lookup: lesspass
author:
  - Markus Bergholz <markuman@gmail.com>
version_added: 2.10
requirements:
  - lesspass
short_description: Calculates a password based on lesspass.
description:
  - lesspass calculates the password based on a profile and a master password.
  - The Minimum profile requirements is a login name and a site name.
  - The profile can be read from file (.yml or .json), defined by options, or mixed (overwrite
    profile file properties with options).
  - See U(https://lesspass.com/)

options:
  login:
    description: A login name.
    default: None
    type: string
  site:
    description: A site.
    default: None
    type: string
  lowercase:
    description: If a password should container lowercase characters.
    default: True
    type: boolean
  uppercase:
    description: If a password should container uppercase characters.
    default: True
    type: boolean
  symbols:
    description: If a password should container symbol characters.
    default: True
    type: boolean
  digits:
    description: If a password should container digits.
    default: True
    type: boolean
  counter:
    description: An Integer value.
    default: 1
    type: integer
  length:
    description: Lenght of the password.
    default: 32
    type: integer
"""


EXAMPLES = """
# Read options from file.
- debug: "msg={{ lookup('lesspass', 'mypassword', profile='ansible-vault-private_key.json')  }}"

# Read options from file, but overwrite 'site' property.
- debug: "msg={{ lookup('lesspass', 'mypassword', profile='ansible-vault-private_key.json', site='ansible.com')  }}"

# Read options from file, but overwrite 'site' and 'login' property.
- debug: "msg={{ lookup('lesspass', 'mypassword', profile='ansible-vault-private_key.json', site='ansible.com', login='alf')  }}"

# Use minimum requirements.
- debug: "msg={{ lookup('lesspass', 'mypassword', site='ansible.com', login='alf')  }}"

# Use minimum requirements, but disable symbols.
- debug: "msg={{ lookup('lesspass', 'mypassword', site='ansible.com', login='alf', digits=false, symbols=false)  }}"
"""


class LookupModule(LookupBase):

    def run(self, terms, variables=None, login=None, site=None,
            lowercase=None, uppercase=None, symbols=None, digits=None,
            counter=None, length=None, profile=None):

        if profile is not None:
            try:
                if profile.find(".yml") == (len(profile) - 4):
                    profile = yaml.load(open(profile))
                elif profile.find(".json") == (len(profile) - 5):
                    profile = json.load(open(profile))
                else:
                    raise AnsibleParserError()
            except AnsibleParserError:
                raise AnsibleError("Cannot open or parse lesspass profile: %s" % profile)

        # overwrite profile items if given
        if profile is not None:
            profile['login'] = login or profile.get('login')
            profile['site'] = site or profile.get('site')
            profile['lowercase'] = lowercase or profile.get('lowercase')
            profile['uppercase'] = uppercase or profile.get('uppercase')
            profile['symbols'] = symbols or profile.get('symbols')
            profile['digits'] = digits or profile.get('digits')
            profile['counter'] = counter or profile.get('counter')
            profile['length'] = length or profile.get('length')

        # build profile of no profile file was given
        # login and site are required in this case
        if profile is None and login is not None and site is not None:
            profile = {'login': login,
                       'site': site,
                       'lowercase': lowercase or True,
                       'uppercase': uppercase or True,
                       'symbols': symbols or True,
                       'digits': digits or True,
                       'counter': 1,
                       'length': 32}

        if profile is None:
            raise AnsibleError("A profile or a pair of login and site is a minimum requirement")

        return [generate_password(profile, terms[0])]
