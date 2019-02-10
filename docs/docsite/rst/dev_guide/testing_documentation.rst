:orphan:

.. _testing_module_documentation:

****************************
Testing module documentation
****************************

Before you submit a module for inclusion in the main Ansible repo, you must test your module documentation for correct HTML rendering and to ensure that the argspec matches the documentation in your Python file. The community pages offer more information on :ref:`testing reStructuredText documentation <testing_documentation_locally>`.

To check the HTML output of your module documentation:

#. Ensure working development environment.
#. Ensure your module is in the correct directory.
#. Build HTML pages: ``make webdocs``
#. View the HTML page at ``file:///${ansibledevdir}/docs/docsite/_build/html/modules/${mymodule}_module.html``.

.. code-block:: bash

   # If you don't already, ensure you are using your local checkout, e.g. in ~/ansible.repo
   ansibledevdir=~/ansible.repo
   git clone git@github.com:ansible/ansible.git ${ansibledevdir}
   cd ${ansibledevdir}
   # install required Python packages (drop '--user' in venv/virtualenv)
   pip install --user -r requirements.txt
   pip install --user -r docs/docsite/requirements.txt

   mymodule=digital_ocean_droplet  # put YOUR module name here
   CATEGORY=cloud/digital_ocean    # put YOUR category here
   # develop $mymodule in ${ansibledevdir}/lib/ansible/modules/$CATEGORY/${mymodule}.py

   # For running ansible-test end development versions of ansible, ansible-playbook etc.
   # You may use your module with them too.
   source ${ansibledevdir}/hacking/env-setup

   # edit your module's DOCUMENTATION, EXAMPLES, RETURN values, then build HTML.
   cd ${ansibledevdir}
   MODULES=${mymodule} make webdocs

   # Open $docURI in your browser
   docURI=file:///${ansibledevdir}/docs/docsite/_build/html/modules/${mymodule}_module.html
   echo $docURI

To build the HTML documentation for multiple modules, use a comma-separated list of module names: ``MODULES=$mymodule,$mymodule2 make webdocs``.

To ensure that your documentation matches your ``argument_spec``, run the ``validate-modules`` test.

.. code-block:: bash

   cd ${ansibledevdir}
   pip install --user -r test/runner/requirements/sanity.txt
   ./test/sanity/validate-modules/validate-modules --arg-spec --warnings lib/ansible/modules/$CATEGORY/${mymodule}.py
