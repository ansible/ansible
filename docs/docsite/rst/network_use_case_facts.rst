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
        password: secretpassword
    tasks:
      - name: Gather facts
        ios_facts:
          provider: "{{ ios_credentials }}"
        register: result

      - name: Display facts
        debug:
          msg: " {{ result }}"

      - name: Write to disk
        copy:
          content: "{{ result | to_nice_json }}"
          dest: "/tmp/switch-config-{{inventory_hostname}}"

Run it
++++++

.. code-block:: console

   ansible-playbook -i inventory fetch-facts.yml
   <snip>
   ios01                      : ok=3    changed=1    unreachable=0    failed=0
   ls /tmp/switch-config-*
   /tmp/switch-config-ios01.example.net
   less /tmp/switch-config-ios01.example.net

Details
-------

* FIXME Details about inventory
* FIXME

Fixme
=====

* Highlight the command to run in the console section - Look at Sphix documentatiom
* Agreed: Hello world https://github.com/Dell-Networking/ansible-dellos-examples/blob/master/getfacts_os10.yaml

* Add filename to code-blocks

* Troubleshooting link to http://docs.ansible.com/ansible/latest/network_debug_troubleshooting.html#unable-to-open-shell
* Duplicate for two platforms
