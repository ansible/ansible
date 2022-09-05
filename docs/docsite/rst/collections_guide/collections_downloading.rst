.. _collections_downloading:

Downloading collections
=======================

To download a collection and its dependencies for an offline install, run ``ansible-galaxy collection download``. This
downloads the collections specified and their dependencies to the specified folder and creates a ``requirements.yml``
file which can be used to install those collections on a host without access to a Galaxy server. All the collections
are downloaded by default to the ``./collections`` folder.

Just like the ``install`` command, the collections are sourced based on the
:ref:`configured galaxy server config <galaxy_server_config>`. Even if a collection to download was specified by a URL
or path to a tarball, the collection will be redownloaded from the configured Galaxy server.

Collections can be specified as one or multiple collections or with a ``requirements.yml`` file just like
``ansible-galaxy collection install``.

To download a single collection and its dependencies:

.. code-block:: bash

   ansible-galaxy collection download my_namespace.my_collection

To download a single collection at a specific version:

.. code-block:: bash

   ansible-galaxy collection download my_namespace.my_collection:1.0.0

To download multiple collections either specify multiple collections as command line arguments as shown above or use a
requirements file in the format documented with :ref:`collection_requirements_file`.

.. code-block:: bash

   ansible-galaxy collection download -r requirements.yml

You can also download a source collection directory. The collection is built with the mandatory ``galaxy.yml`` file.

.. code-block:: bash

   ansible-galaxy collection download /path/to/collection

   ansible-galaxy collection download git+file:///path/to/collection/.git

You can download multiple source collections from a single namespace by providing the path to the namespace.

.. code-block:: text

   ns/
   ├── collection1/
   │   ├── galaxy.yml
   │   └── plugins/
   └── collection2/
       ├── galaxy.yml
       └── plugins/

.. code-block:: bash

   ansible-galaxy collection install /path/to/ns

All the collections are downloaded by default to the ``./collections`` folder but you can use ``-p`` or
``--download-path`` to specify another path:

.. code-block:: bash

   ansible-galaxy collection download my_namespace.my_collection -p ~/offline-collections

Once you have downloaded the collections, the folder contains the collections specified, their dependencies, and a
``requirements.yml`` file. You can use this folder as is with ``ansible-galaxy collection install`` to install the
collections on a host without access to a Galaxy server.

.. code-block:: bash

   # This must be run from the folder that contains the offline collections and requirements.yml file downloaded
   # by the internet-connected host
   cd ~/offline-collections
   ansible-galaxy collection install -r requirements.yml