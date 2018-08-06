*********************
Testing documentation
*********************

Before you submit a module for inclusion in the main Ansible repo, you must test your documentation.

First, you must make sure your module documentation renders correctly as HTML. Save your completed module file into the ``lib/ansible/modules/$CATEGORY/`` directory, move to the docsite directory (``cd /path/to/ansible/docs/docsite/``) and run the command: ``make webdocs``. The documentation for your new module will be built as ``docs/docsite/_build/html/$MODULENAME_module.html``.

To speed up the build process, you can limit the documentation build with the ``MODULES`` environment variable, which accepts a comma-separated list of module names:

``MODULES=my_first_module,my_second_module make webdocs``

Second, you must ensure that your documentation matches your ``argument_spec``. The ``validate-modules`` test does this. Note that this option isn't currently enabled in Shippable due to the time it takes to run.

.. code-block:: bash

   # If you don't already, ensure you are using your local checkout
   source hacking/env-setup
   ./test/sanity/validate-modules/validate-modules --arg-spec --warnings  lib/ansible/modules/your/modules/

