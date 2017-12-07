.. _module_dev_conventions:

Conventions, Best Practices, and Pitfalls
`````````````````````````````````````````

As a reminder from the example code above, here are some basic conventions
and guidelines:

* If the module is addressing an object, the parameter for that object should be called 'name' whenever possible, or accept 'name' as an alias.

* If you have a company module that returns facts specific to your installations, a good name for this module is `site_facts`.

* Modules accepting boolean status should generally accept 'yes', 'no', 'true', 'false', or anything else a user may likely throw at them.  The AnsibleModule common code supports this with "type='bool'".

* Include a minimum of dependencies if possible.  If there are dependencies, document them at the top of the module file, and have the module raise JSON error messages when the import fails.

* Modules must be self-contained in one file to be auto-transferred by ansible.

* If packaging modules in an RPM, they only need to be installed on the control machine and should be dropped into /usr/share/ansible.  This is entirely optional and up to you.

* Modules must output valid JSON only. The top level return type must be a hash (dictionary) although they can be nested.  Lists or simple scalar values are not supported, though they can be trivially contained inside a dictionary.

* In the event of failure, a key of 'failed' should be included, along with a string explanation in 'msg'.  Modules that raise tracebacks (stacktraces) are generally considered 'poor' modules, though Ansible can deal with these returns and will automatically convert anything unparseable into a failed result.  If you are using the AnsibleModule common Python code, the 'failed' element will be included for you automatically when you call 'fail_json'.

* Return codes from modules are actually not significant, but continue on with 0=success and non-zero=failure for reasons of future proofing.

* As results from many hosts will be aggregated at once, modules should return only relevant output.  Returning the entire contents of a log file is generally bad form.

* Modules should have a concise and well defined functionality. Basically, follow the UNIX philosophy of doing one thing well.

* Modules should not require that a user know all the underlying options of an api/tool to be used. For instance, if the legal values for a required module parameter cannot be documented, that's a sign that the module would be rejected.

* Modules should typically encompass much of the logic for interacting with a resource. A lightweight wrapper around an API that does not contain much logic would likely cause users to offload too much logic into a playbook, and for this reason the module would be rejected. Instead try creating multiple modules for interacting with smaller individual pieces of the API.

.. _debugging_ansiblemodule_based_modules:

Debugging AnsibleModule-based modules
`````````````````````````````````````

.. tip::

    If you're using the :file:`hacking/test-module` script then most of this
    is taken care of for you.  If you need to do some debugging of the module
    on the remote machine that the module will actually run on or when the
    module is used in a playbook then you may need to use this information
    instead of relying on test-module.

Starting with Ansible-2.1.0, AnsibleModule-based modules are put together as
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
  files for any :`module:`ansible.module_utils` imports in the module but not
  any files from any other module.  So if your module uses
  :mod:`ansible.module_utils.url` Ansible will include it for you, but if
  your module includes :mod:`requests` then you'll have to make sure that
  the python requests library is installed on the system before running the
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
    different, however.  ``excommunicate`` imports the :func:`main`
    function from the module and then calls that.  This makes excommunicate
    execute the module in the wrapper's process.  This may be useful for
    running the module under some graphical debuggers but it is very different
    from the way the module is executed by Ansible itself.  Some modules may
    not work with ``excommunicate`` or may behave differently than when used
    with Ansible normally.  Those are not bugs in the module; they're
    limitations of ``excommunicate``.  Use at your own risk.


Module Paths
````````````

If you are having trouble getting your module "found" by ansible, be
sure it is in the :envvar:`ANSIBLE_LIBRARY` environment variable.

If you have a fork of one of the ansible module projects, do something like this::

    ANSIBLE_LIBRARY=~/ansible-modules-core

And this will make the items in your fork be loaded ahead of what ships with Ansible.  Just be sure
to make sure you're not reporting bugs on versions from your fork!

To be safe, if you're working on a variant on something in Ansible's normal distribution, it's not
a bad idea to give it a new name while you are working on it, to be sure you know you're pulling
your version.

Common Pitfalls
```````````````

You should never do this in a module:

.. code-block:: python

    print("some status message")

Because the output is supposed to be valid JSON.

Modules must not output anything on standard error, because the system will merge
standard out with standard error and prevent the JSON from parsing. Capturing standard
error and returning it as a variable in the JSON on standard out is fine, and is, in fact,
how the command module is implemented.

If a module returns stderr or otherwise fails to produce valid JSON, the actual output
will still be shown in Ansible, but the command will not succeed.

Don't write to files directly; use a temporary file and then use the `atomic_move` function from `ansible.module_utils.basic` to move the updated temporary file into place. This prevents data corruption and ensures that the correct context for the file is kept.

Avoid creating a module that does the work of other modules; this leads to code duplication and divergence, and makes things less uniform, unpredictable and harder to maintain. Modules should be the building blocks. Instead of creating a module that does the work of other modules, use Plays and Roles instead.  

Avoid creating 'caches'. Ansible is designed without a central server or authority, so you cannot guarantee it will not run with different permissions, options or locations. If you need a central authority, have it on top of Ansible (for example, using bastion/cm/ci server or tower); do not try to build it into modules.

Always use the hacking/test-module script when developing modules and it will warn
you about these kind of things.
