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

