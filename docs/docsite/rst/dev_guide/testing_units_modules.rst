****************************
Unit Testing Ansible Modules
****************************

.. contents:: Topics

Introduction
============

This document explains why how and when you should use unit tests for Ansible modules.
The document doesn't apply to other parts of Ansible for which the recommendations are
normally different.

What
----

In the test/unit directory Ansible has a set of unit tests which primarily cover the
internals but can also can cover Ansible modules.  There is basic documentation for unit
tests in the Ansible developer Guide
(https://docs.ansible.com/ansible/devel/dev_guide/testing_units.html) #

For most modules integration tests can be used instead, however there are situations where
cases cannot be verified using integration tests.  This means that Ansible unit test cases
may well extend beyond testing only minimal units and in some cases will include some
level of functional testing.


Why (and why not)?
------------------

Ansible unit tests have advantages and disadvantages. It is important to understand these:

* most unit tests are much faster than most Ansible integration tests.  
* unit tests can be run by developers who don't have access to system which the module
  (module dependencies aren't required with unit tests)

There are also plenty of potential disadvantages of unit tests.  Unit tests don't normally
test actual useful valuable features of software, instead just internal implementation

* unit tests which test the internal, non visible features of software may make
  refactoring difficult if those internal features have to change (see also naming in How
  below)
* even if the internal feature is working correctly it is possible that there will be a
  problem between the internal code and the actual result delivered to the user

Normally the Ansible integration tests, which are written in Ansible YAML are a better
option for most module tests.  If those tests already test a feature and run acceptably
quickly then there may be little point in providing a unit test as well.

When (and when not)?
--------------------

There are a number of situations where unit tests win out over integration tests For
example testing things which are impossible, slow or very difficult to test with
integration tests, such as:
    
* forcing rare / strange / random situations that can't be forced such as specific network
  failures an exceptions
* extensive testing of slow configuration APIs 

Example:
  A single step of the rds_instance test cases can take up to 20
  minutes (the time to create an RDS instance in Amazon).  The entire
  test run can be well over an hour.  All 16 of the unit tests
  complete execution in less than 2 seconds

The developer time saving of being able to run the code in a unit test makes it worth
creating a unit test to help resolve many of the problems identified in the module even if
those tests do not often identify problems later.  Probably every module should have at
least one unit test which will give quick feedback in easy cases without having to wait
for the integration tests to complete.
    
Providing simple external tests which check the module runs the calls that it makes to
external services in the right way.

Example:
  package managers are often far more efficient when installing multiple packages in one
  go rather than each package separately one after the other in the end the result is the
  same, the packages are all installed, so the efficiency is difficult to verify through
  integration tests by providing a mock package manager and verifying that it is called
  once, we can build a valuable test for module efficiency

Providing specific design tests; By building a requirement for a particular part of the
code and then coding to that requirement, unit tests _can_ sometimes improve the code and
help future developers working on that code to understand it. 

Unit tests which test internal implementation details of code, on the other hand, almost
always do more harm than good.  Testing that your packages to install are stored in a list
would slow down and confuse a later developer who needed to change that list into a
dictionary for efficiency.  This problem can be reduced somewhat with clear test naming so
that the future developer immediately knows to delete the test case, however it's probably
better to simply leave out the test case altogether and test for a real valuable feature
of the code such as installing all of the packages supplied as arguments to the module. 


How to unit test Ansible modules
================================

There are a number of techniques which let you unit test modules.  Beware that most
modules without unit tests are structured in a way that makes testing quite difficult and
lead to very complicated tests which need more work than the code.  Effectively using unit
tests may lead you to restructure your code a bit.  This is often a good thing and leads
to better code overall.  Good restructuring will make your code into clearer and more
easily understood functions, typically ones which can all be viewed on a screen.  Going
too far, to functions of only a line or two may end up being more confusing and bad.


Use of Mocks
------------

Mock objects (from https://docs.python.org/3/library/unittest.mock.html) can be very
useful in building unit tests for special / difficult cases.  On the other hand they can
lead to quite complex and confusing coding situations.  A good user for mocks can be in
simulating an API. As for 'six', 'mock' python package is bundled with Ansible: use
'import ansible.compat.tests.mock'. See for example

mocking of the actual module
----------------------------

Naming unit tests
-----------------

The name of a unit test is a very important feature.  The most important aim is that, if a
future developer working on the module being tested breaks the test case because they have
changed the internal design, it should be very easy and quick for them to understand from
the test name


API definition with unit test cases
-----------------------------------

Normally API interaction is best tested with function tests defined in Ansible's
integration testing section which run against the actual API.  There are a couple of cases
where the unit tests are likely to work better

a) defining a module against an API specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This case is especially important for modules interacting with web services which provide
an API which Ansible uses but which are beyond the control of the user.

By writing a custom emulation of the calls which return data from the API, we can ensure
that only the features which are clearly defined in the specification of the API are
present in the message.  This means that we can check that we use the right, guaranteed
parameters and nothing else.


*Example:  in rds_instance unit tests a simple instance state is defined*::


    def simple_instance_list(status, pending):
        return {u'DBInstances': [{u'DBInstanceArn': 'arn:aws:rds:us-east-1:1234567890:db:fakedb',
                                  u'DBInstanceStatus': status,
                                  u'PendingModifiedValues': pending,
                                  u'DBInstanceIdentifier': 'fakedb'}]}

which is then used to create a list of states::

    rds_client_double = MagicMock()
    rds_client_double.describe_db_instances.side_effect = [
        simple_instance_list('rebooting', {"a": "b", "c": "d"}),
        simple_instance_list('available', {"c": "d", "e": "f"}),
        simple_instance_list('rebooting', {"a": "b"}),
        simple_instance_list('rebooting', {"e": "f", "g": "h"}),
        simple_instance_list('rebooting', {}),
        simple_instance_list('available', {"g": "h", "i": "j"}),
        simple_instance_list('rebooting', {"i": "j", "k": "l"}),
        simple_instance_list('available', {}),
        simple_instance_list('available', {}),
    ]
    
which are then used returns from a mock object to ensure that the await function; By doing
this we check that the await function will keep waiting through various strange states
that it would be impossible to reliably trigger through the integration tests but which
can happen in reality.


b) defining a module to work against multiple API versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This case is especially important for modules interacting with many different versions of
software, for example package installation modules which might be expected to work over
many different operating system versions.

By using previously stored data from various versions of an API we can ensure that the
code is tested against the actual data which will be sent from that version of the system
even when the version is very obscure and unlikely to be available during testing

*** example ****


Ansible special cases for unit testing
======================================

There are a number of special cases for unit testing the environment of an Ansible module.
Some of them are documented below and suggestions for other ones can be found by looking
at the source code of the exiting unit tests or discussed on the Ansible IRC or mailing
lists.

doing module argument processing 
--------------------------------

There are two problems with running the main function of a module.  Firstly, it's a bit
difficult to set up the arguments correctly so that the module will get them as parameters
and secondly all modules finish by calling either the ``module.fail_json`` or
``module.exit_json``, but these won't work correctly in a testing environment.

The first problem, passing in arguments, is solved with a function which stores the
parameters in a special string variable.  Module creation and argument processing is
handled through the AnsibleModule object in the basic section of the utilities.  Normally
this accepts input on ``STDIN`` which is not convenient for unit testing when the special
variable is set it will be treated as if the input came on ``STDIN`` to the module.::

    import json
    from ansible.module_utils._text import to_bytes

    def set_module_args(args):
        args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
        basic._ANSIBLE_ARGS = to_bytes(args)

    simply call that function before setting up your module

        def test_already_registered(self):
            set_module_args({
                'activationkey': 'key',
                'username': 'user',
                'password': 'pass',
            })

handling exit correctly
-----------------------


The other problem: module.exit_json won't work properly in a testing environment, it can
be solved by replacing it (and module.fail_json) with a function which raises an
exception::

    def exit_json(*args, **kwargs):
        if 'changed' not in kwargs:
            kwargs['changed'] = False
        raise AnsibleExitJson(kwargs)

now you can ensure that the first function called is the one you expected simply by
expecting the correct exception::

    def test_returned_value(self):
        set_module_args({
            'activationkey': 'key',
            'username': 'user',
            'password': 'pass',
        })
       with self.assertRaises(AnsibleExitJson) as result:
           my_module.main()

the same technique works for module.fail_json() used for failures or the
aws_module.fail_json_aws() used in modules for Amazon Web Services.

running the main function
-------------------------

If you do want to run the actual main function of a module you must import the module, set
the arguments as above, set up the appropriate exit exception and then run the module::

    def test_main_function(self):
        set_module_args({
            'activationkey': 'key',
            'username': 'user',
            'password': 'pass',
        })
        my_module.main()


handling calls to external executables
--------------------------------------

Module must use AnsibleModule.run_command in order to execute an external command: this
method needs to be mocked:

Here is a simple mock of AnsibleModule.run_command::

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.return_value = 0, '', ''  # successful execution, no output
                with self.assertRaises(AnsibleExitJson) as result:
                    self.module.main()
                self.assertFalse(result.exception.args[0]['changed'])  # assert module returns changed=True
        # Check that run_command has been called
        run_command.assert_called_once_with('/usr/bin/command args')
        self.assertEqual(run_command.call_count, 1)
        self.assertFalse(run_command.called)

Examples taken from test/units/modules/packaging/os/test_rhn_register.py and
test/units/modules/packaging/os/rhn_utils.py

a complete case techniques in context
-------------------------------------

The example below is a complete skeleton reusing mocks explained above and adding a new
mock for Ansible.get_bin_path::
    
    import json

    from ansible.compat.tests import unittest
    from ansible.compat.tests.mock import patch
    from ansible.module_utils import basic
    from ansible.module_utils._text import to_bytes
    from ansible.modules.namespace import my_module


    def set_module_args(args):
        """prepare arguments so that they will be picked up during module creation"""
        args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
        basic._ANSIBLE_ARGS = to_bytes(args)


    class AnsibleExitJson(Exception):
        """Exception class to be raised by module.exit_json and caught by the test case"""
        pass


    class AnsibleFailJson(Exception):
        """Exception class to be raised by module.fail_json and caught by the test case"""
        pass


    def exit_json(*args, **kwargs):
        """function to patch over exit_json; package return data into an exception"""
        if 'changed' not in kwargs:
            kwargs['changed'] = False
        raise AnsibleExitJson(kwargs)


    def fail_json(*args, **kwargs):
        """function to patch over fail_json; package return data into an exception"""
        kwargs['failed'] = True
        raise AnsibleFailJson(kwargs)


    def get_bin_path(self, arg, required=False):
        """Mock AnsibleModule.get_bin_path"""
        if arg.endswith('my_command'):
            return '/usr/bin/my_command'
        else:
            if required:
                fail_json(msg='%r not found !' % arg)


    class TestMyModule(unittest.TestCase):

        def setUp(self):
            self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                     exit_json=exit_json,
                                                     fail_json=fail_json,
                                                     get_bin_path=get_bin_path)
            self.mock_module_helper.start()
            self.addCleanup(self.mock_module_helper.stop)

        def test_module_fail_when_required_args_missing(self):
            with self.assertRaises(AnsibleFailJson):
                set_module_args({})
                self.module.main()


        def test_ensure_command_called(self):
            set_module_args({
                'param1': 10,
                'param2': 'test',
            })

            with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
                stdout = 'configuration updated'
                stderr = ''
                rc = 0
                mock_run_command.return_value = rc, stdout, stderr  # successful execution

                with self.assertRaises(AnsibleExitJson) as result:
                    my_module.main()
                self.assertFalse(result.exception.args[0]['changed']) # ensure result is changed

            mock_run_command.assert_called_once_with('/usr/bin/my_command --value 10 --name test')


restructuring modules to make module set up and other processes easily tested
-----------------------------------------------------------------------------

Often modules have a main() function which both sets up the module and then does other
actions.  This can make it difficult to check argument processing .  Simply moving module
configuration and initialisation into a separate function means that it's easy to run
tests against that.  Move::

    argument_spec = dict(
        # module function variables
        state=dict(choices=['absent', 'present', 'rebooted', 'restarted'], default='present'),
        apply_immediately=dict(type='bool', default=False),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=600),
        allocated_storage=dict(type='int', aliases=['size']),
        db_instance_identifier=dict(aliases=["id"], required=True),
    )

    def setup_module_object():
        module = AnsibleAWSModule(
            argument_spec=argument_spec,
            required_if=required_if,
            mutually_exclusive=[['old_instance_id', 'source_db_instance_identifier',
                                 'db_snapshot_identifier']],
        )
        return module

    def main():
        module = setup_module_object()
        validate_parameters(module)
        conn = setup_client(module)
        return_dict = run_task(module, conn)
        module.exit_json(**return_dict)

this now makes it possible to make tests against the module initiation function::

    def test_rds_module_setup_fails_if_db_instance_identifier_parameter_missing():
        # db_instance_identifier parameter is missing
        set_module_args({
            'state': 'absent',
            'apply_immediately': 'True',
         })

        with self.assertRaises(AnsibleFailJson) as result:
             self.module.setup_json

note that the argument_spec dictionary is visible in a module variable.  This has
advantages, both in allowing explicit testing of the arguments and in allowing the easy
creation of module objects for testing.

see also ``test/units/module_utils/aws/test_rds.py``

ensuring failure cases are visible with mock objects
----------------------------------------------------

functions like::

   module.fail_json() 

are normally expected to terminate execution.  When you run with a mock module object this
doesn't happen since the mock always just returns another mock from a function call.  You
can set up the mock to raise an exception as shown above, but if you don't do that then,
in order to avoid tests seeming to pass when they should actually have failed, simply
assert that these functions have not been called in each test which should not fail::

  module = MagicMock()
  function_to_test(module, argument)
  module.fail_json.assert_not_called() 

please note that this applies not only when calling the main module but almost any other
function in a module which get the module object.  

Traps for maintaining Python 2 compatibility
============================================

As often there are a number of traps of differences between python 2 and 3.  One of the
important ones is that if you use the ``mock`` library from the standard library from
python 2.6 then a number of the assert functions are missing and *will return as if
successful*.  This means that test cases should *not* use functions marked as new in the
python 3 documentation or else the test are likely to pass when they should not have.

A helpful development approach to this should be to ensure that all of the tests have been
run under 2.6 and each assertion in the test cases has been checked to work by breaking
the code in ansible to trigger that failure.

.. seealso::

   :doc:`testing_units`
       Ansible unit tests documentation
   :doc:`developing_modules`
       How to develop modules
   `Python 3 documentation - 26.4. unittest — Unit testing framework <https://docs.python.org/3/library/unittest.html>`_
       The documentation of the unittest framework in python 3 
   `Python 2 documentation - 25.3. unittest — Unit testing framework <https://docs.python.org/3/library/unittest.html>`_
       The documentation of the earliest supported unittest framework - from Python 2.6
   `pytest: helps you write better programs <https://docs.pytest.org/en/latest/>`_
       The documentation of pytest - the framework actually used to run Ansible unit tests
   `Development Mailing List <http://groups.google.com/group/ansible-devel>`_
       Mailing list for development topics
    `Testing Your Code (from The Hitchhiker’s Guide to Python!) <http://docs.python-guide.org/en/latest/writing/tests/>`_
       General advice on testing Python code
    `Uncle Bob's many videos on YouTube <https://www.youtube.com/watch?v=QedpQjxBPMA&list=PLlu0CT-JnSasQzGrGzddSczJQQU7295D2>`_
        Unit testing is a part of the of various philosophies of software development, including
        Extreme Programming (XP), Clean Coding.  Uncle Bob talks through how to benfit from this
   `"Why Most Unit Testing is Waste" http://rbcs-us.com/documents/Why-Most-Unit-Testing-is-Waste.pdf`
       An article warning against the costs of unit testing
   `'A Response to "Why Most Unit Testing is Waste"' https://henrikwarne.com/2014/09/04/a-response-to-why-most-unit-testing-is-waste/` 
       An response pointing to how to maintain the value of unit tests
