# -*- coding: utf-8 -*-

# (c) 2017, Prasanna Nanda < pnanda@cloudsimple.com >
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

from pyVmomi import vim, pbm
from pyVim.connect import SoapStubAdapter
import time
import re
import logging


class SPBMClient(object):

    def __init__(self, vc_si, hostname, version="version2"):
        """
        Creates a Service Instance for VMware Profile Based Management
        :param vc_si: vCenter Service Instance
        :param version: PBM Version
        """
        option_manager = vc_si.RetrieveContent().setting
        hostname_option = option_manager.QueryOptions("config.vpxd.hostnameUrl")
        client_stub = vc_si._GetStub()
        session_cookie = client_stub.cookie.split('"')[1]
        ssl_context = client_stub.schemeArgs.get('context')
        additional_headers = {'vcSessionCookie': session_cookie}
        stub = SoapStubAdapter(host=hostname, path="/pbm/sdk", version="pbm.version.version2",
                               sslContext=ssl_context, requestContext=additional_headers)
        self.vc_si = vc_si
        self.pbm_si = pbm.ServiceInstance("ServiceInstance", stub)
        self.pbm_content = self.pbm_si.PbmRetrieveServiceContent()

    def get_pbmsi(self):
        """
        Returns PBM Service Instance
        :return: PBM Service Instance
        """
        return self.pbm_si

    def get_pbmcontent(self):
        """
        Returns PBM Content
        :return: PBM RetrieveContent()
        """
        return self.pbm_content

    def get_profilemgr(self):
        """
        Gets MoRef to Profile Manager
        :return: Profile Manager
        """
        return self.pbm_content.profileManager

    def get_compliancemgr(self):
        """
        Gets MoRef to Profile Compliance Manager
        """
        return self.pbm_content.complianceManager

    def get_profiles(self):
        """
        Gets list of Storage Profiles on vCenter
        :return: list of Storage Profiles on vCenter
        """
        pm = self.get_profilemgr()
        profileIds = pm.PbmQueryProfile(resourceType=pbm.profile.ResourceType(resourceType="STORAGE"), profileCategory="REQUIREMENT")

        profiles = []
        if len(profileIds) > 0:
            return pm.PbmRetrieveContent(profileIds=profileIds)
        return None

    def return_cap_meta_data(self, metadatas, keyname):
        """
        Return Storage Profile capability metadata
        """
        for metadata in metadatas:
            for capabilityMetadata in metadata.capabilityMetadata:
                if keyname == capabilityMetadata.id.id:
                    return capabilityMetadata
        return None

    def buildCapability(self, capabilityName, value):
        metadatas = self.get_profilemgr().FetchCapabilityMetadata()
        capabilityMeta = self.return_cap_meta_data(metadatas=metadatas, keyname=capabilityName)
        if capabilityMeta is None:
            raise Exception('capabilityMeta is None')
        prop = pbm.PbmCapabilityPropertyInstance()
        prop.id = capabilityName
        prop.value = value
        rule = pbm.PbmCapabilityConstraintInstance()
        rule.propertyInstance.append(prop)

        capability = pbm.PbmCapabilityInstance()
        capability.id = capabilityMeta.id
        capability.constraint.append(rule)
        return capability

    def delete_storage_profile(self, profile_name=None, force=False):
        """
        Deletes a Storage Profile
        """
        profiles = self.get_profiles()
        for profile in profiles:
            if profile.name == profile_name:
                return self.get_profilemgr().PbmDelete(profileId=[profile.profileId])

    def check_compliance_vm(self, vm):
        """
        Checks if a VM is compliant with attached profile
        """
        pbm_object_ref = pbm.ServerObjectRef(key=str(vm._moId), objectType="virtualMachine", serverUuid=self.vc_si.content.about.instanceUuid)
        compliance_status = {}
        compliance_status['vm_name'] = vm.name
        results = self.get_compliancemgr().PbmCheckRollupCompliance(entity=[pbm_object_ref])
        compliance_result = []
        for result in results:
            compliance_status['overallComplianceStatus'] = result.overallComplianceStatus
            if result.result:
                subresults = result.result
                for complianceresult in subresults:
                    individual_compliance = {}
                    individual_compliance['checkTime'] = complianceresult.checkTime
                    individual_compliance['complianceStatus'] = complianceresult.complianceStatus
                    individual_compliance['key'] = complianceresult.entity.key
                    individual_compliance['objectType'] = complianceresult.entity.objectType
                    compliance_result.append(individual_compliance)
        compliance_status['result'] = compliance_result
        return compliance_status

    def get_ds_default_profile(self, ds):
        """
        Get Default Profile for a datastore
        """
        placementhub = pbm.placement.PlacementHub(hubId=ds._moId, hubType='Datastore')
        default_profile = self.get_profilemgr().PbmQueryDefaultRequirementProfile(hub=placementhub)
        if default_profile:
            return default_profile
        return None

    def create_storage_profile(self, profile_name=None, description="Sample Storage Profile", rules=[]):
        """
        Creates a Storage Profile
        """
        metadatas = self.get_profilemgr().FetchCapabilityMetadata()
        res_types = self.get_profilemgr().FetchResourceType()
        # Only supported resurce type is storage
        res_type = res_types[0]
        create_spec = pbm.profile.CapabilityBasedProfileCreateSpec()
        create_spec.name = profile_name
        create_spec.description = description
        create_spec.resourceType = res_type
        constraints = pbm.PbmCapabilitySubProfileConstraints()
        rule_number = 1
        for rule in rules:
            ruleSet = pbm.PbmCapabilitySubProfile()
            capabilities = []
            for key in rule.keys():
                capabilities.append(self.buildCapability(key, rule[key]))
            ruleSet.capability.extend(capabilities)
            ruleSet.name = 'Rule-Set ' + str(rule_number)
            rule_number = rule_number + 1
            constraints.subProfiles.append(ruleSet)
        create_spec.constraints = constraints
        return self.get_profilemgr().PbmCreate(createSpec=create_spec)
