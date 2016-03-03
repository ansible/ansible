profile\_tasks.py
=================

Ansible plugin for timing individual tasks and overall execution time.

Mashup of 2 excellent original works:

-  https://github.com/jlafon/ansible-profile
-  https://github.com/junaid18183/ansible_home/blob/master/ansible_plugins/callback_plugins/timestamp.py.old

Usage
-----

Add ``profile_tasks`` to the ``callback_whitelist`` in ``ansible.cfg``.

Run playbooks as normal.

Certain options are configurable using environment variables. You can specify ``ascending`` or ``none`` for
the environment variable ``PROFILE_TASKS_SORT_ORDER`` to adjust sorting output. If you want to see more than
20 tasks in the output you can set ``PROFILE_TASKS_TASK_OUTPUT_LIMIT`` to any number, or the special value
``all`` to get a list of all tasks.

Features
--------

Tasks
~~~~~

Ongoing timing of each task as it happens.

| Format:
| ``<task start timestamp> (<length of previous task>) <current elapsed playbook execution time>``

Task output example:

.. code:: shell

    TASK: [ensure messaging security group exists] ********************************
    Thursday 11 June 2017  22:50:53 +0100 (0:00:00.721)       0:00:05.322 *********
    ok: [localhost]

    TASK: [ensure db security group exists] ***************************************
    Thursday 11 June 2017  22:50:54 +0100 (0:00:00.558)       0:00:05.880 *********
    changed: [localhost]

Play Recap
~~~~~~~~~~

Recap includes ending timestamp, total playbook execution time and a
sorted list of the top longest running tasks.

No more wondering how old the results in a terminal window are.

.. code:: shell

       ansible <args here>
       <normal output here>
       PLAY RECAP ********************************************************************
       Thursday 11 June 2016  22:51:00 +0100 (0:00:01.011)       0:00:43.247 *********
       ===============================================================================
       old_and_slow : install tons of packages -------------------------------- 20.03s
       /home/bob/ansible/roles/old_and_slow/tasks/main.yml:4 -------------------------
       db : second task to run ------------------------------------------------- 2.03s
       /home/bob/ansible/roles/db/tasks/main.yml:4 -----------------------------------
       setup ------------------------------------------------------------------- 0.42s
       None --------------------------------------------------------------------------
       www : first task to run ------------------------------------------------- 0.03s
       /home/bob/ansible/roles/www/tasks/main.yml:1 ----------------------------------
       fast_task : first task to run ------------------------------------------- 0.01s
       /home/bob/ansible/roles/fast_task.yml:1 ---------------------------------------

Compatibility
-------------

Ansible 2.0+
