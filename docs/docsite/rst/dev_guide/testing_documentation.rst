:orphan:

.. _testing_module_documentation:

****************************
Testing module documentation
****************************

Before you submit a module for inclusion in the main Ansible repo, you must test your module documentation for correct HTML rendering and to ensure that the argspec matches the documentation in your Python file. The community pages offer more information on :ref:`testing reStructuredText documentation <testing_documentation_locally>`.

To check the HTML output of your module documentation:

#. Save your completed module file into the correct directory: ``lib/ansible/modules/$CATEGORY/my_code.py``.
#. Move to the docsite directory: ``cd /path/to/ansible/docs/docsite/``.
#. Run the command to build the docs for your module: ``MODULES=my_code make webdocs``.
#. View the HTML page at ``file:///path/to/ansible/docs/docsite/_build/html/my_code_module.html``.

To build the HTML documentation for multiple modules, use a comma-separated list of module names: ``MODULES=my_code,my_other_code make webdocs``.

To ensure that your documentation matches your ``argument_spec``, run the ``validate-modules`` test.

.. code-block:: bash

   # If you don't already, ensure you are using your local checkout
   source hacking/env-setup
   ./test/sanity/validate-modules/validate-modules --arg-spec --warnings  lib/ansible/modules/$CATEGORY/my_code.py
