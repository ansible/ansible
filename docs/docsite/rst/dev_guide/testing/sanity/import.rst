import
======

All Python imports in the directories specified that are not from a limited set of possibilities listed below
must be imported in a try/except ImportError block as follows:

1. In modules:

   .. code-block:: python

       # Instead of 'import another_library', do:

       import traceback

       try:
           import another_library
       except ImportError:
           HAS_ANOTHER_LIBRARY = False
           ANOTHER_LIBRARY_IMPORT_ERROR = traceback.format_exc()
       else:
           HAS_ANOTHER_LIBRARY = True


       # Later in module code:

       module = AnsibleModule(...)

       if not HAS_ANOTHER_LIBRARY:
           # Needs: from ansible.module_utils.basic import missing_required_lib
           module.fail_json(
               msg=missing_required_lib('another_library'),
               exception=ANOTHER_LIBRARY_IMPORT_ERROR)

2. In plugins:

   .. code-block:: python

       # Instead of 'import another_library', do:

       from ansible.module_utils.six import raise_from

       try:
           import another_library
       except ImportError as imp_exc:
           ANOTHER_LIBRARY_IMPORT_ERROR = imp_exc
       else:
           ANOTHER_LIBRARY_IMPORT_ERROR = None


       # Later in plugin code:

       if ANOTHER_LIBRARY_IMPORT_ERROR:
           raise_from(
               AnsibleError('another_library must be installed to use this plugin'),
               ANOTHER_LIBRARY_IMPORT_ERROR)
           # If you target only newer Python 3 versions, you can also use the
           # 'raise ... from ...' syntax.

The following shows which unchecked imports are allowed from which directories:

* ansible-core:

  * For ``lib/ansible/modules/`` and ``lib/ansible/module_utils/``, unchecked imports are only allowed from the Python standard library;
  * For ``lib/ansible/plugins/``, unchecked imports are only allowed from the Python standard library, from dependencies of ansible-core, and from ansible-core itself;

* collections:

  * For ``plugins/modules/`` and ``plugins/module_utils/``, unchecked imports are only allowed from the Python standard library;
  * For other directories in ``plugins/`` (see `the community collection requirements <https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst#modules-plugins>`_ for a list), unchecked imports are only allowed from the Python standard library, from dependencies of ansible-core, and from ansible-core itself.
