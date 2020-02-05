# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
# (c) 2017 Cisco Systems Inc.
#
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
#


class ModuleDocFragment(object):
    # Cisco Intersight doc fragment
    DOCUMENTATION = '''
options:
  api_private_key:
    description:
    - 'Filename (absolute path) of a PEM formatted file that contains your private key to be used for Intersight API authentication.'
    type: path
    required: yes
  api_uri:
    description:
    - URI used to access the Intersight API.
    type: str
    default: https://intersight.com/api/v1
  api_key_id:
    description:
    - Public API Key ID associated with the private key.
    type: str
    required: yes
  validate_certs:
    description:
    - Boolean control for verifying the api_uri TLS certificate
    type: bool
    default: yes
  use_proxy:
    description:
    - If C(no), it will not use a proxy, even if one is defined in an environment variable on the target hosts.
    type: bool
    default: yes
'''
