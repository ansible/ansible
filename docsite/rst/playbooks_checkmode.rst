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

Running a task in check mode
````````````````````````````

.. versionadded:: 1.3

Sometimes you may want to have a task to be executed even in check
mode. To achieve this, use the `always_run` clause on the task. Its
value is a Jinja2 expression, just like the `when` clause. In simple
cases a boolean YAML value would be sufficient as a value.

Example::

    tasks:

      - name: this task is run even in check mode
        command: /something/to/run --even-in-check-mode
        always_run: yes

As a reminder, a task with a `when` clause evaluated to false, will
still be skipped even if it has a `always_run` clause evaluated to
true. 

Also if you want to skip, or ignore errors on some tasks in check mode
you can use a boolean magic variable `ansible_check_mode` (added in version 2.1)
which will be set to `True` during check mode.

Example::

    tasks:

      - name: this task will be skipped in check mode
        git: repo=ssh://git@github.com/mylogin/hello.git dest=/home/mylogin/hello
        when: not ansible_check_mode

      - name: this task will ignore errors in check mode
        git: repo=ssh://git@github.com/mylogin/hello.git dest=/home/mylogin/hello
        ignore_errors: "{{ ansible_check_mode }}"



.. _diff_mode:

Showing Differences with ``--diff``
```````````````````````````````````

.. versionadded:: 1.1

The ``--diff`` option to ansible-playbook works great with ``--check`` (detailed above) but can also be used by itself.  When this flag is supplied, if any templated files on the remote system are changed, and the ansible-playbook CLI will report back
the textual changes made to the file (or, if used with ``--check``, the changes that would have been made).  Since the diff
feature produces a large amount of output, it is best used when checking a single host at a time, like so::

    ansible-playbook foo.yml --check --diff --limit foo.example.com

