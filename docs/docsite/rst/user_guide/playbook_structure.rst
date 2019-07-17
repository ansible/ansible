Ansible basic structures introduction
=====================================
=====================================


YAML Basics
===========

A `-` identifies a ‘list item’

.. code::
        - one
        - two
        - three

A word with a colon (word:) identifies a mapping/dictionary

.. code::
        this: mapping
        has: two keys

They can intermix so you can have a list of dictionaries and lists in dictionaries as well as lists of lists and dictionaries within dictionaries …

.. code::

    this_list:
        - 1
        - 2
        - hasadict: with
          several: keys
          and: values
          with:
            - a
            - list
            - also


'---'
-----

What is the ``---`` we see on top of YAML files? This is a 'document separator', this is an OPTIONAL indicator that a YAML document is starting and not needed for Ansible to function (though some linting programs will complain if it is missing).


Tasks
=====

Tasks are the most common and used item in Ansible, they are the basis of everythign else and they define the 'actions' to take against our targets. A task only requires an ``action`` this normally corresponds to an existing module and/or action plugin.

.. code::

    - debug: msg=simple task

Task are defined by the single action, you cannot have more than one action per tasks, that is 2 tasks, ``name`` and other keywords are optional in the task.

.. code::
    - name: this is a simple task
      debug: msg=simple task

    - name: this is not a valid task because it has 2 actions
      debug: msg=simple task
      copy: src=/etc/localfile dest=/tmp/remotefile

You may have noticed, tasks are always prefixed by a `-`, this is because they are always an 'item of a list', tasks can only exist inside 'task lists', these task lists must reside inside a play, directly or indirectly via a role, block, include or import.

There are 2 ways to write tasks, 'key value pairs' or k=v and pure yaml, which mostly describes how the module/action arguments are defined.

.. code::

    - name: this is a YAML formatted task to copy a file from the controller to the target host
      copy:
        src: /etc/localfile
        dest: /tmp/remotefile

    - debug: msg='this is a key value  pair task'

Indentation is important in a task, to separate the task keywords from the module/action options:

.. code::

    - name: this is the name keyword
      debug:
        msg: 'this is the msg option of the debug action'
      when: 'this is the conditional keyword for tasks' != 'so it must always align to the task itself'

For a list of keywords and the where you can place them see ...

Handlers
--------

Handlers are special tasks, not on how you define them, but on where they are located, they do not execute normally but on notification.For more information on handlers see here:


Plays
=====

Plays are a simple mapping of hosts to tasks, plays bind the actions we define to the targets we desire to apply them to.

.. code::

  - hosts: all

is the simplest play, it just targets all hosts in inventory and (by default) runs M(gather_facts) on them.


There are many ways a play can contain tasks, the simplest one is the ``tasks`` keyword.

.. code::

    - hosts: all
      tasks:
        - name: this is a simple task
          debug: msg=simple task


This keyword is just the home for a 'list of tasks', other ways a play can contain task is via the ``pre_tasks``, ``post_tasks`` and ``handlers`` keywords.

Plays can ONLY appear inside a playbook, you cannot put a play inside another play nor any other object, see playbooks below.

Blocks
------

Blocks are not tasks (they do look like them), but they act as 'list of tasks' inside the 'list of tasks'

.. code::

  - hosts: all
    pre_tasks:
     - block:
          - name: this is a simple task
            debug: msg=simple task

While not being tasks themselves, blocks can appear anywhere a task can as they just 'wrap' tasks.

For more information on blocks see here:

Roles
-----

Roles also contain tasks, but mostly in a separate file, as such, they can appear in plays in several ways,
most of the time you see them via the ``roles`` keyword:

.. code::

   - hosts: all
     roles:
        - rolename

But they can also be included almost anywhere a task can, via the M(include_role) and M(import_role) actions.

.. code::

   - hosts: all
     tasks:
        - include_role: name=rolename
     post_tasks:
        - include_role: name=otherrole

For more information on roles see here:


Playbooks
=========

The definition is simple, playbooks are a 'list of plays', this is normally used to refer to a file with plays, but can also mean an Ansible execution with multiple plays from one or more files. For now we are going to assume the former. A simple playbook as an example:

.. code::
    - hosts: all

This just contains one play, that targtes all hosts, but you can also have more than play (why it is a 'list of plays').

.. code::

    - name: first play
      hosts: some
      tasks:
        ...

    - name: second play
      hosts: others
      roles:
        ...

playbooks can ONLY have plays, you cannot put a task in a playbook, only inside a play.

import_playbook
---------------
Now this might be a bit confusing due to the following being a valid playbook.

.. code::
   - hosts: all

   - import_playbook: play.yml

This looks like we are mixing plays and tasks, but that is not true, the M(import_playbook) is a special directive that allows referencing other playbook files and importing them into the current one, as such it is not considered a 'real task' and is allowed in playbooks. Note that you can have a list of plays imported by M(import_playbook), not just one play.


Full example
============

The following is the contents of a ``site.yml`` playbook.

.. code::
   :caption: playbook
   :emphasize-lines: 1-23

  - name: setup webservers
    hosts: webservers
    tasks:
       - yum: name=apache state=present
         notify: apache_started

    handlers:
      - name: apache_started
        service: name=apache state=started

  - hosts: apiservers
    pre_tasks:
        - name: Remove repository (and clean up left-over metadata)
          yum_repository:
            name: epel
            state: present
    roles:
      - django
      - postgresql_client
    post_tasks:
      - include_role:
            name: internal_firewall

  - import_playbook: dbservers.yml


Now we just highlight the plays.

.. code::
   :caption: plays
   :emphasize-lines: 1-10,11-21

  - name: setup webservers
    hosts: webservers
    tasks:
       - yum: name=apache state=present
         notify: apache_started

    handlers:
      - name: apache_started
        service: name=apache state=started

  - hosts: apiservers
    pre_tasks:
        - name: Remove repository (and clean up left-over metadata)
          yum_repository:
            name: epel
            state: present
    roles:
      - django
      - postgresql_client
    post_tasks:
      - include_role:
            name: internal_firewall

  - import_playbook: dbservers.yml


Now just the tasks.

.. code::
   :caption: tasks
   :emphasize-lines: 4-5,8-9,13-16,21-22

  - name: setup webservers
    hosts: webservers
    tasks:
       - yum: name=apache state=present
         notify: apache_started

    handlers:
      - name: apache_started
        service: name=apache state=started

  - hosts: apiservers
    pre_tasks:
        - name: Remove repository (and clean up left-over metadata)
          yum_repository:
            name: epel
            state: present
    roles:
      - django
      - postgresql_client
    post_tasks:
      - include_role:
            name: internal_firewall

  - import_playbook: dbservers.yml


There is a lot more to Ansible, but this should be the minimal you need to start writing your own playbooks, plays and tasks.
