# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # gitlab doc fragment.
    DOCUMENTATION = r'''
options:
  api_token:
    description:
      - Gitlab token for logging in.
    type: str
    version_added: "2.8"
    aliases:
      - login_token
      - private_token
      - access_token
  config_files:
    description:
      - Configuration file with Gitlab API connection details
      - See python-gitlab documentation for syntax specification
    type: list
    version_added: "2.8"
    default: ["/etc/python-gitlab.cfg", "~/.python-gitlab.cfg"]
'''
