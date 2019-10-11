
You can use the ``ansible-galaxy collection install`` command to install a collection on your system.

To install a collection hosted in Galaxy:

.. code-block:: bash

   ansible-galaxy collection install my_namespace.my_collection

You can also directly use the tarball from your build:

.. code-block:: bash

   ansible-galaxy collection install my_namespace-my_collection-1.0.0.tar.gz -p ./collections

.. note::
    The install command automatically appends the path ``ansible_collections`` to the one specified  with the ``-p`` option unless the
    parent directory is already in a folder called ``ansible_collections``.


When using the ``-p`` option to specify the install path, use one of the values configured in :ref:`COLLECTIONS_PATHS`, as this is
where Ansible itself will expect to find collections. If you don't specify a path, ``ansible-galaxy collection install`` installs
the collection to the first path defined in :ref:`COLLECTIONS_PATHS`, which by default is ``~/.ansible/collections``

You can also keep a collection adjacent to the current playbook, under a ``collections/ansible_collections/`` directory structure.

.. code-block:: text

    play.yml
    ├── collections/
    │   └── ansible_collections/
    │               └── my_namespace/
    │                   └── my_collection/<collection structure lives here>


See :ref:`collection_structure` for details on the collection directory structure.
