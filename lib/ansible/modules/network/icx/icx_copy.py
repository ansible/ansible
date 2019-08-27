#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: icx_copy
version_added: "2.9"
author: "Ruckus Wireless (@Commscope)"
short_description: Transfer files from or to remote Ruckus ICX 7000 series switches
description:
  - This module transfers files from or to remote devices running ICX.
notes:
  - Tested against ICX 10.1.
  - For information on using ICX platform, see L(the ICX OS Platform Options guide,../network/user_guide/platform_icx.html).
options:
  upload:
    description:
      - Name of the resource to be uploaded. Mutually exclusive with download.
    type: str
    choices: ['running-config', 'startup-config', 'flash_primary', 'flash_secondary']
  download:
    description:
      - Name of the resource to be downloaded. Mutually exclusive with upload.
    type: str
    choices: ['running-config', 'startup-config', 'flash_primary', 'flash_secondary', 'bootrom', 'fips-primary-sig', 'fips-secondary-sig', 'fips-bootrom-sig']
  protocol:
    description:
      - Data transfer protocol to be used
    type: str
    choices: ['scp', 'https']
    required: true
  remote_server:
    description:
      - IP address of the remote server
    type: str
    required: true
  remote_port:
    description:
      - The port number of the remote host. Default values will be selected based on protocol type.
        Default scp:22, http:443
    type: str
  remote_filename:
    description:
      - The name or path of the remote file/resource to be uploaded or downloaded.
    type: str
    required: true
  remote_user:
    description:
      - remote username to be used for scp login.
    type: str
  remote_pass:
    description:
      - remote password to be used for scp login.
    type: str
  public_key:
    description:
      - public key type to be used to login to scp server
    type: str
    choices: ['rsa', 'dsa']

"""

EXAMPLES = """
- name: upload running-config to the remote scp server
  icx_copy:
    upload: running-config
    protocol: scp
    remote_server: 172.16.10.49
    remote_filename: running.conf
    remote_user: user1
    remote_pass: pass123

- name: download running-config from the remote scp server
  icx_copy:
    download: running-config
    protocol: scp
    remote_server: 172.16.10.49
    remote_filename: running.conf
    remote_user: user1
    remote_pass: pass123

- name: download running-config from the remote scp server using rsa public key
  icx_copy:
    download: running-config
    protocol: scp
    remote_server: 172.16.10.49
    remote_filename: running.conf
    remote_user: user1
    remote_pass: pass123
    public_key: rsa

- name: upload startup-config to the remote https server
  icx_copy:
    upload: startup-config
    protocol: https
    remote_server: 172.16.10.49
    remote_filename: config/running.conf
    remote_user: user1
    remote_pass: pass123

- name: upload startup-config to the remote https server
  icx_copy:
    upload: startup-config
    protocol: https
    remote_server: 172.16.10.49
    remote_filename: config/running.conf
    remote_user: user1
    remote_pass: pass123

- name: Download OS image into the flash from remote scp ipv6 server
  icx_copy:
    download: startup-config
    protocol: scp
    remote_server: ipv6 FE80:CD00:0000:0CDE:1257:0000:211E:729C
    remote_filename: img.bin
    remote_user: user1
    remote_pass: pass123

- name: Download OS image into the secondary flash from remote scp ipv6 server
  icx_copy:
    Download: flash_secondary
    protocol: scp
    remote_server: ipv6 FE80:CD00:0000:0CDE:1257:0000:211E:729C
    remote_filename: img.bin
    remote_user: user1
    remote_pass: pass123

- name: Download OS image into the secondary flash from remote scp ipv6 server on port 5000
  icx_copy:
    Download: flash_secondary
    protocol: scp
    remote_server: ipv6 FE80:CD00:0000:0CDE:1257:0000:211E:729C
    remote_port: 5000
    remote_filename: img.bin
    remote_user: user1
    remote_pass: pass123

- name: Download OS image into the primary flash from remote https ipv6 server
  icx_copy:
    Download: flash_primary
    protocol: https
    remote_server: ipv6 FE80:CD00:0000:0CDE:1257:0000:211E:729C
    remote_filename: images/img.bin
    remote_user: user1
    remote_pass: pass123

- name: Download OS image into the primary flash from remote https ipv6 server on port 8080
  icx_copy:
    Download: flash_primary
    protocol: https
    remote_server: ipv6 FE80:CD00:0000:0CDE:1257:0000:211E:729C
    remote_port: 8080
    remote_filename: images/img.bin
    remote_user: user1
    remote_pass: pass123
"""

RETURN = """
changed:
  description: true when downloaded any configuration or flash. false otherwise.
  returned: always
  type: bool
"""


from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import ConnectionError, exec_command
from ansible.module_utils.network.icx.icx import exec_scp, run_commands


def map_params_to_obj(module):
    command = dict()

    if(module.params['protocol'] == 'scp'):
        if(module.params['upload'] is not None):
            module.params["upload"] = module.params["upload"].replace("flash_primary", "primary")
            module.params["upload"] = module.params["upload"].replace("flash_secondary", "secondary")
            if(module.params["upload"] == 'running-config' or module.params["upload"] == 'startup-config'):
                command["command"] = "copy %s scp %s%s %s%s" % (module.params['upload'],
                                                                module.params["remote_server"],
                                                                " " + module.params["remote_port"] if module.params["remote_port"] else "",
                                                                module.params["remote_filename"],
                                                                "public-key " + module.params["public_key"] if module.params["public_key"] else "")
            else:
                command["command"] = "copy flash scp %s%s %s%s %s" % (module.params["remote_server"],
                                                                      " " + module.params["remote_port"] if module.params["remote_port"] else "",
                                                                      module.params["remote_filename"],
                                                                      "public-key " + module.params["public_key"] if module.params["public_key"] else "",
                                                                      module.params["upload"])
            command["scp_user"] = module.params["remote_user"]
            command["scp_pass"] = module.params["remote_pass"]
        if(module.params['download'] is not None):
            module.params["download"] = module.params["download"].replace("flash_primary", "primary")
            module.params["download"] = module.params["download"].replace("flash_secondary", "secondary")
            if(module.params["download"] == 'running-config' or module.params["download"] == 'startup-config'):
                command["command"] = "copy scp %s %s%s %s%s" % (module.params['download'],
                                                                module.params["remote_server"],
                                                                " " + module.params["remote_port"] if module.params["remote_port"] else "",
                                                                module.params["remote_filename"],
                                                                "public-key " + module.params["public_key"] if module.params["public_key"] else "")
            else:
                command["command"] = "copy scp flash %s%s %s%s %s" % (module.params["remote_server"],
                                                                      " " + module.params["remote_port"] if module.params["remote_port"] else "",
                                                                      module.params["remote_filename"],
                                                                      "public-key " + module.params["public_key"] if module.params["public_key"] else "",
                                                                      module.params["download"])
            command["scp_user"] = module.params["remote_user"]
            command["scp_pass"] = module.params["remote_pass"]
    if(module.params['protocol'] == 'https'):
        if(module.params['upload'] is not None):
            module.params["upload"] = module.params["upload"].replace("flash_primary", "primary")
            module.params["upload"] = module.params["upload"].replace("flash_secondary", "secondary")
            if(module.params["upload"] == 'running-config' or module.params["upload"] == 'startup-config'):
                command["command"] = "copy %s https %s %s%s" % (module.params['upload'],
                                                                module.params["remote_server"],
                                                                module.params["remote_filename"],
                                                                " port " + module.params["remote_port"] if module.params["remote_port"] else "")
            else:
                command["command"] = "copy https flash %s %s %s%s" % (module.params["remote_server"],
                                                                      module.params["remote_filename"],
                                                                      module.params['upload'],
                                                                      " port " + module.params["remote_port"] if module.params["remote_port"] else "")
        if(module.params['download'] is not None):
            module.params["download"] = module.params["download"].replace("flash_primary", "primary")
            module.params["download"] = module.params["download"].replace("flash_secondary", "secondary")
            if(module.params["download"] == 'running-config' or module.params["download"] == 'startup-config'):
                command["command"] = "copy https %s %s %s%s" % (module.params['download'],
                                                                module.params["remote_server"],
                                                                module.params["remote_filename"],
                                                                " port " + module.params["remote_port"] if module.params["remote_port"] else "")
            else:
                command["command"] = "copy https flash %s %s %s%s" % (module.params["remote_server"],
                                                                      module.params["remote_filename"],
                                                                      module.params['download'],
                                                                      " port " + module.params["remote_port"] if module.params["remote_port"] else "")
    return command


def checkValidations(module):
    validation = dict(
        scp=dict(
            upload=[
                'running-config',
                'startup-config',
                'flash_primary',
                'flash_secondary'],
            download=[
                'running-config',
                'startup-config',
                'flash_primary',
                'flash_secondary',
                'bootrom',
                'fips-primary-sig',
                'fips-secondary-sig',
                'fips-bootrom-sig']),
        https=dict(
            upload=[
                'running-config',
                'startup-config'],
            download=[
                'flash_primary',
                'flash_secondary',
                'startup-config']))
    protocol = module.params['protocol']
    upload = module.params['upload']
    download = module.params['download']

    if(protocol == 'scp' and module.params['remote_user'] is None):
        module.fail_json(msg="While using scp remote_user argument is required")
    if(upload is None and download is None):
        module.fail_json(msg="Upload or download params are required.")
    if(upload is not None and download is not None):
        module.fail_json(msg="Only upload or download can be used at a time.")
    if(upload):
        if(not (upload in validation.get(protocol).get("upload"))):
            module.fail_json(msg="Specified resource '" + upload + "' can't be uploaded to '" + protocol + "'")
    if(download):
        if(not (download in validation.get(protocol).get("download"))):
            module.fail_json(msg="Specified resource '" + download + "' can't be downloaded from '" + protocol + "'")


def main():
    """entry point for module execution
    """
    argument_spec = dict(
        upload=dict(
            type='str',
            required=False,
            choices=[
                'running-config',
                'flash_primary',
                'flash_secondary',
                'startup-config']),
        download=dict(
            type='str',
            required=False,
            choices=[
                'running-config',
                'startup-config',
                'flash_primary',
                'flash_secondary',
                'bootrom',
                'fips-primary-sig',
                'fips-secondary-sig',
                'fips-bootrom-sig']),
        protocol=dict(
            type='str',
            required=True,
            choices=[
                'https',
                'scp']),
        remote_server=dict(
            type='str',
            required=True),
        remote_port=dict(
            type='str',
            required=False),
        remote_filename=dict(
            type='str',
            required=True),
        remote_user=dict(
            type='str',
            required=False),
        remote_pass=dict(
            type='str',
            required=False,
            no_log=True),
        public_key=dict(
            type='str',
            required=False,
            choices=[
                'rsa',
                'dsa']))
    mutually_exclusive = [['upload', 'download']]
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, mutually_exclusive=mutually_exclusive)

    checkValidations(module)
    warnings = list()
    result = {'changed': False, 'warnings': warnings}
    exec_command(module, 'skip')

    response = ''
    try:
        command = map_params_to_obj(module)
        result['commands'] = [command["command"]]

        if(module.params['protocol'] == 'scp'):
            response = exec_scp(module, command)
        else:
            response = run_commands(module, command)
        if('Response Code: 404' in response):
            module.fail_json(msg=response)
        else:
            result['response'] = "in progress..."
        if(module.params["download"] is not None):
            result['changed'] = True
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
