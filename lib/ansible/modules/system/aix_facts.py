#!/usr/bin/python
#
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aix_facts
version_added: "2.2"
short_description: Gathers AIX specific facts
description:
    - This module gathers AIX specific facts
    - It delivers the folowing ansible_facts
      oslevel, build(ING specific), lpps, filesystems, mounts, vgs, lssrc,
    - niminfo, uname 
author: "Joris.weijters"
options:
  options:
    description:
    - name of the fact you want to recieve, default you will recieve the folowing facts
      'oslevel','build','filesystems','mounts','vgs','lssrc','niminfo','lparstat','uname','drmode'
      the option all will give the folowing facts
      'oslevel','build','lpps','filesystems','mounts','vgs','lssrc','niminfo','lparstat','uname','drmode','ipfilt'

'''


RETURN = '''
ansible_facts: {
    "build": "2010_2",
    "drmode": false,
    "filesystems": [
        {
            "Acct": "no",
            "AutoMount": "yes",
            "Device": "/dev/hd4",
            "MountPoint": "/",
            "Nodename": "",
            "Options": "rw",
            "Size": "262144",
            "Type": "bootfs",
            "Vfs": "jfs2"
        },
        {
            "Acct": "no",
            "AutoMount": "yes",
            "Device": "/dev/var_tem",
            "MountPoint": "/var/opt/BESClient",
            "Nodename": "",
            "Options": "rw",
            "Size": "5242880",
            "Type": "",
            "Vfs": "jfs2"
        }
    ],
    "ipfilt": [
        {
            "action": "permit",
            "apply": "no",
            "desc": "Default Rule",
            "dest": "0.0.0.0",
            "dir": "both",
            "dmask": "0.0.0.0",
            "doper": "eq",
            "dtype": "4001",
            "expt": "0",
            "fid": "1",
            "frag": "all packets",
            "intf": "all",
            "log": "no",
            "patp": "",
            "patt": "",
            "proto": "udp",
            "routing": "both",
            "smask": "0.0.0.0",
            "soper": "eq",
            "source": "0.0.0.0",
            "stype": "4001",
            "tunnel": "0"
        },
        {
            "action": "*** Dynamic filter placement rule for IKE tunnels ***",
            "fid": "2",
            "source": "no"
        },
        {
            "action": "permit",
            "apply": "yes",
            "desc": "Default Rule",
            "dest": "::",
            "dir": "both",
            "dmask": "0",
            "doper": "any",
            "dtype": "0",
            "expt": "0",
            "fid": "0",
            "frag": "all packets",
            "intf": "all",
            "log": "no",
            "patp": "",
            "patt": "",
            "proto": "all",
            "routing": "both",
            "smask": "0",
            "soper": "any",
            "source": "::",
            "stype": "0",
            "tunnel": "0"
        }
    ],
    "lparstat": [
        {
            "Active_CPUs_in_Pool": "16",
            "Active_Physical_CPUs_in_system": "16",
            "Capacity_Increment": "0.01",
            "Desired_Capacity": "0.50",
            "Desired_Memory": "6144",
            "Desired_Variable_Capacity_Weight": "32",
            "Desired_Virtual_CPUs": "2",
            "Entitled_Capacity": "0.50",
            "Entitled_Capacity_of_Pool": "300",
            "Hypervisor_Page_Size": "-",
            "Maximum_Capacity": "14.00",
            "Maximum_Capacity_of_Pool": "1600",
            "Maximum_Memory": "10240",
            "Maximum_Physical_CPUs_in_system": "16",
            "Maximum_Virtual_CPUs": "14",
            "Memory_Group_ID_of_LPAR": "-",
            "Memory_Mode": "Dedicated",
            "Memory_Pool_ID": "-",
            "Minimum_Capacity": "0.10",
            "Minimum_Memory": "1024",
            "Minimum_Virtual_CPUs": "1",
            "Mode": "Uncapped",
            "Node_Name": "nimclient",
            "Online_Memory": "6144",
            "Online_Virtual_CPUs": "2",
            "Partition_Group-ID": "32781",
            "Partition_Name": "nimclient",
            "Partition_Number": "13",
            "Physical_CPU_Percentage": "25.00",
            "Physical_Memory_in_the_Pool": "-",
            "Power_Saving_Mode": "Disabled",
            "Shared_Physical_CPUs_in_system": "16",
            "Shared_Pool_ID": "0",
            "Sub_Processor_Mode": "-",
            "Target_Memory_Expansion_Factor": "-",
            "Target_Memory_Expansion_Size": "-",
            "Total_I/O_Memory_Entitlement": "-",
            "Type": "Shared-SMT-4",
            "Unallocated_Capacity": "0.00",
            "Unallocated_I/O_Memory_entitlement": "-",
            "Unallocated_Variable_Memory_Capacity_Weight": "-",
            "Unallocated_Weight": "0",
            "Variable_Capacity_Weight": "32",
            "Variable_Memory_Capacity_Weight": "-"
        }
    ],
    "lpps": [
        {
            "Automatic": "0",
            "Build_Date": "",
            "Description": "IBM BigFix Agent",
            "Destination_Dir.": " ",
            "EFIX_Locked": "0",
            "Fileset": "BESClient",
            "Fix_State": "C",
            "Install_Path": "/",
            "Level": "9.5.4.38",
            "Message_Catalog": " ",
            "Message_Number": " ",
            "Message_Set": " ",
            "PTF_Id": " ",
            "Package_Name": "BESClient",
            "Parent": " ",
            "State": " ",
            "Type": " ",
            "Uninstaller": " "
        },
        {
            "Automatic": "0",
            "Build_Date": "Fri Jan 15 00",
            "Description": "GCC version 4.2.4 shared support library",
            "Destination_Dir.": " ",
            "EFIX_Locked": " ",
            "Fileset": "libgcc-4.2.4-2",
            "Fix_State": "C",
            "Install_Path": "(none)",
            "Level": "4.2.4-2",
            "Message_Catalog": " ",
            "Message_Number": " ",
            "Message_Set": " ",
            "PTF_Id": " ",
            "Package_Name": "libgcc",
            "Parent": " ",
            "State": " ",
            "Type": "R",
            "Uninstaller": "/bin/rpm -e libgcc"
        }
    ],
    "lssrc": [
        {
            "Group": "",
            "PID": "3604604",
            "Status": "active",
            "Subsystem": "tlmagent"
        },
        {
            "Group": "isnstgtd",
            "PID": "",
            "Status": "inoperative",
            "Subsystem": "isnstgtd"
        }
    ],
    "mounts": [
        {
            "device": "/dev/hd4",
            "fstype": "jfs2",
            "mount": "/",
            "options": "rw,log=/dev/hd8",
            "size_available": 92508160,
            "size_total": 134217728,
            "time": "May 05 14:39"
        },
        {
            "device": "/dev/var_tem",
            "fstype": "jfs2",
            "mount": "/var/opt/BESClient",
            "options": "rw,log=INLINE",
            "size_available": 2369880064,
            "size_total": 2684354560,
            "time": "May 05 14:39"
        }
    ],
    "niminfo": {
        "NIM_BOS_FORMAT": "rte",
        "NIM_BOS_IMAGE": "/SPOT/usr/sys/inst.images/installp/ppc/bos",
        "NIM_CONFIGURATION": "standalone",
        "NIM_FIPS_MODE": "0",
        "NIM_HOSTNAME": "nimclient.local",
        "NIM_HOSTS": "127.0.0.1:loopback:localhost  1.2.3.4:nimclient.local  1.2.3.5:nimserver.local",
        "NIM_MASTERID": "00F7C1234567",
        "NIM_MASTER_HOSTNAME": "nimserver.local",
        "NIM_MASTER_PORT": "1058",
        "NIM_MOUNTS": "",
        "NIM_NAME": "nimclient",
        "NIM_REGISTRATION_PORT": "1059",
        "NIM_SHELL": "nimsh",
        "ROUTES": "default:0:172.27.200.1"
    },
    "oslevel": {
        "BUILD_DATE": "1642",
        "OS_Ver": "71",
        "SP": "03",
        "TL": "04",
        "oslevel_s": "7100-04-03-1642"
    },
    "uname": {
        "architecture": "powerpc",
        "id": "000123456780",
        "lannumber": "166046676",
        "lparid": "11",
        "lparname": "nimclient",
        "model": "8406-71Y",
        "name": "nimclient",
        "os": "AIX",
        "release": "1",
        "serial": "012345678",
        "systemid": "041AC01234567890",
        "version": "7"
    },
    "vgs": {
        "vgname": [
            {
                "free_pps": "346",
                "pp_size": "128 megabyte(s)",
                "pv_name": "hdisk1",
                "pv_state": "active",
                "total_pps": "399"
            }
        ],
        "rootvg": [
            {
                "free_pps": "242",
                "pp_size": "128 megabyte(s)",
                "pv_name": "hdisk0",
                "pv_state": "active",
                "total_pps": "400"
            }
        ]
    }
}
'''

EXAMPLES = '''
# show the default facts
- name: show default facts
  aix_facts_py:

# show all facts
- name: show all facts
  aix_facts:
    options:
      - all

# show facts uname and build:
- name: show facts uname and build
  aix_facts:
    options:
      - uname
      - build

'''

# import modules needed
import sys
import shlex
import os
import platform
import re
import itertools
import commands
import subprocess

try:
    import json
except ImportError:
    import simplejson as json

from ansible.module_utils.basic import AnsibleModule

# end import modules
# start defining the functions


# Internal functions
def _convert_out_to_list(out):
    """
    Internal function to convert colon separtated output to a list of dictionaries.
    The first line of the out contains the keys, and starts with an '#'
    F.i.
        #MountPoint:Device:Vfs:Nodename:Type:Size:Options:AutoMount:Acct
        /:/dev/hd4:jfs2::bootfs:524288:rw:yes:no
        /usr:/dev/hd2:jfs2::bootfs:8912896:rw:yes:no
    """
    lijst = []
    for line in out.splitlines():
        if re.match('^#', line):
            line = line[1:]
            line = line.replace(' ', '_')
            keys = line.split(":")
        else:
            values = line.split(":")
            adict = dict(itertools.izip(keys, values))
            lijst.append(adict)
    return lijst


def _get_mount_size_facts(mountpoint):
    """
    Internal module to determine the filesystem size and free size in bites
    The input is teh mountpoint
    """
    size_total = None
    size_available = None
    try:
        statvfs_result = os.statvfs(mountpoint)
        size_total = statvfs_result.f_frsize * statvfs_result.f_blocks
        size_available = statvfs_result.f_frsize * (statvfs_result.f_bavail)
    except OSError:
        pass
    return size_total, size_available


def get_oslevel(module):
    """
    get the oslevel function delivers oslvel -s output
    <OS Ver>-<TL>-<SP>-<BUILD DATE>
    as wel OV_Version, the tecnology level, TL, the Servicepack, SP and the BUILD_DATE,
    """
    rc, out, err = module.run_command(["/usr/bin/oslevel", "-s"])
    if rc != 0:
        module.fail_json(msg="could not determine oslevel", rc=rc, err=err)
    lijst = {'oslevel_s': out.strip('\n')}
    keys = ('OS_Ver', 'TL', 'SP', 'BUILD_DATE')
    values = out.split('-')
    v_stript = [v.rstrip('0\n') for v in values]
    adict = dict(itertools.izip(keys, v_stript))
    lijst.update(adict)

    return lijst


def get_build(module):
    """
    reads the /var/adm/autoinstall/etc/BUILD to determine the BUILS,
    if this fails, it reads the /etc/BUILD
    the output is the BUILD version
    """
    build = {}
    org_file = '/var/adm/autoinstall/etc/BUILD'
    copy_file = '/etc/BUILD'
    try:
        if os.path.exists(org_file):
            build = ''.join([line.strip() for line in open(org_file, 'r')])
    except IOError as e:
        if os.path.exists(copy_file):
            build = ''.join([line.strip() for line in open(copy_file, 'r')])
    except IOError as e:
        module.fail_json(msg="could not determine BUILD", rc=rc, err=e)
    return build


def get_lpps(module):
    """
    runs the lslpp -Lc and delivers the output to _convert_out_to_list
    for creating the lpps fact
    """
    lpps = []
    rc, out, err = module.run_command(["/usr/bin/lslpp", "-Lc"])
    if rc != 0:
        module.fail_json(msg="could not determine lslpp list", rc=rc, err=err)
    return _convert_out_to_list(out)


def get_filesystems(module):
    """
    runs the lsfs -c and delivers the output to _convert_out_to_list
    for creating the filesystems fact
    """
    filesystems = []
    rc, out, err = module.run_command(["/usr/sbin/lsfs", "-c"])
    if rc != 0:
        module.fail_json(msg="could not determine lsfs list", rc=rc, err=err)
    return _convert_out_to_list(out)


def get_mounts(module):
    """
    create a lists with mounted filesystems
    it calls to _get_mount_size_facts to determine the size and free size
    it outputs all mounts
    """
    mounts = []
    # AIX does not have mtab but mount command is only source of info (or to use
    # api calls to get same info)
    rc, out, err = module.run_command("/usr/sbin/mount")
    if rc != 0:
        module.fail_json(msg="could not determine mounts", rc=rc, err=err)
    else:
        for line in out.splitlines():
            fields = line.split()
            if len(fields) != 0 and fields[0] != 'node' and fields[0][0] != '-' and re.match(
                    '^/.*|^[a-zA-Z].*|^[0-9].*', fields[0]):
                if re.match('^/', fields[0]):
                    # normal mount
                    size_total, size_available = _get_mount_size_facts(
                        fields[1])
                    mounts.append({'mount': fields[1],
                                   'device': fields[0],
                                   'fstype': fields[2],
                                   'options': fields[6],
                                   'size_total': size_total,
                                   'size_available': size_available,
                                   'time': '%s %s %s' % (fields[3], fields[4],
                                                         fields[5])})
                else:
                    # nfs or cifs based mount
                    # in case of nfs if no mount options are provided on command line
                    # add into fields empty string...
                    if len(fields) < 8:
                        fields.append("")
                    mounts.append({'mount': fields[2],
                                   'device': '%s:%s' % (fields[0], fields[1]),
                                   'fstype': fields[3],
                                   'options': fields[7],
                                   'time': '%s %s %s' % (fields[4], fields[5],
                                                         fields[6])})
    return mounts


def get_vgs(module):
    """
    Get vg and pv Facts
    $ lsvg |xargs lsvg -p
    rootvg:
    PV_NAME           PV STATE          TOTAL PPs   FREE PPs    FREE DISTRIBUTION
    hdisk0            active            400         117         29..00..00..40..48
    midwarevg:
    PV_NAME           PV STATE          TOTAL PPs   FREE PPs    FREE DISTRIBUTION
    hdisk1            active            400         3           00..00..00..00..03
    altdiskvg:
    PV_NAME           PV STATE          TOTAL PPs   FREE PPs    FREE DISTRIBUTION
    hdisk2            active            399         399         80..80..79..80..80
    """

    lsvg_path = module.get_bin_path("lsvg")
    xargs_path = module.get_bin_path("xargs")
    cmd = "%s -o| %s %s -p" % (lsvg_path, xargs_path, lsvg_path)
    vgs = {}
    if lsvg_path and xargs_path:
        rc, out, err = module.run_command(cmd, use_unsafe_shell=True)
    if rc != 0:
        module.fail_json(msg="could not determine lsvg |xargs lsvg -p",
                         rc=rc, err=err)
    if rc == 0 and out:
        for m in re.finditer(
            r'(\S+):\n.*FREE DISTRIBUTION(\n(\S+)\s+(\w+)\s+(\d+)\s+(\d+).*)+',
                out):
            vgs[m.group(1)] = []
            pp_size = 0
            cmd = "%s %s" % (lsvg_path, m.group(1))
            rc, out, err = module.run_command(cmd)
            if rc == 0 and out:
                pp_size = re.search(r'PP SIZE:\s+(\d+\s+\S+)', out).group(1)
                for n in re.finditer(
                    r'(\S+)\s+(\w+)\s+(\d+)\s+(\d+).*',
                        m.group(0)):
                    pv_info = {'pv_name': n.group(1),
                               'pv_state': n.group(2),
                               'total_pps': n.group(3),
                               'free_pps': n.group(4),
                               'pp_size': pp_size
                               }
                    vgs[m.group(1)].append(pv_info)
    return vgs


def get_lssrc(module):
    lijst = []
    rc, out, err = module.run_command(["/usr/bin/lssrc", "-a"])
    if rc != 0:
        module.fail_json(
            msg="ERROR: Could not complete lssrc ",
            rc=rc,
            err=err)
    firstline = True
    for line in out.splitlines():
        #        if firstline == True:
        if firstline:
            keys = line.split()
            firstline = False
        else:
            # lssrc output is colomn formatted without specific separator, so
            # use exact positions for each field!
            values = [line[0:18].strip(), line[18:34].strip(),
                      line[34:48].strip(), line[48:60].strip()]
            adict = dict(itertools.izip(keys, values))
            lijst.append(adict)
    return lijst


def get_niminfo(module):
    file = '/etc/niminfo'

    try:
        if os.path.exists(file):
            '''
            the niminfo looks like:
            #------------------ Network Install Manager ---------------
            # warning - this file contains NIM configuration information
            #       and should only be updated by NIM
            export NIM_NAME=nimclient
            export NIM_HOSTNAME=nimclient.local
            export NIM_CONFIGURATION=standalone
            export NIM_MASTER_HOSTNAME=nimserver.local
            export NIM_MASTER_PORT=1058
            export NIM_REGISTRATION_PORT=1059
            export NIM_SHELL="nimsh"
            export NIM_MASTERID=00F62C634C00
            export NIM_FIPS_MODE=0
            export NIM_BOS_IMAGE=/SPOT/usr/sys/inst.images/installp/ppc/bos
            export NIM_BOS_FORMAT=rte
            export NIM_HOSTS=" 127.0.0.1:loopback:localhost
                               1.2.3.4:nimclient.local
                               1.2.3.5:nimserver.local"
            export NIM_MOUNTS=""
            export ROUTES=" default:0:1.2.3.1 "

            The next line will do 3 things
            It opens the file and reads all lines string with 'export'
            ((l for l in open(file, 'r') if l.startswith('export')))
            it puts the output in line, and if line is not empty, if not re.match(r'^\s*$',line)
            then it splits that line into 2 blocks showing only the second and
            splits this into 2 block with '=' as separator:
            line.split(' ', 1)[1].split('=')
            the output is put into k anv v
            than it strips k and v and creates a dictionary from these:
            dict((k.strip(), v.strip(' "\n'))
            '''
            niminfo = dict(
                (k.strip(), v.strip(' "\n')) for k, v in (
                    line.split(
                        ' ', 1)[1].split(
                        '=', 1) for line in (
                        (l for l in open(
                            file, 'r') if l.startswith('export'))) if not re.match(
                            r'^\s*$', line)))
    except IOError as e:
        #       module.fail_json(msg="could not read /etc/niminfo", rc=rc, err=e)
        module.warnings.append('could not read /etc/niminfo')
        niminfo = {}
    return niminfo


def get_lparstat(module):
    lijst = []
    adict = {}
    rc, out, err = module.run_command(["/usr/bin/lparstat", "-i"])
    if rc != 0:
        module.fail_json(msg="ERROR: could not complete lparstat -i", rc=rc,
                         err=err)
    for line in out.splitlines():
        key, value = line.split(":")
        key = key.strip().replace(' ', '_')
        value = value.strip().split(" ")
        value[0] = value[0].replace('%', '')
        if len(value) == 2:
            if value[1] == 'GB':
                value[0] = float(value[0]) * 1024
        adict[key] = value[0]
    lijst.append(adict)
    return lijst


def get_uname(module):
    options = {
        "systemid": "-F",
        "lannumber": "-l",
        "lpar": "-L",
        "id": "-m",
        "model": "-M",
        "name": "-n",
        "architecture": "-p",
        "release": "-r",
        "os": "-s",
        "serial": "-u",
        "version": "-v",
    }
    list = {}
    for key in options:
        rc, out, err = module.run_command(["/usr/bin/uname", options[key]])
        if rc != 0:
            warning = "failed to execute uname %s" % options[key]
            module.warnings.append(warning)
            attribute_dict = {}
        else:
            if key == "lpar":
                list["lparid"] = out.strip().split()[0]
                list["lparname"] = out.strip().split()[1]
            elif key == "model":
                list["model"] = out.strip().split(",")[1]
            elif key == "serial":
                list["serial"] = out.strip().split(",")[1]
            else:
                list[key] = out.strip()
    return list


def get_drmode(module):
    drmode = {}
    uname_list = get_uname(module)
    try:
        profile = uname_list['lparname']
        if re.search("[_|-]dr$", profile):
            drmode = True
        else:
            drmode = False
    except BaseException:
        module.warnings.append("Unable to retrieve drmode")
    return drmode


def get_ipfilt(module):
    lijst = []
    cmd = ['/usr/sbin/lsfilt', '-O']
    try:
        p = subprocess.Popen(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    except OSError:
        warning = "Insufficient rights to retrieve ipsec rules"
        module.warnings.append(warning)
        return lijst
    else:
        out, err = p.communicate()
        keys = (
            'fid',
            'action',
            'source',
            'smask',
            'dest',
            'dmask',
            'apply',
            'proto',
            'soper',
            'stype',
            'doper',
            'dtype',
            'routing',
            'dir',
            'log',
            'frag',
            'tunnel',
            'intf',
            'expt',
            'patp',
            'patt',
            'desc')
        for line in out.splitlines():
            values = line.split("|")
            adict = dict(itertools.izip(keys, values))
            lijst.append(adict)
        return lijst


def main():
    all_facts = [
        'oslevel',
        'build',
        'lpps',
        'filesystems',
        'mounts',
        'vgs',
        'lssrc',
        'niminfo',
        'lparstat',
        'uname',
        'drmode',
        'ipfilt']
    default_facts = [
        'oslevel',
        'build',
        'filesystems',
        'mounts',
        'vgs',
        'lssrc',
        'niminfo',
        'lparstat',
        'uname',
        'drmode']
    module = AnsibleModule(
        argument_spec=dict(
            options=dict(type='list', default=['default'])
        ))
    module.warnings = []
    factstoget = []
    if module.params['options'] == ['default']:
        factstoget = default_facts
    elif module.params['options'] == ['all']:
        factstoget = all_facts
    else:
        factstoget = module.params['options']

    facts = {}
    for f in factstoget:
        if f in all_facts:
            facts[f] = getattr(sys.modules[__name__], 'get_%s' % f)(module)
        else:
            warning = "%s is not a fact" % f
            module.warnings.append(warning)

    module.exit_json(changed=False, rc=0, ansible_facts=facts,
                     warnings=module.warnings)


if __name__ == '__main__':
    main()
