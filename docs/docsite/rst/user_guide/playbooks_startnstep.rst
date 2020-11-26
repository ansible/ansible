.. _playbooks_start_and_step:

***************************************
Executing playbooks for troubleshooting
***************************************

When you are testing new plays or debugging playbooks, you may need to run the same play multiple times. To make this more efficient, Ansible offers two alternative ways to execute a playbook: start-at-task and step mode.

.. _start_at_task:

start-at-task
-------------

To start executing your playbook at a particular task (usually the task that failed on the previous run), use the ``--start-at-task`` option::

    ansible-playbook playbook.yml --start-at-task="install packages"

In this example, Ansible starts executing your playbook at a task named "install packages". This feature does not work with tasks inside dynamically re-used roles or tasks (``include_*``), see :ref:`dynamic_vs_static`.

.. _step:

Step mode
---------

To execute a playbook interactively, use ``--step``::

    ansible-playbook playbook.yml --step

With this option, Ansible stops on each task, and asks if it should execute that task. For example, if you have a task called "configure ssh", the playbook run will stop and ask::

    Perform task: configure ssh (y/n/c):

Answer "y" to execute the task, answer "n" to skip the task, and answer "c" to exit step mode, executing all remaining tasks without asking.

.. seealso::

   :ref:`playbooks_intro`
       An introduction to playbooks
   :ref:`playbook_debugger`
       Using the Ansible debugger
