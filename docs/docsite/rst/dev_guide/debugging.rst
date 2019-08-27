.. _debugging:

*****************
Debugging modules
*****************

Debugging (local)
=================

To break into a module running on ``localhost`` and step through with the debugger:

- Set a breakpoint in the module: ``import pdb; pdb.set_trace()``
- Run the module on the local machine: ``$ python -m pdb ./my_new_test_module.py ./args.json``

Example
-------

`echo '{"msg": "hello"}' | python ./my_new_test_module.py`

Debugging (remote)
==================

To debug a module running on a remote target (i.e. not ``localhost``):

#. On your controller machine (running Ansible) set ``ANSIBLE_KEEP_REMOTE_FILES=1`` to tell Ansible to retain the modules it sends to the remote machine instead of removing them after you playbook runs.
#. Run your playbook targeting the remote machine and specify ``-vvvv`` (verbose) to display the remote location Ansible is using for the modules (among many other things).
#. Take note of the directory Ansible used to store modules on the remote host. This directory is usually under the home directory of your ``ansible_user``, in the form ``~/.ansible/tmp/ansible-tmp-...``.
#. SSH into the remote target after the playbook runs.
#. Navigate to the directory you noted in step 3.
#. Extract the module you want to debug from the zipped file that Ansible sent to the remote host: ``$ python AnsiballZ_my_test_module.py explode``. Ansible will expand the module into ``./debug-dir``. You can optionally run the zipped file by specifying ``python AnsiballZ_my_test_module.py``.
#. Navigate to the debug directory: ``$ cd debug-dir``.
#. Modify or set a breakpoint in ``__main__.py``.
#. Ensure that the unzipped module is executable: ``$ chmod 755 __main__.py``.
#. Run the unzipped module directly, passing the ``args`` file that contains the params that were originally passed: ``$ ./__main__.py args``. This approach is good for reproducing behavior as well as modifying the parameters for debugging.


.. _debugging_ansiblemodule_based_modules:

Debugging AnsibleModule-based modules
=====================================

.. tip::

    If you're using the :file:`hacking/test-module.py` script then most of this
    is taken care of for you.  If you need to do some debugging of the module
    on the remote machine that the module will actually run on or when the
    module is used in a playbook then you may need to use this information
    instead of relying on :file:`test-module.py`.

Starting with Ansible 2.1, AnsibleModule-based modules are put together as
a zip file consisting of the module file and the various python module
boilerplate inside of a wrapper script instead of as a single file with all of
the code concatenated together.  Without some help, this can be harder to
debug as the file needs to be extracted from the wrapper in order to see
what's actually going on in the module.  Luckily the wrapper script provides
some helper methods to do just that.

If you are using Ansible with the :envvar:`ANSIBLE_KEEP_REMOTE_FILES`
environment variables to keep the remote module file, here's a sample of how
your debugging session will start:

.. code-block:: shell-session

    $ ANSIBLE_KEEP_REMOTE_FILES=1 ansible localhost -m ping -a 'data=debugging_session' -vvv
    <127.0.0.1> ESTABLISH LOCAL CONNECTION FOR USER: badger
    <127.0.0.1> EXEC /bin/sh -c '( umask 77 && mkdir -p "` echo $HOME/.ansible/tmp/ansible-tmp-1461434734.35-235318071810595 `" && echo "` echo $HOME/.ansible/tmp/ansible-tmp-1461434734.35-235318071810595 `" )'
    <127.0.0.1> PUT /var/tmp/tmpjdbJ1w TO /home/badger/.ansible/tmp/ansible-tmp-1461434734.35-235318071810595/ping
    <127.0.0.1> EXEC /bin/sh -c 'LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 LC_MESSAGES=en_US.UTF-8 /usr/bin/python /home/badger/.ansible/tmp/ansible-tmp-1461434734.35-235318071810595/ping'
    localhost | SUCCESS => {
        "changed": false,
        "invocation": {
            "module_args": {
                "data": "debugging_session"
            },
            "module_name": "ping"
        },
        "ping": "debugging_session"
    }

Setting :envvar:`ANSIBLE_KEEP_REMOTE_FILES` to ``1`` tells Ansible to keep the
remote module files instead of deleting them after the module finishes
executing.  Giving Ansible the ``-vvv`` option makes Ansible more verbose.
That way it prints the file name of the temporary module file for you to see.

If you want to examine the wrapper file you can.  It will show a small python
script with a large, base64 encoded string.  The string contains the module
that is going to be executed.  Run the wrapper's explode command to turn the
string into some python files that you can work with:

.. code-block:: shell-session

    $ python /home/badger/.ansible/tmp/ansible-tmp-1461434734.35-235318071810595/ping explode
    Module expanded into:
    /home/badger/.ansible/tmp/ansible-tmp-1461434734.35-235318071810595/debug_dir

When you look into the debug_dir you'll see a directory structure like this::

    ├── ansible_module_ping.py
    ├── args
    └── ansible
        ├── __init__.py
        └── module_utils
            ├── basic.py
            └── __init__.py

* :file:`ansible_module_ping.py` is the code for the module itself.  The name
  is based on the name of the module with a prefix so that we don't clash with
  any other python module names.  You can modify this code to see what effect
  it would have on your module.

* The :file:`args` file contains a JSON string.  The string is a dictionary
  containing the module arguments and other variables that Ansible passes into
  the module to change its behaviour.  If you want to modify the parameters
  that are passed to the module, this is the file to do it in.

* The :file:`ansible` directory contains code from
  :mod:`ansible.module_utils` that is used by the module.  Ansible includes
  files for any :mod:`ansible.module_utils` imports in the module but not
  any files from any other module.  So if your module uses
  :mod:`ansible.module_utils.url` Ansible will include it for you, but if
  your module includes `requests <http://docs.python-requests.org/en/master/api/>`_ then you'll have to make sure that
  the python `requests library <https://pypi.org/project/requests/>`_ is installed on the system before running the
  module.  You can modify files in this directory if you suspect that the
  module is having a problem in some of this boilerplate code rather than in
  the module code you have written.

Once you edit the code or arguments in the exploded tree you need some way to
run it.  There's a separate wrapper subcommand for this:

.. code-block:: shell-session

    $ python /home/badger/.ansible/tmp/ansible-tmp-1461434734.35-235318071810595/ping execute
    {"invocation": {"module_args": {"data": "debugging_session"}}, "changed": false, "ping": "debugging_session"}

This subcommand takes care of setting the PYTHONPATH to use the exploded
:file:`debug_dir/ansible/module_utils` directory and invoking the script using
the arguments in the :file:`args` file.  You can continue to run it like this
until you understand the problem.  Then you can copy it back into your real
module file and test that the real module works via :command:`ansible` or
:command:`ansible-playbook`.

.. note::

    The wrapper provides one more subcommand, ``excommunicate``.  This
    subcommand is very similar to ``execute`` in that it invokes the exploded
    module on the arguments in the :file:`args`.  The way it does this is
    different, however.  ``excommunicate`` imports the ``main``
    function from the module and then calls that.  This makes excommunicate
    execute the module in the wrapper's process.  This may be useful for
    running the module under some graphical debuggers but it is very different
    from the way the module is executed by Ansible itself.  Some modules may
    not work with ``excommunicate`` or may behave differently than when used
    with Ansible normally.  Those are not bugs in the module; they're
    limitations of ``excommunicate``.  Use at your own risk.
