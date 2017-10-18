.. network-getting-started-example:

*******************************
Network getting started example
*******************************

.. contents:: Topics


Overview
========

Objective
---------

I want to understand how Ansible can be used to connect to multiple network devices.

This is not for production use, it's more to demonstrate the different areas that need to be considered and provide a foundation level knowledge.

Future examples FIXMELINK will build on this knowledge.

Prerequisites
-------------

* Ansible 2.3 (or higher) installed :doc:`intro_installation`
* One or more network device compatible with Ansible FIXMELINK

.. FIXME FUTURE Gundalow - Once created we will link to the connection table here (which platforms support network_cli & credentials through inventory)

Audience
--------

* Basic Linux (comfortable on the command line)
* Basic Network switch & router configuration knowledge


Solution
=========

Create an inventory file.


**Inventory file**

Create a file called ``inventory``, containing:

.. code-block::

   [switches:children]
   ios
   vyos

   [ios]
   ios01.example.net ansible_connection=local ansible_user=cisco ansible_ssh_pass=cisco

   [vyos]
   vyos01.example.net ansible_connection=local ansible_user=admin ansible_ssh_pass=admin


**Playbook**

Create a file called ``fetch-facts.yml`` containing the following:

.. code-block:: yaml

   - name: "Download switch configuration"
     hosts: switches
     gather_facts: no

     tasks:
       ###
       # Collect data
        - name: Gather facts (ios)
          ios_facts:
          register: result_ios
          when: "'ios' in group_names"

        - name: Gather facts (vyos)
          vyos_facts:
          register: result_vyos
          when: "'vyos' in group_names"

        ###
        # Demonstrate variables
        #
        - name: Display some facts
          debug:
            msg: "The hostname is {{ ansible_net_hostname }} and the OS is {{ ansible_net_version }}"

        - debug:
            var: hostvars['vyos01.example.net']

        - name: Write facts to disk using a template
          copy:
            content: |
              IOS device info:
                {% for host in groups['ios'] %}
                Hostname: {{ hostvars[host].ansible_net_version }}
                Version: {{ hostvars[host].ansible_net_version }}
                Model: {{ hostvars[host].ansible_net_model }}
                Serial: {{ hostvars[host].ansible_net_serialnum }}
                {% endfor %}

              VyOS device info:
                {% for host in groups['vyos'] %}
                Hostname: {{ hostvars[host].ansible_net_version }}
                Version: {{ hostvars[host].ansible_net_version }}
                Model: {{ hostvars[host].ansible_net_model }}
                Serial: {{ hostvars[host].ansible_net_serialnum }}
                {% endfor %}
            dest: /tmp/switch-facts
          run_once: yes

        ###
        # Get running configuration
        #

        - name: Backup switch (ios)
          ios_config:
            backup: yes
          register: backup_ios
          when: "'ios' in group_names"

        - name: backup switch (vyos)
          vyos_config:
            backup: yes
          register: backup_vyos
          when: "'vyos' in group_names"

        - name: Create backup dir
          file:
            path: "/tmp/backups/{{ inventory_hostname }}"
            state: directory
            recurse: yes

        - name: Copy backup files into /tmp/backups/ (ios)
          copy:
            src: "{{ backup_ios.backup_path }}"
            dest: "/tmp/backups/{{ inventory_hostname }}/{{ inventory_hostname }}.bck"
          when: "'ios' in group_names"

        - name: Copy backup files into /tmp/backups/ (vyos)
          copy:
            src: "{{ backup_vyos.backup_path }}"
            dest: "/tmp/backups/{{ inventory_hostname }}/{{ inventory_hostname }}.bck"
          when: "'vyos' in group_names"


Run it
------

.. code-block:: console

   ansible-playbook -i inventory fetch-facts.yml
   <snip>
   PLAY RECAP
   ios01.example.net          : ok=7    changed=2    unreachable=0    failed=0
   vyos01.example.net         : ok=6    changed=2    unreachable=0    failed=0

   cat /tmp/switch-facts

Details
=======

Inventory
---------

The ``inventory`` file is an INI-like configuration file that defines the mapping of hosts into groups.

The above inventory file defines the groups ``ios``, ``vyos`` and a "group of groups" called ``switches``. Further details about subgroups and inventory files can be found in the :ref:`Ansible inventory Group documentation <subgroups>`.


Credentials
^^^^^^^^^^^

Although there are many ways to supply credentials in Ansible in this case we are using ``ansible_user`` and ``ansible_ssh_pass`` as a simple example.

.. FIXME FUTURE Gundalow - Link to network auth & proxy page (to be written)

.. warning:: Never store passwords in plain text

   Passwords should never be stored in plain text. The "Vault" feature of Ansible allows keeping sensitive data such as passwords or keys in encrypted files, rather than as plaintext in your playbooks or roles. These vault files can then be distributed or placed in source control. The :doc:`playbooks_vault` contains further information.

ansible_connection
^^^^^^^^^^^^^^^^^^

Setting ``ansible_connection=local`` informs Ansible to execute the module on the controlling machine (i.e. the one executing Ansible). Without this Ansible would attempt to ssh onto the remote and execute the Python script on the network device, which would fail as Python generally isn't available on network devices.


Playbook
--------

Gathering facts
^^^^^^^^^^^^^^^

Here we use the ``_facts`` modules :ref:`ios_facts <ios_facts>` and :ref:`vyos_facts <vyos_facts>` to connect to the remote device. As the credentials are not explicitly passed via module arguments, Ansible uses the username and password from the inventory file.

The data that the module returns is stored due to the use of the ``register:`` keyword into a variable called ``results_ios`` or ``results_vyos``.

The return values (data returned by a module) are documented in the `Return Values` section of the module docs, in this case :ref:`ios_facts <ios_facts>` and :ref:`vyos_facts <vyos_facts>`.

The task is conditionally run based on the group defined in the inventory file, for more information on the use of conditionals in Ansible Playbooks see :ref:`the_when_statement`.



Debug
-----

Although these tasks are not needed to write data to disk, they are useful to demonstrate some methods of accessing facts about the given or a named host.

More information on this can be found in :ref:`magic_variables_and_hostvars`.

Writing to disk
---------------

* FIXME Link to module docs ios_facts, vyos_facts, copy, debug

Troubleshooting
===============

If you receive an error ``unable to open shell`` please follow the debug steps in :doc:`network_debug_troubleshooting`.


.. seealso::

  * Network landing page
  * intro_inventory
  * playbooks_best_practices.html#best-practices-for-variables-and-vaults

Fixme
=====

* Highlight the command to run in the console section - Look at Sphix documentation
* Agreed: Hello world https://github.com/Dell-Networking/ansible-dellos-examples/blob/master/getfacts_os10.yaml

* Add filename to code-blocks

* Other examples


* Using ``ansible_ssh_pass`` will not work for REST transports such as ``eapi``, ``nxapi`` - What do we here?

* External updates needed

  * Improve vault page and link between ``playbooks_best_practices.html#best-practices-for-variables-and-vaults``, ``ansible-playbook.rst``
  * Link to network intro page table of Persistent connection and version_added table
