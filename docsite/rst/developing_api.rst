Python API
==========

.. contents:: Topics

Please note that while we make this API available it is not intended for direct consumption, it is here
for the support of the Ansible command line tools. We try not to make breaking changes but we reserve the
right to do so at any time if it makes sense for the Ansible toolset.


The following documentation is provided for those that still want to use the API directly, but be mindful this is not something the Ansible team supports.

There are several interesting ways to use Ansible from an API perspective.   You can use
the Ansible python API to control nodes, you can extend Ansible to respond to various python events, you can
write various plugins, and you can plug in inventory data from external data sources.  This document
covers the execution and Playbook API at a basic level.

If you are looking to use Ansible programmatically from something other than Python, trigger events asynchronously, 
or have access control and logging demands, take a look at :doc:`tower` 
as it has a very nice REST API that provides all of these things at a higher level.

Ansible is written in its own API so you have a considerable amount of power across the board.  
This chapter discusses the Python API.

.. _python_api:

The Python API is very powerful, and is how the all the ansible CLI tools are implemented.
In version 2.0 the core ansible got rewritten and the API was mostly rewritten.

.. note:: Ansible relies on forking processes, as such the API is not thread safe.

.. _python_api_20:

Python API 2.0
--------------

In 2.0 things get a bit more complicated to start, but you end up with much more discrete and readable classes::


    #!/usr/bin/python2

    from collections import namedtuple
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars import VariableManager
    from ansible.inventory import Inventory
    from ansible.playbook.play import Play
    from ansible.executor.task_queue_manager import TaskQueueManager

    Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check'])
    # initialize needed objects
    variable_manager = VariableManager()
    loader = DataLoader()
    options = Options(connection='local', module_path='/path/to/mymodules', forks=100, become=None, become_method=None, become_user=None, check=False)
    passwords = dict(vault_pass='secret')

    # create inventory and pass to var manager
    inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list='localhost')
    variable_manager.set_inventory(inventory)

    # create play with tasks
    play_source =  dict(
            name = "Ansible Play",
            hosts = 'localhost',
            gather_facts = 'no',
            tasks = [
                dict(action=dict(module='shell', args='ls'), register='shell_out'),
                dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
             ]
        )
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    # actually run it
    tqm = None
    try:
        tqm = TaskQueueManager(
                  inventory=inventory,
                  variable_manager=variable_manager,
                  loader=loader,
                  options=options,
                  passwords=passwords,
                  stdout_callback='default',
              )
        result = tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()


.. _python_api_old:

Python API pre 2.0
------------------

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

.. _detailed_api_old_example:

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

Advanced programmers may also wish to read the source to ansible itself,
for it uses the API (with all available options) to implement the ``ansible``
command line tools (``lib/ansible/cli/``).

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

