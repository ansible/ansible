#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ce_file_copy
version_added: "2.4"
short_description: Copy a file to a remote cloudengine device over SCP on HUAWEI CloudEngine switches.
description:
    - Copy a file to a remote cloudengine device over SCP on HUAWEI CloudEngine switches.
author:
    - Zhou Zhijin (@QijunPan)
notes:
    - The feature must be enabled with feature scp-server.
    - If the file is already present, no transfer will take place.
requirements:
    - paramiko
options:
    local_file:
        description:
            - Path to local file. Local directory must exist.
              The maximum length of I(local_file) is C(4096).
        required: true
    remote_file:
        description:
            - Remote file path of the copy. Remote directories must exist.
              If omitted, the name of the local file will be used.
              The maximum length of I(remote_file) is C(4096).
    file_system:
        description:
            - The remote file system of the device. If omitted,
              devices that support a I(file_system) parameter will use
              their default values.
              File system indicates the storage medium and can be set to as follows,
              1) C(flash) is root directory of the flash memory on the master MPU.
              2) C(slave#flash) is root directory of the flash memory on the slave MPU.
                 If no slave MPU exists, this drive is unavailable.
              3) C(chassis ID/slot number#flash) is root directory of the flash memory on
                 a device in a stack. For example, C(1/5#flash) indicates the flash memory
                 whose chassis ID is 1 and slot number is 5.
        default: 'flash:'
'''

EXAMPLES = '''
- name: File copy test
  hosts: cloudengine
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:

  - name: "Copy a local file to remote device"
    ce_file_copy:
      local_file: /usr/vrpcfg.cfg
      remote_file: /vrpcfg.cfg
      file_system: 'flash:'
      provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
transfer_result:
    description: information about transfer result.
    returned: always
    type: str
    sample: 'The local file has been successfully transferred to the device.'
local_file:
    description: The path of the local file.
    returned: always
    type: str
    sample: '/usr/work/vrpcfg.zip'
remote_file:
    description: The path of the remote file.
    returned: always
    type: str
    sample: '/vrpcfg.zip'
'''

import re
import os
import sys
import time
from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import ce_argument_spec, run_commands, get_nc_config

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

try:
    from scp import SCPClient
    HAS_SCP = True
except ImportError:
    HAS_SCP = False

CE_NC_GET_FILE_INFO = """
<filter type="subtree">
  <vfm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <dirs>
      <dir>
        <fileName>%s</fileName>
        <dirName>%s</dirName>
        <DirSize></DirSize>
      </dir>
    </dirs>
  </vfm>
</filter>
"""

CE_NC_GET_SCP_ENABLE = """
<filter type="subtree">
  <sshs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <sshServer>
      <scpEnable></scpEnable>
    </sshServer>
  </sshs>
</filter>
"""


def get_cli_exception(exc=None):
    """Get cli exception message"""

    msg = list()
    if not exc:
        exc = sys.exc_info[1]
    if exc:
        errs = str(exc).split("\r\n")
        for err in errs:
            if not err:
                continue
            if "matched error in response:" in err:
                continue
            if " at '^' position" in err:
                err = err.replace(" at '^' position", "")
            if err.replace(" ", "") == "^":
                continue
            if len(err) > 2 and err[0] in ["<", "["] and err[-1] in [">", "]"]:
                continue
            if err[-1] == ".":
                err = err[:-1]
            if err.replace(" ", "") == "":
                continue
            msg.append(err)
    else:
        msg = ["Error: Fail to get cli exception message."]

    while msg[-1][-1] == ' ':
        msg[-1] = msg[-1][:-1]

    if msg[-1][-1] != ".":
        msg[-1] += "."

    return ", ".join(msg).capitalize()


class FileCopy(object):
    """File copy function class"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # file copy parameters
        self.local_file = self.module.params['local_file']
        self.remote_file = self.module.params['remote_file']
        self.file_system = self.module.params['file_system']

        # state
        self.transfer_result = None
        self.changed = False

    def init_module(self):
        """Init module"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def remote_file_exists(self, dst, file_system='flash:'):
        """Remote file whether exists"""

        full_path = file_system + dst
        file_name = os.path.basename(full_path)
        file_path = os.path.dirname(full_path)
        file_path = file_path + '/'
        xml_str = CE_NC_GET_FILE_INFO % (file_name, file_path)
        ret_xml = get_nc_config(self.module, xml_str)
        if "<data/>" in ret_xml:
            return False, 0

        xml_str = ret_xml.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get file info
        root = ElementTree.fromstring(xml_str)
        topo = root.find("data/vfm/dirs/dir")
        if topo is None:
            return False, 0

        for eles in topo:
            if eles.tag in ["DirSize"]:
                return True, int(eles.text.replace(',', ''))

        return False, 0

    def local_file_exists(self):
        """Local file whether exists"""

        return os.path.isfile(self.local_file)

    def enough_space(self):
        """Whether device has enough space"""

        commands = list()
        cmd = 'dir %s' % self.file_system
        commands.append(cmd)
        output = run_commands(self.module, commands)
        if not output:
            return True

        match = re.search(r'\((.*) KB free\)', output[0])
        kbytes_free = match.group(1)
        kbytes_free = kbytes_free.replace(',', '')
        file_size = os.path.getsize(self.local_file)
        if int(kbytes_free) * 1024 > file_size:
            return True

        return False

    def transfer_file(self, dest):
        """Begin to transfer file by scp"""

        if not self.local_file_exists():
            self.module.fail_json(
                msg='Could not transfer file. Local file doesn\'t exist.')

        if not self.enough_space():
            self.module.fail_json(
                msg='Could not transfer file. Not enough space on device.')

        hostname = self.module.params['provider']['host']
        username = self.module.params['provider']['username']
        password = self.module.params['provider']['password']
        port = self.module.params['provider']['port']

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, username=username, password=password, port=port)
        full_remote_path = '{0}{1}'.format(self.file_system, dest)
        scp = SCPClient(ssh.get_transport())
        try:
            scp.put(self.local_file, full_remote_path)
        except Exception:
            time.sleep(10)
            file_exists, temp_size = self.remote_file_exists(
                dest, self.file_system)
            file_size = os.path.getsize(self.local_file)
            if file_exists and int(temp_size) == int(file_size):
                pass
            else:
                scp.close()
                self.module.fail_json(msg='Could not transfer file. There was an error '
                                      'during transfer. Please make sure the format of '
                                      'input parameters is right.')

        scp.close()
        return True

    def get_scp_enable(self):
        """Get scp enable state"""

        xml_str = CE_NC_GET_SCP_ENABLE
        ret_xml = get_nc_config(self.module, xml_str)
        if "<data/>" in ret_xml:
            return False

        xml_str = ret_xml.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get file info
        root = ElementTree.fromstring(xml_str)
        topo = root.find("data/sshs/sshServer")
        if topo is None:
            return False

        for eles in topo:
            if eles.tag in ["scpEnable"]:
                return True, eles.text

        return False

    def work(self):
        """Excute task """

        if not HAS_SCP:
            self.module.fail_json(
                msg="'Error: No scp package, please install it.'")

        if not HAS_PARAMIKO:
            self.module.fail_json(
                msg="'Error: No paramiko package, please install it.'")

        if self.local_file and len(self.local_file) > 4096:
            self.module.fail_json(
                msg="'Error: The maximum length of local_file is 4096.'")

        if self.remote_file and len(self.remote_file) > 4096:
            self.module.fail_json(
                msg="'Error: The maximum length of remote_file is 4096.'")

        retcode, cur_state = self.get_scp_enable()
        if retcode and cur_state == 'Disable':
            self.module.fail_json(
                msg="'Error: Please ensure SCP server is enabled.'")

        if not os.path.isfile(self.local_file):
            self.module.fail_json(
                msg="Local file {0} not found".format(self.local_file))

        dest = self.remote_file or ('/' + os.path.basename(self.local_file))
        remote_exists, file_size = self.remote_file_exists(
            dest, file_system=self.file_system)
        if remote_exists and (os.path.getsize(self.local_file) != file_size):
            remote_exists = False

        if not remote_exists:
            self.changed = True
            file_exists = False
        else:
            file_exists = True
            self.transfer_result = 'The local file already exists on the device.'

        if not file_exists:
            self.transfer_file(dest)
            self.transfer_result = 'The local file has been successfully transferred to the device.'

        if self.remote_file is None:
            self.remote_file = '/' + os.path.basename(self.local_file)

        self.module.exit_json(
            changed=self.changed,
            transfer_result=self.transfer_result,
            local_file=self.local_file,
            remote_file=self.remote_file,
            file_system=self.file_system)


def main():
    """Main function entry"""

    argument_spec = dict(
        local_file=dict(required=True),
        remote_file=dict(required=False),
        file_system=dict(required=False, default='flash:')
    )
    argument_spec.update(ce_argument_spec)
    filecopy_obj = FileCopy(argument_spec)
    filecopy_obj.work()


if __name__ == '__main__':
    main()
