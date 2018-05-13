.. _appendix_module_utilities:

**************************
Appendix: Module Utilities
**************************

A mechanism exists to ship utility modules imported by a :ref:`New-Style
Module <flow_new_style_modules>` alongside for execution on the target. When a
new-style module executes, utility modules may be imported via the
``ansible.module_utils`` Python package namespace. The module entry point is
imported from this namespace, and must always be present:

.. code-block:: python

  from ansible.module_utils.basic import AnsibleModule

The ``ansible.module_utils`` namespace is not a plain Python package: it is
constructed dynamically for each task invocation, by extracting imports and
resolving those matching the namespace against a search path derived from the
active configuration.


Search Path
~~~~~~~~~~~

The search path grows incrementally over a run. If an invocation includes
multiple playbooks and roles that contribute directories to the search path,
newly discovered directories are appended to the path as they are encountered,
and remain for the duration of the run, including after the respective playbook
has finished executing.

1. A directory adjacent to a playbook specified on the command line is added
   first. Given an invocation like ``ansible-playbook /path/to/play.yml``,
   ``/path/to/module_utils`` is appended if it exists.

2. A directory adjacent to a playbook that was statically imported by a
   playbook specified on the command line. Given the above invocation, but with
   ``play.yml`` including ``- import_playbook: /path/to/subdir/play1.yml``,
   ``/path/to/subdir/module_utils`` is appended if it exists.

3. A subdirectory of a role directory referenced by a playbook. Given
   ``/path/to/play.yml`` that references ``myrole``,
   ``/path/to/roles/myrole/module_utils`` is appended if it exists.

4. A directory specified via :ref:`DEFAULT_MODULE_UTILS_PATH`. This may be set
   via ``ansible.cfg`` or an environment variable.

5. The standard directory that ships as part of the Ansible distribution.
   Refer to :ref:`standard_mod_utils` for a list of included modules.

.. caution::

    Modules are resolved via user-specified directories prior to falling back
    to the standard distribution. This means critical utility modules like
    ``ansible.module_utils.basic`` may be overridden by including a like-named
    ``basic.py`` replacement in a user-specified directory.

    When like-named modules exist in unrelated directories, it is possible for
    one to be found before the other due to reordering of the command line or
    roles within playbooks.


.. _standard_mod_utils:

Standard Modules
~~~~~~~~~~~~~~~~

A comprehensive library of utility modules are included with Ansible, appearing
under the `lib/ansible/module_utils directory
<https://github.com/ansible/ansible/tree/devel/lib/ansible/module_utils>`_.
Refer to the source code for detailed descriptions of each.

.. include:: shared_snippets/licensing.txt

- ``api.py`` - Adds shared support for generic API modules.
- ``azure_rm_common.py`` - Definitions and utilities for Microsoft Azure Resource Manager template deployments.
- ``basic.py`` - General definitions and helper utilities for Ansible modules.
- ``cloudstack.py`` - Utilities for CloudStack modules.
- ``database.py`` - Miscellaneous helper functions for PostGRES and MySQL
- ``docker_common.py`` - Definitions and helper utilities for modules working with Docker.
- ``ec2.py`` - Definitions and utilities for modules working with Amazon EC2
- ``facts/`` - Folder containing helper functions for modules that return facts. See https://github.com/ansible/ansible/pull/23012 for more information.
- ``gce.py`` - Definitions and helper functions for modules that work with Google Compute Engine resources.
- ``ismount.py`` - Contains single helper function that fixes os.path.ismount
- ``keycloak.py`` - Definitions and helper functions for modules working with the Keycloak API
- ``known_hosts.py`` - utilities for working with known_hosts file
- ``manageiq.py`` - Functions and utilities for modules that work with ManageIQ platform and its resources.
- ``memset.py`` - Helper functions and utilities for interacting with Memset's API.
- ``mysql.py`` - Allows modules to connect to a MySQL instance
- ``netapp.py`` - Functions and utilities for modules that work with the NetApp storage platforms.
- ``network/a10/a10.py`` - Utilities used by the a10_server module to manage A10 Networks devices.
- ``network/aci/aci.py`` - Definitions and helper functions for modules that manage Cisco ACI Fabrics.
- ``network/aireos/aireos.py`` - Definitions and helper functions for modules that manage Cisco WLC devices.
- ``network/aos/aos.py`` - Module support utilities for managing Apstra AOS Server.
- ``network/aruba/aruba.py`` - Helper functions for modules working with Aruba networking devices.
- ``network/asa/asa.py`` - Module support utilities for managing Cisco ASA network devices.
- ``network/avi/avi.py`` - Helper functions for modules working with AVI networking devices.
- ``network/bigswitch/bigswitch_utils.py`` - Utilities used by the bigswitch module to manage Big Switch Networks devices.
- ``network/cloudengine/ce.py`` - Module support utilities for managing Huawei Cloudengine switch.
- ``network/cnos/cnos.py`` - Helper functions for modules working on devices running Lenovo CNOS.
- ``network/common/config.py`` - Configuration utility functions for use by networking modules
- ``network/common/netconf.py`` - Definitions and helper functions for modules that use Netconf transport.
- ``network/common/parsing.py`` - Definitions and helper functions for Network modules.
- ``network/common/network.py`` - Functions for running commands on networking devices
- ``network/common/utils.py`` - Defines commands and comparison operators and other utilises for use in networking modules
- ``network/dellos6/dellos6.py`` - Module support utilities for managing device running Dell OS6.
- ``network/dellos9/dellos9.py`` - Module support utilities for managing device running Dell OS9.
- ``network/dellos10/dellos10.py`` - Module support utilities for managing device running Dell OS10.
- ``network/enos/enos.py`` - Helper functions for modules working with Lenovo ENOS devices.
- ``network/eos/eos.py`` - Helper functions for modules working with EOS networking devices.
- ``network/fortios/fortios.py`` - Module support utilities for managing FortiOS devices.
- ``network/ios/ios.py`` - Definitions and helper functions for modules that manage Cisco IOS networking devices
- ``network/iosxr/iosxr.py`` - Definitions and helper functions for modules that manage Cisco IOS-XR networking devices.
- ``network/ironware/ironware.py`` - Module support utilities for managing Brocade IronWare devices.
- ``network/junos/junos.py`` -  Definitions and helper functions for modules that manage Junos networking devices.
- ``network/meraki/meraki.py`` - Utilities specifically for the Meraki network modules.
- ``network/netscaler/netscaler.py`` - Utilities specifically for the netscaler network modules.
- ``network/nso/nso.py`` - Utilities for modules that work with Cisco NSO.
- ``network/nxos/nxos.py`` - Contains definitions and helper functions specific to Cisco NXOS networking devices.
- ``network/onyx/onyx.py`` - Definitions and helper functions for modules that manage Mellanox ONYX networking devices.
- ``network/ordance/ordance.py`` - Module support utilities for managing Ordnance devices.
- ``network/sros/sros.py`` - Helper functions for modules working with Open vSwitch bridges.
- ``network/vyos/vyos.py`` - Definitions and functions for working with VyOS networking
- ``openstack.py`` - Utilities for modules that work with Openstack instances.
- ``openswitch.py`` - Definitions and helper functions for modules that manage OpenSwitch devices
- ``powershell.ps1`` - Utilities for working with Microsoft Windows clients
- ``pure.py`` - Functions and utilities for modules that work with the Pure Storage storage platforms.
- ``pycompat24.py`` - Exception workaround for Python 2.4.
- ``rax.py`` -  Definitions and helper functions for modules that work with Rackspace resources.
- ``redhat.py`` - Functions for modules that manage Red Hat Network registration and subscriptions
- ``service.py`` - Contains utilities to enable modules to work with Linux services (placeholder, not in use).
- ``shell.py`` - Functions to allow modules to create shells and work with shell commands
- ``six/__init__.py`` - Bundled copy of the `Six Python library <https://pythonhosted.org/six/>`_ to aid in writing code compatible with both Python 2 and Python 3.
- ``splitter.py`` - String splitting and manipulation utilities for working with Jinja2 templates
- ``urls.py`` - Utilities for working with http and https requests
- ``vca.py`` - Contains utilities for modules that work with VMware vCloud Air
- ``vmware.py`` - Contains utilities for modules that work with VMware vSphere VMs
