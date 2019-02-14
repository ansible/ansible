.. _appendix_module_utilities:

**************************
Appendix: Module Utilities
**************************

Ansible provides a number of module utilities that provide helper functions that you can use when developing your own modules. The ``basic.py`` module utility provides the main entry point for accessing the Ansible library, and all Python Ansible modules must, at minimum, import ``AnsibleModule``::

  from ansible.module_utils.basic import AnsibleModule

If you need to share Python code between some of your own local modules, you can use Ansible's ``module_utils`` directories for this. When you run ``ansible-playbook``, Ansible will merge any files in the local ``module_utils`` directory into the ``ansible.module_utils`` namespace. For example, if you have your own custom modules that import a ``my_shared_code`` library, you can place that into a ``./module_utils/my_shared_code.py`` file in the root location where your playbook lives, and then import it in your modules like so::

  from ansible.module_utils.my_shared_code import MySharedCodeClient

Your custom ``module_utils`` directories can live in the root directory of your playbook, or in the individual role directories, or in the directories specified by the ``ANSIBLE_MODULE_UTILS`` configuration setting.

Ansible ships with the following list of ``module_utils`` files. The module utility source code lives in the ``./lib/ansible/module_utils`` directory under your main Ansible path - for more details on any specific module utility, please see the source code.

.. include:: shared_snippets/licensing.txt

- alicloud_ecs.py - Definitions and utilities for modules working with Alibaba Cloud ECS.
- api.py - Adds shared support for generic API modules.
- azure_rm_common.py - Definitions and utilities for Microsoft Azure Resource Manager template deployments.
- basic.py - General definitions and helper utilities for Ansible modules.
- cloudstack.py  - Utilities for CloudStack modules.
- database.py - Miscellaneous helper functions for PostGRES and MySQL
- docker_common.py - Definitions and helper utilities for modules working with Docker.
- ec2.py - Definitions and utilities for modules working with Amazon EC2
- facts/- Folder containing helper functions for modules that return facts. See https://github.com/ansible/ansible/pull/23012 for more information.
- gce.py - Definitions and helper functions for modules that work with Google Compute Engine resources.
- ismount.py - Contains single helper function that fixes os.path.ismount
- keycloak.py - Definitions and helper functions for modules working with the Keycloak API
- known_hosts.py - utilities for working with known_hosts file
- manageiq.py - Functions and utilities for modules that work with ManageIQ platform and its resources.
- memset.py - Helper functions and utilities for interacting with Memset's API.
- mysql.py - Allows modules to connect to a MySQL instance
- netapp.py - Functions and utilities for modules that work with the NetApp storage platforms.
- network/a10/a10.py - Utilities used by the a10_server module to manage A10 Networks devices.
- network/aci/aci.py - Definitions and helper functions for modules that manage Cisco ACI Fabrics.
- network/aireos/aireos.py - Definitions and helper functions for modules that manage Cisco WLC devices.
- network/aos/aos.py - Module support utilities for managing Apstra AOS Server.
- network/aruba/aruba.py - Helper functions for modules working with Aruba networking devices.
- network/asa/asa.py - Module support utilities for managing Cisco ASA network devices.
- network/avi/avi.py - Helper functions for modules working with AVI networking devices.
- network/bigswitch/bigswitch_utils.py - Utilities used by the bigswitch module to manage Big Switch Networks devices.
- network/cloudengine/ce.py - Module support utilities for managing Huawei Cloudengine switch.
- network/cnos/cnos.py - Helper functions for modules working on devices running Lenovo CNOS.
- network/common/config.py - Configuration utility functions for use by networking modules
- network/common/netconf.py - Definitions and helper functions for modules that use Netconf transport.
- network/common/parsing.py - Definitions and helper functions for Network modules.
- network/common/network.py - Functions for running commands on networking devices
- network/common/utils.py - Defines commands and comparison operators and other utilises for use in networking modules
- network/dellos6/dellos6.py - Module support utilities for managing device running Dell OS6.
- network/dellos9/dellos9.py - Module support utilities for managing device running Dell OS9.
- network/dellos10/dellos10.py - Module support utilities for managing device running Dell OS10.
- network/enos/enos.py - Helper functions for modules working with Lenovo ENOS devices.
- network/eos/eos.py - Helper functions for modules working with EOS networking devices.
- network/fortios/fortios.py - Module support utilities for managing FortiOS devices.
- network/ios/ios.py - Definitions and helper functions for modules that manage Cisco IOS networking devices
- network/iosxr/iosxr.py - Definitions and helper functions for modules that manage Cisco IOS-XR networking devices.
- network/ironware/ironware.py - Module support utilities for managing Brocade IronWare devices.
- network/junos/junos.py -  Definitions and helper functions for modules that manage Junos networking devices.
- network/meraki/meraki.py - Utilities specifically for the Meraki network modules.
- network/netscaler/netscaler.py - Utilities specifically for the netscaler network modules.
- network/nso/nso.py - Utilities for modules that work with Cisco NSO.
- network/nxos/nxos.py - Contains definitions and helper functions specific to Cisco NXOS networking devices.
- network/onyx/onyx.py - Definitions and helper functions for modules that manage Mellanox ONYX networking devices.
- network/ordance/ordance.py - Module support utilities for managing Ordnance devices.
- network/sros/sros.py - Helper functions for modules working with Open vSwitch bridges.
- network/vyos/vyos.py - Definitions and functions for working with VyOS networking
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
- utm_utils.py - Contains base class for creating new Sophos UTM Modules and helper functions for handling the rest interface of Sophos UTM
- vca.py - Contains utilities for modules that work with VMware vCloud Air
- vmware.py - Contains utilities for modules that work with VMware vSphere VMs
- xenserver.py - Contains utilities for modules that work with XenServer.
