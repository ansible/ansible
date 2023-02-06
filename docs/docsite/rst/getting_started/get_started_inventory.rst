.. _get_started_inventory:

*********************
Building an inventory
*********************

Inventories organize managed nodes in centralized files that provide Ansible with system information and network locations.
Using an inventory file, Ansible can manage a large number of hosts with a single command.
Inventories also help you use Ansible more efficiently by reducing the number of command-line options you need to specify.
For example, inventories usually contain the SSH user so you do not need to include the ``-u`` flag when running Ansible commands.

In the previous section, you added managed nodes directly to the ``/etc/ansible/hosts`` file.
Now let's create an inventory file that you can add to source control for flexibility, reuse, and for sharing with other users.

.. note::
   Inventory files can be in ``INI`` or ``YAML`` format.
   For demonstration purposes, this section uses ``YAML`` format only.

Complete the following steps: 

#. Open a terminal window on your control node.
#. Create a new inventory file named ``inventory.yaml`` in any directory and open it for editing.
#. Add a new group for your hosts then specify the IP address or fully qualified domain name (FQDN) of each managed node with the ``ansible_host`` field.
   The following example adds the IP addresses of three virtual machines in KVM: 

   .. literalinclude:: yaml/inventory_example_vms.yaml
      :language: yaml

#. Verify your inventory.
   If you created your inventory in a directory other than your home directory, specify the full path with the ``-i`` option.

   .. code-block:: bash 

      ansible-inventory -i inventory.yaml --list

#. Ping the managed nodes in your inventory.
   In this example, the group name is ``virtualmachines`` which you can specify with the ``ansible`` command instead of ``all``.

   .. code-block:: bash 

      ansible virtualmachines -m ping -i inventory.yaml

   .. literalinclude:: ansible_output/ping_inventory_output.txt
      :language: text

Congratulations! You have successfully built an inventory.

Tips for building inventories
=============================

* Ensure that group names are meaningful and unique. Group names are also case sensitive.
* Avoid spaces, hyphens, and preceding numbers (use ``floor_19``, not ``19th_floor``) in group names.
* Group hosts in your inventory logically according to their **What**, **Where**, and **When**.

  What 
     Group hosts according to the topology, for example: db, web, leaf, spine.
  Where 
     Group hosts by geographic location, for example: datacenter, region, floor, building.
  When 
     Group hosts by stage, for example: development, test, staging, production.

Use metagroups
--------------

Create a metagroup that organizes multiple groups in your inventory with the following syntax:

.. code-block:: yaml 
   
   metagroupname:
     children:

The following inventory illustrates a basic structure for a data center.
This example inventory contains a ``network`` metagroup that includes all network devices and a ``datacenter`` metagroup that includes the ``network`` group and all webservers.

.. literalinclude:: yaml/inventory_group_structure.yaml
   :language: yaml

Create variables
----------------

Variables set values for managed nodes, such as the IP address, FQDN, operating system, and SSH user, so you do not need to pass them when running Ansible commands.

Variables can apply to specific hosts.

.. literalinclude:: yaml/inventory_variables_host.yaml
   :language: yaml

Variables can also apply to all hosts in a group.

.. literalinclude:: yaml/inventory_variables_group.yaml
   :language: yaml

Now that you know how to build an inventory, continue by :ref:`learning how to create a playbook<get_started_playbook>`.

.. seealso::

   :ref:`intro_inventory`
       Learn more about inventories in ``YAML`` or ``INI`` format.
   :ref:`variables_in_inventory`
       Find out more about inventory variables and their syntax.
   :ref:`vault`
       Find out how to encrypt sensitive content in your inventory such as passwords and keys.
