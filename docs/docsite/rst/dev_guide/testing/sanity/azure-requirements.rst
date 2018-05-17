Sanity Tests » azure-requirements
=================================

Update the Azure integration test requirements file when changes are made to the Azure packaging requirements file:

.. code-block:: bash

    cp packaging/requirements/requirements-azure.txt test/runner/requirements/integration.cloud.azure.txt

This copy of the requirements file is used when building the ``ansible/ansible:default`` Docker container from ``test/runner/Dockerfile``.
