.. _developing_api:

Python API
==========

.. note:: This document is out of date: 'ansible.parsing.dataloader' and 'ansible.runner' are not available in the current version of Ansible.

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
or have access control and logging demands, take a look at :doc:`../tower` 
as it has a very nice REST API that provides all of these things at a higher level.

Ansible is written in its own API so you have a considerable amount of power across the board.  
This chapter discusses the Python API.

.. note:: Ansible relies on forking processes, as such the API is not thread safe.

.. _python_api_example:

Python API example
------------------

This example is by no means comphrehensive and is not meant to show you how to use all of Ansible's feautres,
it is just a simple demonstration on how to minmally run a couple of tasks.::

    #!/usr/bin/env python

    import json
    import shutil
    from collections import namedtuple
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible.playbook.play import Play
    from ansible.executor.task_queue_manager import TaskQueueManager
    from ansible.plugins.callback import CallbackBase
    import ansible.constants as C

    class ResultCallback(CallbackBase):
        """A sample callback plugin used for performing an action as results come in

        If you want to collect all results into a single object for processing at
        the end of the execution, look into utilizing the ``json`` callback plugin
        or writing your own custom callback plugin
        """
        def v2_runner_on_ok(self, result, **kwargs):
            """Print a json representation of the result

            This method could store the result in an instance attribute for retrieval later
            """
            host = result._host
            print(json.dumps({host.name: result._result}, indent=4))

    # since API is constructed for CLI it expects certain options to always be set, named tuple 'fakes' the args parsing options object
    Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check', 'diff'])
    options = Options(connection='local', module_path=['/to/mymodules'], forks=10, become=None, become_method=None, become_user=None, check=False, diff=False)

    # initialize needed objects
    loader = DataLoader() # Takes care of finding and reading yaml, json and ini files
    passwords = dict(vault_pass='secret')

    # Instantiate our ResultCallback for handling results as they come in, Ansible expects this to be one of it's main display outlets
    results_callback = ResultCallback()

    # create inventory, use path to host config file as source or hosts in a comma separated string
    inventory = InventoryManager(loader=loader, sources='localhost,')

    # variable manager takes care of merging all the different sources to give you a unifed view of variables available in each context
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    # create datastructure that represents our play, including tasks, this is basically what our YAML loader does internally.
    play_source =  dict(
            name = "Ansible Play",
            hosts = 'localhost',
            gather_facts = 'no',
            tasks = [
                dict(action=dict(module='shell', args='ls'), register='shell_out'),
                dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
             ]
        )

    # Create play object, playbook objects use .load instead of init or new methods,
    # this will also automatically create the task objects from the info provided in play_source
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    # actually run it, instantiate task queue manager, which takes care of forking and setting up all objects to iterate over host list and tasks
    tqm = None
    try:
        tqm = TaskQueueManager(
                  inventory=inventory,
                  variable_manager=variable_manager,
                  loader=loader,
                  options=options,
                  passwords=passwords,
                  stdout_callback=results_callback,  # Use our custom callback instead of the ``default`` callback plugin, which prints to stdout
              )
        result = tqm.run(play) # most interesting data for a play is actually sent to the callback's methods
    finally:
        # we always need to cleanup child procs, and the strucutres we use to communicate with them
        if tqm is not None:
            tqm.cleanup()
        
         # Remove ansible tmpdir
         shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)


.. note:: Ansible emits warnings and errors via the display object, which prints directly to stdout, stderr and the Ansible log.

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

