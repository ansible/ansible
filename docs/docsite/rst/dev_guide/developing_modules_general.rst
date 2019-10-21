.. _developing_modules_general:
.. _module_dev_tutorial_sample:

*******************************************
Ansible module development: getting started
*******************************************

A module is a reusable, standalone script that Ansible runs on your behalf, either locally or remotely. Modules interact with your local machine, an API, or a remote system to perform specific tasks like changing a database password or spinning up a cloud instance. Each module can be used by the Ansible API, or by the :command:`ansible` or :command:`ansible-playbook` programs. A module provides a defined interface, accepting arguments and returning information to Ansible by printing a JSON string to stdout before exiting. Ansible ships with thousands of modules, and you can easily write your own. If you're writing a module for local use, you can choose any programming language and follow your own rules. This tutorial illustrates how to get started developing an Ansible module in Python.

.. contents:: Topics
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


Starting a new module
=====================

To create a new module:

1. Navigate to the correct directory for your new module: ``$ cd lib/ansible/modules/cloud/azure/``
2. Create your new module file: ``$ touch my_test.py``
3. Paste the content below into your new module file. It includes the :ref:`required Ansible format and documentation <developing_modules_documenting>` and some example code.
4. Modify and extend the code to do what you want your new module to do. See the :ref:`programming tips <developing_modules_best_practices>` and :ref:`Python 3 compatibility <developing_python_3>` pages for pointers on writing clean, concise module code.

.. code-block:: python

    #!/usr/bin/python

    # Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
    # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

    ANSIBLE_METADATA = {
        'metadata_version': '1.1',
        'status': ['preview'],
        'supported_by': 'community'
    }

    DOCUMENTATION = '''
    ---
    module: my_test

    short_description: This is my test module

    version_added: "2.4"

    description:
        - "This is my longer description explaining my test module"

    options:
        name:
            description:
                - This is the message to send to the test module
            required: true
        new:
            description:
                - Control to demo if the result of this module is changed or not
            required: false

    extends_documentation_fragment:
        - azure

    author:
        - Your Name (@yourhandle)
    '''

    EXAMPLES = '''
    # Pass in a message
    - name: Test with a message
      my_test:
        name: hello world

    # pass in a message and have changed true
    - name: Test with a message and changed output
      my_test:
        name: hello world
        new: true

    # fail the module
    - name: Test failure of the module
      my_test:
        name: fail me
    '''

    RETURN = '''
    original_message:
        description: The original name param that was passed in
        type: str
        returned: always
    message:
        description: The output message that the test module generates
        type: str
        returned: always
    '''

    from ansible.module_utils.basic import AnsibleModule

    def run_module():
        # define available arguments/parameters a user can pass to the module
        module_args = dict(
            name=dict(type='str', required=True),
            new=dict(type='bool', required=False, default=False)
        )

        # seed the result dict in the object
        # we primarily care about changed and state
        # change is if this module effectively modified the target
        # state will include any data that you want your module to pass back
        # for consumption, for example, in a subsequent task
        result = dict(
            changed=False,
            original_message='',
            message=''
        )

        # the AnsibleModule object will be our abstraction working with Ansible
        # this includes instantiation, a couple of common attr would be the
        # args/params passed to the execution, as well as if the module
        # supports check mode
        module = AnsibleModule(
            argument_spec=module_args,
            supports_check_mode=True
        )

        # if the user is working with this module in only check mode we do not
        # want to make any changes to the environment, just return the current
        # state with no modifications
        if module.check_mode:
            module.exit_json(**result)

        # manipulate or modify the state as needed (this is going to be the
        # part where your module will do what it needs to do)
        result['original_message'] = module.params['name']
        result['message'] = 'goodbye'

        # use whatever logic you need to determine whether or not this module
        # made any modifications to your target
        if module.params['new']:
            result['changed'] = True

        # during the execution of the module, if there is an exception or a
        # conditional state that effectively causes a failure, run
        # AnsibleModule.fail_json() to pass in the message and the result
        if module.params['name'] == 'fail me':
            module.fail_json(msg='You requested this to fail', **result)

        # in the event of a successful module execution, you will want to
        # simple AnsibleModule.exit_json(), passing the key/value results
        module.exit_json(**result)

    def main():
        run_module()

    if __name__ == '__main__':
        main()


Exercising your module code
===========================

Once you've modified the sample code above to do what you want, you can try out your module.
Our :ref:`debugging tips <debugging>` will help if you run into bugs as you exercise your module code.

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
   ``$ python -m ansible.modules.cloud.azure.my_test /tmp/args.json``

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

Sanity tests
------------

You can run through Ansible's sanity checks in a container:

``$ ansible-test sanity -v --docker --python 2.7 MODULE_NAME``

Note that this example requires Docker to be installed and running. If you'd rather not use a
container for this, you can choose to use ``--tox`` instead of ``--docker``.

Unit tests
----------

You can add unit tests for your module in ``./test/units/modules``. You must first setup your testing environment. In this example, we're using Python 3.5.

- Install the requirements (outside of your virtual environment): ``$ pip3 install -r ./test/lib/ansible_test/_data/requirements/units.txt``
- To run all tests do the following: ``$ ansible-test units --python 3.5`` (you must run ``. hacking/env-setup`` prior to this)

.. note:: Ansible uses pytest for unit testing.

To run pytest against a single test module, you can do the following (provide the path to the test module appropriately):

``$ pytest -r a --cov=. --cov-report=html --fulltrace --color yes
test/units/modules/.../test/my_test.py``

Contributing back to Ansible
============================

If you would like to contribute to the main Ansible repository
by adding a new feature or fixing a bug, `create a fork <https://help.github.com/articles/fork-a-repo/>`_
of the Ansible repository and develop against a new feature
branch using the ``devel`` branch as a starting point.
When you you have a good working code change, you can
submit a pull request to the Ansible repository by selecting
your feature branch as a source and the Ansible devel branch as
a target.

If you want to contribute your module back to the upstream Ansible repo,
review our :ref:`submission checklist <developing_modules_checklist>`, :ref:`programming tips <developing_modules_best_practices>`,
and :ref:`strategy for maintaining Python 2 and Python 3 compatibility <developing_python_3>`, as well as
information about :ref:`testing <developing_testing>` before you open a pull request.
The :ref:`Community Guide <ansible_community_guide>` covers how to open a pull request and what happens next.


Communication and development support
=====================================

Join the IRC channel ``#ansible-devel`` on freenode for discussions
surrounding Ansible development.

For questions and discussions pertaining to using the Ansible product,
use the ``#ansible`` channel.

Credit
======

Thank you to Thomas Stringer (`@trstringer <https://github.com/trstringer>`_) for contributing source
material for this topic.
