:orphan:

.. _testing_module_documentation:

****************************
Testing module documentation
****************************

Before you submit a module for inclusion in the main Ansible repo, you must test your module documentation for correct HTML rendering and to ensure that the argspec matches the documentation in your Python file. The community pages offer more information on :ref:`testing reStructuredText documentation <testing_documentation_locally>`.

To check the HTML output of your module documentation:

#. Ensure working :ref:`development environment <environment_setup>`.
#. Install required Python packages (drop '--user' in venv/virtualenv):

   .. code-block:: bash

      pip install --user -r requirements.txt
      pip install --user -r docs/docsite/requirements.txt

#. Ensure your module is in the correct directory: ``lib/ansible/modules/$CATEGORY/mymodule.py``.
#. Build HTML from your module documentation: ``MODULES=mymodule make webdocs``.
#. To build the HTML documentation for multiple modules, use a comma-separated list of module names: ``MODULES=mymodule,mymodule2 make webdocs``.
#. View the HTML page at ``file:///path/to/docs/docsite/_build/html/modules/mymodule_module.html``.

To ensure that your module documentation matches your ``argument_spec``:

#. Install required Python packages (drop '--user' in venv/virtualenv):

   .. code-block:: bash

      pip install --user -r test/lib/ansible_test/_data/requirements/sanity.txt

#. run the ``validate-modules`` test::

    ansible-test sanity --test validate-modules mymodule
