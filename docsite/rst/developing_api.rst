Python API
==========

.. contents:: Topics

There are several interesting ways to use Ansible from an API perspective.   You can use
the Ansible python API to control nodes, you can extend Ansible to respond to various python events, you can
write various plugins, and you can plug in inventory data from external data sources.  This document
covers the Runner and Playbook API at a basic level.

If you are looking to use Ansible programmatically from something other than Python, trigger events asynchronously, 
or have access control and logging demands, take a look at :doc:`tower` 
as it has a very nice REST API that provides all of these things at a higher level.

Ansible is written in its own API so you have a considerable amount of power across the board.  
This chapter discusses the Python API.

.. _python_api:

Python API
----------

The Python API is very powerful, and is how the ansible CLI and ansible-playbook
are implemented.

It's pretty simple::

    import ansible.runner

    runner = ansible.runner.Runner(
       module_name='ping',
       module_args='',
       pattern='web*',
       forks=10
    )
    datastructure = runner.run()

The run method returns results per host, grouped by whether they
could be contacted or not.  Return types are module specific, as
expressed in the :doc:`modules` documentation.::

    {
        "dark" : {
           "web1.example.com" : "failure message"
        },
        "contacted" : {
           "web2.example.com" : 1
        }
    }

A module can return any type of JSON data it wants, so Ansible can
be used as a framework to rapidly build powerful applications and scripts.

.. _detailed_api_example:

Detailed API Example
````````````````````

The following script prints out the uptime information for all hosts::

    #!/usr/bin/python

    import ansible.runner
    import sys

    # construct the ansible runner and execute on all hosts
    results = ansible.runner.Runner(
        pattern='*', forks=10,
        module_name='command', module_args='/usr/bin/uptime',
    ).run()

    if results is None:
       print "No hosts found"
       sys.exit(1)

    print "UP ***********"
    for (hostname, result) in results['contacted'].items():
        if not 'failed' in result:
            print "%s >>> %s" % (hostname, result['stdout'])

    print "FAILED *******"
    for (hostname, result) in results['contacted'].items():
        if 'failed' in result:
            print "%s >>> %s" % (hostname, result['msg'])

    print "DOWN *********"
    for (hostname, result) in results['dark'].items():
        print "%s >>> %s" % (hostname, result)

Advanced programmers may also wish to read the source to ansible itself, for
it uses the Runner() API (with all available options) to implement the
command line tools ``ansible`` and ``ansible-playbook``.

.. seealso::

   :doc:`developing_inventory`
       Developing dynamic inventory integrations
   :doc:`developing_modules`
       How to develop modules
   :doc:`developing_plugins`
       How to develop plugins
   `Development Mailing List <http://groups.google.com/group/ansible-devel>`_
       Mailing list for development topics
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

