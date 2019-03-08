.. _vmware_troubleshooting:

**********************************
Troubleshooting Ansible for VMware
**********************************

.. contents:: Topics

This section lists things that can go wrong and possible ways to fix them.

Debugging Ansible for VMware
============================

When debugging or creating a new issue, you will need information about your VMware infrastructure. You can get this information using
`govc <https://github.com/vmware/govmomi/tree/master/govc>`_, For example:


.. code-block:: bash

    $ export GOVC_USERNAME=ESXI_OR_VCENTER_USERNAME
    $ export GOVC_PASSWORD=ESXI_OR_VCENTER_PASSWORD
    $ export GOVC_URL=https://ESXI_OR_VCENTER_HOSTNAME:443
    $ govc find /

Known issues with Ansible for VMware
====================================


Network settings with vmware_guest in Ubuntu 18.04
--------------------------------------------------

Setting the network with ``vmware_guest`` in Ubuntu 18.04 is known to be broken, due to missing support for ``netplan`` in the ``open-vm-tools``.
This issue is tracked via:

* https://github.com/vmware/open-vm-tools/issues/240
* https://github.com/ansible/ansible/issues/41133

Potential Workarounds
^^^^^^^^^^^^^^^^^^^^^

There are several workarounds for this issue.

1) Modify the Ubuntu 18.04 images and installing ``ifupdown`` in them via ``sudo apt install ifupdown``.
   If so you need to remove ``netplan`` via ``sudo apt remove netplan.io`` and you need stop ``systemd-networkd`` via ``sudo systemctl disable systemctl-networkd``.

2) Generate the ``systemd-networkd`` files with a task in your VMware Ansible role:

.. code-block:: yaml

   - name: make sure cache directory exists
     file: path="{{ inventory_dir }}/cache" state=directory
     delegate_to: localhost

   - name: generate network templates
     template: src=network.j2 dest="{{ inventory_dir }}/cache/{{ inventory_hostname }}.network"
     delegate_to: localhost

   - name: copy generated files to vm
     vmware_guest_file_operation:
       hostname: "{{ vmware_general.hostname }}"
       username: "{{ vmware_username }}"
       password: "{{ vmware_password }}"
       datacenter: "{{ vmware_general.datacenter }}"
       validate_certs: "{{ vmware_general.validate_certs }}"
       vm_id: "{{ inventory_hostname }}"
       vm_username: root
       vm_password: "{{ template_password }}"
       copy:
           src: "{{ inventory_dir }}/cache/{{ inventory_hostname }}.network"
           dest: "/etc/systemd/network/ens160.network"
           overwrite: False
     delegate_to: localhost

   - name: restart systemd-networkd
     vmware_vm_shell:
       hostname: "{{ vmware_general.hostname }}"
       username: "{{ vmware_username }}"
       password: "{{ vmware_password }}"
       datacenter: "{{ vmware_general.datacenter }}"
       folder: /vm
       vm_id: "{{ inventory_hostname}}"
       vm_username: root
       vm_password: "{{ template_password }}"
       vm_shell: /bin/systemctl
       vm_shell_args: " restart systemd-networkd"
     delegate_to: localhost

   - name: restart systemd-resolved
     vmware_vm_shell:
       hostname: "{{ vmware_general.hostname }}"
       username: "{{ vmware_username }}"
       password: "{{ vmware_password }}"
       datacenter: "{{ vmware_general.datacenter }}"
       folder: /vm
       vm_id: "{{ inventory_hostname}}"
       vm_username: root
       vm_password: "{{ template_password }}"
       vm_shell: /bin/systemctl
       vm_shell_args: " restart systemd-resolved"
     delegate_to: localhost

3) Wait for ``netplan`` support in ``open-vm-tools``
