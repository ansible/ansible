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


Inventory file
++++++++++++++

Create a file called ``inventory``, containing:

.. code-block::

   [switches]
   sw1.example.net

Playbook
++++++++

Create a file called ``fetch-facts.yml`` containing the following:

.. code-block:: yaml

   ---
   - name: "Download switch configuration"
     hosts: switches
     connection: local
     gather_facts: no

     vars:
       ios_credentials:
         username: cisco
         password: cisco
       vyos_credentials:
         username: admin
         password: admin

     tasks:
       - name: Gather facts (ios)
         ios_facts:
           provider: "{{ ios_credentials }}"
         register: result_ios
         when: "'ios' in group_names"

       - name: Gather facts (vyos)
         vyos_facts:
           provider: "{{ vyos_credentials }}"
         register: result_vyos
         when: "'vyos' in group_names"

       - name: Display some facts
         debug:
           msg: "The hostname is {{ ansible_net_hostname }} and the OS is {{ ansible_net_version }}"

       - debug: var=hostvars['vyos01.example.net']

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



This is where we explain what the above is doing

* FIXME Details about inventory

    * What do we need to link to in main docs: ``:children``, what else?
    * Host groups
      
* FIXME Step though playbook

  * Link to module docs for ios_facts, vyos_facts

Troubleshooting
---------------

If you receive an error ``unable to open shell`` please follow the debug steps in :doc:`network_debug_troubleshooting`_.

Fixme
=====

* Highlight the command to run in the console section - Look at Sphix documentatiom
* Agreed: Hello world https://github.com/Dell-Networking/ansible-dellos-examples/blob/master/getfacts_os10.yaml

* Add filename to code-blocks

* Troubleshooting link to http://docs.ansible.com/ansible/latest/network_debug_troubleshooting.html#unable-to-open-shell
