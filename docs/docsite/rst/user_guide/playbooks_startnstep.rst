Start and Step
======================

This shows a few alternative ways to run playbooks. These modes are very useful for testing new plays or debugging.


.. _start_at_task:

Start-at-task
`````````````
If you want to start executing your playbook at a particular task, you can do so with the ``--start-at-task`` option::

    ansible-playbook playbook.yml --start-at-task="install packages"

The above will start executing your playbook at a task named "install packages".


.. _step:

Step
````

Playbooks can also be executed interactively with ``--step``::

    ansible-playbook playbook.yml --step

This will cause ansible to stop on each task, and ask if it should execute that task.
Say you had a task called "configure ssh", the playbook run will stop and ask::

    Perform task: configure ssh (y/n/c):

Answering "y" will execute the task, answering "n" will skip the task, and answering "c"
will continue executing all the remaining tasks without asking.

