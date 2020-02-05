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
            port=dict(type='int',
                      default=443,
                      fallback=(env_fallback, ['VMWARE_PORT'])),
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
        port = self.params.get('port')
        session = requests.Session()
        session.verify = self.params.get('validate_certs')

        if not all([hostname, username, password]):
            self.module.fail_json(msg="Missing one of the following : hostname, username, password."
                                      " Please read the documentation for more information.")

        client = create_vsphere_client(
            server="%s:%s" % (hostname, port),
            username=username,
            password=password,
            session=session)
        if client is None:
            self.module.fail_json(msg="Failed to login to %s" % hostname)

        return client

    def get_tags_for_object(self, tag_service=None, tag_assoc_svc=None, dobj=None):
        """
        Return list of tag objects associated with an object
        Args:
            dobj: Dynamic object
            tag_service: Tag service object
            tag_assoc_svc: Tag Association object
        Returns: List of tag objects associated with the given object
        """
        # This method returns list of tag objects only,
        # Please use get_tags_for_dynamic_obj for more object details
        tags = []
        if not dobj:
            return tags

        if not tag_service:
            tag_service = self.api_client.tagging.Tag

        if not tag_assoc_svc:
            tag_assoc_svc = self.api_client.tagging.TagAssociation

        tag_ids = tag_assoc_svc.list_attached_tags(dobj)

        for tag_id in tag_ids:
            tags.append(tag_service.get(tag_id))

        return tags

    def get_tags_for_dynamic_obj(self, dobj=None):
        """
        Return list of tag object details associated with object
        Args:
            mid: Dynamic object for specified object

        Returns: List of tag object details associated with the given object

        """
        tags = []
        if dobj is None:
            return tags

        temp_tags_model = self.get_tags_for_object(dobj)

        category_service = self.api_client.tagging.Category

        for tag_obj in temp_tags_model:
            tags.append({
                'id': tag_obj.id,
                'category_name': category_service.get(tag_obj.category_id).name,
                'name': tag_obj.name,
                'description': tag_obj.description,
                'category_id': tag_obj.category_id,
            })

        return tags

    def get_tags_for_cluster(self, cluster_mid=None):
        """
        Return list of tag object associated with cluster
        Args:
            cluster_mid: Dynamic object for cluster

        Returns: List of tag object associated with the given cluster

        """
        dobj = DynamicID(type='cluster', id=cluster_mid)
        return self.get_tags_for_dynamic_obj(dobj)

    def get_tags_for_hostsystem(self, hostsystem_mid=None):
        """
        Return list of tag object associated with host system
        Args:
            hostsystem_mid: Dynamic object for host system

        Returns: List of tag object associated with the given host system

        """
        dobj = DynamicID(type='HostSystem', id=hostsystem_mid)
        return self.get_tags_for_dynamic_obj(dobj)

    def get_tags_for_vm(self, vm_mid=None):
        """
        Return list of tag object associated with virtual machine
        Args:
            vm_mid: Dynamic object for virtual machine

        Returns: List of tag object associated with the given virtual machine

        """
        dobj = DynamicID(type='VirtualMachine', id=vm_mid)
        return self.get_tags_for_dynamic_obj(dobj)

    def get_vm_tags(self, tag_service=None, tag_association_svc=None, vm_mid=None):
        """
        Return list of tag name associated with virtual machine
        Args:
            tag_service:  Tag service object
            tag_association_svc: Tag association object
            vm_mid: Dynamic object for virtual machine

        Returns: List of tag names associated with the given virtual machine

        """
        # This API returns just names of tags
        # Please use get_tags_for_vm for more tag object details
        tags = []
        if vm_mid is None:
            return tags

        temp_tags_model = self.get_tags_for_object(
            tag_service=tag_service,
            tag_assoc_svc=tag_association_svc,
            dobj=vm_mid
        )

        for tag_obj in temp_tags_model:
            tags.append(tag_obj.name)

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

    def get_tag_by_name(self, tag_name=None):
        """
        Return tag object by name
        Args:
            tag_name: Name of tag

        Returns: Tag object if found else None
        """
        if not tag_name:
            return None

        return self.search_svc_object_by_name(service=self.api_client.tagging.Tag, svc_obj_name=tag_name)

    def get_category_by_name(self, category_name=None):
        """
        Return category object by name
        Args:
            category_name: Name of category

        Returns: Category object if found else None
        """
        if not category_name:
            return None

        return self.search_svc_object_by_name(service=self.api_client.tagging.Category, svc_obj_name=category_name)

    def get_tag_by_category(self, tag_name=None, category_name=None):
        """
        Return tag object by name and category name specified
        Args:
            tag_name: Name of tag
            category_name: Name of category

        Returns: Tag object if found else None
        """

        if not tag_name:
            return None

        if category_name:
            category_obj = self.get_category_by_name(category_name=category_name)

            if not category_obj:
                return None

            for tag_object in self.api_client.tagging.Tag.list():
                tag_obj = self.api_client.tagging.Tag.get(tag_object)

                if tag_obj.name == tag_name and tag_obj.category_id == category_obj.id:
                    return tag_obj
        else:
            return self.search_svc_object_by_name(service=self.api_client.tagging.Tag, svc_obj_name=tag_name)
