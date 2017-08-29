Appendix: Module Utilities
``````````````````````````

Ansible provides a number of module utilities that provide helper functions that you can use when developing your own modules. The `basic.py` module utility provides the main entry point for accessing the Ansible library, and all Ansible modules must, at minimum, import from basic.py::

  from ansible.module_utils.basic import *


The following is a list of module_utils files and a general description. The module utility source code lives in the `./lib/module_utils` directory under your main Ansible path - for more details on any specific module utility, please see the source code.

- a10.py - Utilities used by the a10_server module to manage A10 Networks devices.
- aireos.py - Definitions and helper functions for modules that manage Cisco WLC devices.
- api.py - Adds shared support for generic API modules.
- aos.py - Module support utilities for managing Apstra AOS Server.
- aruba.py - Helper functions for modules working with Aruba networking devices.
- asa.py - Module support utilities for managing Cisco ASA network devices.
- azure_rm_common.py - Definitions and utilities for Microsoft Azure Resource Manager template deployments.
- basic.py - General definitions and helper utilities for Ansible modules.
- cloudstack.py  - Utilities for CloudStack modules.
- database.py - Miscellaneous helper functions for PostGRES and MySQL
- docker_common.py - Definitions and helper utilities for modules working with Docker.
- ec2.py - Definitions and utilities for modules working with Amazon EC2
- eos.py - Helper functions for modules working with EOS networking devices.
- f5.py - Helper functions for modules working with F5 networking devices.
- facts.py - Helper functions for modules that return facts.
- gce.py - Definitions and helper functions for modules that work with Google Compute Engine resources.
- ios.py - Definitions and helper functions for modules that manage Cisco IOS networking devices
- iosxr.py - Definitions and helper functions for modules that manage Cisco IOS-XR networking devices
- ismount.py - Contains single helper function that fixes os.path.ismount
- junos.py -  Definitions and helper functions for modules that manage Junos networking devices
- known_hosts.py - utilities for working with known_hosts file
- manageiq.py - Functions and utilities for modules that work with ManageIQ platform and its resources.
- mysql.py - Allows modules to connect to a MySQL instance
- netapp.py - Functions and utilities for modules that work with the NetApp storage platforms.
- netcfg.py - Configuration utility functions for use by networking modules
- netcmd.py - Defines commands and comparison operators for use in networking modules
- netscaler.py - Utilities specifically for the netscaler network modules.
- network.py - Functions for running commands on networking devices
- nxos.py - Contains definitions and helper functions specific to Cisco NXOS networking devices
- openstack.py - Utilities for modules that work with Openstack instances.
- openswitch.py - Definitions and helper functions for modules that manage OpenSwitch devices
- powershell.ps1 - Utilities for working with Microsoft Windows clients
- pure.py - Functions and utilities for modules that work with the Pure Storage storage platforms.
- pycompat24.py - Exception workaround for Python 2.4.
- rax.py -  Definitions and helper functions for modules that work with Rackspace resources.
- redhat.py - Functions for modules that manage Red Hat Network registration and subscriptions
- service.py - Contains utilities to enable modules to work with Linux services (placeholder, not in use).
- shell.py - Functions to allow modules to create shells and work with shell commands
- six/__init__.py - Bundled copy of the `Six Python library <https://pythonhosted.org/six/>`_ to aid in writing code compatible with both Python 2 and Python 3.
- splitter.py - String splitting and manipulation utilities for working with Jinja2 templates
- urls.py - Utilities for working with http and https requests
- vca.py - Contains utilities for modules that work with VMware vCloud Air
- vmware.py - Contains utilities for modules that work with VMware vSphere VMs
- vyos.py - Definitions and functions for working with VyOS networking
