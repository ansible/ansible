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
short_description: Set boot options like boot, kickstart image and issu.
description:
    - Install an operating system by setting the boot options like boot
      image and kickstart image and optionally select to install using
      ISSU (In Server Software Upgrade).
notes:
    - Tested against the following platforms and images:
        - N9k: 7.0(3)I5(3), 7.0(3)I6(1), 7.0(3)I7(1)
        - N3k: 6.0(2)A8(6), 6.0(2)A8(8)
        - N7k: 7.3(0)D1(1), 8.0(1), 8.2(1)
    - This module executes longer then the default ansible timeout value and
      will generate errors unless the module timeout parameter is set to a
      value of 500 seconds or higher.
      NOTE: The example time is sufficent for most upgrades but this can be
            tuned higher based on specific upgrade time requirements.
            The module will exit with a failure message if the timer is
            not set to 500 seconds or higher.
    - Do not include full file paths, just the name of the file(s) stored on
      the top level flash directory.
    - This module attempts to install the software immediately,
      which may trigger a reboot.
    - In check mode, the module will indicate if an upgrade is needed and
      weather or not the upgrade is disruptive or non-disruptive(ISSU).
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbibo (@GGabriele)
version_added: 2.2
options:
    system_image_file:
        description:
            - Name of the system (or combined) image file on flash.
        required: true
    timeout:
        description:
            - The upgrade commands are long running so the timeout value must
              be set to a value of 500 or greater or the module will exit
              with a failure message.
        required: true
    kickstart_image_file:
        description:
            - Name of the kickstart image file on flash.
        required: false
        default: null
    issu:
        description:
            - Upgrade using In Service Software Upgrade (ISSU).
              (Only supported on N9k platforms)
        required: false
        choices: ['required','desired', 'yes', 'no']
            - Selecting 'required' or 'yes' means that upgrades will only
              proceed if the switch is capable of ISSU.
            - Selecting 'desired' means that upgrades will use ISSU if possible
              but will fall back to disruptive upgrade if needed.
            - Selecting 'no' means do not use ISSU. Forced disruptive.
        default: 'no'
'''

EXAMPLES = '''
- name: Install OS on N9k
  check_mode: no
  nxos_install_os:
    system_image_file: nxos.7.0.3.I6.1.bin
    issu: desired
    provider: "{{ connection | combine({'timeout': 500}) }}"

 - name: Wait for device to come back up with new image
   wait_for:
    port: 22
    state: started
    timeout: 500
    delay: 60
    host: "{{ inventory_hostname }}"

  - name: "Check installed OS for newly installed version"
    nxos_command:
      commands: ['show version | json']
      provider: "{{ connection }}"
    register: output
  - assert:
      that:
      - output['stdout'][0]['kickstart_ver_str'] == '7.0(3)I6(1)'
'''

RETURN = '''
install_state:
    description: Boot and install information.
    returned: always
    type: dictionary
    sample: {
    "install_state": [
        "Compatibility check is done:", 
        "Module  bootable          Impact  Install-type  Reason", 
        "------  --------  --------------  ------------  ------", 
        "     1       yes  non-disruptive         reset  ", 
        "Images will be upgraded according to following table:", 
        "Module       Image                  Running-Version(pri:alt)           New-Version  Upg-Required", 
        "------  ----------  ----------------------------------------  --------------------  ------------", 
        "     1        nxos                               7.0(3)I6(1)           7.0(3)I7(1)           yes", 
        "     1        bios                        v4.4.0(07/12/2017)    v4.4.0(07/12/2017)            no"
    ], 
    }
'''


import re
from time import sleep
from ansible.module_utils.nxos import load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def check_ansible_timer(module):
    '''Check Ansible Timer Values'''
    msg = "The 'timeout' provider param value for this module to execute\n"
    msg = msg + 'properly is too low.\n'
    msg = msg + 'Upgrades can take a long time so the value needs to be set\n'
    msg = msg + 'to the recommended value of 500 seconds or higher in the\n'
    msg = msg + 'ansible playbook for the nxos_install_os module.\n'
    msg = msg + '\n'
    msg = msg + 'provider: "{{ connection | combine({\'timeout\': 500}) }}"'
    data = module.params.get('provider')
    timer_low = False
    if data.get('timeout') is None:
        timer_low = True
    if data.get('timeout') is not None and data.get('timeout') < 500:
        timer_low = True
    if timer_low:
        module.fail_json(msg=msg.split('\n'))


# Output options are 'text' or 'json'
def execute_show_command(module, command, output='text'):
    cmds = [{
        'command': command,
        'output': output,
    }]

    return run_commands(module, cmds)


def get_platform(module):
    """Determine platform type"""
    data = execute_show_command(module, 'show inventory', 'json')
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


def kickstart_image_required(module):
    '''Determine if platform requires a kickstart image'''
    data = execute_show_command(module, 'show version')[0]
    kickstart_required = False
    for x in data.split('\n'):
        if re.search(r'kickstart image file is:', x):
            kickstart_required = True

    return kickstart_required


def parse_show_install(data):
    """Helper method to parse the output of the 'show install all impact' or
        'install all' commands.

    Sample Output:

    Installer will perform impact only check. Please wait.

    Verifying image bootflash:/nxos.7.0.3.F2.2.bin for boot variable "nxos".
    [####################] 100% -- SUCCESS

    Verifying image type.
    [####################] 100% -- SUCCESS

    Preparing "bios" version info using image bootflash:/nxos.7.0.3.F2.2.bin.
    [####################] 100% -- SUCCESS

    Preparing "nxos" version info using image bootflash:/nxos.7.0.3.F2.2.bin.
    [####################] 100% -- SUCCESS

    Performing module support checks.
    [####################] 100% -- SUCCESS

    Notifying services about system upgrade.
    [####################] 100% -- SUCCESS



    Compatibility check is done:
    Module  bootable          Impact  Install-type  Reason
    ------  --------  --------------  ------------  ------
         8       yes      disruptive         reset  Incompatible image for ISSU
        21       yes      disruptive         reset  Incompatible image for ISSU


    Images will be upgraded according to following table:
    Module       Image  Running-Version(pri:alt)    New-Version   Upg-Required
    ------  ----------  ----------------------------------------  ------------
         8       lcn9k                7.0(3)F3(2)    7.0(3)F2(2)           yes
         8        bios                     v01.17         v01.17            no
        21       lcn9k                7.0(3)F3(2)    7.0(3)F2(2)           yes
        21        bios                     v01.70         v01.70            no
    """
    if len(data) > 0:
        data = massage_install_data(data)
    ud = {'raw': data}
    ud['list_data'] = data.split('\n')
    ud['processed'] = []
    ud['disruptive'] = False
    ud['upgrade_needed'] = False
    ud['error'] = False
    ud['install_in_progress'] = False
    ud['backend_processing_error'] = False
    ud['upgrade_succeeded'] = False
    ud['use_impact_data'] = False
    for x in ud['list_data']:
        # Check for errors and exit if found.
        if re.search(r'Pre-upgrade check failed', x):
            ud['error'] = True
            break
        if re.search(r'[I|i]nvalid command', x):
            ud['error'] = True
            break
        if re.search(r'No install all data found', x):
            ud['error'] = True
            break

        # Check for potentially transient conditions
        if re.search(r'Another install procedure may be in progress', x):
            ud['install_in_progress'] = True
            break
        if re.search(r'Backend processing error', x):
            ud['backend_processing_error'] = True
            break

        # Check for messages indicating a successful upgrade.
        if re.search(r'Finishing the upgrade', x):
            ud['upgrade_succeeded'] = True
            break
        if re.search(r'Install has been successful', x):
            ud['upgrade_succeeded'] = True
            break

        # We get these messages when the upgrade is non-disruptive and
        # we loose connection with the switchover but far enough along that
        # we can be confident the upgrade succeeded.
        if re.search(r'timeout trying to send command: install', x):
            ud['upgrade_succeeded'] = True
            ud['use_impact_data'] = True
            break
        if re.search(r'[C|c]onnection failure: timed out', x):
            ud['upgrade_succeeded'] = True
            ud['use_impact_data'] = True
            break

        # Begin normal parsing.
        if re.search(r'----|Module|Images will|Compatibility', x):
            ud['processed'].append(x)
            continue
        # Check to see if upgrade will be disruptive or non-disruptive and
        # build dictionary of individual modules and their status.
        # Sample Line:
        #
        # Module  bootable      Impact  Install-type  Reason
        # ------  --------  ----------  ------------  ------
        #     8        yes  disruptive         reset  Incompatible image
        rd = r'(\d+)\s+(\S+)\s+(disruptive|non-disruptive)\s+(\S+)'
        mo = re.search(rd, x)
        if mo:
            ud['processed'].append(x)
            key = 'm%s' % mo.group(1)
            field = 'disruptive'
            if mo.group(3) == 'non-disruptive':
                ud[key] = {field: False}
            else:
                ud[field] = True
                ud[key] = {field: True}
            field = 'bootable'
            if mo.group(2) == 'yes':
                ud[key].update({field: True})
            else:
                ud[key].update({field: False})
            continue

        # Check to see if switch needs an upgrade and build a dictionary
        # of individual modules and their individual upgrade status.
        # Sample Line:
        #
        # Module  Image  Running-Version(pri:alt)    New-Version  Upg-Required
        # ------  -----  ----------------------------------------  ------------
        # 8       lcn9k                7.0(3)F3(2)    7.0(3)F2(2)           yes
        mo = re.search(r'(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(yes|no)', x)
        if mo:
            ud['processed'].append(x)
            key = 'm%s_%s' % (mo.group(1), mo.group(2))
            field = 'upgrade_needed'
            if mo.group(5) == 'yes':
                ud[field] = True
                ud[key] = {field: True}
            else:
                ud[key] = {field: False}
            continue

    return ud


def massage_install_data(data):
    # Transport cli returns a list containing one result item.
    # Transport nxapi returns a list containing two items.  The second item
    # contains the data we are interested in.
    default_error_msg = 'No install all data found'
    if len(data) == 1:
        result_data = data[0]
    elif len(data) == 2:
        result_data = data[1]
    else:
        result_data = default_error_msg

    # Further processing may be needed for result_data
    if len(data) == 2 and type(data[1]) is dict:
        if 'clierror' in data[1].keys():
            result_data = data[1]['clierror']
        elif 'code' in data[1].keys() and data[1]['code'] == '500':
            # We encountered a backend processing error for nxapi
            result_data = data[1]['msg']
        else:
            result_data = default_error_msg
    return result_data


def build_install_cmd_set(issu, image, kick, type):
    commands = ['terminal dont-ask']
    if re.search(r'required|desired|yes', issu):
        issu_cmd = 'non-disruptive'
    else:
        issu_cmd = ''
    if type == 'impact':
        rootcmd = 'show install all impact'
    else:
        rootcmd = 'install all'
    if kick is None:
        commands.append(
            '%s nxos %s %s' % (rootcmd, image, issu_cmd))
    else:
        commands.append(
            '%s system %s kickstart %s' % (rootcmd, image, kick))
    return commands


def parse_show_version(data):
    version_data = {'raw': data[0].split('\n')}
    version_data['version'] = ''
    version_data['error'] = False
    for x in version_data['raw']:
        mo = re.search(r'(kickstart|system|NXOS):\s+version\s+(\S+)', x)
        if mo:
            version_data['version'] = mo.group(2)
            continue

    if version_data['version'] == '':
        version_data['error'] = True

    return version_data


def check_mode_legacy(module, issu, image, kick=None):
    """Some platforms/images/transports don't support the 'install all impact'
        command so we need to use a different method."""
    current = execute_show_command(module, 'show version', 'json')[0]
    # Call parse_show_data on empty string to create the default upgrade
    # data stucture dictionary
    data = parse_show_install('')
    upgrade_msg = 'No upgrade required'

    # Process System Image
    data['error'] = False
    tsver = 'show version image bootflash:%s' % image
    target_image = parse_show_version(execute_show_command(module, tsver))
    if target_image['error']:
        data['error'] = True
        data['raw'] = target_image['raw']
    if current['kickstart_ver_str'] != target_image['version'] and not data['error']:
        data['upgrade_needed'] = True
        data['disruptive'] = True
        upgrade_msg = 'Switch upgraded: system: %s' % tsver

    # Process Kickstart Image
    if kick is not None and not data['error']:
        tkver = 'show version image bootflash:%s' % kick
        target_kick = parse_show_version(execute_show_command(module, tkver))
        if target_kick['error']:
            data['error'] = True
            data['raw'] = target_kick['raw']
        if current['kickstart_ver_str'] != target_kick['version'] and not data['error']:
            data['upgrade_needed'] = True
            data['disruptive'] = True
            upgrade_msg = upgrade_msg + ' kickstart: %s' % tkver

    data['processed'] = upgrade_msg
    return data


def check_mode_nextgen(module, issu, image, kick=None):
    """Use the 'install all impact' command for check_mode"""
    opts = {'ignore_timeout': True}
    commands = build_install_cmd_set(issu, image, kick, 'impact')
    data = parse_show_install(load_config(module, commands, True, opts))
    # If an error is encountered when issu is 'desired' then try again
    # but set issu to 'no'
    if data['error'] and issu == 'desired':
        issu = 'no'
        commands = build_install_cmd_set(issu, image, kick, 'impact')
        # The system may be busy from the previous call to check_mode so loop
        # until it's done.
        data = check_install_in_progress(module, commands, opts)
    if re.search(r'No install all data found', data['raw']):
        data['error'] = True
    return data


def check_install_in_progress(module, commands, opts):
    for attempt in range(20):
        data = parse_show_install(load_config(module, commands, True, opts))
        if data['install_in_progress']:
            sleep(1)
            continue
        break
    return data


def check_mode(module, issu, image, kick=None):
    """Check switch upgrade impact using 'show install all impact' command"""
    data = check_mode_nextgen(module, issu, image, kick)
    if data['backend_processing_error']:
        # We encountered an unrecoverable error in the attempt to get upgrade
        # impact data from the 'show install all impact' command.
        # Fallback to legacy method.
        data = check_mode_legacy(module, issu, image, kick)
    return data


def do_install_all(module, issu, image, kick=None):
    """Perform the switch upgrade using the 'install all' command"""
    impact_data = check_mode(module, issu, image, kick)
    if module.check_mode:
        # Check mode set in the playbook so just return the impact data.
        msg = '*** SWITCH WAS NOT UPGRADED: IMPACT DATA ONLY ***'
        impact_data['processed'].append(msg)
        return impact_data
    if impact_data['error']:
        # Check mode discovered an error so return with this info.
        return impact_data
    elif not impact_data['upgrade_needed']:
        # The switch is already upgraded.  Nothing more to do.
        return impact_data
    else:
        # If we get here, check_mode returned no errors and the switch
        # needs to be upgraded.
        if impact_data['disruptive']:
            # Check mode indicated that ISSU is not possible so issue the
            # upgrade command without the non-disruptive flag.
            issu = 'no'
        commands = build_install_cmd_set(issu, image, kick, 'install')
        opts = {'ignore_timeout': True}
        # The system may be busy from the call to check_mode so loop until
        # it's done.
        upgrade = check_install_in_progress(module, commands, opts)

        # Special case:  If we encounter a backend processing error at this
        # stage, then we consider the switch upgraded.
        if upgrade['backend_processing_error']:
            upgrade['upgrade_succeeded'] = True
            upgrade['use_impact_data'] = True

        if upgrade['use_impact_data']:
            if upgrade['upgrade_succeeded']:
                upgrade = impact_data
                upgrade['upgrade_succeeded'] = True
            else:
                upgrade = impact_data
                upgrade['upgrade_succeeded'] = False

        if not upgrade['upgrade_succeeded']:
            upgrade['error'] = True
    return upgrade


def main():
    argument_spec = dict(
        system_image_file=dict(required=True),
        kickstart_image_file=dict(required=False),
        issu=dict(choices=['required', 'desired', 'no', 'yes'], default='no'),
    )
    # ISSU choices, 'required', 'desired', 'no', 'yes'
    # parse intsall all commands for everything.

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    # This module will error out if the Ansible task timeout value is not
    # tuned high enough.
    check_ansible_timer(module)

    global platform
    platform = get_platform(module)

    # Get system_image_file(sif), kickstart_image_file(kif) and
    # issu settings from module params.
    sif = module.params['system_image_file']
    kif = module.params['kickstart_image_file']
    issu = module.params['issu']

    if kif == 'null' or kif == '':
        kif = None

    if kickstart_image_required(module) and kif is None:
        msg = 'This platform requires a kickstart_image_file'
        module.fail_json(msg=msg)

    install_result = do_install_all(module, issu, sif, kick=kif)
    if install_result['error']:
        msg = "Failed to upgrade device using image "
        if kif:
            msg = msg + "files: kickstart: %s, system: %s" % (kif, sif)
        else:
            msg = msg + "file: system: %s" % sif
        module.fail_json(msg=msg, raw_data=install_result['list_data'])
    else:
        state = install_result['processed']
        changed = install_result['upgrade_needed']

    module.exit_json(changed=changed, install_state=state, warnings=warnings)


if __name__ == '__main__':
    main()
