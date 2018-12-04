
.. _using_network_roles:

******************************************
Use Ansible network roles
******************************************

The Ansible Network team develops and supports a set of `network-related roles <https://galaxy.ansible.com/ansible-network>`_ on Galaxy. You can use these roles to jumpstart your network automation efforts. These roles are updated approximately every two weeks to give you access to the latest Ansible networking content.

These roles come in the following categories:

* **User roles** - You use these roles, such as `config_manager <https://galaxy.ansible.com/ansible-network/config_manager>`_ and `cloud_vpn <https://galaxy.ansible.com/ansible-network/cloud_vpn>`_, directly in your playbooks. These roles are platform/provider agnostic, allowing you to use the same roles and playbooks across different network platforms or cloud providers.
* **Platform provider roles** - Network user roles depend on these provider roles to implement their functions. For example, the `config_manager <https://galaxy.ansible.com/ansible-network/config_manager>`_ role  uses the  `cisco_ios <https://galaxy.ansible.com/ansible-network/cisco_ios>`_ provider role to implement tasks on Cisco IOS network devices.
* **Cloud provider and provisioner roles** - Similarly, cloud user roles depend on cloud provider and provisioner roles to implement cloud functions for specific cloud providers. For example, the `cloud_vpn <https://galaxy.ansible.com/ansible-network/cloud_vpn>`_ role depends on the `aws <https://galaxy.ansible.com/ansible-network/aws>`_ provider role to communicate with AWS.

.. tip::

    You need to install at least one platform provider role for your network user roles, and set ``ansible_network_provider`` to that provider (for example, ``ansible_network_provider: ansible-network.cisco_ios``). Galaxy automatically installs any other dependencies listed in the role details on Galaxy.

Roles are fully documented with examples in Galaxy on the **Read Me** tab for each role.

Network roles release cycle
===========================

The Ansible network team releases updates and new roles every two weeks. The role details on Galaxy lists the role versions available, and you can look in the GitHub repository to find the changelog file (for example, `CHANGELOG.rst <https://github.com/ansible-network/cisco_ios/blob/devel/CHANGELOG.rst>`_ ) that lists what has changed in each version of the role.

The Galaxy role version has two components:

* Major release number - (for example, 2.6) which shows the Ansible engine version this role supports.
* Minor release number (for example .1) which denotes the role release cycle and does not reflect the Ansible engine minor release version.

.. seealso::

       `Galaxy documentation <https://galaxy.ansible.com/docs/>`_
           Galaxy user guide
       `Ansible supported network roles <https://galaxy.ansible.com/ansible-network>`_
           List of Ansible-supported network and cloud roles on Galaxy
