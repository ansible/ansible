#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_install_os
extends_documentation_fragment: nxos
short_description: Set boot options like boot image and kickstart image.
description:
    - Install an operating system by setting the boot options like boot
      image and kickstart image.
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - The module will fail due to timeout issues, but the install will go on
      anyway. Ansible's block and rescue can be leveraged to handle this kind
      of failure and check actual module results. See EXAMPLE for more about
      this. The first task on the rescue block is needed to make sure the
      device has completed all checks and it started to reboot. The second
      task is needed to wait for the device to come back up. The last two tasks
      are used to verify the installation process was successful.
    - Do not include full file paths, just the name of the file(s) stored on
      the top level flash directory.
    - You must know if your platform supports taking a kickstart image as a
      parameter. If supplied but not supported, errors may occur.
    - This module attempts to install the software immediately,
      which may trigger a reboot.
    - In check mode, the module tells you if the current boot images are set
      to the desired images.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbibo (@GGabriele)
version_added: 2.2
options:
    system_image_file:
        description:
            - Name of the system (or combined) image file on flash.
        required: true
    kickstart_image_file:
        description:
            - Name of the kickstart image file on flash.
        required: false
        default: null
    issu:
        description:
            - Enable In Service Software Upgrade (ISSU).
        required: false
        choices: ['true','false']
        default: 'false'
'''

EXAMPLES = '''
- block:
    - name: Install OS
      nxos_install_os:
        system_image_file: nxos.7.0.3.I2.2d.bin
  rescue:
    - name: Wait for device to perform checks
      wait_for:
        port: 22
        state: stopped
        timeout: 300
        delay: 60
    - name: Wait for device to come back up
      wait_for:
        port: 22
        state: started
        timeout: 300
        delay: 60
    - name: Check installed OS
      nxos_command:
        commands:
          - show version
      register: output
    - assert:
        that:
          - output['stdout'][0]['kickstart_ver_str'] == '7.0(3)I4(1)'
'''

RETURN = '''
install_state:
    description: Boot and install information.
    returned: always
    type: dictionary
    sample: {
        "kick": "n5000-uk9-kickstart.7.2.1.N1.1.bin",
        "sys": "n5000-uk9.7.2.1.N1.1.bin",
        "status": "This is the log of last installation.\n
            Continuing with installation process, please wait.\n
            The login will be disabled until the installation is completed.\n
            Performing supervisor state verification. \n
            SUCCESS\n
            Supervisor non-disruptive upgrade successful.\n
            Install has been successful.\n",
    }
'''


import re

from ansible.module_utils.nxos import load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


# Output options are 'text' or 'json'
def execute_show_command(command, module, output='text'):
    cmds = [{
        'command': command,
        'output': output,
    }]

    return run_commands(module, cmds)


def get_platform(module):
    """Determine platform type"""
    data = execute_show_command('show inventory', module, 'json')
    pid = data[0]['TABLE_inv']['ROW_inv'][0]['productid']

    if re.search(r'N3K', pid):
        type = 'N3K'
    elif re.search(r'N5K', pid):
        type = 'N5K'
    elif re.search(r'N6K', pid):
        type = 'N6K'
    elif re.search(r'N7K', pid):
        type = 'N7K'
    elif re.search(r'N9K', pid):
        type = 'N9K'
    else:
        type = 'unknown'

    return type


def get_boot_options(module):
    """Get current boot variables
    like system image and kickstart image.
    Returns:
        A dictionary, e.g. { 'kick': router_kick.img, 'sys': 'router_sys.img'}
    """
    command = 'show boot'
    body = execute_show_command(command, module)[0]
    boot_options_raw_text = body.split('Boot Variables on next reload')[1]

    if 'kickstart' in boot_options_raw_text:
        kick_regex = r'kickstart variable = bootflash:/(\S+)'
        sys_regex = r'system variable = bootflash:/(\S+)'

        kick = re.search(kick_regex, boot_options_raw_text).group(1)
        sys = re.search(sys_regex, boot_options_raw_text).group(1)
        retdict = dict(kick=kick, sys=sys)
    else:
        nxos_regex = r'NXOS variable = bootflash:/(\S+)'
        nxos = re.search(nxos_regex, boot_options_raw_text).group(1)
        retdict = dict(sys=nxos)

    command = 'show install all status'
    retdict['status'] = execute_show_command(command, module)[0]

    return retdict


def already_set(current_boot_options, system_image_file, kickstart_image_file):
    return current_boot_options.get('sys') == system_image_file \
        and current_boot_options.get('kick') == kickstart_image_file


def do_install_all(module, issu, image_name, kickstart=None):
    """Set boot variables
    like system image and kickstart image and boot the os.
    Args:
        The main system image file name.
    Keyword Args: many implementors may choose
        to supply a kickstart parameter to specify a kickstart image.
    """
    commands = ['terminal dont-ask']
    issu_cmd = 'non-disruptive' if issu else ''
    if kickstart is None:
        commands.append('install all nxos %s %s' % (image_name, issu_cmd))
    else:
        commands.append(
            'install all system %s kickstart %s' % (image_name, kickstart))
    install_result = load_config(module, commands)
    return install_result


def main():
    argument_spec = dict(
        system_image_file=dict(required=True),
        kickstart_image_file=dict(required=False),
        issu=dict(required=False, type='bool', default='false'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    platform = get_platform(module)

    # Get system_image_file(sif), kickstart_image_file(kif) and
    # issu settings from module params.
    sif = module.params['system_image_file']
    kif = module.params['kickstart_image_file']
    issu = module.params['issu']

    if issu and not platform == 'N9K':
        msg = "ISSU option is not supported on %s platforms" % platform
        module.fail_json(msg=msg)

    if kif == 'null':
        kif = None

    # Determine current boot options
    cbo = get_boot_options(module)
    changed = False
    if not already_set(cbo, sif, kif):
        changed = True

    if not module.check_mode and changed is True:
        ir = do_install_all(module, issu, sif, kickstart=kif)[0]
        if re.search(r'Finishing the upgrade, switch will reboot', ir):
            cbo = ir
        else:
            module.fail_json(msg=ir)

    module.exit_json(changed=changed, install_state=cbo,
                     warnings=warnings)


if __name__ == '__main__':
    main()
