# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Gregory Shulov <gregory.shulov@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard Infinibox documentation fragment
    DOCUMENTATION = r'''
options:
  system:
    description:
      - Infinibox Hostname or IPv4 Address.
    type: str
    required: true
  user:
    description:
      - Infinibox User username with sufficient priveledges ( see notes ).
    required: false
  password:
    description:
      - Infinibox User password.
    type: str
notes:
  - This module requires infinisdk python library
  - You must set INFINIBOX_USER and INFINIBOX_PASSWORD environment variables
    if user and password arguments are not passed to the module directly
  - Ansible uses the infinisdk configuration file C(~/.infinidat/infinisdk.ini) if no credentials are provided.
    See U(http://infinisdk.readthedocs.io/en/latest/getting_started.html)
requirements:
  - "python >= 2.7"
  - infinisdk
'''
