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
       really slow task  | Download project packages----------------------------11.61s
       security | Really slow security policies----------------------------------7.03s
       common-base | Install core system dependencies----------------------------3.62s
       common | Install pip------------------------------------------------------3.60s
       common | Install boto-----------------------------------------------------3.57s
       nginx | Install nginx-----------------------------------------------------3.41s
       serf | Install system dependencies----------------------------------------3.38s
       duo_security | Install Duo Unix SSH Integration---------------------------3.37s
       loggly | Install TLS version----------------------------------------------3.36s

Compatibility
-------------

Ansible 2.0+
