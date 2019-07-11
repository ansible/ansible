# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Parameters for Service Now modules
    DOCUMENTATION = r'''
options:
    instance:
      description:
      - The service now instance name.
      required: true
      type: str
    username:
      description:
      - User to connect to ServiceNow as.
      required: true
      type: str
    password:
      description:
      - Password for username.
      required: true
      type: str
'''
