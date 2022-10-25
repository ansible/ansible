.. _collection_updating_integration_tests:

Adding to an existing integration test
=======================================

The test tasks are stored in the ``tests/integration/targets/<target_name>/tasks`` directory.

The ``main.yml`` file holds test tasks and includes other test files.
Look for a suitable test file to integrate your tests or create and include/import a separate test file.
You can use one of the existing test files as a draft.

When fixing a bug
-----------------

When fixing a bug:

1. :ref:`Determine if integration tests for the module exist<collection_integration_prepare>`. If they do not, see :ref:`collection_creating_integration_tests` section.
2. Add a task that reproduces the bug to an appropriate file within the ``tests/integration/targets/<target_name>/tasks`` directory.
3. :ref:`Run the tests<collection_run_integration_tests>`. The newly added task should fail.
4. If they do not fail, re-check if your environment/test task satisfies the conditions described in the ``Steps to Reproduce`` section of the issue.
5. If you reproduce the bug and tests fail, change the code.
6. :ref:`Run the tests<collection_run_integration_tests>` again.
7. If they fail, repeat steps 5-6 until the tests pass.

Here is an example.

Let's say someone reported an issue in the ``community.postgresql`` collection that when users pass a name containing underscores to the ``postgresql_user`` module, the module fails.

We cloned the collection repository to the ``~/ansible_collections/community/postgresql`` directory and :ref:`prepared our environment <collection_prepare_environment>`. From the collection's root directory, we run ``ansible-test integration --list-targets`` and it shows a target called ``postgresql_user``. It means that we already have tests for the module.

We start with reproducing the bug.

First, we look into the ``tests/integration/targets/postgresql_user/tasks/main.yml`` file. In this particular case, the file imports other files from the ``tasks`` directory.  The ``postgresql_user_general.yml`` looks like an appropriate one to add our tests.

.. code-block:: yaml

  # General tests:
  - import_tasks: postgresql_user_general.yml
    when: postgres_version_resp.stdout is version('9.4', '>=')

We will add the following code to the file.

.. code-block:: yaml

  # https://github.com/ansible-collections/community.postgresql/issues/NUM
  - name: Test user name containing underscore
    community.postgresql.postgresql_user:
      name: underscored_user
    register: result

  - name: Check the module returns what we expect
    assert:
      that:
        - result is changed

  - name: Query the database if the user exists
    community.postgresql.postgresql_query:
      query: SELECT * FROM pg_authid WHERE rolename = 'underscored_user'
    register: result

  - name: Check the database returns one row
    assert:
      that:
        - result.query_result.rowcount == 1

When we :ref:`run the tests<collection_run_integration_tests>` with ``postgresql_user`` as a test target, this task must fail.

Now that we have our failing test; we will fix the bug and run the same tests again. Once the tests pass, we will consider the bug fixed and will submit a pull request.

When adding a new feature
-------------------------

.. note::

  The process described in this section also applies when you want to add integration tests to a feature that already exists, but is missing integration tests.

If you have not already implemented the new feature, you can start by writing the integration tests for it. They will not work as the code does not yet exist, but they can help you improve your implementation design before you start writing any code.

When adding new features, the process of adding tests consists of the following steps:

1. :ref:`Determine if integration tests for the module exist<collection_integration_prepare>`. If they do not, see :ref:`collection_creating_integration_tests`.
2. Find an appropriate file for your tests within the ``tests/integration/targets/<target_name>/tasks`` directory.
3. Cover your feature with tests. Refer to the :ref:`Recommendations on coverage<collection_integration_recommendations>` section for details.
4. :ref:`Run the tests<collection_run_integration_tests>`.
5. If they fail, see the test output for details. Fix your code or tests and run the tests again.
6. Repeat steps 4-5 until the tests pass.

Here is an example.

Let's say we decided to add a new option called ``add_attribute`` to the ``postgresql_user`` module of the ``community.postgresql`` collection.

The option is boolean. If set to ``yes``, it adds an additional attribute to a database user.

We cloned the collection repository to the ``~/ansible_collections/community/postgresql`` directory and :ref:`prepared our environment<collection_integration_prepare>`. From the collection's root directory, we run ``ansible-test integration --list-targets`` and it shows a target called ``postgresql_user``. Therefore, we already have some tests for the module.

First, we look at the ``tests/integration/targets/<target_name>/tasks/main.yml`` file. In this particular case, the file imports other files from the ``tasks`` directory. The ``postgresql_user_general.yml`` file looks like an appropriate one to add our tests.

.. code-block:: yaml

  # General tests:
  - import_tasks: postgresql_user_general.yml
    when: postgres_version_resp.stdout is version('9.4', '>=')

We will add the following code to the file.

.. code-block:: yaml

  # https://github.com/ansible-collections/community.postgresql/issues/NUM
  # We should also run the same tasks with check_mode: yes. We omit it here for simplicity.
  - name: Test for new_option, create new user WITHOUT the attribute
    community.postgresql.postgresql_user:
      name: test_user      
    register: result

  - name: Check the module returns what we expect
    assert:
      that:
        - result is changed

  - name: Query the database if the user exists but does not have the attribute (it is NULL)
    community.postgresql.postgresql_query:
      query: SELECT * FROM pg_authid WHERE rolename = 'test_user' AND attribute = NULL
    register: result

  - name: Check the database returns one row
    assert:
      that:
        - result.query_result.rowcount == 1

  - name: Test for new_option, create new user WITH the attribute
    community.postgresql.postgresql_user:
      name: test_user
    register: result

  - name: Check the module returns what we expect
    assert:
      that:
        - result is changed

  - name: Query the database if the user has the attribute (it is TRUE)
    community.postgresql.postgresql_query:
      query: SELECT * FROM pg_authid WHERE rolename = 'test_user' AND attribute = 't'
    register: result

  - name: Check the database returns one row
    assert:
      that:
        - result.query_result.rowcount == 1

Then we :ref:`run the tests<collection_run_integration_tests>` with ``postgresql_user`` passed as a test target.

In reality, we would alternate the tasks above with the same tasks run with the ``check_mode: yes`` option to be sure our option works as expected in check-mode as well. See :ref:`Recommendations on coverage<collection_integration_recommendations>` for details.

If we expect a task to fail, we use the ``ignore_errors: true`` option and check that the task actually failed and returned the message we expect:

.. code-block:: yaml

  - name: Test for fail_when_true option
    community.postgresql.postgresql_user:
      name: test_user
      fail_when_true: true
    register: result
    ignore_errors: true

  - name: Check the module fails and returns message we expect
    assert:
      that:
        - result is failed
        - result.msg == 'The message we expect'
