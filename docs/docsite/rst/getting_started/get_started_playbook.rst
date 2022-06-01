.. _get_started_playbook:

*******************
Creating a playbook
*******************

Playbooks are automation blueprints, in ``YAML`` format, that Ansible uses to deploy and configure managed nodes.

Playbook 
   A list of plays that define the order in which Ansible performs operations, from top to bottom, to achieve an overall goal.

Play
   An ordered list of tasks that maps to managed nodes in an inventory.

Task
   A list of one or more modules that defines the operations that Ansible performs.

Module
   A unit of code or binary that Ansible runs on managed nodes.
   Ansible modules are grouped in collections with a :term:`Fully Qualified Collection Name (FQCN)` for each module.

In the previous section, you used the ``ansible`` command to ping hosts in your inventory.
Now let's create a playbook that pings your hosts and also prints a "Hello world" message.

Complete the following steps:

#. Open a terminal window on your control node.
#. Create a new playbook file named ``playbook.yaml`` in any directory and open it for editing.
#. Add the following content to ``playbook.yaml``:

   .. literalinclude:: yaml/first_playbook.yaml
      :language: yaml

#. Run your playbook.

   .. code-block:: bash

      ansible-playbook -i inventory.yaml playbook.yaml

Ansible returns the following output:

.. literalinclude:: ansible_output/first_playbook_output.txt
      :language: text

In this output you can see:

* The names that you give the play and each task.
  You should always use descriptive names that make it easy to verify and troubleshoot playbooks.

* The ``Gather Facts`` task runs implicitly.
  By default Ansible gathers information about your inventory that it can use in the playbook.

* The status of each task.
  Each task has a status of ``ok`` which means it ran successfully.

* The play recap that summarizes results of all tasks in the playbook per host.
  In this example, there are three tasks so ``ok=3`` indicates that each task ran successfully.

Congratulations! You have just created your first Ansible playbook.

.. seealso::

   :ref:`playbooks_intro`
       Start building playbooks for real world scenarios.
   :ref:`working_with_playbooks`
       Go into more detail with Ansible playbooks.
   :ref:`playbooks_best_practices`
       Get tips and tricks for using playbooks.
   :ref:`vars_and_facts`
       Learn more about the ``gather_facts`` keyword in playbooks.