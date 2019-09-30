.. _VMware_module_development:

****************************************
Guidelines for VMware module development
****************************************

The VMware modules and these guidelines are maintained by the VMware Working Group. For
further information see the `team community page <https://github.com/ansible/community/wiki/VMware>`_.

.. contents::
   :local:

Testing with govcsim
====================

Most of the existing modules are covered by functional tests. The tests are located in the :file:`test/integration/targets/`.

By default, the tests run against a vCenter API simulator called `govcsim <https://github.com/vmware/govmomi/tree/master/vcsim>`_. ``ansible-test`` will automatically pull a `govcsim container <https://quay.io/repository/ansible/vcenter-test-container>` and use it to set-up the test environment.

You can trigger the test of a module manually with the ``ansible-test`` command. For example, to trigger ``vcenter_folder`` tests:

.. code-block:: shell

    source hacking/env-setup
    ansible-test integration --python 3.7 vcenter_folder

``govcsim`` is handy because it's much more fast that than a regular test environment. However, it does not
support all the ESXi or vCenter features.

.. note::

   Do not confuse ``govcsim`` with ``vcsim``. It's old outdated version of vCenter simulator whereas govcsim is new and written in go lang

Testing with your own infrastructure
====================================

You can also target a regular VMware environment. This paragraph explains step by step how you can run the test-suite yourself.

Requirements
------------

- 2 ESXi hosts (6.5 or 6.7)
   - with 2 NIC, the second ones should be available for the test
- a VCSA host
- a NFS server
- Python dependencies:
    - `pyvmomi <https://github.com/vmware/pyvmomi/tree/master/pyVmomi>`
    - `requests <https://2.python-requests.org/en/master/>`.

If you want to deploy your test environment in a hypervisor, both VMware or Libvirt <https://github.com/goneri/vmware-on-libvirt> work well.

NFS server configuration
~~~~~~~~~~~~~~~~~~~~~~~~

Your NFS server must expose the following directory structure:

.. code-block:: shell

    $ tree /srv/share/
    /srv/share/
    ├── isos
    │   ├── base.iso
    │   ├── centos.iso
    │   └── fedora.iso
    └── vms
    2 directories, 3 files

On a Linux system, you can expose the directory over NFS with the following export file:

.. code-block:: shell

    $ cat /etc/exports
    /srv/share  192.168.122.0/255.255.255.0(rw,anonuid=1000,anongid=1000)

.. note::

    With this configuration all the new files will be owned by the user with the UID and GID 1000/1000.
    Adjust the configuration to match your user's UID/GID.

The service can be enabled with:

.. code-block:: shell

   $ sudo systemctl enable --now nfs-server


Configure your installation
---------------------------

Prepare a configuration file that describes your set-up. The file
should be called :file:`test/integration/cloud-config-vcenter.ini` and based on
:file:`test/lib/ansible_test/config/cloud-config-vcenter.ini.template`. For instance, if you've deployed your lab with
`vmware-on-libvirt <https://github.com/goneri/vmware-on-libvirt>`:

.. code-block:: ini

    [DEFAULT]
    vcenter_username: administrator@vsphere.local
    vcenter_password: !234AaAa56
    vcenter_hostname: vcenter.test
    vmware_validate_certs: false
    esxi1_username: root
    esxi1_hostname: esxi1.test
    esxi1_password: root
    esxi2_username: root
    esxi2_hostname: test2.test
    esxi2_password: root

If you use an HTTP proxy
-------------------------
Support for hosting test infrastructure behind an HTTP proxy is currently in development. See the following pull requests for more information:

- ansible-test: vcenter behind an HTTP proxy <https://github.com/ansible/ansible/pull/58208>
- pyvmomi: proxy support <https://github.com/vmware/pyvmomi/pull/799>
- VMware: add support for HTTP proxy in connection API <https://github.com/ansible/ansible/pull/52936>

Once you have incorporated the code from those PRs, specify the location of the proxy server with the two extra keys:

.. code-block:: ini

    vmware_proxy_host: esxi1-gw.ws.testing.ansible.com
    vmware_proxy_port: 11153

In addition, you may need to adjust the variables of the following file to match the configuration of your lab:
:file:`test/integration/targets/prepare_vmware_tests/vars/real_lab.yml`. If you use `vmware-on-libvirt <https://github.com/goneri/vmware-on-libvirt>` to prepare you lab, you don't have anything to change.

Run the test-suite
------------------

Once your configuration is ready, you can trigger a run with the following command:

.. code-block:: shell

    source hacking/env-setup
    VMWARE_TEST_PLATFORM=static ansible-test integration --python 3.7 vmware_host_firewall_manager

``vmware_host_firewall_manager`` is the name of the module to test.

``vmware_guest`` is much larger than any other test role and is rather slow. You can enable or disable some of its test playbooks in
:file:`test/integration/targets/vmware_guest/defaults/main.yml`.


Unit-test
=========

The VMware modules have limited unit-test coverage. You can run the test suite with the
following commands:

.. code-block:: shell

    source hacking/env-setup
    ansible-test units --tox --python 3.7 '.*vmware.*'

Code style and best practice
============================

datacenter argument with ESXi
-----------------------------

The ``datacenter`` parameter should not use ``ha-datacenter`` by default. This is because the user may
not realize that Ansible silently targets the wrong data center.

esxi_hostname should not be mandatory
-------------------------------------

Depending upon the functionality provided by ESXi or vCenter, some modules can seamlessly work with both. In this case,
``esxi_hostname`` parameter should be optional.

.. code-block:: python

    if self.is_vcenter():
        esxi_hostname = module.params.get('esxi_hostname')
        if not esxi_hostname:
            self.module.fail_json("esxi_hostname parameter is mandatory")
        self.host = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_hostname)[0]
    else:
        self.host = find_obj(self.content, [vim.HostSystem], None)
    if self.host is None:
        self.module.fail_json(msg="Failed to find host system.")

Functional tests
----------------

Writing new tests
~~~~~~~~~~~~~~~~~

If you are writing a new collection of integration tests, there are a few VMware-specific things to note beyond
the standard Ansible :ref:`integration testing<testing_integration>` process.

The test-suite uses a set of common, pre-defined vars located in the :file:`test/integration/targets/prepare_vmware_tests/` role.
The resources defined there are automatically created by importing that role at the start of your test:

.. code-block:: yaml

  - import_role:
      name: prepare_vmware_tests
    vars:
      setup_datacenter: true

This will give you a ready to use cluster, datacenter, datastores, folder, switch, dvswitch, ESXi hosts, and VMs.

No need to create too much resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most of the time, it's not necessary to use ``with_items`` to create multiple resources. By avoiding it,
you speed up the test execution and you simplify the clean up afterwards.

VM names should be predictable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need to create a new VM during your test, you can use ``test_vm1``, ``test_vm2`` or ``test_vm3``. This
way it will be automatically clean up for you.


Typographic convention
======================

Nomenclature
------------

We try to enforce the following rules in our documentation:

- VMware, not VMWare or vmware
- ESXi, not esxi or ESXI
- vCenter, not vcenter or VCenter

We also refer to vcsim's Go implementation with ``govcsim``. This to avoid any confusion with the outdated implementation.
