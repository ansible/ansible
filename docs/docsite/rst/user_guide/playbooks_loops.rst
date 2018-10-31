.. _playbooks_loops:

*****
Loops
*****

Sometimes you want to repeat a task multiple times. In computer programming, this is called a loop. Common Ansible loops include installing several packages with the :ref:`yum module <yum_module>`, creating multiple users with the :ref:`user module <user_module>`, and
repeating a polling step until a certain result is reached. Ansible offers two keywords for creating loops: ``loop`` and ``with_<lookup>``.

.. note::
   * We added ``loop`` in Ansible 2.5, but it is not yet a full replacement for ``with_<lookup>``.
   * We have not deprecated the use of ``with_<lookup>``.
   * We are still discussing what UX changes can be made to enable ``loop`` to replace ``with_<lookup>`` in the future.
   * If we eventually deprecate the ``with_`` syntax, the deprecation cycle will be longer than usual.

.. contents::
   :local:

Comparing ``loop`` and ``with_*``
=================================

* The ``with_<lookup>`` keywords rely on :ref:`lookup_plugins` - even  ``items`` is a lookup.
* The ``loop`` keyword is equivalent to ``with_list``, and is the best choice for simple loops.
* Generally speaking, any use of ``with_*`` covered in :ref:`migrating_to_loop` can be updated to use ``loop``.
* Be careful when changing ``with_items`` to ``loop``, as ``with_items`` performed implicit flattening. You may need to use ``flatten`` with ``loop`` to match the exact outcome.
* Any ``with_*`` statement that requires using ``lookup`` within a loop should not be converted to use the ``loop`` keyword.

.. _standard_loops:

Standard loops
==============

Iterating over a simple list
----------------------------

Repeated tasks can be written as standard loops over a simple list of strings. You can define the list directly in the task::

    - name: add several users
      user:
        name: "{{ item }}"
        state: present
        groups: "wheel"
      loop:
         - testuser1
         - testuser2

You can define the list in a variables file, or in the 'vars' section of your play, then refer to the name of the list in the task::

    loop: "{{ somelist }}"

Either of these examples would be the equivalent of::

    - name: add user testuser1
      user:
        name: "testuser1"
        state: present
        groups: "wheel"

    - name: add user testuser2
      user:
        name: "testuser2"
        state: present
        groups: "wheel"

You can pass a list directly to a parameter for some plugins, like the yum and apt modules. When available, passing the list to a parameter is better than looping over the task. For example::

   - name: optimal yum
     yum:
       name: "{{  list_of_packages  }}"
       state: present

   - name: non-optimal yum, slower and may cause issues with interdependencies
     yum:
       name: "{{  item  }}"
       state: present
     loop: "{{  list_of_packages  }}"

Review the module or plugin's documentation for details.

Iterating over a list of hashes
-------------------------------

If you have a list of hashes, you can reference subkeys in a loop. For example::

    - name: add several users
      user:
        name: "{{ item.name }}"
        state: present
        groups: "{{ item.groups }}"
      loop:
        - { name: 'testuser1', groups: 'wheel' }
        - { name: 'testuser2', groups: 'root' }

When combining :ref:`playbooks_conditionals` with a loop, the ``when:`` statement is processed separately for each item.
See :ref:`the_when_statement` for examples.

Iterating over a dictionary
---------------------------

To loop over a dict, use the ``dict2items`` :ref:`dict_filter`::

    - name: create a tag dictionary of non-empty tags
      set_fact:
        tags_dict: "{{ (tags_dict|default({}))|combine({item.key: item.value}) }}"
      loop: "{{ tags|dict2items }}"
      vars:
        tags:
          Environment: dev
          Application: payment
          Another: "{{ doesnotexist|default() }}"
      when: item.value != ""

Here, we don't want to set empty tags, so we create a dictionary containing only non-empty tags.

Registering variables with a loop
=================================

You can register the output of a loop as a variable. For example::

   - shell: "echo {{ item }}"
     loop:
       - "one"
       - "two"
     register: echo

When you use ``register`` with a loop, the data structure placed in the variable will contain a ``results`` attribute that is a list of all responses from the module. This differs from the data structure returned when using ``register`` without a loop::

    {
        "changed": true,
        "msg": "All items completed",
        "results": [
            {
                "changed": true,
                "cmd": "echo \"one\" ",
                "delta": "0:00:00.003110",
                "end": "2013-12-19 12:00:05.187153",
                "invocation": {
                    "module_args": "echo \"one\"",
                    "module_name": "shell"
                },
                "item": "one",
                "rc": 0,
                "start": "2013-12-19 12:00:05.184043",
                "stderr": "",
                "stdout": "one"
            },
            {
                "changed": true,
                "cmd": "echo \"two\" ",
                "delta": "0:00:00.002920",
                "end": "2013-12-19 12:00:05.245502",
                "invocation": {
                    "module_args": "echo \"two\"",
                    "module_name": "shell"
                },
                "item": "two",
                "rc": 0,
                "start": "2013-12-19 12:00:05.242582",
                "stderr": "",
                "stdout": "two"
            }
        ]
    }

Subsequent loops over the registered variable to inspect the results may look like::

    - name: Fail if return code is not 0
      fail:
        msg: "The command ({{ item.cmd }}) did not have a 0 return code"
      when: item.rc != 0
      loop: "{{ echo.results }}"

During iteration, the result of the current item will be placed in the variable::

    - shell: echo "{{ item }}"
      loop:
        - one
        - two
      register: echo
      changed_when: echo.stdout != "one"

.. _complex_loops:

Complex loops
=============

Iterating over nested lists
---------------------------

Sometimes you need more than what a simple list provides, you can use Jinja2 expressions to create complex lists:
For example, using the 'nested' lookup, you can combine lists::

    - name: give users access to multiple databases
      mysql_user:
        name: "{{ item[0] }}"
        priv: "{{ item[1] }}.*:ALL"
        append_privs: yes
        password: "foo"
      loop: "{{ ['alice', 'bob'] |product(['clientdb', 'employeedb', 'providerdb'])|list }}"


.. _do_until_loops:

Retrying a task until a condition is met
----------------------------------------

.. versionadded:: 1.4

You can use the ``until`` keyword to retry a task until a certain condition is met.  Here's an example::

    - shell: /usr/bin/foo
      register: result
      until: result.stdout.find("all systems go") != -1
      retries: 5
      delay: 10

This task runs up to 5 times with a delay of 10 seconds between each attempt. If the result of any attempt has "all systems go" in its stdout, the task succeeds. The default value for "retries" is 3 and "delay" is 5.

To see the results of individual retries, run the play with ``-vv``.

When you run a task with ``until`` and register the result as a variable, the registered variable will include a key called "attempts", which records the number of the retries for the task.

.. note:: You must set the ``until`` parameter if you want a task to retry. If ``until`` is not defined, the value for the ``retries`` parameter is forced to 1.

Looping over inventory
----------------------

To loop over your inventory, or just a subset of it, you can use a regular ``loop`` with the ``ansible_play_batch`` or ``groups`` variables::

    # show all the hosts in the inventory
    - debug:
        msg: "{{ item }}"
      loop: "{{ groups['all'] }}"

    # show all the hosts in the current play
    - debug:
        msg: "{{ item }}"
      loop: "{{ ansible_play_batch }}"

There is also a specific lookup plugin ``inventory_hostnames`` that can be used like this::

    # show all the hosts in the inventory
    - debug:
        msg: "{{ item }}"
      loop: "{{ query('inventory_hostnames', 'all') }}"

    # show all the hosts matching the pattern, ie all but the group www
    - debug:
        msg: "{{ item }}"
      loop: "{{ query('inventory_hostnames', 'all:!www') }}"

More information on the patterns can be found on :ref:`intro_patterns`

Ensuring list input for ``loop``: ``query`` vs. ``lookup``
==========================================================

The ``loop`` keyword requires a list as input, but the ``lookup`` keyword returns a string of comma-separated values by default. Ansible 2.5 introduced a new Jinja2 function named :ref:`query` that always returns a list, offering a simpler interface and more predictable output from lookup plugins when using the ``loop`` keyword.

You can force ``lookup`` to return a list to ``loop`` by using ``wantlist=True``, or you can use ``query`` instead.

These examples do the same thing::

    loop: "{{ query('inventory_hostnames', 'all') }}"

    loop: "{{ lookup('inventory_hostnames', 'all', wantlist=True) }}"


.. _loop_control:

Adding controls to loops
========================

.. versionadded:: 2.1

In 2.0 you are again able to use loops and task includes (but not playbook includes). This adds the ability to loop over the set of tasks in one shot.
Ansible by default sets the loop variable ``item`` for each loop, which causes these nested loops to overwrite the value of ``item`` from the "outer" loops.
As of Ansible 2.1, the ``loop_control`` option can be used to specify the name of the variable to be used for the loop::

    # main.yml
    - include_tasks: inner.yml
      loop:
        - 1
        - 2
        - 3
      loop_control:
        loop_var: outer_item

    # inner.yml
    - debug:
        msg: "outer item={{ outer_item }} inner item={{ item }}"
      loop:
        - a
        - b
        - c

.. note:: If Ansible detects that the current loop is using a variable which has already been defined, it will raise an error to fail the task.

.. versionadded:: 2.2

When using complex data structures for looping the display might get a bit too "busy", this is where the ``label`` directive comes to help::

    - name: create servers
      digital_ocean:
        name: "{{ item.name }}"
        state: present
      loop:
        - name: server1
          disks: 3gb
          ram: 15Gb
          network:
            nic01: 100Gb
            nic02: 10Gb
            ...
      loop_control:
        label: "{{ item.name }}"

This will now display just the ``label`` field instead of the whole structure per ``item``, it defaults to ``{{ item }}`` to display things as usual.

.. versionadded:: 2.2

Another option to loop control is ``pause``, which allows you to control the time (in seconds) between execution of items in a task loop.::

    # main.yml
    - name: create servers, pause 3s before creating next
      digital_ocean:
        name: "{{ item }}"
        state: present
      loop:
        - server1
        - server2
      loop_control:
        pause: 3

.. versionadded:: 2.5

If you need to keep track of where you are in a loop, you can use the ``index_var`` option to loop control to specify a variable name to contain the current loop index.::

    - name: count our fruit
      debug:
        msg: "{{ item }} with index {{ my_idx }}"
      loop:
        - apple
        - banana
        - pear
      loop_control:
        index_var: my_idx

.. versionadded:: 2.8

As of Ansible 2.8 you can get extended loop information using the ``extended`` option to loop control. This option will expose the following information.

==========================  ===========
Variable                    Description
--------------------------  -----------
``ansible_loop.allitems``   The list of all items in the loop
``ansible_loop.index``      The current iteration of the loop. (1 indexed)
``ansible_loop.index0``     The current iteration of the loop. (0 indexed)
``ansible_loop.revindex``   The number of iterations from the end of the loop (1 indexed)
``ansible_loop.revindex0``  The number of iterations from the end of the loop (0 indexed)
``ansible_loop.first``      ``True`` if first iteration
``ansible_loop.last``       ``True`` if last iteration
``ansible_loop.length``     The number of items in the loop
``ansible_loop.previtem``   The item from the previous iteration of the loop. Undefined during the first iteration.
``ansible_loop.nextitem``   The item from the following iteration of the loop. Undefined during the last iteration.
==========================  ===========

::

      loop_control:
        extended: yes
=======

.. _migrating_to_loop:

Migrating from with_X to loop
=============================

.. include:: shared_snippets/with2loop.txt

.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :ref:`playbooks_reuse_roles`
       Playbook organization by roles
   :ref:`playbooks_best_practices`
       Best practices in playbooks
   :ref:`playbooks_conditionals`
       Conditional statements in playbooks
   :ref:`playbooks_variables`
       All about variables
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
