.. _module_dev_tutorial_sample:

Building A Simple Module
````````````````````````

Let's build a very-basic module to get and set the system time.  For starters, let's build
a module that just outputs the current time.

We are going to use Python here but any language is possible.  Only File I/O and outputting to standard
out are required.  So, bash, C++, clojure, Python, Ruby, whatever you want
is fine.

Now Python Ansible modules contain some extremely powerful shortcuts (that all the core modules use)
but first we are going to build a module the very hard way.  The reason we do this is because modules
written in any language OTHER than Python are going to have to do exactly this.  We'll show the easy
way later.

So, here's an example.  You would never really need to build a module to set the system time,
the 'command' module could already be used to do this.

Reading the modules that come with Ansible (linked above) is a great way to learn how to write
modules.   Keep in mind, though, that some modules in Ansible's source tree are internalisms,
so look at :ref:`service` or :ref:`yum`, and don't stare too close into things like ``async_wrapper`` or
you'll turn to stone.  Nobody ever executes ``async_wrapper`` directly.

Ok, let's get going with an example.  We'll use Python.  For starters, save this as a file named :file:`timetest.py`

.. code-block:: python

    #!/usr/bin/python

    import datetime
    import json

    date = str(datetime.datetime.now())
    print json.dumps({
        "Hello world!" : date
    })
.. _module_testing:

Testing Modules
````````````````

There's a useful test script in the source checkout for Ansible:

.. code-block:: shell-session

    git clone git://github.com/ansible/ansible.git --recursive
    source ansible/hacking/env-setup

For instructions on setting up Ansible from source, please see
:doc:`../intro_installation`.

Let's run the script you just wrote with that:

.. code-block:: shell-session

    ansible/hacking/test-module -m ./timetest.py

You should see output that looks something like this:

.. code-block:: json

    {"time": "2012-03-14 22:13:48.539183"}

If you did not, you might have a typo in your module, so recheck it and try again.

.. _reading_input:

Reading Input
`````````````
Let's modify the module to allow setting the current time.  We'll do this by seeing
if a key value pair in the form `time=<string>` is passed in to the module.

Ansible internally saves arguments to an arguments file.  So we must read the file
and parse it.  The arguments file is just a string, so any form of arguments are legal.
Here we'll do some basic parsing to treat the input as key=value.

The example usage we are trying to achieve to set the time is::

   time time="March 14 22:10"

If no time parameter is set, we'll just leave the time as is and return the current time.

.. note::
   This is obviously an unrealistic idea for a module.  You'd most likely just
   use the command module.  However, it makes for a decent tutorial.

Let's look at the code.  Read the comments as we'll explain as we go.  Note that this
is highly verbose because it's intended as an educational example.  You can write modules
a lot shorter than this:

.. code-block:: python

    #!/usr/bin/python

    # import some python modules that we'll use.  These are all
    # available in Python's core

    import datetime
    import sys
    import json
    import os
    import shlex

    # read the argument string from the arguments file
    args_file = sys.argv[1]
    args_data = file(args_file).read()

    # For this module, we're going to do key=value style arguments.
    # Modules can choose to receive json instead by adding the string:
    #   WANT_JSON
    # Somewhere in the file.
    # Modules can also take free-form arguments instead of key-value or json
    # but this is not recommended.

    arguments = shlex.split(args_data)
    for arg in arguments:

        # ignore any arguments without an equals in it
        if "=" in arg:

            (key, value) = arg.split("=")

            # if setting the time, the key 'time'
            # will contain the value we want to set the time to

            if key == "time":

                # now we'll affect the change.  Many modules
                # will strive to be idempotent, generally
                # by not performing any actions if the current
                # state is the same as the desired state.
                # See 'service' or 'yum' in the main git tree
                # for an illustrative example.

                rc = os.system("date -s \"%s\"" % value)

                # always handle all possible errors
                #
                # when returning a failure, include 'failed'
                # in the return data, and explain the failure
                # in 'msg'.  Both of these conventions are
                # required however additional keys and values
                # can be added.

                if rc != 0:
                    print json.dumps({
                        "failed" : True,
                        "msg"    : "failed setting the time"
                    })
                    sys.exit(1)

                # when things do not fail, we do not
                # have any restrictions on what kinds of
                # data are returned, but it's always a
                # good idea to include whether or not
                # a change was made, as that will allow
                # notifiers to be used in playbooks.

                date = str(datetime.datetime.now())
                print json.dumps({
                    "time" : date,
                    "changed" : True
                })
                sys.exit(0)

    # if no parameters are sent, the module may or
    # may not error out, this one will just
    # return the time

    date = str(datetime.datetime.now())
    print json.dumps({
        "time" : date
    })

Let's test that module::

    ansible/hacking/test-module -m ./timetest.py -a "time=\"March 14 12:23\""

This should return something like::

    {"changed": true, "time": "2012-03-14 12:23:00.000307"}

.. _module_testing:

Testing Modules
````````````````

There's a useful test script in the source checkout for Ansible:

.. code-block:: shell-session

    git clone git://github.com/ansible/ansible.git --recursive
    source ansible/hacking/env-setup

For instructions on setting up Ansible from source, please see
:doc:`../intro_installation`.

Let's run the script you just wrote with that:

.. code-block:: shell-session

    ansible/hacking/test-module -m ./timetest.py

You should see output that looks something like this:

.. code-block:: json

    {"time": "2012-03-14 22:13:48.539183"}

If you did not, you might have a typo in your module, so recheck it and try again.

.. _reading_input:

Reading Input
`````````````
Let's modify the module to allow setting the current time.  We'll do this by seeing
if a key value pair in the form `time=<string>` is passed in to the module.

Ansible internally saves arguments to an arguments file.  So we must read the file
and parse it.  The arguments file is just a string, so any form of arguments are legal.
Here we'll do some basic parsing to treat the input as key=value.

The example usage we are trying to achieve to set the time is::

   time time="March 14 22:10"

If no time parameter is set, we'll just leave the time as is and return the current time.

.. note::
   This is obviously an unrealistic idea for a module.  You'd most likely just
   use the command module.  However, it makes for a decent tutorial.

Let's look at the code.  Read the comments as we'll explain as we go.  Note that this
is highly verbose because it's intended as an educational example.  You can write modules
a lot shorter than this:

.. code-block:: python

    #!/usr/bin/python

    # import some python modules that we'll use.  These are all
    # available in Python's core

    import datetime
    import sys
    import json
    import os
    import shlex

    # read the argument string from the arguments file
    args_file = sys.argv[1]
    args_data = file(args_file).read()

    # For this module, we're going to do key=value style arguments.
    # Modules can choose to receive json instead by adding the string:
    #   WANT_JSON
    # Somewhere in the file.
    # Modules can also take free-form arguments instead of key-value or json
    # but this is not recommended.

    arguments = shlex.split(args_data)
    for arg in arguments:

        # ignore any arguments without an equals in it
        if "=" in arg:

            (key, value) = arg.split("=")

            # if setting the time, the key 'time'
            # will contain the value we want to set the time to

            if key == "time":

                # now we'll affect the change.  Many modules
                # will strive to be idempotent, generally
                # by not performing any actions if the current
                # state is the same as the desired state.
                # See 'service' or 'yum' in the main git tree
                # for an illustrative example.

                rc = os.system("date -s \"%s\"" % value)

                # always handle all possible errors
                #
                # when returning a failure, include 'failed'
                # in the return data, and explain the failure
                # in 'msg'.  Both of these conventions are
                # required however additional keys and values
                # can be added.

                if rc != 0:
                    print json.dumps({
                        "failed" : True,
                        "msg"    : "failed setting the time"
                    })
                    sys.exit(1)

                # when things do not fail, we do not
                # have any restrictions on what kinds of
                # data are returned, but it's always a
                # good idea to include whether or not
                # a change was made, as that will allow
                # notifiers to be used in playbooks.

                date = str(datetime.datetime.now())
                print json.dumps({
                    "time" : date,
                    "changed" : True
                })
                sys.exit(0)

    # if no parameters are sent, the module may or
    # may not error out, this one will just
    # return the time

    date = str(datetime.datetime.now())
    print json.dumps({
        "time" : date
    })

Let's test that module::

    ansible/hacking/test-module -m ./timetest.py -a "time=\"March 14 12:23\""

This should return something like::

    {"changed": true, "time": "2012-03-14 12:23:00.000307"}

.. _binary_module_reading_input:

Binary Modules Input
++++++++++++++++++++

Support for binary modules was added in Ansible 2.2.  When Ansible detects a binary module, it will proceed to
supply the argument input as a file on ``argv[1]`` that is formatted as JSON.  The JSON contents of that file
would resemble something similar to the following payload for a module accepting the same arguments as the
``ping`` module:

.. code-block:: json

    {
        "data": "pong",
        "_ansible_verbosity": 4,
        "_ansible_diff": false,
        "_ansible_debug": false,
        "_ansible_check_mode": false,
        "_ansible_no_log": false
    }

.. _module_provided_facts:

Module Provided 'Facts'
````````````````````````

The :ref:`setup` module that ships with Ansible provides many variables about a system that can be used in playbooks
and templates.  However, it's possible to also add your own facts without modifying the system module.  To do
this, just have the module return a `ansible_facts` key, like so, along with other return data:

.. code-block:: json

    {
        "changed" : true,
        "rc" : 5,
        "ansible_facts" : {
            "leptons" : 5000,
            "colors" : {
                "red"   : "FF0000",
                "white" : "FFFFFF"
            }
        }
    }

These 'facts' will be available to all statements called after that module (but not before) in the playbook.
A good idea might be to make a module called 'site_facts' and always call it at the top of each playbook, though
we're always open to improving the selection of core facts in Ansible as well.
 
Returning a new fact from a python module could be done like::

        module.exit_json(msg=message, ansible_facts=dict(leptons=5000, colors=my_colors))

.. _common_module_boilerplate:

Common Module Boilerplate
`````````````````````````

As mentioned, if you are writing a module in Python, there are some very powerful shortcuts you can use.
Modules are still transferred as one file, but an arguments file is no longer needed, so these are not
only shorter in terms of code, they are actually FASTER in terms of execution time.

Rather than mention these here, the best way to learn is to read some of the `source of the modules <https://github.com/ansible/ansible-modules-core>`_ that come with Ansible.

The 'group' and 'user' modules are reasonably non-trivial and showcase what this looks like.

Key parts include always importing the boilerplate code from
:mod:`ansible.module_utils.basic` like this:

.. code-block:: python

    from ansible.module_utils.basic import AnsibleModule
    if __name__ == '__main__':
        main()

.. note::
    Prior to Ansible-2.1.0, importing only what you used from
    :mod:`ansible.module_utils.basic` did not work.  You needed to use
    a wildcard import like this:

.. code-block:: python

        from ansible.module_utils.basic import *

And instantiating the module class like:

.. code-block:: python

    def main():
        module = AnsibleModule(
            argument_spec = dict(
                state     = dict(default='present', choices=['present', 'absent']),
                name      = dict(required=True),
                enabled   = dict(required=True, type='bool'),
                something = dict(aliases=['whatever'])
            )
        )

The :class:`AnsibleModule` provides lots of common code for handling returns, parses your arguments
for you, and allows you to check inputs.

Successful returns are made like this:

.. code-block:: python

    module.exit_json(changed=True, something_else=12345)

And failures are just as simple (where `msg` is a required parameter to explain the error):

.. code-block:: python

    module.fail_json(msg="Something fatal happened")

There are also other useful functions in the module class, such as :func:`module.sha1(path)`.  See
:file:`lib/ansible/module_utils/basic.py` in the source checkout for implementation details.

Again, modules developed this way are best tested with the :file:`hacking/test-module` script in the git
source checkout.  Because of the magic involved, this is really the only way the scripts
can function outside of Ansible.

If submitting a module to Ansible's core code, which we encourage, use of
:class:`AnsibleModule` is required.

.. _developing_for_check_mode:

Check Mode
``````````
.. versionadded:: 1.1

Modules may optionally support check mode. If the user runs Ansible in check
mode, the module should try to predict whether changes will occur.

For your module to support check mode, you must pass ``supports_check_mode=True``
when instantiating the AnsibleModule object. The AnsibleModule.check_mode attribute
will evaluate to True when check mode is enabled. For example:

.. code-block:: python

    module = AnsibleModule(
        argument_spec = dict(...),
        supports_check_mode=True
    )

    if module.check_mode:
        # Check if any changes would be made but don't actually make those changes
        module.exit_json(changed=check_if_system_state_would_be_changed())

Remember that, as module developer, you are responsible for ensuring that no
system state is altered when the user enables check mode.

If your module does not support check mode, when the user runs Ansible in check
mode, your module will simply be skipped.

.. _module_dev_pitfalls:

Common Pitfalls
```````````````

You should also NEVER do this in a module:

.. code-block:: python

    print "some status message"

Because the output is supposed to be valid JSON.

Modules must not output anything on standard error, because the system will merge
standard out with standard error and prevent the JSON from parsing. Capturing standard
error and returning it as a variable in the JSON on standard out is fine, and is, in fact,
how the command module is implemented.

If a module returns stderr or otherwise fails to produce valid JSON, the actual output
will still be shown in Ansible, but the command will not succeed.

Don't write to files directly; use a temporary file and then use the `atomic_move` function from `ansibile.module_utils.basic` to move the updated temporary file into place. This prevents data corruption and ensures that the correct context for the file is kept.

Avoid creating a module that does the work of other modules; this leads to code duplication and divergence, and makes things less uniform, unpredictable and harder to maintain. Modules should be the building blocks. Instead of creating a module that does the work of other modules, use Plays and Roles instead.  

Avoid creating 'caches'. Ansible is designed without a central server or authority, so you cannot guarantee it will not run with different permissions, options or locations. If you need a central authority, have it on top of Ansible (for example, using bastion/cm/ci server or tower); do not try to build it into modules.

Always use the hacking/test-module script when developing modules and it will warn
you about these kind of things.

.. _module_dev_conventions:

Conventions/Recommendations
```````````````````````````

As a reminder from the example code above, here are some basic conventions
and guidelines:

* If the module is addressing an object, the parameter for that object should be called 'name' whenever possible, or accept 'name' as an alias.

* If you have a company module that returns facts specific to your installations, a good name for this module is `site_facts`.

* Modules accepting boolean status should generally accept 'yes', 'no', 'true', 'false', or anything else a user may likely throw at them.  The AnsibleModule common code supports this with "type='bool'".

* Include a minimum of dependencies if possible.  If there are dependencies, document them at the top of the module file, and have the module raise JSON error messages when the import fails.

* Modules must be self-contained in one file to be auto-transferred by ansible.

* If packaging modules in an RPM, they only need to be installed on the control machine and should be dropped into /usr/share/ansible.  This is entirely optional and up to you.

* Modules must output valid JSON only. The toplevel return type must be a hash (dictionary) although they can be nested.  Lists or simple scalar values are not supported, though they can be trivially contained inside a dictionary.

* In the event of failure, a key of 'failed' should be included, along with a string explanation in 'msg'.  Modules that raise tracebacks (stacktraces) are generally considered 'poor' modules, though Ansible can deal with these returns and will automatically convert anything unparseable into a failed result.  If you are using the AnsibleModule common Python code, the 'failed' element will be included for you automatically when you call 'fail_json'.

* Return codes from modules are actually not significant, but continue on with 0=success and non-zero=failure for reasons of future proofing.

* As results from many hosts will be aggregated at once, modules should return only relevant output.  Returning the entire contents of a log file is generally bad form.

Building & Testing
++++++++++++++++++

Put your completed module file into the 'library' directory and then
run the command: ``make webdocs``. The new 'modules.html' file will be
built and appear in the 'docsite/' directory.

.. tip::

   If you're having a problem with the syntax of your YAML you can
   validate it on the `YAML Lint <http://www.yamllint.com/>`_ website.

.. tip::

    You can set the environment variable ANSIBLE_KEEP_REMOTE_FILES=1 on the controlling host to prevent ansible from
    deleting the remote files so you can debug your module.

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
executing.  Giving Ansible the ``-vvv`` optin makes Ansible more verbose.
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
  the module to change it's behaviour.  If you want to modify the parameters
  that are passed to the module, this is the file to do it in.

* The :file:`ansible` directory contains code from
  :mod:`ansible.module_utils` that is used by the module.  Ansible includes
  files for any :`module:`ansible.module_utils` imports in the module but not
  no files from any other module.  So if your module uses
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

.. _module_paths:

Module Paths
````````````

If you are having trouble getting your module "found" by ansible, be
sure it is in the :envvar:`ANSIBLE_LIBRARY` environment variable.

If you have a fork of one of the ansible module projects, do something like this::

    ANSIBLE_LIBRARY=~/ansible-modules-core:~/ansible-modules-extras

And this will make the items in your fork be loaded ahead of what ships with Ansible.  Just be sure
to make sure you're not reporting bugs on versions from your fork!

To be safe, if you're working on a variant on something in Ansible's normal distribution, it's not
a bad idea to give it a new name while you are working on it, to be sure you know you're pulling
your version.

.. _module_contribution:

Getting Your Module Into Ansible
````````````````````````````````

High-quality modules with minimal dependencies
can be included in Ansible, but modules (just due to the programming
preferences of the developers) will need to be implemented in Python and use
the AnsibleModule common code, and should generally use consistent arguments with the rest of
the program.   Stop by the mailing list to inquire about requirements if you like, and submit
a github pull request to the `extras <https://github.com/ansible/ansible-modules-extras>`_ project.
Included modules will ship with ansible, and also have a chance to be promoted to 'core' status, which
gives them slightly higher development priority (though they'll work in exactly the same way).


