.. _playbooks_tests:

Tests
-----

.. contents:: Topics


`Tests <http://jinja.pocoo.org/docs/dev/templates/#tests>`_ in Jinja are a way of evaluating template expressions and returning True or False.
Jinja ships with many of these. See `builtin tests`_ in the official Jinja template documentation.

The main difference between tests and filters are that Jinja tests are used for comparisons, whereas filters are used for data manipulation, and have different applications in jinja. Tests can also be used in list processing filters, like ``map()`` and ``select()`` to choose items in the list.

Like all templating, tests always execute on the Ansible controller, **not** on the target of a task, as they test local data.

In addition to those Jinja2 tests, Ansible supplies a few more and users can easily create their own.

.. _test_syntax:

Test syntax
```````````

`Test syntax <http://jinja.pocoo.org/docs/dev/templates/#tests>`_ varies from `filter syntax <http://jinja.pocoo.org/docs/dev/templates/#filters>`_ (``variable | filter``). Historically Ansible has registered tests as both jinja tests and jinja filters, allowing for them to be referenced using filter syntax.

As of Ansible 2.5, using a jinja test as a filter will generate a warning.

The syntax for using a jinja test is as follows::

    variable is test_name

Such as::

    result is failed

.. _testing_strings:

Testing strings
```````````````

To match strings against a substring or a regular expression, use the "match", "search" or "regex" filters::

    vars:
      url: "http://example.com/users/foo/resources/bar"

    tasks:
        - debug:
            msg: "matched pattern 1"
          when: url is match("http://example.com/users/.*/resources/.*")

        - debug:
            msg: "matched pattern 2"
          when: url is search("/users/.*/resources/.*")

        - debug:
            msg: "matched pattern 3"
          when: url is search("/users/")

        - debug:
            msg: "matched pattern 4"
          when: url is regex("example.com/\w+/foo")

'match' requires zero or more characters at the beginning of the string, while 'search' only requires matching a subset of the string. By default, 'regex' works like `search`, but `regex` can be configured to perform other tests as well.

.. _testing_versions:

Version Comparison
``````````````````

.. versionadded:: 1.6

.. note:: In 2.5 ``version_compare`` was renamed to ``version``

To compare a version number, such as checking if the ``ansible_facts['distribution_version']``
version is greater than or equal to '12.04', you can use the ``version`` test.

The ``version`` test can also be used to evaluate the ``ansible_facts['distribution_version']``::

    {{ ansible_facts['distribution_version'] is version('12.04', '>=') }}

If ``ansible_facts['distribution_version']`` is greater than or equal to 12.04, this test returns True, otherwise False.

The ``version`` test accepts the following operators::

    <, lt, <=, le, >, gt, >=, ge, ==, =, eq, !=, <>, ne

This test also accepts a 3rd parameter, ``strict`` which defines if strict version parsing as defined by ``distutils.version.StrictVersion`` should be used.  The default is ``False`` (using ``distutils.version.LooseVersion``), ``True`` enables strict version parsing::

    {{ sample_version_var is version('1.0', operator='lt', strict=True) }}


.. _math_tests:

Set theory tests
````````````````

.. versionadded:: 2.1

.. note:: In 2.5 ``issubset`` and ``issuperset`` were renamed to ``subset`` and ``superset``

To see if a list includes or is included by another list, you can use 'subset' and 'superset'::

    vars:
        a: [1,2,3,4,5]
        b: [2,3]
    tasks:
        - debug:
            msg: "A includes B"
          when: a is superset(b)

        - debug:
            msg: "B is included in A"
          when: b is subset(a)

.. _contains_test:

Test if a list contains a value
```````````````````````````````

.. versionadded:: 2.8

Ansible includes a ``contains`` test which operates similarly, but in reverse of the Jinja2 provided ``in`` test.
The ``contains`` test is designed to work with the ``select``, ``reject``, ``selectattr``, and ``rejectattr`` filters::

    vars:
      lacp_groups:
        - master: lacp0
          network: 10.65.100.0/24
          gateway: 10.65.100.1
          dns4:
            - 10.65.100.10
            - 10.65.100.11
          interfaces:
            - em1
            - em2

        - master: lacp1
          network: 10.65.120.0/24
          gateway: 10.65.120.1
          dns4:
            - 10.65.100.10
            - 10.65.100.11
          interfaces:
              - em3
              - em4

    tasks:
      - debug:
          msg: "{{ (lacp_groups|selectattr('interfaces', 'contains', 'em1')|first).master }}"

.. _path_tests:

.. versionadded:: 2.4

You can use `any` and `all` to check if any or all elements in a list are true or not::

  vars:
    mylist:
        - 1
        - "{{ 3 == 3 }}"
        - True
    myotherlist:
        - False
        - True
  tasks:

    - debug:
        msg: "all are true!"
      when: mylist is all

    - debug:
        msg: "at least one is true"
      when: myotherlist is any


Testing paths
`````````````

.. note:: In 2.5 the following tests were renamed to remove the ``is_`` prefix

The following tests can provide information about a path on the controller::

    - debug:
        msg: "path is a directory"
      when: mypath is directory

    - debug:
        msg: "path is a file"
      when: mypath is file

    - debug:
        msg: "path is a symlink"
      when: mypath is link

    - debug:
        msg: "path already exists"
      when: mypath is exists

    - debug:
        msg: "path is {{ (mypath is abs)|ternary('absolute','relative')}}"

    - debug:
        msg: "path is the same file as path2"
      when: mypath is same_file(path2)

    - debug:
        msg: "path is a mount"
      when: mypath is mount


.. _test_task_results:

Task results
````````````

The following tasks are illustrative of the tests meant to check the status of tasks::

    tasks:

      - shell: /usr/bin/foo
        register: result
        ignore_errors: True

      - debug:
          msg: "it failed"
        when: result is failed

      # in most cases you'll want a handler, but if you want to do something right now, this is nice
      - debug:
          msg: "it changed"
        when: result is changed

      - debug:
          msg: "it succeeded in Ansible >= 2.1"
        when: result is succeeded

      - debug:
          msg: "it succeeded"
        when: result is success

      - debug:
          msg: "it was skipped"
        when: result is skipped

.. note:: From 2.1, you can also use success, failure, change, and skip so that the grammar matches, for those who need to be strict about it.



.. _builtin tests: http://jinja.pocoo.org/docs/templates/#builtin-tests

.. seealso::

   :ref:`playbooks_intro`
       An introduction to playbooks
   :ref:`playbooks_conditionals`
       Conditional statements in playbooks
   :ref:`playbooks_variables`
       All about variables
   :ref:`playbooks_loops`
       Looping in playbooks
   :ref:`playbooks_reuse_roles`
       Playbook organization by roles
   :ref:`playbooks_best_practices`
       Best practices in playbooks
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel
