Developer Labs
==============

.. contents:: Topics

Ansible has a lot of documentation and is increasingly building out development docs, but not everyone learns the same way. This page provides self-guided labs which are intended to teach new Ansible developers the ins and outs of writing code and working with the github PR process and shippable CI system. It is expected that the developer does a commit+push and waits for tests to run after each step in the process to learn how the behavior of shippable tests and ansibot. You are expected to see a lot of errors and failures through this process. Please use the docs, the sourcecode, the community and the Ansible core team (in that order) if you find yourself stuck at any point.

.. _level_1:
Level 1
-------

.. _module:

Module
++++++

Build a module and tests from scratch by starting with a broken python script.

.. _module_hello_world:

module from scratch
```````````````````

1. fork ansible
2. checkout the fork
3. create a feature branch named FILAMENT_MODULE
4. create a new module file lib/ansible/modules/system/filament.py
5. put "hello world" in filament.py
6. git add and commit the new file
7. push the commit to the feature branch
8. open the branch on github.com and send it as a pullrequest to ansible/ansible
9. fix all shippable test failures

.. _module_debugging:

module debugging
````````````````

1. set a variable named "foo" in the filament module
2. use the python-q library to have the filament module log the value of "foo"
3. set a breakpoint in the module with pdb/epdb
4. run the filament module with test-module
    * get to the breakpoint
    * use the "h" command
    * print "foo"
5. run the filament module with ansible adhoc
    * get to the breakpoint
    * print "foo"
6. run the module with ansible-playbook
    * get to the breakpoint
    * print "foo"
7. commit and push the module with the breakpoint added to see CI test failures.
8. remove the breakpoint and then commit and push again.


.. _module_integration_tests:

module integration tests
````````````````````````

1. Create, commit and push an empty file named test/integration/targets/filament/tasks/main.yml
2. Make sure the test is being run in shippable.
3. Observe the test failures and re-run the test locally with ansible-test.
4. Fill in main.yml with 2 tasks
    * call the filament module and register the result
    * assert that the result contains a key "foo" with a value of "bar"
5. Fix the module so that the test passes by running the test locally with ansible-test.
6. Commit and push your changes.

.. _module_unit_tests:

module unit tests
`````````````````

1. Add a new function to the module that adds two integeters.
2. Write a unit test to assert that the function returns the correct value for integers, floats, strings, booleans and NoneTypes.

.. _module_util:

Module Util
+++++++++++

1. echo "hello world" > lib/ansible/module_utils/filament_utils.py
2. make the filament module import the function "foobar" from filament_utils
3. fix any shippable errors

.. _action_plugin:

Action Plugin
+++++++++++++

1. make an action plugin that changes the filament module result from "bar" to "!bar".

.. _level_2:

Level 2
-------

.. _lookup_plugin:

Lookup Plugin
+++++++++++++

1. create a new feature branch on your fork
2. make a lookup that queries the process table and gets the pid for a process based on an input string
3. make a pullrequest from the branch
4. write a unit test for that lookup
5. write an integration test for the lookup

.. _callback_plugin:

Callback Plugin
+++++++++++++++

1. create a new feature branch on your fork
2. create a new empty file lib/ansible/plugins/callbacks/filament.py
3. create an ansible.cfg that enables and switches the default callback to "filament"
4. run a simple playbook
5. fix any errors until the ansible-playbook output is readable by referencing the code in existing callbacks

.. _level_3:

Level 3
-------

.. _connection_plugin:

Connection Plugin
+++++++++++++++++

1. create a new feature branch
2. create an empty file lib/ansible/plugins/connections/filament.py
3. create a playbook that uses the "filament" connection plugin to run the shell module with "whoami"
4. run the playbook
5. fix whatever errors you see by referencing the other connection plugins
