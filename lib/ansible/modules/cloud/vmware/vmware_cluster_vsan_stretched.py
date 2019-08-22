#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2019 VMware, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, find_hostsystem_by_name, find_cluster_by_name
from ansible.module_utils.basic import AnsibleModule
from pyVim.connect import SmartConnect, Disconnect
from pyVim.task import WaitForTask
from pyVmomi import vim, vmodl
import sys
import ssl
import atexit
import time
import ansible.module_utils.vsanmgmtObjects
import ansible.module_utils.vsanapiutils


class VMwareVsanStretchedCluster(PyVmomi):
    def __init__(self, module):
        super(VMwareVsanStretchedCluster, self).__init__(module)
        self.module = module

        self.state = module.params['state']
        self.preferedFaultDomain = module.params['preferedFaultDomain']
        self.secondaryFaultDomain = module.params['secondaryFaultDomain']

        self.update = {'witnessHost': False,
                       'prefferedFd': False,
                       'secondaryFd': False}

        self.content, self.vc_mos = self.connect_to_vc_api(module.params['hostname'],
                                                           module.params['username'],
                                                           module.params['password'],
                                                           module.params['port'],
                                                           module.params['validate_certs'])
        self.vsanScSystem = self.vc_mos['vsan-stretched-cluster-system']
        self.vsanConfigSystem = self.vc_mos['vsan-cluster-config-system']

        self.cluster = find_cluster_by_name(module.params['cluster_name'], module.params['datacenter'])
        self.witnessHost = find_hostsystem_by_name(module.params['witnessHost'])

    def connect_to_vc_api(self, hostname, username, password, port, validate_certs):
        # set SSL cert checking
        context = ssl.create_default_context()
        if validate_certs:
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
        else:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        try:
            self.si = SmartConnect(host=hostname,
                                   user=username,
                                   pwd=password,
                                   port=port,
                                   sslContext=context)
        except vim.fault.InvalidLogin as invalid_login:
            self.module.fail_json(msg=invalid_login.msg,
                                  apierror=str(invalid_login))
        except ConnectionError as connection_error:
            self.module.fail_json(msg="Unable to connect to vCenter API ",
                                  apierror=str(connection_error))

        atexit.register(Disconnect, self.si)

        return self.si.RetrieveContent(), ansible.module_utils.vsanapiutils.GetVsanVcMos(self.si._stub, context=context)

    def wait_for_vsanTask(self, vsanTask):
        vcTask = ansible.module_utils.vsanapiutils.ConvertVsanTaskToVcTask(vsanTask, self.si._stub)
        state = WaitForTask(vcTask)

        if state == vim.TaskInfo.State.success:
            changed = True
            result = vcTask.info.state
        else:
            changed = False
            result = vcTask.info.error

        return changed, result

    def process_state(self):
        # object to choose operation
        if not self.module.check_mode:
            vsan_states = {
                'absent': {
                    'absent': self.state_exit_unchanged,
                    'present': self.state_unset_stretched,
                },
                'present': {
                    'absent': self.state_set_stretched,
                    'update': self.state_update_stretched,
                    'present': self.state_exit_unchanged,
                }
            }
        else:
            vsan_states = {
                'absent': {
                    'absent': self.state_exit_unchanged,
                    'present': self.state_exit_checkmode_unset,
                },
                'present': {
                    'absent': self.state_exit_checkmode_set,
                    'update': self.state_exit_checkmode_update,
                    'present': self.state_exit_unchanged,
                }
            }

        # trigger function to to react to state
        vsan_states[self.state][self.current_state()]()

    def current_state(self):
        try:
            preferredFd = self.vsanScSystem.VSANVcGetPreferredFaultDomain(self.cluster)
        except (vim.fault.InvalidState, vmodl.RuntimeFault, vim.fault.VsanFault) as e:
            self.module.fail_json(msg='Fault while checking preffered fault domain: ' + str(e))

        # if preffered fault domain is not set vSAN stretched cluster is not configured
        if preferredFd.preferredFaultDomainId is None:
            return 'absent'

        '''
        if it is set vSAN stretched cluster is present and we have to check for needed changes
        '''
        # state-machine does not care about present or update if desired state is absent
        if self.state == 'absent':
            return 'present'

        # check if witnessHost is correct
        if self.vsanScSystem.VSANVcGetWitnessHosts(self.cluster)[0].host.name != self.witnessHost:
            self.update.witnessHost = True
            return 'update'

        # get current fault domain config
        currentPreferredFdHosts = []
        currentSecondaryFdHosts = []
        for host in self.cluster.host:
            if host.config.vsanHostConfig.faultDomainInfo.name == self.preferedFaultDomain['name']:
                currentPreferredFdHosts.append(host.name)
            elif host.config.vsanHostConfig.faultDomainInfo.name == self.secondaryFaultDomain['name']:
                currentSecondaryFdHosts.append(host.name)
        # check if preffered fault domain is correct
        diffPrefFd = [host for host in currentPreferredFdHosts if host not in self.preferedFaultDomain['hosts']]
        if len(diffPrefFd) > 0:
            self.update.prefferedFd = True
            return 'update'
        # check if secondary fault domain is correct
        diffSecFd = [host for host in currentSecondaryFdHosts if host not in self.secondaryFaultDomain['hosts']]
        if len(diffSecFd) > 0:
            self.update.secondaryFd = True
            return 'update'

        # return present if no changes are detected
        return 'present'

    def state_set_stretched(self):
        '''
        Migrate from non-stretched to stretched cluster
        '''
        # set first and second faultDomain
        firstFdHosts = []
        secondFdHosts = []
        for host in self.cluster.host:
            if host in self.preferedFaultDomain['hosts']:
                firstFdHosts.append(host)
        for host in set(self.cluster.host) - set(firstFdHosts):
            if host in self.secondaryFaultDomain['hosts']:
                secondFdHosts.append(host)
        # create faultDomain config
        faultDomainConfig = vim.VimClusterVSANStretchedClusterFaultDomainConfig(firstFdHosts=firstFdHosts,
                                                                                firstFdName=self.preferedFaultDomain['name'],
                                                                                secondFdHosts=secondFdHosts,
                                                                                secondFdName=self.secondaryFaultDomain['name'])

        # start vSAN stretched cluster migration
        task = self.vsanScSystem.VSANVcConvertToStretchedCluster(cluster=self.cluster,
                                                                 faultDomainConfig=faultDomainConfig,
                                                                 witnessHost=self.witnessHost,
                                                                 preferredFd=self.preferedFaultDomain['name'],
                                                                 diskMapping=self.create_witnessHost_diskMapping(self.witnessHost))

        # wait for migration and return
        changed, result = self.wait_for_vsanTask(task)
        if changed:
            self.module.exit_json(changed=changed, msg=result)
        else:
            self.module.fail_json(msg=result)

    def state_update_stretched(self):
        '''
        Update stretched cluster
        '''
        self.module.fail_json(msg='update stretched cluster not implemented')
        result = ""
        # change witness host
        if self.update.witnessHost:
            task = self.vsanScSystem.VSANVcAddWitnessHost(self.cluster,
                                                          self.witnessHost,
                                                          self.preferedFaultDomain['name'],
                                                          self.create_witnessHost_diskMapping(self.witnessHost))
            witnessChanged, witnessResult = self.wait_for_vsanTask(task)

            # fail if task fails
            if not witnessChanged:
                self.module.fail_json(msg=witnessResult)
            result += witnessResult

        # change preffered fault domain
        faultDomains = []
        if self.update.prefferedFd:
            prefferedFdHosts = []
            for host in self.cluster.host:
                if host in self.preferedFaultDomain['hosts']:
                    prefferedFdHosts.append(host)

            prefferedFdSpec = vim.cluster.VsanFaultDomainSpec(name=self.preferedFaultDomain['name'], hosts=prefferedFdHosts)
            faultDomains.append(prefferedFdSpec)
        # change secondary fault domain
        if self.update.secondaryFd:
            secondaryFdHosts = []
            for host in self.cluster.host:
                if host in self.secondaryFaultDomain['hosts']:
                    secondaryFdHosts.append(host)

            secondaryFdSpec = vim.cluster.VsanFaultDomainSpec(name=self.preferedFaultDomain['name'], hosts=secondaryFdHosts)
            faultDomains.append(secondaryFdSpec)

        # apply changes to fault domains
        if self.update.prefferedFd or self.update.secondaryFd:
            vsanReconfigSpec = vim.VimVsanReconfigSpec(modify=True)
            vsanReconfigSpec.faultDomainsSpec = vim.VimClusterVsanFaultDomainsConfigSpec(faultDomains=faultDomains)
            # Configure Fault Domains
            task = self.vsanConfigSystem.VsanClusterReconfig(self.cluster, vsanReconfigSpec)
            fdChanged, fdResult = self.wait_for_vsanTask(task)

            # fail if task fails
            if not fdChanged:
                self.module.fail_json(msg=fdResult)
            result += " "
            result += fdResult

        self.module.exit_json(changed=True, msg=result)

    def state_unset_stretched(self):
        '''
        Migrate from stretched to non-stretched cluster
        '''
        # remove witness host from cluster. This will disable stretched cluster
        task = self.vsanScSystem.VSANVcRemoveWitnessHost(cluster=self.cluster)

        # wait for migration and return
        changed, result = self.wait_for_vsanTask(task)
        self.module.exit_json(changed=changed, msg=result)

    def state_exit_unchanged(self):
        '''
        Exit without any changes
        '''
        self.module.exit_json(changed=False, msg='nothing to do')

    def create_witnessHost_diskMapping(self, witnessHost):
        '''
        build VsanHostDiskMapping object for witnessHost
        '''
        disks = [result.disk for result in witnessHost.configManager.vsanSystem.QueryDisksForVsan() if result.state == 'eligible']
        diskMapping = None
        if disks:
            ssds = [disk for disk in disks if disk.ssd]
            nonSsds = [disk for disk in disks if not disk.ssd]
        # host with hybrid disks
        if len(ssds) > 0 and len(nonSsds) > 0:
            diskMapping = vim.VsanHostDiskMapping(ssd=ssds[0],
                                                  nonSsd=nonSsds)
        # host with all-flash disks,choose the ssd with smaller capacity for cache layer.
        if len(ssds) > 0 and len(nonSsds) == 0:
            smallerSize = min([disk.capacity.block * disk.capacity.blockSize for disk in ssds])
            smallSsds = []
            biggerSsds = []
            for ssd in ssds:
                size = ssd.capacity.block * ssd.capacity.blockSize
                if size == smallerSize:
                    smallSsds.append(ssd)
                else:
                    biggerSsds.append(ssd)
            diskMapping = vim.VsanHostDiskMapping(ssd=smallSsds[0],
                                                  nonSsd=biggerSsds)

        return diskMapping

    def state_exit_checkmode_set(self):
        '''
        CHECKMODE: Migrate from non-stretched to stretched cluster
        '''
        self.module.exit_json(changed=True, msg='CHECKMODE: Migrate from non-stretched to stretched cluster')

    def state_exit_checkmode_update(self):
        '''
        CHECKMODE: Update stretched cluster
        '''
        self.module.exit_json(changed=True, msg='CHECKMODE: Update stretched cluster')

    def state_exit_checkmode_unset(self):
        '''
        CHECKMODE: Migrate from stretched to non-stretched cluster
        '''
        self.module.exit_json(changed=True, msg='CHECKMODE: Migrate from stretched to non-stretched cluster')


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        cluster_name=dict(type='str',
                          required=True),
        datacenter=dict(type='str',
                        required=True,
                        aliases=['datacenter_name']),
        state=dict(type='str',
                   default='present',
                   choices=['present', 'absent']),
        preferedFaultDomain=dict(type='dict',
                                 required=True,
                                 options=dict(name=dict(type='str', required=True),
                                              hosts=dict(type='list', required=True))),
        secondaryFaultDomain=dict(type='dict',
                                  required=True,
                                  options=dict(name=dict(type='str', required=True),
                                               hosts=dict(type='list', required=True))),
        witnessHost=dict(type='str',
                         required=True))
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    vmware_vsan_stretchedCluster = VMwareVsanStretchedCluster(module)
    vmware_vsan_stretchedCluster.process_state()


if __name__ == '__main__':
    main()
