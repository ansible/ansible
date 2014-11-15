Start and Step
======================
.. versionadded:: 1.8

.. contents:: Topics

This shows a few special ways to run playbooks, very useful for testing and debugging.


Start-at-task
`````````````
.. versionadded:: 1.2

If you want to start executing your playbook at a particular task, you can do so
with the ``--start-at`` option::

    ansible-playbook playbook.yml --start-at="install packages"

The above will start executing your playbook at a task named "install packages".


Step
````
.. versionadded:: 1.1


Playbooks can also be executed interactively with ``--step``::

    ansible-playbook playbook.yml --step

This will cause ansible to stop on each task, and ask if it should execute that task.
Say you had a task called "configure ssh", the playbook run will stop and ask::

    Perform task: configure ssh (y/n/c):

Answering "y" will execute the task, answering "n" will skip the task, and answering "c"
will continue executing all the remaining tasks without asking.

