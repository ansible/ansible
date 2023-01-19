import
======

Ansible allows unchecked imports of some libraries from specific directories, listed at the bottom of this section. Import all other Python libraries in a try/except ImportError block to support sanity tests such as ``validate-modules`` and to allow Ansible to give better error messages to the user. To import a library in a try/except ImportError block:

Handling import errors
----------------------

In modules
^^^^^^^^^^

Instead of using ``import another_library``:

.. code-block:: python

   import traceback

   from ansible.module_utils.basic import missing_required_lib

   try:
       import another_library
   except ImportError:
       HAS_ANOTHER_LIBRARY = False
       ANOTHER_LIBRARY_IMPORT_ERROR = traceback.format_exc()
   else:
       HAS_ANOTHER_LIBRARY = True

.. note::

   The ``missing_required_lib`` import above will be used below.

Then in the module code:

.. code-block:: python

   module = AnsibleModule(...)

   if not HAS_ANOTHER_LIBRARY:
       module.fail_json(
           msg=missing_required_lib('another_library'),
           exception=ANOTHER_LIBRARY_IMPORT_ERROR)

In plugins
^^^^^^^^^^

Instead of using ``import another_library``:

.. code-block:: python

   try:
       import another_library
   except ImportError as imp_exc:
       ANOTHER_LIBRARY_IMPORT_ERROR = imp_exc
   else:
       ANOTHER_LIBRARY_IMPORT_ERROR = None

Then in the plugin code, for example in ``__init__`` of the plugin:

.. code-block:: python

   if ANOTHER_LIBRARY_IMPORT_ERROR:
       raise AnsibleError('another_library must be installed to use this plugin') from ANOTHER_LIBRARY_IMPORT_ERROR

When used as base classes
^^^^^^^^^^^^^^^^^^^^^^^^^

.. important::

   This solution builds on the previous two examples.
   Make sure to pick the appropriate one before continuing with this solution.

Sometimes an import is used in a base class, for example:

.. code-block:: python

   from another_library import UsefulThing

   class CustomThing(UsefulThing):
       pass

One option is make the entire class definition conditional:

.. code-block:: python

   if not ANOTHER_LIBRARY_IMPORT_ERROR:
       class CustomThing(UsefulThing):
           pass

Another option is to define a substitute base class by modifying the exception handler:

.. code-block:: python

   try:
       from another_library import UsefulThing
   except ImportError:
       class UsefulThing:
           pass
       ...

.. note::

   If this is for module code running on Python 2.7 you'll want to use ``class UsefulThing(object):`` instead.

Allowed unchecked imports
-------------------------

Ansible allows the following unchecked imports from these specific directories:

* ansible-core:

  * For ``lib/ansible/modules/`` and ``lib/ansible/module_utils/``, unchecked imports are only allowed from the Python standard library;
  * For ``lib/ansible/plugins/``, unchecked imports are only allowed from the Python standard library, from public dependencies of ansible-core, and from ansible-core itself;

* collections:

  * For ``plugins/modules/`` and ``plugins/module_utils/``, unchecked imports are only allowed from the Python standard library;
  * For other directories in ``plugins/`` (see `the community collection requirements <https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst#modules-plugins>`_ for a list), unchecked imports are only allowed from the Python standard library, from public dependencies of ansible-core, and from ansible-core itself.

Public dependencies of ansible-core are:

  * Jinja2
  * PyYAML
  * MarkupSafe (as a dependency of Jinja2)
