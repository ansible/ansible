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

VCLOUD_IMP_ERR = None
try:
    from vmware.vapi.lib.connect import get_requests_connector
    from vmware.vapi.security.session import create_session_security_context
    from vmware.vapi.security.user_password import create_user_password_security_context
    from com.vmware.cis_client import Session
    from com.vmware.vapi.std_client import DynamicID
    HAS_VCLOUD = True
except ImportError:
    VCLOUD_IMP_ERR = traceback.format_exc()
    HAS_VCLOUD = False

VSPHERE_IMP_ERR = None
try:
    from vmware.vapi.stdlib.client.factories import StubConfigurationFactory
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
        self.connect = self.connect_to_rest()

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
        if not HAS_VCLOUD:
            self.module.fail_json(
                msg=missing_required_lib('vCloud Suite SDK',
                                         url='https://code.vmware.com/web/sdk/60/vcloudsuite-python'),
                exception=VCLOUD_IMP_ERR)

    def connect_to_rest(self):
        """
        Connect to server using username and password

        """
        session = requests.Session()
        session.verify = self.params.get('validate_certs')

        username = self.params.get('username', None)
        password = self.params.get('password', None)
        protocol = self.params.get('protocol', 'https')
        hostname = self.params.get('hostname')

        if not all([self.params.get('hostname', None), username, password]):
            self.module.fail_json(msg="Missing one of the following : hostname, username, password."
                                      " Please read the documentation for more information.")

        vcenter_url = "%s://%s/api" % (protocol, hostname)

        # Get request connector
        connector = get_requests_connector(session=session, url=vcenter_url)
        # Create standard Configuration
        stub_config = StubConfigurationFactory.new_std_configuration(connector)
        # Use username and password in the security context to authenticate
        security_context = create_user_password_security_context(username, password)
        # Login
        stub_config.connector.set_security_context(security_context)
        # Create the stub for the session service and login by creating a session.
        session_svc = Session(stub_config)
        session_id = None
        try:
            session_id = session_svc.create()
        except OSError as os_err:
            self.module.fail_json(msg="Failed to login to %s: %s" % (hostname,
                                                                     to_native(os_err)))

        if session_id is None:
            self.module.fail_json(msg="Failed to create session using provided credentials."
                                      " Please check hostname, username and password.")
        # After successful authentication, store the session identifier in the security
        # context of the stub and use that for all subsequent remote requests
        session_security_context = create_session_security_context(session_id)
        stub_config.connector.set_security_context(session_security_context)

        if stub_config is None:
            self.module.fail_json(msg="Failed to login to %s" % hostname)
        return stub_config

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
