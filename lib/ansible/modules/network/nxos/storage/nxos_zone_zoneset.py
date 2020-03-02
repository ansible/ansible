#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_zone_zoneset
version_added: "2.10"
short_description: Configuration of zone/zoneset.
description:
    - Configuration of zone/zoneset for Cisco MDS NXOS.
author:
    - Suhas Bharadwaj (@srbharadwaj) (subharad@cisco.com)
notes:
  - Tested against NX-OS 8.4(1)
options:
    zone_zoneset_details:
        description:
            - List of zone/zoneset details to be added or removed
        type: list
        suboptions:
            vsan:
                description:
                    - vsan id
                required:
                    True
                type: int
            mode:
                description:
                    - mode of the zone for the vsan
                choices: ['enhanced', 'basic']
                type: str
            default_zone:
                description:
                    - default zone behaviour for the vsan
                choices: ['permit', 'deny']
                type: str
            smart_zoning:
                description:
                    - Removes the vsan if True
                type: bool
                default: False
            zone:
                description:
                    - List of zone options for that vsan
                type: list
                suboptions:
                    name:
                        description:
                            - name of the zone
                        required:
                            True
                        type: str
                    remove:
                        description:
                            - Deletes the zone if True
                        type: bool
                        default: False
                    members:
                        description:
                            - Members of the zone that needs to be removed or added
                        type: list
                        suboptions:
                            pwwn:
                                description:
                                   - pwwn member of the zone, use alias 'device_alias' as option for device_alias member
                                aliases: [device_alias]
                                required: true
                                type: str
                            remove:
                                description:
                                    - Removes member from the zone if True
                                type: bool
                                default: false
                            devtype:
                                description:
                                    - devtype of the zone member used along with Smart zoning config
                                choices: ['initiator', 'target', 'both']
                                type: str
            zoneset:
                description:
                    - List of zoneset options for the vsan
                type: list
                suboptions:
                    name:
                        description:
                            - name of the zoneset
                        required:
                            True
                        type: str
                    remove:
                        description:
                            - Removes zoneset if True
                        type: bool
                        default: False
                    action:
                        description:
                            - activates/de-activates the zoneset
                        choices: ['activate', 'deactivate']
                        type: str
                    members:
                        description:
                            - Members of the zoneset that needs to be removed or added
                        type: list
                        suboptions:
                            name:
                                description:
                                    - name of the zone that needs to be added to the zoneset or removed from the zoneset
                                required: True
                                type: str
                            remove:
                                description:
                                    - Removes zone member from the zoneset
                                type: bool
                                default: False
'''

EXAMPLES = '''
---
-
  name: 'Test that zone/zoneset module works'
  nxos_zone_zoneset:
    zone_zoneset_details:
      - mode: enhanced
        vsan: 22
        zone:
          - members:
              - pwwn: '11:11:11:11:11:11:11:11'
              - device_alias: test123
              - pwwn: '61:61:62:62:12:12:12:12'
                remove: true
            name: zoneA
          - members:
              - pwwn: '10:11:11:11:11:11:11:11'
              - pwwn: '62:62:62:62:21:21:21:21'
            name: zoneB
          - name: zoneC
            remove: true
        zoneset:
          - action: activate
            members:
              - name: zoneA
              - name: zoneB
              - name: zoneC
                remove: true
            name: zsetname1
          - action: deactivate
            name: zsetTestExtra
            remove: true
      - mode: basic
        smart_zoning: true
        vsan: 21
        zone:
          - members:
              - devtype: both
                pwwn: '11:11:11:11:11:11:11:11'
              - pwwn: '62:62:62:62:12:12:12:12'
              - devtype: both
                pwwn: '92:62:62:62:12:12:1a:1a'
                remove: true
            name: zone21A
          - members:
              - pwwn: '10:11:11:11:11:11:11:11'
              - pwwn: '62:62:62:62:21:21:21:21'
            name: zone21B
        zoneset:
          - action: activate
            members:
              - name: zone21A
              - name: zone21B
            name: zsetname212

'''

RETURN = '''
commands:
  description: commands sent to the device
  returned: always
  type: list
  sample:
    - terminal dont-ask
    - zone name zoneA vsan 923
    - member pwwn 11:11:11:11:11:11:11:11
    - no member device-alias test123
    - zone commit vsan 923
    - no terminal dont-ask
'''


import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.nxos.nxos import load_config, run_commands


__metaclass__ = type


class ShowZonesetActive(object):
    """docstring for ShowZonesetActive"""

    def __init__(self, module, vsan):
        self.vsan = vsan
        self.module = module
        self.activeZSName = None
        self.parseCmdOutput()

    def execute_show_zoneset_active_cmd(self):
        command = 'show zoneset active vsan ' + str(self.vsan) + ' | grep zoneset'
        output = execute_show_command(command, self.module)[0]
        return output

    def parseCmdOutput(self):
        patZoneset = r"zoneset name (\S+) vsan " + str(self.vsan)
        output = self.execute_show_zoneset_active_cmd().split("\n")
        if len(output) == 0:
            return
        else:
            for line in output:
                line = line.strip()
                mzs = re.match(patZoneset, line.strip())
                if mzs:
                    self.activeZSName = mzs.group(1).strip()
                    return

    def isZonesetActive(self, zsname):
        if zsname == self.activeZSName:
            return True
        return False


class ShowZoneset(object):
    """docstring for ShowZoneset"""

    def __init__(self, module, vsan):
        self.vsan = vsan
        self.module = module
        self.zsDetails = {}
        self.parseCmdOutput()

    def execute_show_zoneset_cmd(self):
        command = 'show zoneset vsan ' + str(self.vsan)
        output = execute_show_command(command, self.module)[0]
        return output

    def parseCmdOutput(self):
        patZoneset = r"zoneset name (\S+) vsan " + str(self.vsan)
        patZone = r"zone name (\S+) vsan " + str(self.vsan)
        output = self.execute_show_zoneset_cmd().split("\n")
        for line in output:
            line = line.strip()
            mzs = re.match(patZoneset, line.strip())
            mz = re.match(patZone, line.strip())
            if mzs:
                zonesetname = mzs.group(1).strip()
                self.zsDetails[zonesetname] = []
                continue
            elif mz:
                zonename = mz.group(1).strip()
                v = self.zsDetails[zonesetname]
                v.append(zonename)
                self.zsDetails[zonesetname] = v

    def isZonesetPresent(self, zsname):
        return zsname in self.zsDetails.keys()

    def isZonePresentInZoneset(self, zsname, zname):
        if zsname in self.zsDetails.keys():
            return zname in self.zsDetails[zsname]
        return False


class ShowZone(object):
    """docstring for ShowZone"""

    def __init__(self, module, vsan):
        self.vsan = vsan
        self.module = module
        self.zDetails = {}
        self.parseCmdOutput()

    def execute_show_zone_vsan_cmd(self):
        command = 'show zone vsan ' + str(self.vsan)
        output = execute_show_command(command, self.module)[0]
        return output

    def parseCmdOutput(self):
        patZone = r"zone name (\S+) vsan " + str(self.vsan)
        output = self.execute_show_zone_vsan_cmd().split("\n")
        for line in output:
            line = ' '.join(line.strip().split())
            m = re.match(patZone, line)
            if m:
                zonename = m.group(1).strip()
                self.zDetails[zonename] = []
                continue
            else:
                # For now we support only pwwn and device-alias under zone
                # Ideally should use 'supported_choices'....but maybe next time.
                if "pwwn" in line or "device-alias" in line:
                    v = self.zDetails[zonename]
                    v.append(line)
                    self.zDetails[zonename] = v

    def isZonePresent(self, zname):
        return zname in self.zDetails.keys()

    def isZoneMemberPresent(self, zname, cmd):
        if zname in self.zDetails.keys():
            return cmd in self.zDetails[zname]
        return False


class ShowZoneStatus(object):
    """docstring for ShowZoneStatus"""

    def __init__(self, module, vsan):
        self.vsan = vsan
        self.vsanAbsent = False
        self.module = module
        self.default_zone = ""
        self.mode = ""
        self.session = ""
        self.sz = ""
        self.locked = False
        self.update()

    def execute_show_zone_status_cmd(self):
        command = 'show zone status vsan ' + str(self.vsan)
        output = execute_show_command(command, self.module)[0]
        return output

    def update(self):

        output = self.execute_show_zone_status_cmd().split("\n")

        patfordefzone = "VSAN: " + str(self.vsan) + r" default-zone:\s+(\S+).*"
        patformode = r".*mode:\s+(\S+).*"
        patforsession = r".*session:\s+(\S+).*"
        patforsz = r".*smart-zoning:\s+(\S+).*"
        for line in output:
            if "is not configured" in line:
                self.vsanAbsent = True
                break
            mdefz = re.match(patfordefzone, line.strip())
            mmode = re.match(patformode, line.strip())
            msession = re.match(patforsession, line.strip())
            msz = re.match(patforsz, line.strip())

            if mdefz:
                self.default_zone = mdefz.group(1)
            if mmode:
                self.mode = mmode.group(1)
            if msession:
                self.session = msession.group(1)
                if self.session != "none":
                    self.locked = True
            if msz:
                self.sz = msz.group(1)

    def isLocked(self):
        return self.locked

    def getDefaultZone(self):
        return self.default_zone

    def getMode(self):
        return self.mode

    def getSmartZoningStatus(self):
        return self.sz

    def isVsanAbsent(self):
        return self.vsanAbsent


def execute_show_command(command, module, command_type='cli_show'):
    output = 'text'
    commands = [{
        'command': command,
        'output': output,
    }]
    return run_commands(module, commands)


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def getMemType(supported_choices, allmemkeys, default='pwwn'):
    for eachchoice in supported_choices:
        if eachchoice in allmemkeys:
            return eachchoice
    return default


def main():

    supported_choices = ['device_alias']
    zone_member_spec = dict(
        pwwn=dict(required=True, type='str', aliases=['device_alias']),
        devtype=dict(type='str', choices=['initiator', 'target', 'both']),
        remove=dict(type='bool', default=False)
    )

    zone_spec = dict(
        name=dict(required=True, type='str'),
        members=dict(type='list', elements='dict', options=zone_member_spec),
        remove=dict(type='bool', default=False)
    )

    zoneset_member_spec = dict(
        name=dict(required=True, type='str'),
        remove=dict(type='bool', default=False)
    )

    zoneset_spec = dict(
        name=dict(type='str', required=True),
        members=dict(type='list', elements='dict', options=zoneset_member_spec),
        remove=dict(type='bool', default=False),
        action=dict(type='str', choices=['activate', 'deactivate'])
    )

    zonedetails_spec = dict(
        vsan=dict(required=True, type='int'),
        mode=dict(type='str', choices=['enhanced', 'basic']),
        default_zone=dict(type='str', choices=['permit', 'deny']),
        smart_zoning=dict(type='bool'),
        zone=dict(type='list', elements='dict', options=zone_spec),
        zoneset=dict(type='list', elements='dict', options=zoneset_spec),
    )

    argument_spec = dict(
        zone_zoneset_details=dict(type='list', elements='dict', options=zonedetails_spec)
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    messages = list()
    commands = list()
    result = {'changed': False}

    commands_executed = []
    listOfZoneDetails = module.params['zone_zoneset_details']
    for eachZoneZonesetDetail in listOfZoneDetails:
        vsan = eachZoneZonesetDetail['vsan']
        op_mode = eachZoneZonesetDetail['mode']
        op_default_zone = eachZoneZonesetDetail['default_zone']
        op_smart_zoning = eachZoneZonesetDetail['smart_zoning']
        op_zone = eachZoneZonesetDetail['zone']
        op_zoneset = eachZoneZonesetDetail['zoneset']

        # Step1: execute show zone status and get
        shZoneStatusObj = ShowZoneStatus(module, vsan)
        sw_default_zone = shZoneStatusObj.getDefaultZone()
        sw_mode = shZoneStatusObj.getMode()
        sw_smart_zoning = shZoneStatusObj.getSmartZoningStatus()

        if sw_smart_zoning.lower() == "Enabled".lower():
            sw_smart_zoning_bool = True
        else:
            sw_smart_zoning_bool = False

        if shZoneStatusObj.isVsanAbsent():
            module.fail_json(msg='Vsan ' + str(vsan) + ' is not present in the switch. Hence cannot procced.')

        if shZoneStatusObj.isLocked():
            module.fail_json(msg='zone has acquired lock on the switch for vsan ' + str(vsan) + '. Hence cannot procced.')

        # Process zone default zone options
        if op_default_zone is not None:
            if op_default_zone != sw_default_zone:
                if op_default_zone == "permit":
                    commands_executed.append("zone default-zone permit vsan " + str(vsan))
                    messages.append("default zone configuration changed from deny to permit for vsan " + str(vsan))
                else:
                    commands_executed.append("no zone default-zone permit vsan " + str(vsan))
                    messages.append("default zone configuration changed from permit to deny for vsan " + str(vsan))
            else:
                messages.append("default zone is already " + op_default_zone + " ,no change in default zone configuration for vsan " + str(vsan))

        # Process zone mode options
        if op_mode is not None:
            if op_mode != sw_mode:
                if op_mode == "enhanced":
                    commands_executed.append("zone mode enhanced vsan " + str(vsan))
                    messages.append("zone mode configuration changed from basic to enhanced for vsan " + str(vsan))
                else:
                    commands_executed.append("no zone mode enhanced vsan " + str(vsan))
                    messages.append("zone mode configuration changed from enhanced to basic for vsan " + str(vsan))
            else:
                messages.append("zone mode is already " + op_mode + " ,no change in zone mode configuration for vsan " + str(vsan))

        # Process zone smart-zone options
        if op_smart_zoning is not None:
            if op_smart_zoning != sw_smart_zoning_bool:
                if op_smart_zoning:
                    commands_executed.append("zone smart-zoning enable vsan " + str(vsan))
                    messages.append("smart-zoning enabled for vsan " + str(vsan))
                else:
                    commands_executed.append("no zone smart-zoning enable vsan " + str(vsan))
                    messages.append("smart-zoning disabled for vsan " + str(vsan))
            else:
                messages.append("smart-zoning is already set to " + sw_smart_zoning + " , no change in smart-zoning configuration for vsan " + str(vsan))

        # Process zone member options
        # TODO: Obviously this needs to be cleaned up properly, as there are a lot of ifelse statements which is bad
        # Will take it up later becoz of time constraints
        if op_zone is not None:
            shZoneObj = ShowZone(module, vsan)
            for eachzone in op_zone:
                zname = eachzone['name']
                zmembers = eachzone['members']
                removeflag = eachzone['remove']
                if removeflag:
                    if shZoneObj.isZonePresent(zname):
                        messages.append("zone '" + zname + "' is removed from vsan " + str(vsan))
                        commands_executed.append("no zone name " + zname + " vsan " + str(vsan))
                    else:
                        messages.append("zone '" + zname + "' is not present in vsan " + str(vsan) + " , so nothing to remove")
                else:
                    if zmembers is None:
                        if shZoneObj.isZonePresent(zname):
                            messages.append("zone '" + zname + "' is already present in vsan " + str(vsan))
                        else:
                            commands_executed.append("zone name " + zname + " vsan " + str(vsan))
                            messages.append("zone '" + zname + "' is created in vsan " + str(vsan))
                    else:
                        cmdmemlist = []
                        for eachmem in zmembers:
                            memtype = getMemType(supported_choices, eachmem.keys())
                            cmd = memtype.replace('_', '-') + " " + eachmem[memtype]
                            if op_smart_zoning or sw_smart_zoning_bool:
                                if eachmem['devtype'] is not None:
                                    cmd = cmd + " " + eachmem['devtype']
                            if eachmem["remove"]:
                                if shZoneObj.isZonePresent(zname):
                                    if shZoneObj.isZoneMemberPresent(zname, cmd):
                                        cmd = "no member " + cmd
                                        cmdmemlist.append(cmd)
                                        if op_smart_zoning and eachmem['devtype'] is not None:
                                            messages.append(
                                                "removing zone member '" +
                                                eachmem[memtype] +
                                                " of device type '" +
                                                eachmem['devtype'] +
                                                "' from zone '" +
                                                zname +
                                                "' in vsan " +
                                                str(vsan))
                                        else:
                                            messages.append("removing zone member '" + eachmem[memtype] + "' from zone '" + zname + "' in vsan " + str(vsan))
                                    else:
                                        if op_smart_zoning and eachmem['devtype'] is not None:
                                            messages.append(
                                                "zone member '" +
                                                eachmem[memtype] +
                                                "' of device type '" +
                                                eachmem['devtype'] +
                                                "' is not present in zone '" +
                                                zname +
                                                "' in vsan " +
                                                str(vsan) +
                                                " hence nothing to remove")
                                        else:
                                            messages.append(
                                                "zone member '" +
                                                eachmem[memtype] +
                                                "' is not present in zone '" +
                                                zname +
                                                "' in vsan " +
                                                str(vsan) +
                                                " hence nothing to remove")
                                else:
                                    messages.append("zone '" + zname + "' is not present in vsan " + str(vsan) + " , hence cannot remove the members")

                            else:
                                if shZoneObj.isZoneMemberPresent(zname, cmd):
                                    if op_smart_zoning and eachmem['devtype'] is not None:
                                        messages.append(
                                            "zone member '" +
                                            eachmem[memtype] +
                                            "' of device type '" +
                                            eachmem['devtype'] +
                                            "' is already present in zone '" +
                                            zname +
                                            "' in vsan " +
                                            str(vsan) +
                                            " hence nothing to add")
                                    else:
                                        messages.append(
                                            "zone member '" +
                                            eachmem[memtype] +
                                            "' is already present in zone '" +
                                            zname +
                                            "' in vsan " +
                                            str(vsan) +
                                            " hence nothing to add")
                                else:
                                    cmd = "member " + cmd
                                    cmdmemlist.append(cmd)
                                    if op_smart_zoning and eachmem['devtype'] is not None:
                                        messages.append(
                                            "adding zone member '" +
                                            eachmem[memtype] +
                                            "' of device type '" +
                                            eachmem['devtype'] +
                                            "' to zone '" +
                                            zname +
                                            "' in vsan " +
                                            str(vsan))
                                    else:
                                        messages.append("adding zone member '" + eachmem[memtype] + "' to zone '" + zname + "' in vsan " + str(vsan))
                        if len(cmdmemlist) != 0:
                            commands_executed.append("zone name " + zname + " vsan " + str(vsan))
                            commands_executed = commands_executed + cmdmemlist

        # Process zoneset member options
        if op_zoneset is not None:
            dactcmd = []
            actcmd = []
            shZonesetObj = ShowZoneset(module, vsan)
            shZonesetActiveObj = ShowZonesetActive(module, vsan)
            for eachzoneset in op_zoneset:
                zsetname = eachzoneset['name']
                zsetmembers = eachzoneset['members']
                removeflag = eachzoneset['remove']
                actionflag = eachzoneset['action']
                if removeflag:
                    if shZonesetObj.isZonesetPresent(zsetname):
                        messages.append("zoneset '" + zsetname + "' is removed from vsan " + str(vsan))
                        commands_executed.append("no zoneset name " + zsetname + " vsan " + str(vsan))
                    else:
                        messages.append("zoneset '" + zsetname + "' is not present in vsan " + str(vsan) + " ,hence there is nothing to remove")
                else:
                    if zsetmembers is not None:
                        cmdmemlist = []
                        for eachzsmem in zsetmembers:
                            zsetmem_name = eachzsmem['name']
                            zsetmem_removeflag = eachzsmem['remove']
                            if zsetmem_removeflag:
                                if shZonesetObj.isZonePresentInZoneset(zsetname, zsetmem_name):
                                    cmd = "no member " + zsetmem_name
                                    cmdmemlist.append(cmd)
                                    messages.append("removing zoneset member '" + zsetmem_name + "' from zoneset '" + zsetname + "' in vsan " + str(vsan))
                                else:
                                    messages.append("zoneset member '" + zsetmem_name + "' is not present in zoneset '" +
                                                    zsetname + "' in vsan " + str(vsan) + " ,hence there is nothing to remove")
                            else:
                                if shZonesetObj.isZonePresentInZoneset(zsetname, zsetmem_name):
                                    messages.append("zoneset member '" + zsetmem_name + "' is already present in zoneset '" +
                                                    zsetname + "' in vsan " + str(vsan) + " ,hence there is nothing to add")
                                else:
                                    cmd = "member " + zsetmem_name
                                    cmdmemlist.append(cmd)
                                    messages.append("adding zoneset member '" + zsetmem_name + "' to zoneset '" + zsetname + "' in vsan " + str(vsan))
                        if len(cmdmemlist) != 0:
                            commands_executed.append("zoneset name " + zsetname + " vsan " + str(vsan))
                            commands_executed = commands_executed + cmdmemlist
                    else:
                        if shZonesetObj.isZonesetPresent(zsetname):
                            messages.append("zoneset '" + zsetname + "' is already present in vsan " + str(vsan))
                        else:
                            commands_executed.append("zoneset name " + zsetname + " vsan " + str(vsan))
                            messages.append("zoneset '" + zsetname + "' is created in vsan " + str(vsan))

                # Process zoneset activate options
                if actionflag == 'deactivate':
                    if shZonesetActiveObj.isZonesetActive(zsetname):
                        messages.append("deactivating zoneset '" + zsetname + "' in vsan " + str(vsan))
                        dactcmd.append("no zoneset activate name " + zsetname + " vsan " + str(vsan))
                    else:
                        messages.append("zoneset '" + zsetname + "' in vsan " + str(vsan) + " is not activated, hence cannot deactivate")
                elif actionflag == 'activate':
                    if shZonesetActiveObj.isZonesetActive(zsetname):
                        messages.append("zoneset '" + zsetname + "' in vsan " + str(vsan) + " is already activated")
                    else:
                        messages.append("activating zoneset '" + zsetname + "' in vsan " + str(vsan))
                        actcmd.append("zoneset activate name " + zsetname + " vsan " + str(vsan))
            commands_executed = commands_executed + dactcmd + actcmd

        if commands_executed:
            if op_mode == "enhanced":
                commands_executed.append("zone commit vsan " + str(vsan))
            elif op_mode is None:
                if sw_mode == "enhanced":
                    commands_executed.append("zone commit vsan " + str(vsan))

    if commands_executed:
        commands_executed = ["terminal dont-ask"] + commands_executed + ["no terminal dont-ask"]

    cmds = flatten_list(commands_executed)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=False, commands=cmds, msg="Check Mode: No cmds issued to the hosts")
        else:
            result['changed'] = True
            commands = commands + cmds
            load_config(module, cmds)

    result['messages'] = messages
    result['commands'] = commands_executed
    result['warnings'] = warnings
    module.exit_json(**result)


if __name__ == '__main__':
    main()
