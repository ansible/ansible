# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Ansible Tower documentation fragment
    DOCUMENTATION = r'''
options:
  tower_host:
    description:
    - URL to your Tower instance.
    type: str
  tower_username:
    description:
    - Username for your Tower instance.
    type: str
  tower_password:
    description:
    - Password for your Tower instance.
    type: str
  validate_certs:
    description:
    - Whether to allow insecure connections to Tower.
    - If C(no), SSL certificates will not be validated.
    - This should only be used on personally controlled sites using self-signed certificates.
    type: bool
    aliases: [ tower_verify_ssl ]
  tower_config_file:
    description:
    - Path to the Tower config file.
    type: path

requirements:
- ansible-tower-cli >= 3.0.2

notes:
- If no I(config_file) is provided we will attempt to use the tower-cli library
  defaults to find your Tower host information.
- I(config_file) should contain Tower configuration in the following format
    host=hostname
    username=username
    password=password
'''
