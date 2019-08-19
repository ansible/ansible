:orphan:

no-wildcard-import
==================

Using :code:`import *` is a bad habit which pollutes your namespace, hinders
debugging, and interferes with static analysis of code.  For those reasons, we
do want to limit the use of :code:`import *` in the ansible code.  Change our
code to import the specific names that you need instead.

Examples of unfixed code:

.. code-block:: python

    from ansible.module_utils.six import *
    if isinstance(variable, string_types):
        do_something(variable)

    from ansible.module_utils.basic import *
    module = AnsibleModule()

Examples of fixed code:

.. code-block:: python

    from ansible.module_utils import six
    if isinstance(variable, six.string_types):
        do_something(variable)

    from ansible.module_utils.basic import AnsibleModule
    module = AnsibleModule()
