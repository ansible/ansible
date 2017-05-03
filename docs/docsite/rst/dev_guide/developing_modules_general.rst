==========================
Developing Ansible Modules
==========================

.. contents:: Topics

.. _module_dev_tutorial_sample:

Building A Simple Module
------------------------

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
        "time" : date
    })

.. _module_testing:

Testing Your Module
-------------------

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
-------------

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

Module Provided 'Facts
----------------------

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
-------------------------

FIXME Add in a minimal module example, then have linkable subsections for each section. Use highlight line to mark the sections


As mentioned, if you are writing a module in Python, there are some very powerful shortcuts you can use.
Modules are still transferred as one file, but an arguments file is no longer needed, so these are not
only shorter in terms of code, they are actually FASTER in terms of execution time.

Rather than mention these here, the best way to learn is to read some of the `source of the modules <https://github.com/ansible/ansible/tree/devel/lib/ansible/modules>`_ that come with Ansible.

The 'group' and 'user' modules are reasonably non-trivial and showcase what this looks like.

Key parts include always importing the boilerplate code from
:mod:`ansible.module_utils.basic` like this:

FIXME This sample is wrong

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


main() and AnsibleModule & argument_spec
++++++++++++++++++++++++++++++++++++++++


# FIXME Flesh out example showing all options

# FIXME Add a module & integration test that defends all of this (I think modules can go relative to the roles dir)

.. code-block:: python

    def main():
        module = AnsibleModule(
            argument_spec=dict(
                state=dict(default='present', choices=['present', 'absent']),
                username=dict(type='str'),
                password=dict(no_log=True),
                token=dict(no_log=True),
                src=dict(type='path'),
                priority=dict(type='int'),
            ),
            mutually_exclusive=(['password', 'token'],),
            required_together=(['username', 'password'],),
            required_one_of=[['password', 'token']],
            required_if=[('state', 'present', ['src', 'priority'])],
            supports_check_mode=True
        )

The ``AnsibleModule`` class takes the following:

All arguments are optional unless otherwise specified.

:argument_spec:
  A dictionary of options in the following form:

  :name: `required`
    The (primary) name of the option. A ``dict`` defines the following parameters:

    :required:
      Is this option `always` required?
      Only needed if True, as the default is False.
      If the option is only required sometimes see the conditional options such as ``mutually_exclusive``, ``required_together``, etc.
    :default:
     FIXME
    :fallback:
      If a value isn't specified in the playbook gives the ability to read from another source.
      Currently supports ``env_fallback``. In this case the environment variable of where Ansible is run is used.
    :type:
      Optionally validate the format of the data.
      If you wish to add extra validation rules, see ``module_utils/basic.py``.
      The following types are built into Ansible.

        :str:
        :list:
        :dict:
        :bool:
          This option should accept the common terms for truth, such as "yes", "on", 1, True, etc.
          If you find yourself trying to create an option that access bool & other values then that's an indication that the design needs revisiting.
          Do not specify ``choices`` when using bool.
        :int:
        :float:
        :path:
          Ensure option is a path where the playbook is executed.
        :raw:
        :jsonarg:
          FIXME details of when this would be useful
        :json:
        :bytes: # example (human_to_bytes)
          # FIXME test and check return type
        :bits: # example (human_to_bytes)
          # FIXME test and check return type
    :choices:
      A list of possible allowed values for this option.
      Must not be set when using ``type='bool'``.
    :aliases:
      A list of aliases that this option name can be referred to in playbooks.
    :no_log:
      Boolean to state if this option may contain sensitive data, such as passwords, or authentication tokens.
    :removed_in_version:
      FIXME






Things to document (same style RST field table?)
* fallback env
* reimoved_in_version


* suboptions

* Link to how to document your module
* Shared arguments (cloud, network)
* add_file_common_args


* mutually_exclusive
* required_together
* required_one_of
* required_if
* supports_check_mode
* Naming of common options (verify_ssl)



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

Supporting Check Mode
---------------------

.. versionadded:: 1.1

Modules may optionally support `check mode <http://docs.ansible.com/ansible/playbooks_checkmode.html>`. If the user runs Ansible in check mode, a module should try to predict and report whether changes will occur but not actually make any changes (modules that do not support check mode will also take no action, but just will not report what changes they might have made).

For your module to support check mode, you must pass ``supports_check_mode=True`` when instantiating the AnsibleModule object. The AnsibleModule.check_mode attribute will evaluate to True when check mode is enabled. For example:

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



