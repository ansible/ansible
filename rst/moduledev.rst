Module Development Guide
========================

.. seealso::

   :doc:`modules`
       Learn about available modules
   `Github modules directory <https://github.com/ansible/ansible/tree/master/library>`_
       Browse source of core modules


Ansible modules are reusable units of magic that can be used by the Ansible API, 
or by the `ansible` or `ansible-playbook` programs.

Modules can be written in any language and are found in the path specified 
by `ANSIBLE_LIBRARY_PATH` or the `--module-path` command line option.
 
Tutorial 
````````

Let's build a module to get and set the system time.  For starters, let's build
a module that just outputs the current time.  

We are going to use Python here but any language is possible.  Only File I/O and outputing to standard
out are required.  So, bash, C++, clojure, Python, Ruby, whatever you want
is fine.

It's obvious that you would never really need to build a module to set the system time,
the 'command' module could already be used to do this.  However, it makes for a decent example.
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

Testing Modules
```````````````

There's a useful test script in the source checkout for ansible::

    git clone git@github.com:ansible/ansible.git
    chmod +x ansible/hacking/test-module

Let's run the script you just wrote with that::

    ansible/hacking/test-module ./time

You should see output that looks something like this::

    {u'time': u'2012-03-14 22:13:48.539183'}

If you did not, you might have a typo in your module, so recheck it and try again

Reading Input
`````````````

Let's modify the module to allow setting the current time.  We'll do this by seeing
if a key value pair in the form `time=<string>` is passed in to the module.

Ansible internally saves arguments to a arguments file.  So we must read the file
and parse it.  The arguments file is just a string, so any form of arguments are legal.
Here we'll do some basic parsing to treat the input as key=value.

The example usage we are trying to achieve to set the time is::

   time time="March 14 22:10"

If no time parameter is set, we'll just leave the time as is and return the current time.

.. note:
   This is obviously an unrealistic idea for a module.  You'd most likely just
   use the shell module.  However, it probably makes a decent tutorial.

Let's look at the code.  Read the comments as we'll explain as we go.  Note that this
highly verbose because it's intended as an educational example.  You can write modules 
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
        if arg.find("=") != -1:
 
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

    ../ansible/hacking/test-module ./rst/time time=\"March 14 12:23\"

This should return something like::

    {"changed": true, "time": "2012-03-14 12:23:00.000307"}


Common Pitfalls
```````````````

If writing a module in Python and you have managed nodes running
Python 2.4 or lower, this is generally a good idea, because
json isn't in the Python standard library until 2.5.::

    try:
        import json
    except ImportError:
        import simplejson as json

You should also never do this in a module::

    print "some status message"
    
Because the output is supposed to be valid JSON.  Except that's not quite true,
but we'll get to that later.

Conventions
-----------

As a reminder from the example code above, here are some basic conventions
and guidelines:

* Include a minimum of dependencies if possible.  If there are dependencies, document them at the top of the module file

* Modules must be self contained in one file to be auto-transferred by ansible

* If packaging modules in an RPM, they only need to be installed on the control machine and should be dropped into /usr/share/ansible.  This is entirely optional.

* Modules should return JSON or key=value results all on one line.  JSON is best if you can do JSON.  All return types must be hashes (dictionaries) although they can be nested.

* In the event of failure, a key of 'failed' should be included, along with a string explanation in 'msg'.  Modules that raise tracebacks (stacktraces) are generally considered 'poor' modules, though Ansible can deal with these returns and will automatically convert anything unparseable into a failed result.

* Return codes are actually not signficant, but continue on with 0=success and non-zero=failure for reasons of future proofing.

* As results from many hosts will be aggregrated at once, modules should return only relevant output.  Returning the entire contents of a log file is generally bad form.


Shorthand Vs JSON
-----------------

To make it easier to write modules in bash and in cases where a JSON
module might not be available, it is acceptable for a module to return
key=value output all on one line, like this.   The Ansible parser
will know what to do.::

    somekey=1 somevalue=two favcolor=red

If you're writing a module in Python or Ruby or whatever, though, returning
JSON is probably the simplest way to go.


Sharing Your Module
```````````````````

If you think your module is generally useful to others, Ansible is preparing
an 'ansible-contrib' repo.  Stop by the mailing list and we'll help you to
get your module included.  Contrib modules can be implemented in a variety
of languages.  Including a README with your module is a good idea so folks
can understand what arguments it takes and so on.  We would like to build
up as many of these as possible in as many languages as possible.

`Ansible Mailing List <http://groups.google.com/group/ansible-project>`_

Getting Your Module Into Core
`````````````````````````````

High-quality modules with minimal dependencies 
can be included in the core, but core modules (just due to the programming
preferences of the developers) will need to be implemented in Python.
Stop by the mailing list to inquire about requirements.


