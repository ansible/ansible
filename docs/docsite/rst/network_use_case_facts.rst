.. network-example-facts:

************************************
Gathering facts from network devices
************************************

.. contents:: Topics


Overview
========

Objective
---------

I want to connect to a remote network device, download it's configuration and write it to a file.

Prerequisites
-------------

* Ansible 2.3 (or higher) installed :doc:`intro_installation`
* One or more network device compatible with Ansible FIXMELINK

Audience
--------

* Basic Linux (comfortable on the command line)
* Basic Network switch & router configuration knowledge


Solution
=========

Create an inventory file


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
     # Which group in the inventory file this applies to
     hosts: switches

     gather_facts: no

     tasks:
       - name: Gather facts (ios)
         ios_facts:
         register: result_ios
         when: "'ios' in group_names"

       - name: Gather facts (vyos)
         vyos_facts:
         register: result_vyos
         when: "'vyos' in group_names"

       - name: Display some facts
         debug:
           msg: "The hostname is {{ ansible_net_hostname }} and the OS is {{ ansible_net_version }}"

       - name: Show how to get a fact from a specific host
         debug:
           var: hostvars['vyos01.example.net']

       - name: Write to disk
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


FIXME: Use ``_config`` to download full configuration and write to disk?

Run it
------

.. code-block:: console

   ansible-playbook -i inventory fetch-facts.yml
   <snip>
   PLAY RECAP
   ios01.example.net          : ok=3    changed=0    unreachable=0    failed=0
   vyos01.example.net         : ok=3    changed=0    unreachable=0    failed=0

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


New page: Auth & Proxy
----------------------

This section needs moving to a new page, just made notes here while I was developing this:

FIXME Link to details regarding different ways to specify credentials (this should be in the main docs somewhere). This should just be a summary that links to the existing docs (``intro_inventory``, ``playbooks_best_practices.html#best-practices-for-variables-and-vaults``, ``ansible-playbook.rst``, etc)

Somewhere in the main docs we need to list the different ways of authenticating


:Command line:

  * Using ``--user`` (``-u``) and ``--ask-pass`` (``-k``).
  * Note: This only works if all devices use the same credentials

:Inventory file:

  :``ansible_user``:

    * Details
    * Link to main docs

  :``ansible_ssh_pass``:

    * Generally used along side ``ansible_user``.
    * Not for REST transports such as `eapi`, `nxapi`.
    * Link to main docs

  :``ansible_ssh_private_key_file``:

    * Details
    * Link to main docs

:top-level module options:

  * As of Ansible 2.3 this is deprecated.
  * Link to main docs

:``provider:`` argument to module:

  * This is OK
  * Link to main docs

