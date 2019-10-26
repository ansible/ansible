#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Mikhail Morev <mmorev@live.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This is a virtual module that is entirely implemented as an action plugin and runs on the controller

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: consul_template
short_description: Parses Go templates using consul-template and values from HashiCorp Vault and Consul
version_added: '2.10'
author: Mikhail Morev (@mmorev)
requirements:
  - consul-template (binary) in $PATH
description:
- Templates are processed by the L(consul-template,https://github.com/hashicorp/consul-template).
- Documentation on the template formatting can be found on consul-template GitHub page.
- Additional arguments listed below can be used in playbooks.
- C(src) is a path to source Go-syntax template on Ansible controller
- C(dest) is destination file path on destination machine
- C(content) can contain inline template
- C(consul_addr) specifies Consul server address
- C(consul_token) specifies Consul authorization token
- C(vault_addr) specifies Vault server address
- C(vault_token) specifies Vault authorization token
options:
  src:
    description:
    - Path of a Go-formatted template file on the Ansible controller.
    - This can be a relative or an absolute path.
    - This can be remote path if C(remote_src) is set to C(yes)
    type: path
    required: yes
  dest:
    description:
    - Location to place rendered template on the remote machine.
    type: path
    required: yes
  content:
    description:
    - When used instead of C(src), sets the contents of a source template to the specified text.
    - To avoid conflicts with Jinja2 template engine using ``!unsafe`` prefix is required!
    type: str
  consul_addr:
    description:
    - Consul server URL
    type: str
  consul_token:
    description:
    - Consul authorization token
    type: str
    env:
      - name: CONSUL_TOKEN
  vault_addr:
    description:
    - Vault server URL
    type: str
    env:
      - name: VAULT_ADDR
  vault_token:
    description:
    - Vault authorization token
    type: str
    env:
      - name: VAULT_TOKEN
  remote_src:
    description:
      - Set to C(yes) to indicate the template file is on the remote system and not local to the Ansible controller.
      - This option is mutually exclusive with C(content).
    type: bool
    default: no
notes:
- You can use the M(consul_template) module with the C(content:) option if you prefer the template inline,
  as part of the playbook. In this case C(src:) parameter is not permitted
- Any environment variables passed to Ansible executable or using task environment (see examples below) can
  be used inside template (for use single template in different environments like dev/test/prod, for example)
seealso:
- module: copy
extends_documentation_fragment:
- backup
- files
- validate
'''

EXAMPLES = r'''
  - name: Create file using inline template
    consul_template:
      vault_addr: 'http://127.0.0.1:8200/'
      vault_token: "..."
      dest: "/opt/rmcp/none/conf/none.properties"
      content: !unsafe |
        {{ with secret "secret/test" -}}
        app.name={{ index .Data.data "secretkey" }}
        {{- end }}

  - name: Create file with root-only access
    consul_template:
      src: "secretconfig.ctmpl"
      dest: "/etc/secretconfig.ini"
      mode: "0600"
      owner: root
      group: wheel

  - name: Use environment variables in template
    consul_template:
      content: !unsafe |
        {{ with secret (printf "/kv/%s/secret" (env "ENV_NAME")) -}}
        secretkey={{ index .Data.data "secretkey" }}
        {{- end }}
      dest: "/etc/secretconfig.ini"
    environment:
      ENV_NAME: dev
'''

RETURN = r''' # '''
