.. _check_mode_dry:

Check Mode ("Dry Run")
======================

.. versionadded:: 1.1

.. contents:: Topics

When ansible-playbook is executed with ``--check`` it will not make any changes on remote systems.  Instead, any module
instrumented to support 'check mode' (which contains most of the primary core modules, but it is not required that all modules do
this) will report what changes they would have made rather than making them.  Other modules that do not support check mode will also take no action, but just will not report what changes they might have made.

Check mode is just a simulation, and if you have steps that use conditionals that depend on the results of prior commands,
it may be less useful for you.  However it is great for one-node-at-time basic configuration management use cases.

Example::

    ansible-playbook foo.yml --check

.. _forcing_to_run_in_check_mode:

Enabling or disabling check mode for tasks
``````````````````````````````````````````

.. versionadded:: 2.2

Sometimes you may want to modify the check mode behavior of individual tasks. This is done via the ``check_mode`` option, which can
be added to tasks.

There are two options:

1. Force a task to **run in check mode**, even when the playbook is called **without** ``--check``. This is called ``check_mode: yes``.
2. Force a task to **run in normal mode** and make changes to the system, even when the playbook is called **with** ``--check``. This is called ``check_mode: no``.

.. note:: Prior to version 2.2 only the equivalent of ``check_mode: no`` existed. The notation for that was ``always_run: yes``.

Instead of ``yes``/``no`` you can use a Jinja2 expression, just like the ``when`` clause.

Example::

  tasks:
    - name: this task will make changes to the system even in check mode
      command: /something/to/run --even-in-check-mode
      check_mode: no

    - name: this task will always run under checkmode and not change the system
      lineinfile:
          line: "important config"
          dest: /path/to/myconfig.conf
          state: present
      check_mode: yes


Running single tasks with ``check_mode: yes`` can be useful to write tests for
ansible modules, either to test the module itself or to the conditions under
which a module would make changes.
With ``register`` (see :ref:`playbooks_conditionals`) you can check the
potential changes.

Information about check mode in variables
`````````````````````````````````````````

.. versionadded:: 2.1

If you want to skip, or ignore errors on some tasks in check mode
you can use a boolean magic variable ``ansible_check_mode``
which will be set to ``True`` during check mode.

Example::


  tasks:

    - name: this task will be skipped in check mode
      git:
        repo: ssh://git@github.com/mylogin/hello.git
        dest: /home/mylogin/hello
      when: not ansible_check_mode

    - name: this task will ignore errors in check mode
      git:
        repo: ssh://git@github.com/mylogin/hello.git
        dest: /home/mylogin/hello
      ignore_errors: "{{ ansible_check_mode }}"

.. _diff_mode:

Showing Differences with ``--diff``
```````````````````````````````````

.. versionadded:: 1.1

The ``--diff`` option to ansible-playbook works great with ``--check`` (detailed above) but can also be used by itself.
When this flag is supplied and the module supports this, Ansible will report back the changes made or, if used with ``--check``, the changes that would have been made.
This is mostly used in modules that manipulate files (i.e. template) but other modules might also show 'before and after' information (i.e. user).
Since the diff feature produces a large amount of output, it is best used when checking a single host at a time. For example::

    ansible-playbook foo.yml --check --diff --limit foo.example.com

.. versionadded:: 2.4

The ``--diff`` option can reveal sensitive information. This option can disabled for tasks by specifying ``diff: no``.

Example::

  tasks:
    - name: this task will not report a diff when the file changes
      template:
        src: secret.conf.j2
        dest: /etc/secret.conf
        owner: root
        group: root
        mode: '0600'
      diff: no
