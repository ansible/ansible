:orphan:

azure-requirements
==================

Update the Azure integration test requirements file when changes are made to the Azure packaging requirements file:

.. code-block:: bash

    cp packaging/requirements/requirements-azure.txt test/lib/ansible_test/_data/requirements/integration.cloud.azure.txt
