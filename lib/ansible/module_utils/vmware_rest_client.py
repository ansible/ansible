# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from pyVim import connect
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

try:
    from vmware.vapi.lib.connect import get_requests_connector
    from vmware.vapi.security.session import create_session_security_context
    from vmware.vapi.security.user_password import create_user_password_security_context
    from com.vmware.cis_client import Session
    from com.vmware.vapi.std_client import DynamicID
    HAS_VCLOUD = True
except ImportError:
    HAS_VCLOUD = False

try:
    from vmware.vapi.stdlib.client.factories import StubConfigurationFactory
    HAS_VSPHERE = True
except ImportError:
    HAS_VSPHERE = False

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import env_fallback


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
        Function to check required libraries

        """
        if not HAS_REQUESTS:
            self.module.fail_json(msg="Unable to find 'requests' Python library which is required."
                                      " Please install using 'pip install requests'")
        if not HAS_PYVMOMI:
            self.module.fail_json(msg="PyVmomi Python module required. Install using 'pip install PyVmomi'")
        if not HAS_VSPHERE:
            self.module.fail_json(msg="Unable to find 'vSphere Automation SDK' Python library which is required."
                                      " Please refer this URL for installation steps"
                                      " - https://code.vmware.com/web/sdk/65/vsphere-automation-python")
        if not HAS_VCLOUD:
            self.module.fail_json(msg="Unable to find 'vCloud Suite SDK' Python library which is required."
                                      " Please refer this URL for installation steps"
                                      " - https://code.vmware.com/web/sdk/60/vcloudsuite-python")

    def connect_to_rest(self):
        """
        Function to connect to server using username and password

        """
        session = requests.Session()
        session.verify = self.params.get('validate_certs')

        username = self.params.get('username', None)
        password = self.params.get('password', None)

        if not all([self.params.get('hostname', None), username, password]):
            self.module.fail_json(msg="Missing one of the following : hostname, username, password."
                                      " Please read the documentation for more information.")

        vcenter_url = "%(protocol)s://%(hostname)s/api" % self.params

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
            self.module.fail_json(msg="Failed to login to %s: %s" % (self.params['hostname'],
                                                                     to_native(os_err)))

        if session_id is None:
            self.module.fail_json(msg="Failed to create session using provided credentials."
                                      " Please check hostname, username and password.")
        # After successful authentication, store the session identifier in the security
        # context of the stub and use that for all subsequent remote requests
        session_security_context = create_session_security_context(session_id)
        stub_config.connector.set_security_context(session_security_context)

        if stub_config is None:
            self.module.fail_json(msg="Failed to login to %(hostname)s" % self.params)
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
