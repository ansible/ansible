Developing Modules
==================

.. contents:: Topics

Ansible modules are reusable units of magic that can be used by the Ansible API,
or by the `ansible` or `ansible-playbook` programs.

See :doc:`modules` for a list of various ones developed in core.

Modules can be written in any language and are found in the path specified
by `ANSIBLE_LIBRARY` or the ``--module-path`` command line option.

Should you develop an interesting Ansible module, consider sending a pull request to the
`github project <http://github.com/ansible/ansible>`_ to see about getting your module
included in the core project.

.. _module_dev_tutorial:

Tutorial
````````

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
the 'command' module could already be used to do this.  Though we're going to make one.

Reading the modules that come with ansible (linked above) is a great way to learn how to write
modules.   Keep in mind, though, that some modules in ansible's source tree are internalisms,
so look at `service` or `yum`, and don't stare too close into things like `async_wrapper` or
you'll turn to stone.  Nobody ever executes async_wrapper directly.

Ok, let's get going with an example.  We'll use Python.  For starters, save this as a file named `time`::

    #!/usr/bin/python

    import datetime
    import json

    date = str(datetime.datetime.now())
    print json.dumps({
        "time" : date
    })

.. _module_testing:

Testing Modules
```````````````

There's a useful test script in the source checkout for ansible::

    git clone git@github.com:ansible/ansible.git
    source ansible/hacking/env-setup
    chmod +x ansible/hacking/test-module

Let's run the script you just wrote with that::

    ansible/hacking/test-module -m ./time

You should see output that looks something like this::

    {u'time': u'2012-03-14 22:13:48.539183'}

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
   use the shell module.  However, it probably makes a decent tutorial.

Let's look at the code.  Read the comments as we'll explain as we go.  Note that this
is highly verbose because it's intended as an educational example.  You can write modules
a lot shorter than this::

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

    # for this module, we're going to do key=value style arguments
    # this is up to each module to decide what it wants, but all
    # core modules besides 'command' and 'shell' take key=value
    # so this is highly recommended

    arguments = shlex.split(args_data)
    for arg in arguments:

        # ignore any arguments without an equals in it
        if "=" in arg:

            (key, value) = arg.split("=")

            # if setting the time, the key 'time'
            # will contain the value we want to set the time to

            if key == "time":

                # now we'll affect the change.  Many modules
                # will strive to be 'idempotent', meaning they
                # will only make changes when the desired state
                # expressed to the module does not match
                # the current state.  Look at 'service'
                # or 'yum' in the main git tree for an example
                # of how that might look.

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

    ansible/hacking/test-module -m ./time -a time=\"March 14 12:23\"

This should return something like::

    {"changed": true, "time": "2012-03-14 12:23:00.000307"}

.. _module_provided_facts:

Module Provided 'Facts'
```````````````````````

The 'setup' module that ships with Ansible provides many variables about a system that can be used in playbooks
and templates.  However, it's possible to also add your own facts without modifying the system module.  To do
this, just have the module return a `ansible_facts` key, like so, along with other return data::

    {
        "changed" : True,
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
A good idea might be make a module called 'site_facts' and always call it at the top of each playbook, though
we're always open to improving the selection of core facts in Ansible as well.

.. _common_module_boilerplate:

Common Module Boilerplate
`````````````````````````

As mentioned, if you are writing a module in Python, there are some very powerful shortcuts you can use.
Modules are still transferred as one file, but an arguments file is no longer needed, so these are not
only shorter in terms of code, they are actually FASTER in terms of execution time.

Rather than mention these here, the best way to learn is to read some of the `source of the modules <https://github.com/ansible/ansible/tree/devel/library>`_ that come with Ansible.

The 'group' and 'user' modules are reasonably non-trivial and showcase what this looks like.

Key parts include always ending the module file with::

    from ansible.module_utils.basic import *
    main()

And instantiating the module class like::

    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(default='present', choices=['present', 'absent']),
            name      = dict(required=True),
            enabled   = dict(required=True, choices=BOOLEANS),
            something = dict(aliases=['whatever'])
        )
    )

The AnsibleModule provides lots of common code for handling returns, parses your arguments
for you, and allows you to check inputs.

Successful returns are made like this::

    module.exit_json(changed=True, something_else=12345)

And failures are just as simple (where 'msg' is a required parameter to explain the error)::

    module.fail_json(msg="Something fatal happened")

There are also other useful functions in the module class, such as module.md5(path).  See
lib/ansible/module_common.py in the source checkout for implementation details.

Again, modules developed this way are best tested with the hacking/test-module script in the git
source checkout.  Because of the magic involved, this is really the only way the scripts
can function outside of Ansible.

If submitting a module to ansible's core code, which we encourage, use of the AnsibleModule
class is required.

.. _developing_for_check_mode:

Check Mode
``````````
.. versionadded:: 1.1

Modules may optionally support check mode. If the user runs Ansible in check
mode, the module should try to predict whether changes will occur.

For your module to support check mode, you must pass ``supports_check_mode=True``
when instantiating the AnsibleModule object. The AnsibleModule.check_mode attribute
will evaluate to True when check mode is enabled. For example::

    module = AnsibleModule(
        argument_spec = dict(...),
        supports_check_mode=True
    )

    if module.check_mode:
        # Check if any changes would be made by don't actually make those changes
        module.exit_json(changed=check_if_system_state_would_be_changed())

Remember that, as module developer, you are responsible for ensuring that no
system state is altered when the user enables check mode.

If your module does not support check mode, when the user runs Ansible in check
mode, your module will simply be skipped.

.. _module_dev_pitfalls:

Common Pitfalls
```````````````

You should also never do this in a module::

    print "some status message"

Because the output is supposed to be valid JSON.  Except that's not quite true,
but we'll get to that later.

Modules must not output anything on standard error, because the system will merge
standard out with standard error and prevent the JSON from parsing. Capturing standard
error and returning it as a variable in the JSON on standard out is fine, and is, in fact,
how the command module is implemented.

If a module returns stderr or otherwise fails to produce valid JSON, the actual output
will still be shown in Ansible, but the command will not succeed.

Always use the hacking/test-module script when developing modules and it will warn
you about these kind of things.

.. _module_dev_conventions:

Conventions/Recommendations
```````````````````````````

As a reminder from the example code above, here are some basic conventions
and guidelines:

* If the module is addressing an object, the parameter for that object should be called 'name' whenever possible, or accept 'name' as an alias.

* If you have a company module that returns facts specific to your installations, a good name for this module is `site_facts`.

* Modules accepting boolean status should generally accept 'yes', 'no', 'true', 'false', or anything else a user may likely throw at them.  The AnsibleModule common code supports this with "choices=BOOLEANS" and a module.boolean(value) casting function.

* Include a minimum of dependencies if possible.  If there are dependencies, document them at the top of the module file, and have the module raise JSON error messages when the import fails.

* Modules must be self-contained in one file to be auto-transferred by ansible.

* If packaging modules in an RPM, they only need to be installed on the control machine and should be dropped into /usr/share/ansible.  This is entirely optional and up to you.

* Modules should return JSON or key=value results all on one line.  JSON is best if you can do JSON.  All return types must be hashes (dictionaries) although they can be nested.  Lists or simple scalar values are not supported, though they can be trivially contained inside a dictionary.

* In the event of failure, a key of 'failed' should be included, along with a string explanation in 'msg'.  Modules that raise tracebacks (stacktraces) are generally considered 'poor' modules, though Ansible can deal with these returns and will automatically convert anything unparseable into a failed result.  If you are using the AnsibleModule common Python code, the 'failed' element will be included for you automatically when you call 'fail_json'.

* Return codes from modules are not actually not significant, but continue on with 0=success and non-zero=failure for reasons of future proofing.

* As results from many hosts will be aggregated at once, modules should return only relevant output.  Returning the entire contents of a log file is generally bad form.

.. _module_dev_shorthand:

Shorthand Vs JSON
`````````````````

To make it easier to write modules in bash and in cases where a JSON
module might not be available, it is acceptable for a module to return
key=value output all on one line, like this.   The Ansible parser
will know what to do::

    somekey=1 somevalue=2 rc=3 favcolor=red

If you're writing a module in Python or Ruby or whatever, though, returning
JSON is probably the simplest way to go.

.. _module_documenting:

Documenting Your Module
```````````````````````

All modules included in the CORE distribution must have a
``DOCUMENTATION`` string. This string MUST be a valid YAML document
which conforms to the schema defined below. You may find it easier to
start writing your ``DOCUMENTATION`` string in an editor with YAML
syntax highlighting before you include it in your Python file.

.. _module_doc_example:

Example
+++++++

See an example documentation string in the checkout under `examples/DOCUMENTATION.yml <https://github.com/ansible/ansible/blob/devel/examples/DOCUMENTATION.yml>`_.

Include it in your module file like this::

    #!/usr/bin/env python
    # Copyright header....

    DOCUMENTATION = '''
    ---
    module: modulename
    short_description: This is a sentence describing the module
    # ... snip ...
    '''

The ``description``, and ``notes`` fields 
support formatting with some special macros.  

These formatting functions are ``U()``, ``M()``, ``I()``, and ``C()``
for URL, module, italic, and constant-width respectively. It is suggested
to use ``C()`` for file and option names, and ``I()`` when referencing
parameters; module names should be specifies as ``M(module)``.

Examples (which typically contain colons, quotes, etc.) are difficult
to format with YAML, so these must be
written in plain text in an ``EXAMPLES`` string within the module
like this::

    EXAMPLES = '''
    - action: modulename opt1=arg1 opt2=arg2
    '''

The EXAMPLES section, just like the documentation section, is required in
all module pull requests for new modules.

.. _module_dev_testing:

Building & Testing
++++++++++++++++++

Put your completed module file into the 'library' directory and then
run the command: ``make webdocs``. The new 'modules.html' file will be
built and appear in the 'docsite/' directory.

.. tip::

   If you're having a problem with the syntax of your YAML you can
   validate it on the `YAML Lint <http://www.yamllint.com/>`_ website.

.. tip::

    You can use ANSIBLE_KEEP_REMOTE_FILES=1 to prevent ansible from
    deleting the remote files so you can debug your module.

.. _module_contribution:

Getting Your Module Into Core
`````````````````````````````

High-quality modules with minimal dependencies
can be included in the core, but core modules (just due to the programming
preferences of the developers) will need to be implemented in Python and use
the AnsibleModule common code, and should generally use consistent arguments with the rest of
the program.   Stop by the mailing list to inquire about requirements if you like, and submit
a github pull request to the main project.

.. seealso::

   :doc:`modules`
       Learn about available modules
   :doc:`developing_plugins`
       Learn about developing plugins
   :doc:`developing_api`
       Learn about the Python API for playbook and task execution
   `Github modules directory <https://github.com/ansible/ansible/tree/devel/library>`_
       Browse source of core modules
   `Mailing List <http://groups.google.com/group/ansible-devel>`_
       Development mailing list
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


