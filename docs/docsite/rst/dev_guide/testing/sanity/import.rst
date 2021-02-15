import
======

All Python imports in the directories specified that are not from a limited set of possibilities listed below
must be imported in a try/except ImportError block as follows:

.. code-block:: python

    # Instead of 'import another_library', do:

    try:
        import another_library
    except ImportError:
        HAS_ANOTHER_LIBRARY = False
    else:
        HAS_ANOTHER_LIBRARY = True


    # Later in module code:

        if not HAS_ANOTHER_LIBRARY:
            # Needs: from ansible.module_utils.basic import missing_required_lib
            module.fail_json(msg=missing_required_lib('another_library'))

    # Later in plugin code:

        if not HAS_ANOTHER_LIBRARY:
            raise AnsibleError('another_library must be installed to use this plugin')

The following shows which unchecked imports are allowed from which directories:

* ansible-core:

  * For ``lib/ansible/modules/`` and ``lib/ansible/module_utils/``, unchecked imports are only allowed from the Python standard library;
  * For ``lib/ansible/plugins/``, unchecked imports are only allowed from the Python standard library, from dependencies of ansible-core, and from ansible-core itself;

* collections:

  * For ``plugins/modules/`` and ``plugins/module_utils/``, unchecked imports are only allowed from the Python standard library;
  * For other directories in ``plugins/`` (see `the community collection requirements <https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst#modules-plugins>`_ for a list), unchecked imports are only allowed from the Python standard library, from dependencies of ansible-core, and from ansible-core itself.
