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
                    'version': '1.0'}


DOCUMENTATION = '''
---
author: "Joris Weijters (@molekuul)"
module: aix_nimclient
short_description: installs software using the nimclient, and removes software
description:
    - installs software at the nimclient using nimclient command and removes software using local commands also updates ALL to latest version
version_added: "2.3"
options:
  name:
    description:
    - Name of the fileset to install or update_all to update all filesets to latest level
    alias: filesets
    type: list
  state:
    description:
    - State of the fileset or nimclient to be
    choices: [
              commit,
              present,
              absent,
              installed,
              removed,
              allocate,
              deallocate,
              reset
              ]
    default : present
    type: string
  lpp_source:
    description:
    - Name of the lpp_source at the nimserver to be used for installation
    type: string
  spot:
    description:
    - Name of the Spot at the nimserver
    type: string
  commit:
    description:
    - boolean for committing the fileset during install or not
    type: bool
    default: True
  installp_flags:
    description:
    - installp flags
    type: string
    default:'acgwXY'

notes:
  - The changes are persistent across reboots.
  - You need root rights to install or remove software
  - tested on AIX 6.1 and 7.1.
requirements: [ 're' ]
'''

EXAMPLES = '''
- name: install latest version of OpenGL.OpenGL_X.rte.soft from lpp_source lppsource_aix6109-06
  aix_nimclient:
    name:
      - OpenGL.OpenGL_X.rte.soft
    lpp_source: lppsource_aix6109-06

- name: install latest version of OpenGL.OpenGL_X.rte.soft from lpp_source lppsource_aix6109-06 and apply only
  aix_nimclient:
    name:
      - OpenGL.OpenGL_X.rte.soft
    lpp_source: lppsource_aix6109-06
    commit: False

- name: install version 6.1.9.30 of OpenGL.OpenGL_X.rte.soft from lpp_source lppsource_aix6109-06
  aix_nimclient:
    name:
      - OpenGL.OpenGL_X.rte.soft 6.1.9.30
    lpp_source: lppsource_aix6109-06

- name: remove fileset OpenGL.OpenGL_X.rte.soft
  aix_nimclient:
  name:
    - OpenGL.OpenGL_X.rte.soft
  state: absent

- name: commit fileset OpenGL.OpenGL_X.rte.soft
  aix_nimclient:
  name:
    - OpenGL.OpenGL_X.rte.soft
  state: commit

# install all filesets to latest level f.i. install a TL or ML
- name: update all filesets to latest level from lpp_source lppsource_aix6109-06
  aix_nimclient:
    name:
      - update_all
    lpp_source: lppsource_aix6109-06

- name: allocate spot and lpp_source to the nimclient
  aix_nimclient:
    lpp_source: lppsource_aix6109-06
    spot: spot_aix6109-06
    state: allocate

- name: deallocate all resources from the nimclient
  aix_nimclient:
    state: deallocate

- name: reset the nimclient
  aix_nimclient:
    state: reset
'''

RETURN = '''



'''

# Import necessary libraries
import re
from ansible.module_utils.basic import AnsibleModule
from distutils.version import LooseVersion

# end import modules
# start defining the functions


# internal procedures

def _check(module, resourcename):
    cmd = "/usr/sbin/nimclient -l " + resourcename
    rc, out, err = module.run_command(cmd)
    if rc == 0:
        if err != '':
            msg = "ERROR: there is no NIM object named " + resourcename
            module.fail_json(
                msg=msg, err=err, rc=1)
    else:
        msg = "ERROR: could not get state of nimobject: " + resourcename
        module.fail_json(
            msg=msg, err=err, rc=rc)
    return True


def _check_fileset_installed(module, filesetname):
    reqcmd = "/usr/bin/lslpp -Lcq " + filesetname
    rc, out, err = module.run_command(reqcmd)
    if rc == 0:
        res = True
    elif "not installed" in err:
        res = False
    else:
        msg = "ERROR: recieving install status for fileset " + filesetname
        module.fail_json(
            msg=msg, err=msg, rc=rc)
    return res

def _check_fileset_install_state(module, filesetname):
    reqcmd = "/usr/bin/lslpp -Lcq " + filesetname
    rc, out, err = module.run_command(reqcmd)
    if rc == 0:
        outsplit = out.split(':')
        install_state = outsplit[5]
    return install_state


def _check_fileset_type(module, filesetname):
    reqcmd = "/usr/bin/lslpp -Lcq " + filesetname
    rc, out, err = module.run_command(reqcmd)
    if rc == 0:
        outsplit = out.split(':')
        filesettype = outsplit[6]
        if outsplit[6] == "R":
            filesettype = 'RPM'
        elif outsplit[6] == " " or outsplit[6] == "F":
            filesettype = 'LPP'
        else:
            msg = "ERROR: Unable to determine the fileset type of fileset: " + filesetname
            module.fail_json(
                msg=msg, err=err, rc=rc)
    else:
        msg = "ERROR: Fileset: " + filesetname + " not installed"
        module.fail_json(
            msg=msg, err=err, rc=rc)
    return filesettype

# functions


def allocate(module):
    # allocate resources to the nimclient
    # build the options
    result = {}
    cmd = ['/usr/sbin/nimclient']
    options = ['-o', 'allocate']
    msg = []
    if module.params['lpp_source'] is not None:
        option = "lpp_source=" + module.params['lpp_source']
        options.append('-a')
        options.append(option)
        msg.append(module.params['lpp_source'])
    if module.params['spot'] is not None:
        option = "spot=" + module.params['spot']
        options.append('-a')
        options.append(option)
        msg.append(module.params['spot'])
    cmd += options
    rc, out, err = module.run_command(cmd)
    if rc != 0:
        msg = "ERROR: could not allocate resources: " + \
            module.params['lpp_source'] + " " + module.params['spot']
        module.fail_json(
            msg=msg, rc=rc, err=err)
    else:
        result['msg'] = "SUCCESS: resources " + ' '.join(msg) + " allocated"
        result['changed'] = True
    return result


def deallocate(module):
    # deallocate resources
    result = {}
    cmd = ['/usr/sbin/nimclient']
    options = ['-o', 'deallocate', '-a', 'subclass=all']
    cmd += options
    rc, out, err = module.run_command(cmd)
    if rc != 0:
        msg = "ERROR: could not deallocate resources: "
        module.fail_json(
            msg=msg, rc=rc, err=err)
    else:
        result['msg'] = "SUCCESS: All resources deallocated"
        result['changed'] = True
    return result


def reset(module):
    # first deallocate resources
    # then reset nimclient
    result = {}
    result = deallocate(module)
    cmd = ['/usr/sbin/nimclient']
    options = ['-F', '-o', 'reset']
    cmd += options
    rc, out, err = module.run_command(cmd)
    if rc != 0:
        msg = "ERROR: could not reset the nimclient"
        module.fail_json(
            msg=msg, rc=rc, err=err)
    else:
        result['msg'] = "SUCCESS: All resources deallocated and resetted"
        result['changed'] = True
    return result


def uninstall(module):
    # first findout what the type of fileset it is with lslpp
    # then remove the fileset with installp or rpm
    result = {}
    result['msg'] = "SUCCESS: "
    for fileset in module.params['name']:
        fileset = fileset.split()[0]
        if _check_fileset_installed(module, fileset):
            filesettype = _check_fileset_type(module, fileset)
            if filesettype == 'RPM':
                rmcmd = "rpm -e " + fileset
            elif filesettype == 'LPP':
                rmcmd = "installp -gu " + fileset
            else:
                msg = "ERROR: install type of fileset: " + fileset + " not known"
                module.fail_json(
                    msg=msg, err=err, rc='1')
            # remove the fileset
            rc, out, err = module.run_command(rmcmd)
            if rc != 0:
                msg = "ERROR: Fileset: " + fileset + " not removed"
                module.fail_json(
                    msg=msg, err=err, rc=rc)
            else:
                result['msg'] = result['msg'] + \
                    " Fileset: " + fileset + " removed"
                result['changed'] = True
    return result


def commit(module):
    # This function will commit applied filesets
    # find out if fileset is installed
    # findout if the fileset is applied or commited
    # if fileset is applied, commit the fileset including requisites
    result = {}
    result['changed'] = False
    result['msg'] = ""
    for fileset in module.params['name']:
        if _check_fileset_installed(module, fileset):
            fileset_state = _check_fileset_install_state(module, fileset)
            if fileset_state == "A":
                cmd = "installp -gc " + fileset
                rc, out, err = module.run_command(cmd)
                if rc != 0:
                    msg = "ERROR: could not commit fileset: " + fileset
                    module.fail_json(
                        msg=msg, err=err, rc=rc)
                else:
                    result['msg'] = result['msg'] + \
                        " Fileset: " + fileset + " COMMITTED"
                    result['changed'] = True

            elif fileset_state == "C":
                result['msg'] = result['msg'] + fileset + " is already commited"
            else:
                msg = "ERROR: install_state of fileset: " + fileset + \
                    " is not applied or commited: " + fileset_state
                module.fail_json(msg=msg)
    return result


def install(module):
    # This function will install individual filesets
    # findout what version is installed
    # findout what version in in the lppsource ( resource)
    # and if the fileset is in the lpp_source
    # if the version in the lpp source is newer, install newer version if a
    # version is not specified, otherwise install specified version
    result = {}
    result['changed'] = False
    list_filesets_to_install = []
    fsversion_in_lppsource = {}
    requested_version = ''
    for fileset in module.params['name']:
        # if fileset is installed check the version of installed fileset
        if len(fileset.split()) == 2:
            filesetname, requested_version = fileset.split()
        else:
            filesetname = fileset.split()[0]
        # if the fileset in an RPM, it might the version of the RPM in included in the name
        if _check_fileset_installed(module, filesetname):
            cmd = "/usr/sbin/nimclient -o showres -a resource=" + \
                module.params['lpp_source']
            rc, out, err = module.run_command(cmd)
            # output is like:
            #
            # xlsmp.rte                                                          ALL  @@I:xlsmp.rte _all_filesets
            # + 3.1.0.6  SMP Runtime Library                                         @@I:xlsmp.rte 3.1.0.6
            #  @ 4.1.2.0  SMP Runtime Library                                         @@I:xlsmp.rte 4.1.2.0
            #
            #  cdrecord                                                           ALL  @@R:cdrecord _all_filesets
            #  @@R:cdrecord-1.9-9 1.9-9
            #
            # first find all line with an @@
            # Then remove all line with "ALL"
            # Then split the the lines with @@. We keep output like
            # I:xlsmp.rte 3.1.0.6
            # I:xlsmp.rte 4.1.2.0
            # R:cdrecord-1.9-9 1.9-9
            # if the fileset is an RPM ( starts with an R )
            # then stip the version name of the filesetname

            if rc == 0:
                for line in out.splitlines():
                    line = line.rstrip()
                    if re.search(
                            '@@[A-Z]:', line):  # only all lines with @@ in the line
                        if not "ALL" in line:
                            restline = line.split('@@')
                            filesettype = restline[1].split(':')[0]  # find the fileset type ( R = RPM , I/S = LPP )
                            fs, ver = restline[1].split(':')[1].split()
                            if filesettype == "R":
                                fs = re.split('-[0-9]+', fs)[0]  # remove the version number from the filesetname
                            if fs in fsversion_in_lppsource.keys():
                                if LooseVersion(ver) > LooseVersion(
                                        fsversion_in_lppsource[fs]):
                                    fsversion_in_lppsource[fs] = ver
                            else:
                                fsversion_in_lppsource[fs] = ver

                if not filesetname in fsversion_in_lppsource.keys():
                    msg = "ERROR: fileset: " + fileset + \
                        " is not avalable in LPP_SOURCE: " + module.params['lpp_source']
                    module.fail_json(
                        msg=msg, err=err, rc=rc)
            else:
                msg = "ERROR: could not retrieve fileset level on fileset: " + fileset
                module.fail_json(
                    msg=msg, err=err, rc=rc)

            # check fileset version
            fileset_version_installed = ""
            cmd = "/usr/bin/lslpp -Lqc " + filesetname
            rc, out, err = module.run_command(cmd)
            if rc == 0:
                fileset_version_installed = out.split(":")[2].strip()
            else:
                msg = "ERROR: cant determine current installed version"
                module.fail_json(
                    msg=msg, err=err, rc=rc)
            # if installed version < requested version:  install requested version if requested version is available
            # if no requested version: install latest version
            # if installed version => requested version: Do nothing
            if not requested_version == '':
                if LooseVersion(fileset_version_installed) < LooseVersion(
                        requested_version):
                    list_filesets_to_install.append(fileset)
            else:
                if LooseVersion(fileset_version_installed) < LooseVersion(
                        fsversion_in_lppsource[fileset]):
                    list_filesets_to_install.append(fileset)
        else:
            list_filesets_to_install.append(fileset)
    # install the filesets is there is a list of filesets to install
    if list_filesets_to_install:
        list_filesets_to_install_str = ' '.join(list_filesets_to_install)
        cmd = "/usr/sbin/nimclient -o cust -a installp_flags=" + module.params['installp_flags'] + " -a lpp_source=" + \
            module.params['lpp_source'] + " -a filesets=" + '"' + list_filesets_to_install_str + '"'
        rc, out, err = module.run_command(cmd)
        if rc == 0:
            result['changed'] = True
            result['msg'] = "SUCCESS: filesets: " + \
                list_filesets_to_install_str + " installed"
        else:
#            msg = "ERROR: installing filesets: " + list_filesets_to_install_str + " Failed" + cmd
            msg = ("ERROR: installing filesets: " +
                   list_filesets_to_install_str + " Failed. Command used: " +
                   cmd)
            module.fail_json(
                msg=msg, err=err, rc=rc)
    return result


def update(module):
    # this function will do an update_all
    # it needs the lpp_source and runs the nim -o cust -a installp_flags acgwXY
    result = {}
    cmd = "/usr/sbin/nimclient -o cust -a installp_flags=" + module.params['installp_flags'] + \
          " -a lpp_source=" + module.params['lpp_source'] + " -a fixes=update_all"
    rc, out, err = module.run_command(cmd)

    if rc == 0:
        result['changed'] = True
        result['msg'] = "SUCCESS: All filesets updated to latest version"
    else:
        if 'No filesets on the media could be used to update' in err:
            result['changed'] = False
            result[
                'msg'] = "INFO: No filesets on the media to update the installed filesets"
        else:
            msg = "ERROR: updateing filesets failed" + out
            module.fail_json(
                msg=msg, err=err, rc=rc)
    return result


def main():
    # initialize
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='list', aliases=['filesets']),
            state=dict(choices=[
                'present',
                'commit',
                'absent',
                'installed',
                'removed',
                'allocate',
                'deallocate',
                'reset',
            ], default='present'),
            lpp_source=dict(type='str'),
            spot=dict(type='str'),
            commit=dict(type='bool', default='True'),
            installp_flags=dict(type='str', default='acgwXY'),
        ),
    )

    result = {
        'name': module.params['state'],
        'changed': False,
        'msg': "module did do nothing"
    }

    # Find commandline strings
    nimclient = module.get_bin_path('nimclient')
    lslpp = module.get_bin_path('lslpp')
    rpm = module.get_bin_path('rpm')
    rc = 0

    # remove the installp commit flag if commit is False
    if not module.params['commit']:
        new_flags = module.params['installp_flags'].replace("c", "")
        module.params['installp_flags'] = new_flags

    if module.params['state'] == 'allocate':
        if module.params['lpp_source'] is not None:
            _check(module, module.params['lpp_source'])
        if module.params['spot'] is not None:
            _check(module, module.params['spot'])
        if module.params['spot'] is None and module.params[
                'lpp_source'] is None:
            msg = "ERROR: give at least the spot or lpp_source to allocate"
            module.fail_json(
                msg=msg, rc=1)
        result = allocate(module)

    if module.params['state'] == 'deallocate':
        result = deallocate(module)

    if module.params['state'] == 'commit':
        result = commit(module)

    if module.params['state'] == 'reset':
        result = reset(module)

    if module.params['state'] == 'absent' or module.params[
            'state'] == 'removed':
        result = uninstall(module)
    if module.params['state'] == 'present' or module.params[
            'state'] == 'installed':
        if module.params['lpp_source'] is None:
            msg = "ERROR: lpp_source may not be empty"
            module.fail_json(
                msg=msg, rc=1)
        else:
            _check(module, module.params['lpp_source'])
        if "update_all" in module.params['name']:
            result = update(module)
        else:
            result = install(module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
