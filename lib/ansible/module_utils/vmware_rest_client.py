# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback

REQUESTS_IMP_ERR = None
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    REQUESTS_IMP_ERR = traceback.format_exc()
    HAS_REQUESTS = False

PYVMOMI_IMP_ERR = None
try:
    from pyVim import connect
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    PYVMOMI_IMP_ERR = traceback.format_exc()
    HAS_PYVMOMI = False

VSPHERE_IMP_ERR = None
try:
    from com.vmware.vapi.std_client import DynamicID
    from vmware.vapi.vsphere.client import create_vsphere_client
    from com.vmware.vapi.std.errors_client import Unauthorized
    from com.vmware.content.library_client import Item
    from com.vmware.vcenter_client import (Folder,
                                           Datacenter,
                                           ResourcePool,
                                           Datastore,
                                           Cluster,
                                           Host)
    HAS_VSPHERE = True
except ImportError:
    VSPHERE_IMP_ERR = traceback.format_exc()
    HAS_VSPHERE = False

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import env_fallback, missing_required_lib


class VmwareRestClient(object):
    def __init__(self, module):
        """
        Constructor

        """
        self.module = module
        self.params = module.params
        self.check_required_library()
        self.api_client = self.connect_to_vsphere_client()

    # Helper function
    def get_error_message(self, error):
        """
        Helper function to show human readable error messages.
        """
        err_msg = []
        if not error.messages:
            if isinstance(error, Unauthorized):
                return "Authorization required."
            return "Generic error occurred."

        for err in error.messages:
            err_msg.append(err.default_message % err.args)

        return " ,".join(err_msg)

    def check_required_library(self):
        """
        Check required libraries

        """
        if not HAS_REQUESTS:
            self.module.fail_json(msg=missing_required_lib('requests'),
                                  exception=REQUESTS_IMP_ERR)
        if not HAS_PYVMOMI:
            self.module.fail_json(msg=missing_required_lib('PyVmomi'),
                                  exception=PYVMOMI_IMP_ERR)
        if not HAS_VSPHERE:
            self.module.fail_json(
                msg=missing_required_lib('vSphere Automation SDK',
                                         url='https://code.vmware.com/web/sdk/65/vsphere-automation-python'),
                exception=VSPHERE_IMP_ERR)

    @staticmethod
    def vmware_client_argument_spec():
        return dict(
            hostname=dict(type='str',
                          fallback=(env_fallback, ['VMWARE_HOST'])),
            username=dict(type='str',
                          fallback=(env_fallback, ['VMWARE_USER']),
                          aliases=['user', 'admin']),
            password=dict(type='str',
                          fallback=(env_fallback, ['VMWARE_PASSWORD']),
                          aliases=['pass', 'pwd'],
                          no_log=True),
            protocol=dict(type='str',
                          default='https',
                          choices=['https', 'http']),
            validate_certs=dict(type='bool',
                                fallback=(env_fallback, ['VMWARE_VALIDATE_CERTS']),
                                default=True),
        )

    def connect_to_vsphere_client(self):
        """
        Connect to vSphere API Client with Username and Password

        """
        username = self.params.get('username')
        password = self.params.get('password')
        hostname = self.params.get('hostname')
        session = requests.Session()
        session.verify = self.params.get('validate_certs')

        if not all([hostname, username, password]):
            self.module.fail_json(msg="Missing one of the following : hostname, username, password."
                                      " Please read the documentation for more information.")

        client = create_vsphere_client(
            server=hostname,
            username=username,
            password=password,
            session=session)
        if client is None:
            self.module.fail_json(msg="Failed to login to %s" % hostname)

        return client

    def get_tags_for_object(self, tag_service, tag_assoc_svc, dobj):
        """
        Return list of tag objects associated with an object
        Args:
            dobj: Dynamic object
            tag_service: Tag service object
            tag_assoc_svc: Tag Association object
        Returns: List of tag objects associated with the given object
        """
        tag_ids = tag_assoc_svc.list_attached_tags(dobj)
        tags = []
        for tag_id in tag_ids:
            tags.append(tag_service.get(tag_id))
        return tags

    def get_vm_tags(self, tag_service, tag_association_svc, vm_mid=None):
        """
        Return list of tag name associated with virtual machine
        Args:
            tag_service:  Tag service object
            tag_association_svc: Tag association object
            vm_mid: Dynamic object for virtual machine

        Returns: List of tag names associated with the given virtual machine

        """
        tags = []
        if vm_mid is None:
            return tags
        dynamic_managed_object = DynamicID(type='VirtualMachine', id=vm_mid)

        temp_tags_model = self.get_tags_for_object(tag_service, tag_association_svc, dynamic_managed_object)
        for t in temp_tags_model:
            tags.append(t.name)
        return tags

    def get_library_item_by_name(self, name):
        """
        Returns the identifier of the library item with the given name.

        Args:
            name (str): The name of item to look for

        Returns:
            str: The item ID or None if the item is not found
        """
        find_spec = Item.FindSpec(name=name)
        item_ids = self.api_client.content.library.Item.find(find_spec)
        item_id = item_ids[0] if item_ids else None
        return item_id

    def get_datacenter_by_name(self, datacenter_name):
        """
        Returns the identifier of a datacenter
        Note: The method assumes only one datacenter with the mentioned name.
        """
        filter_spec = Datacenter.FilterSpec(names=set([datacenter_name]))
        datacenter_summaries = self.api_client.vcenter.Datacenter.list(filter_spec)
        datacenter = datacenter_summaries[0].datacenter if len(datacenter_summaries) > 0 else None
        return datacenter

    def get_folder_by_name(self, datacenter_name, folder_name):
        """
        Returns the identifier of a folder
        with the mentioned names.
        """
        datacenter = self.get_datacenter_by_name(datacenter_name)
        if not datacenter:
            return None
        filter_spec = Folder.FilterSpec(type=Folder.Type.VIRTUAL_MACHINE,
                                        names=set([folder_name]),
                                        datacenters=set([datacenter]))
        folder_summaries = self.api_client.vcenter.Folder.list(filter_spec)
        folder = folder_summaries[0].folder if len(folder_summaries) > 0 else None
        return folder

    def get_resource_pool_by_name(self, datacenter_name, resourcepool_name):
        """
        Returns the identifier of a resource pool
        with the mentioned names.
        """
        datacenter = self.get_datacenter_by_name(datacenter_name)
        if not datacenter:
            return None
        names = set([resourcepool_name]) if resourcepool_name else None
        filter_spec = ResourcePool.FilterSpec(datacenters=set([datacenter]),
                                              names=names)
        resource_pool_summaries = self.api_client.vcenter.ResourcePool.list(filter_spec)
        resource_pool = resource_pool_summaries[0].resource_pool if len(resource_pool_summaries) > 0 else None
        return resource_pool

    def get_datastore_by_name(self, datacenter_name, datastore_name):
        """
        Returns the identifier of a datastore
        with the mentioned names.
        """
        datacenter = self.get_datacenter_by_name(datacenter_name)
        if not datacenter:
            return None
        names = set([datastore_name]) if datastore_name else None
        filter_spec = Datastore.FilterSpec(datacenters=set([datacenter]),
                                           names=names)
        datastore_summaries = self.api_client.vcenter.Datastore.list(filter_spec)
        datastore = datastore_summaries[0].datastore if len(datastore_summaries) > 0 else None
        return datastore

    def get_cluster_by_name(self, datacenter_name, cluster_name):
        """
        Returns the identifier of a cluster
        with the mentioned names.
        """
        datacenter = self.get_datacenter_by_name(datacenter_name)
        if not datacenter:
            return None
        names = set([cluster_name]) if cluster_name else None
        filter_spec = Cluster.FilterSpec(datacenters=set([datacenter]),
                                         names=names)
        cluster_summaries = self.api_client.vcenter.Cluster.list(filter_spec)
        cluster = cluster_summaries[0].cluster if len(cluster_summaries) > 0 else None
        return cluster

    def get_host_by_name(self, datacenter_name, host_name):
        """
        Returns the identifier of a Host
        with the mentioned names.
        """
        datacenter = self.get_datacenter_by_name(datacenter_name)
        if not datacenter:
            return None
        names = set([host_name]) if host_name else None
        filter_spec = Host.FilterSpec(datacenters=set([datacenter]),
                                      names=names)
        host_summaries = self.api_client.vcenter.Host.list(filter_spec)
        host = host_summaries[0].host if len(host_summaries) > 0 else None
        return host

    @staticmethod
    def search_svc_object_by_name(service, svc_obj_name=None):
        """
        Return service object by name
        Args:
            service: Service object
            svc_obj_name: Name of service object to find

        Returns: Service object if found else None

        """
        if not svc_obj_name:
            return None

        for svc_object in service.list():
            svc_obj = service.get(svc_object)
            if svc_obj.name == svc_obj_name:
                return svc_obj
        return None
