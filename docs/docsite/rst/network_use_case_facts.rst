.. network-example-facts:

************************************
Gathering facts from network devices
************************************

.. contents:: Topics


Gather facts
============

Objective
---------

I want to connect to a remote network device, download it's configuration and write it to a file

Solution
--------

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


Run it
++++++

.. code-block:: console

   ansible-playbook -i inventory fetch-facts.yml
   <snip>
   PLAY RECAP
   ios01.example.net          : ok=3    changed=0    unreachable=0    failed=0
   vyos01.example.net         : ok=3    changed=0    unreachable=0    failed=0

   cat /tmp/switch-facts

Details
-------

Inventory
+++++++++

The ``inventory`` file is an INI-like configuration file that defines the mapping of hosts into groups

The above inventory file defines the groups ``ios``, ``vyos`` and a "group of groups" called ``switches``. Further details about subgroups and inventory files can be found in the :ref:`Ansible inventory Group documentation <subgroups>`.

The inventory file can be used to define the credentials to log in with, there are various ways credentials could be supplied:

FIXME Link to details regarding different ways to specify credentials (this should be in the main docs somewhere). This should just be a summary that links to the existing docs (``intro_inventory``, ``playbooks_best_practices.html#best-practices-for-variables-and-vaults``, ``ansible-playbook.rst``, etc)

:Command line:

  * Using ``--user`` (``-u``) and ``--ask-pass`` (``-k``).
  * Note: This only works if all devices use the same credentials

:Inventory file:

  :``ansible_user``:

    * Details

  : ``ansible_ssh_pass``:

    * Details

  : ``ansible_ssh_private_key_file``:

    * Details

:top-level:

  * Details

:provider:

  * Details





.. warning:: Never store passwords in plain text

   FIXME Details and links to vault go here


* FIXME: ``ansible_connection=local``


* FIXME Link to module docs ios_facts, vyos_facts, copy, debug

Troubleshooting
---------------

If you receive an error ``unable to open shell`` please follow the debug steps in :doc:`network_debug_troubleshooting`_.

Fixme
=====

* Highlight the command to run in the console section - Look at Sphix documentatiom
* Agreed: Hello world https://github.com/Dell-Networking/ansible-dellos-examples/blob/master/getfacts_os10.yaml

* Add filename to code-blocks

* Troubleshooting link to http://docs.ansible.com/ansible/latest/network_debug_troubleshooting.html#unable-to-open-shell




See also

* Network landing page
* intro_inventory
* playbooks_best_practices.html#best-practices-for-variables-and-vaults
