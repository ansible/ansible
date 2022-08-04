.. _documenting_collections:

***********************
Documenting collections
***********************

Documenting modules and plugins
===============================

Documenting modules is thoroughly documented in :ref:`module_documenting`. Plugins can be documented the same way as modules, that is with ``DOCUMENTATION``, ``EXAMPLES``, and ``RETURN`` blocks.

Documenting roles
=================

To document a role, you have to add a role argument spec by creating a file ``meta/argument_specs.yml`` in your role. See :ref:`role_argument_spec` for details. As an example, you can look at `the argument specs file <https://github.com/sensu/sensu-go-ansible/blob/master/roles/install/meta/argument_specs.yml>`_ of the :ref:`sensu.sensu_go.install role <ansible_collections.sensu.sensu_go.install_role>` on GitHub.

.. _build_collection_docsite:

Build a docsite with antsibull-docs
===================================

You can use `antsibull-docs <https://pypi.org/project/antsibull-docs>`_ to build a Sphinx-based docsite for your collection:

#. Create your collection and make sure you can use it with ansible-core by adding it to your :ref:`COLLECTIONS_PATHS`.
#. Create a directory ``dest`` and run ``antsibull-docs sphinx-init --use-current --dest-dir dest namespace.name``, where ``namespace.name`` is the name of your collection.
#. Go into ``dest`` and run ``pip install -r requirements.txt``. You might want to create a venv and activate it first to avoid installing this globally.
#. Then run ``./build.sh``.
#. Open ``build/html/index.html`` in a browser of your choice.

If you want to add additional documentation to your collection next to the plugin, module, and role documentation, see :ref:`collections_doc_dir`.
