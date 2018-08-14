.. _testing_documentation:

*********************
Testing documentation
*********************

Before you submit a module for inclusion in the main Ansible repo, you must test your documentation for correct HTML rendering and to ensure that the argspec matches the documentation.

To check the HTML output of your module documentation:

* save your completed module file into the ``lib/ansible/modules/$CATEGORY/`` directory
* move to the docsite directory: ``cd /path/to/ansible/docs/docsite/``
* run the command to build the docs for your module: ``MODULES=my_module make webdocs``
* view the HTML page at ``file:///path/to/ansible/docs/docsite/_build/html/$MODULENAME_module.html``

To build the HTML documentation for multiple modules, use a comma-separated list of module names: ``MODULES=my_first_module,my_second_module make webdocs``.

To ensure that your documentation matches your ``argument_spec``, run the ``validate-modules`` test. Note that this option isn't currently enabled in Shippable due to the time it takes to run.

.. code-block:: bash

   # If you don't already, ensure you are using your local checkout
   source hacking/env-setup
   ./test/sanity/validate-modules/validate-modules --arg-spec --warnings  lib/ansible/modules/your/modules/

