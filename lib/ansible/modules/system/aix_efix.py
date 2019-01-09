#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Joris Weijters <joris.weijters@gmail.com>
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
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}


DOCUMENTATION = '''
---
author: "Joris Weijters (@molekuul)"
module: 'aix_efix'
short_description: Installs and removes efixes
description:
    - Installs and removes efixes delivered by an nfs mount.
      If "name= ALL" is given, it removes all efixes installed which are not on the share, and installs all efixes which are present on the share, but not currently installed.
      If a single efix is given as a parameter, this will be installed or removed.
version_added: "2.4"
options:
  name:
    description:
    - Name of the efix or ALL for all efixes on the share
    aliases: efix
    default: ALL
    type: list
  state:
    description:
    - State of the efix
    choices: [ present,
               absent,
               installed,
               removed
               ]
    default: present
  nfs_server:
    description:
    - name of the nfs server
    default: { NIM_MASTER }
  nfs_share:
    description:
    - name of the remote directory, if not given, it will be "/export/nim/aix<OSVER>efix"
      where OSVER is  OSVERSION + TL + -SP 
      fi. /export/nim/aix7104-03/efix

notes:
  - the changes are persistent
  - you need root rights to install and remove efixes
  - tested on aix 6.1 and aix 7.1
requirements: [ 'os', 're', 'tempfile', 'shutil', 'glob' ]
'''


EXAMPLES = '''
# Synchronize ALL efixes from the NIM_MASTER on the standard share
- name: Install All efixes
  aix_efix:
    name:
      - ALL

# Install efix IV91487s3 from the nfs_server: nfsserver.local  from the share: /export/nim/aix7104-03/lpp_new
- name: Install efix IV91487s3
  aix_efix:
    name:
      - IV91487s3
    nfs_server: nfsserver.local
    nfs_share: /export/nim/aix7104-03/lpp_new

# Remove efix IV91487s3
- name: remove efix IV91487s3
  aix_efix:
    name:
      - IV91487s3
    state: absent
'''


RETURN = '''
name:
    description: name of the efixes to be installed
    returned: always
    type: list
    sample: ["IV80588s6a"]
msg:
    description: message
    returned: always
    type: list
    sample: ["INFO: removed efixes", ["IV80588s6a"]]
changed:
    description: whether efixes changed or not
    returned: always
    type: boolean
    sample: False
warnings:
    description: if the Prerequisites fail for an efix, a warning is generated
    returned: on warnings
    type: list
    sample: [ "WARNING: Prerequsites Failed for efix: IV92240m3a ",
              "WARNING: Prerequsites Failed for efix: IV91951m3a "
                ]
'''

# Import necessary libraries
import re
import os
import tempfile
import shutil
import glob
from ansible.module_utils.basic import AnsibleModule

# end import modules


def nim_master(module):
    file = '/etc/niminfo'

    try:
        if os.path.exists(file):
            niminfo = dict(
                (k.strip(), v.strip(' "\n')) for k, v in (
                    line.split(
                        ' ', 1)[1].split(
                        '=', 1) for line in (
                        (l for l in open(
                            file, 'r') if l.startswith('export')))))
    except IOError as e:
        module.fail_json(msg="could not determine NIM_MASTER", rc=rc, err=e)
    return niminfo['NIM_MASTER_HOSTNAME']


def efixes_installed(module):
    # emgr -lv2 delivers output in which the folowing lines appear:
    # example:
    # +-----------------------------------------------------------------------------+
    # EFIX ID: 1
    # EFIX LABEL: IV80188s6a
    # +-----------------------------------------------------------------------------+
    # so going through the output and looking for lines with "EFIX LABEL" will
    # deliver the efixes

    allefixesinstalled = []
    emgr = module.get_bin_path('emgr')
    (rc, out, err) = module.run_command("%s %s" % (emgr, '-lv2'))
    if rc != 0:
        module.fail_json(
            msg="ERROR: could not determine current installed efixes",
            rc=rc,
            err=err)
    for line in out.splitlines():
        line = line.rstrip()
        if re.search('EFIX LABEL', line):
            (label, efixinstalled) = line.split(':')
            allefixesinstalled.append(efixinstalled.strip())
    return allefixesinstalled


def nfs_mount(module):
    dirpath = tempfile.mkdtemp()
    nfsserver = module.params['nfs_server']
    nfsshare = module.params['nfs_share']
    nfs_string = nfsserver + ":" + nfsshare
    mount = module.get_bin_path('mount')
    (rc, err, out) = module.run_command("%s %s %s %s" %
                                        (mount, '-o soft', nfs_string, dirpath))
    if rc != 0:
        msg = "ERROR: could not mount: " + nfs_string
        module.fail_json(
            msg=msg,
            err=err,
            rc=rc)
    return dirpath


def nfs_umount(module, path):
    umount = module.get_bin_path('umount')
    (rc, err, out) = module.run_command("%s %s" % (umount, path))
    if rc != 0:
        err = "ERROR: could not unmount" + path + err
        module.fail_json(
            err=err, rc=rc)
    shutil.rmtree(path)


def efixes_at_share(module, path):
    # this function looks into the mounted directory and looks for the fix files
    # The fix files are named: <EFIX>.yymmdd.epkg.Z
    # where     yy is the year in decimals
    #           mm is the month
    #           dd is the day
    #           epkg.Z is the file extension
    efixlist = []
    efixesinpath = [f for f in os.listdir(path) if f.endswith('.epkg.Z')]
    for e in efixesinpath:
        efixlist.append(e.split('.', 1)[0])
    if efixlist == []:
        msg = "WARNING: No efixes found on share"
        nfs_umount(module, path)
        module.exit_json(
            msg=msg, skipped=1, rc=0)
    return efixlist


def remove_efixes(module, list):
    changed = False
    msg = []
    emgr = module.get_bin_path('emgr')
    for efix in list:
        rc = 0
        if module.check_mode:
            params = "-p -r -L"
        else:
            params = "-r -L"
        (rc, out, err) = module.run_command("%s %s %s" % (emgr, params, efix))
        if rc != 0:
            msg = "ERROR: could not remove efix: " + efix + " " + err
            module.fail_json(
                msg=msg,
                err=err,
                rc=rc)
        else:
            changed = True
            msg = ['INFO: removed efixes', list]
    return changed, msg


def install_efixes(module, path, list):
    changed = False
    msg = []
    emgr = module.get_bin_path('emgr')
    for efix in list:
        # because you can only install efixes from the filename,
        # the filename has to be found out
        efixfiles = glob.glob(path + '/' + efix + '*')
        for efixfile in efixfiles:
            rc = 0
            if module.check_mode:
                params = "-p -X -e"
            else:
                params = "-X -e"
            (rc, out, err) = module.run_command(
                "%s %s %s" % (emgr, params, efixfile))
            if rc != 0:
                if 'Prerequisite' in err:
                    module.warnings.append(
                        'WARNING: Prerequsites Failed for efix: %s ' %
                        (efix))
                else:
                    nfs_umount(module, path)
                    msg = "ERROR: could not install efix: " + efixfile + " " + err
                    module.fail_json(
                        msg=msg,
                        err=err,
                        rc=rc)
            else:
                changed = True
                msg = ['INFO: installed efixes', list]
    return changed, msg


def main():
    # initalise
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(default='ALL', aliases=['efix'], type='list'),
            state=dict(choices=[
                'present',
                'absent',
                'installed',
                'removed',
            ], default='present'),
            nfs_server=dict(default='NIM_MASTER', type='str'),
            nfs_share=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    module.warnings = []
    result = {
        'name': module.params['name'],
        'changed': False,
        'msg': [],
        'warnings': module.warnings
    }

    # find which efixes are installed
    efixesinstalled = efixes_installed(module)
    #
    # Remove efix
    if module.params['state'] == 'absent' or module.params[
            'state'] == 'removed':
        # if the mentioned efix is installed, remove it
        # is the name  = ALL remove all efixes
        if module.params['name'][0].upper() == 'ALL':
            # remove all efixes
            (result['changed'], result['msg']) = remove_efixes(
                module, efixesinstalled)
        else:
            # findout if efix is in the efix installed list
            fix2rm = []
            for efix in module.params['name']:
                if efix in efixesinstalled:
                    fix2rm.append(efix)
                    (result['changed'], result['msg']
                     ) = remove_efixes(module, fix2rm)
    #
    # Install efix
    elif module.params['state'] == 'present' or module.params['state'] == 'installed':
        # if the nim_master is requested findout the nim_master an use that as
        # nfsserver
        if module.params['nfs_server'].upper() == 'NIM_MASTER':
            module.params['nfs_server'] = nim_master(module)
        # if the nfs_share is not givven, create a nfs_share
        # /export/nim/aix<OSLEVEL><TL>-<SP>/efix
        if module.params['nfs_share'] is None:
            # get oslevel -s and parse the output to get oslevel, TL and SP
            oslevel = module.get_bin_path('oslevel')
            (rc, out, err) = module.run_command("%s %s" % (oslevel, '-s'))
            if rc != 0:
                module.fail_json(
                    msg='ERROR: Could not determine the oslevel',
                    err=err,
                    rc=rc)
            osver = out[:2]
            ostl = out[5:7]
            ossp = out[7:10]
            module.params['nfs_share'] = '/export/nim/aix' + \
                osver + ostl + ossp + '/efix'
        # Mount the remote filesystem and get the mountpath
        mountpath = nfs_mount(module)
        # find which efixes are at the share
        efixesatshare = efixes_at_share(module, mountpath)
        if module.params['name'][0].upper() != 'ALL':
            # loop through the list of efixes
            efix2install = []
            for efix in module.params['name']:
                # if an efix is requested but it is allready installed, do nothing
                # if an efix is requested, and it is available at the share and it is not allready installed, install it
                # if an efix is requested but it is not available on the share,
                # give an error that it is not available
                if efix not in efixesinstalled:
                    if efix in efixesatshare:
                        # Install efix
                        efix2install.append(efix)
                        (result['changed'], result['msg']) = install_efixes(
                            module, mountpath, efix2install)
                    else:
                        # error, efix is not on share
                        nfs_umount(module, mountpath)
                        module.fail_json(
                            msg='ERROR: efix: %s is not available on share: %s:%s' %
                            (efix, module.params['nfs_server'], module.params['nfs_share']), rc=1)
            # finnished installing efix, unmounting the share
            nfs_umount(module, mountpath)
        else:
            # efix on the system but not on the share must be removed
            # efix on the share but not on the system must be installed
            efixes2remove = []
            efixes2install = []
	    rchanged = False
	    ichanged = False
            for efix in efixesinstalled:
                if efix not in efixesatshare:
                    efixes2remove.append(efix)
            for efix in efixesatshare:
                if efix not in efixesinstalled:
                    efixes2install.append(efix)
            # remove the filesets
            if len(efixes2remove) != 0:
                (rchanged, result['msg']) = remove_efixes(
                    module, efixes2remove)
            # install the filesets
            if len(efixes2install) != 0:
                (ichanged, resultmsg2add) = install_efixes(
                    module, mountpath, efixes2install)
                result['msg'].append(resultmsg2add)
	    result['changed'] = rchanged or ichanged
            # finnished installing efixes, unmounting the share
            nfs_umount(module, mountpath)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
