:orphan:

.. _testing_module_documentation:
.. _testing_plugin_documentation:

****************************
Testing plugin documentation
****************************

A quick test while developing is to use ``ansible-doc -t <plugin_type> <name>`` to see if it renders, you might need to add ``-M /path/to/module`` if the module is not somewhere Ansible expects to find it.

Before you submit a plugin for inclusion in Ansible, you must test your documentation for correct HTML rendering and for modules to ensure that the argspec matches the documentation in your Python file.
The community pages offer more information on :ref:`testing reStructuredText documentation <testing_documentation_locally>`.

For example, to check the HTML output of your module documentation for modules:

#. Ensure working :ref:`development environment <environment_setup>`.
#. Install required Python packages (drop '--user' in venv/virtualenv):

   .. code-block:: bash

      pip install --user -r requirements.txt
      pip install --user -r docs/docsite/requirements.txt

#. Ensure your module is in the correct directory: ``lib/ansible/modules/mymodule.py`` or in a configured path.
#. Build HTML from your module documentation: ``MODULES=mymodule make webdocs``.
#. To build the HTML documentation for multiple modules, use a comma-separated list of module names: ``MODULES=mymodule,mymodule2 make webdocs``.
#. View the HTML page at ``file:///path/to/docs/docsite/_build/html/modules/mymodule_module.html``.

To ensure that your module documentation matches your ``argument_spec``:

#. Install required Python packages (drop '--user' in venv/virtualenv):

   .. code-block:: bash

      pip install --user -r test/lib/ansible_test/_data/requirements/sanity.txt

#. run the ``validate-modules`` test:

   .. code-block:: bash

    ansible-test sanity --test validate-modules mymodule

For other plugin types the steps are similar, just adjusting names and paths to the specific type.
