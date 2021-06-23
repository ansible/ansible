.. _developing_modules_general:
.. _module_dev_tutorial_sample:

*******************************************
Ansible module development: getting started
*******************************************

A module is a reusable, standalone script that Ansible runs on your behalf, either locally or remotely. Modules interact with your local machine, an API, or a remote system to perform specific tasks like changing a database password or spinning up a cloud instance. Each module can be used by the Ansible API, or by the :command:`ansible` or :command:`ansible-playbook` programs. A module provides a defined interface, accepts arguments, and returns information to Ansible by printing a JSON string to stdout before exiting.

If you need functionality that is not available in any of the thousands of Ansible modules found in collections, you can easily write your own custom module. When you write a module for local use, you can choose any programming language and follow your own rules. Use this topic to learn how to create an Ansible module in Python. After you create a module, you must add it locally to the appropriate directory so that Ansible can find and execute it. For details about adding a module locally, see :ref:`developing_locally`.

.. contents::
   :local:

.. _environment_setup:

Environment setup
=================

Prerequisites via apt (Ubuntu)
------------------------------

Due to dependencies (for example ansible -> paramiko -> pynacl -> libffi):

.. code:: bash

    sudo apt update
    sudo apt install build-essential libssl-dev libffi-dev python-dev

Common environment setup
------------------------------

1. Clone the Ansible repository:
   ``$ git clone https://github.com/ansible/ansible.git``
2. Change directory into the repository root dir: ``$ cd ansible``
3. Create a virtual environment: ``$ python3 -m venv venv`` (or for
   Python 2 ``$ virtualenv venv``. Note, this requires you to install
   the virtualenv package: ``$ pip install virtualenv``)
4. Activate the virtual environment: ``$ . venv/bin/activate``
5. Install development requirements:
   ``$ pip install -r requirements.txt``
6. Run the environment setup script for each new dev shell process:
   ``$ . hacking/env-setup``

.. note:: After the initial setup above, every time you are ready to start
   developing Ansible you should be able to just run the following from the
   root of the Ansible repo:
   ``$ . venv/bin/activate && . hacking/env-setup``


Creating an info or a facts module
==================================

Ansible gathers information about the target machines using facts modules, and gathers information on other objects or files using info modules.
If you find yourself trying to add ``state: info`` or ``state: list`` to an existing module, that is often a sign that a new dedicated ``_facts`` or ``_info`` module is needed.

In Ansible 2.8 and onwards, we have two type of information modules, they are ``*_info`` and ``*_facts``.

If a module is named ``<something>_facts``, it should be because its main purpose is returning ``ansible_facts``. Do not name modules that do not do this with ``_facts``.
Only use ``ansible_facts`` for information that is specific to the host machine, for example network interfaces and their configuration, which operating system and which programs are installed.

Modules that query/return general information (and not ``ansible_facts``) should be named ``_info``.
General information is non-host specific information, for example information on online/cloud services (you can access different accounts for the same online service from the same host), or information on VMs and containers accessible from the machine, or information on individual files or programs.

Info and facts modules, are just like any other Ansible Module, with a few minor requirements:

1. They MUST be named ``<something>_info`` or ``<something>_facts``, where <something> is singular.
2. Info ``*_info`` modules MUST return in the form of the :ref:`result dictionary<common_return_values>` so other modules can access them.
3. Fact ``*_facts`` modules MUST return in the ``ansible_facts`` field of the :ref:`result dictionary<common_return_values>` so other modules can access them.
4. They MUST support :ref:`check_mode <check_mode_dry>`.
5. They MUST NOT make any changes to the system.
6. They MUST document the :ref:`return fields<return_block>` and :ref:`examples<examples_block>`.

To create an info module:

1. Navigate to the correct directory for your new module: ``$ cd lib/ansible/modules/``. If you are developing module using collection, ``$ cd plugins/modules/`` inside your collection development tree.
2. Create your new module file: ``$ touch my_test_info.py``.
3. Paste the content below into your new info module file. It includes the :ref:`required Ansible format and documentation <developing_modules_documenting>`, a simple :ref:`argument spec for declaring the module options <argument_spec>`, and some example code.
4. Modify and extend the code to do what you want your new info module to do. See the :ref:`programming tips <developing_modules_best_practices>` and :ref:`Python 3 compatibility <developing_python_3>` pages for pointers on writing clean and concise module code.

.. literalinclude:: ../../../../examples/scripts/my_test_info.py
   :language: python

Use the same process to create a facts module.

.. literalinclude:: ../../../../examples/scripts/my_test_facts.py
   :language: python

Creating a module
=================

To create a new module:

1. Navigate to the correct directory for your new module: ``$ cd lib/ansible/modules/``. If you are developing a module in a :ref:`collection <developing_collections>`, ``$ cd plugins/modules/`` inside your collection development tree.
2. Create your new module file: ``$ touch my_test.py``.
3. Paste the content below into your new module file. It includes the :ref:`required Ansible format and documentation <developing_modules_documenting>`, a simple :ref:`argument spec for declaring the module options <argument_spec>`, and some example code.
4. Modify and extend the code to do what you want your new module to do. See the :ref:`programming tips <developing_modules_best_practices>` and :ref:`Python 3 compatibility <developing_python_3>` pages for pointers on writing clean and concise module code.

.. literalinclude:: ../../../../examples/scripts/my_test.py
   :language: python

Exercising your module code
===========================

After you modify the sample code above to do what you want, you can try out your module.
Our :ref:`debugging tips <debugging_modules>` will help if you run into bugs as you verify your module code.


Exercising module code locally
------------------------------

If your module does not need to target a remote host, you can quickly and easily exercise your code locally like this:

-  Create an arguments file, a basic JSON config file that passes parameters to your module so you can run it. Name the arguments file ``/tmp/args.json`` and add the following content:

.. code:: json

    {
        "ANSIBLE_MODULE_ARGS": {
            "name": "hello",
            "new": true
        }
    }

-  If you are using a virtual environment (highly recommended for
   development) activate it: ``$ . venv/bin/activate``
-  Setup the environment for development: ``$ . hacking/env-setup``
-  Run your test module locally and directly:
   ``$ python -m ansible.modules.my_test /tmp/args.json``

This should return output like this:

.. code:: json

    {"changed": true, "state": {"original_message": "hello", "new_message": "goodbye"}, "invocation": {"module_args": {"name": "hello", "new": true}}}


Exercising module code in a playbook
------------------------------------

The next step in testing your new module is to consume it with an Ansible playbook.

-  Create a playbook in any directory: ``$ touch testmod.yml``
-  Add the following to the new playbook file::

    - name: test my new module
      hosts: localhost
      tasks:
      - name: run the new module
        my_test:
          name: 'hello'
          new: true
        register: testout
      - name: dump test output
        debug:
          msg: '{{ testout }}'

- Run the playbook and analyze the output: ``$ ansible-playbook ./testmod.yml``

Testing basics
====================

These two examples will get you started with testing your module code. Please review our :ref:`testing <developing_testing>` section for more detailed
information, including instructions for :ref:`testing module documentation <testing_module_documentation>`, adding :ref:`integration tests <testing_integration>`, and more.

.. note::
  Every new module and plugin should have integration tests, even if the tests cannot be run on Ansible CI infrastructure.
  In this case, the tests should be marked with the ``unsupported`` alias in `aliases file <https://docs.ansible.com/ansible/latest/dev_guide/testing/sanity/integration-aliases.html>`_.

Performing sanity tests
-----------------------

You can run through Ansible's sanity checks in a container:

``$ ansible-test sanity -v --docker --python 2.7 MODULE_NAME``

.. note::
	Note that this example requires Docker to be installed and running. If you'd rather not use a container for this, you can choose to use ``--venv`` instead of ``--docker``.

Unit tests
----------

You can add unit tests for your module in ``./test/units/modules``. You must first setup your testing environment. In this example, we're using Python 3.5.

- Install the requirements (outside of your virtual environment): ``$ pip3 install -r ./test/lib/ansible_test/_data/requirements/units.txt``
- Run ``. hacking/env-setup``
- To run all tests do the following: ``$ ansible-test units --python 3.5``. If you are using a CI environment, these tests will run automatically.

.. note:: Ansible uses pytest for unit testing.

To run pytest against a single test module, you can do the following (provide the path to the test module appropriately):

``$ pytest -r a --cov=. --cov-report=html --fulltrace --color yes
test/units/modules/.../test/my_test.py``

Contributing back to Ansible
============================

If you would like to contribute to ``ansible-base`` by adding a new feature or fixing a bug, `create a fork <https://help.github.com/articles/fork-a-repo/>`_ of the ansible/ansible repository and develop against a new feature branch using the ``devel`` branch as a starting point. When you you have a good working code change, you can submit a pull request to the Ansible repository by selecting your feature branch as a source and the Ansible devel branch as a target.

If you want to contribute a module to an :ref:`Ansible collection <contributing_maintained_collections>`, review our :ref:`submission checklist <developing_modules_checklist>`, :ref:`programming tips <developing_modules_best_practices>`, and :ref:`strategy for maintaining Python 2 and Python 3 compatibility <developing_python_3>`, as well as information about :ref:`testing <developing_testing>` before you open a pull request.

The :ref:`Community Guide <ansible_community_guide>` covers how to open a pull request and what happens next.


Communication and development support
=====================================

Join the IRC channel ``#ansible-devel`` on `irc.libera.chat <https://libera.chat/>`_ for
discussions surrounding Ansible development.

For questions and discussions pertaining to using the Ansible product,
use the ``#ansible`` channel.

For more specific IRC channels look at :ref:`Community Guide, Communicating <communication_irc>`.

Credit
======

Thank you to Thomas Stringer (`@trstringer <https://github.com/trstringer>`_) for contributing source
material for this topic.
