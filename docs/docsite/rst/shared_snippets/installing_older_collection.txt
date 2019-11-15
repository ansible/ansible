
By default ``ansible-galaxy`` installs the latest collection that is available but you can add a version range
identifier to install a specific version.

To install the 1.0.0 version of the collection:

.. code-block:: bash

   ansible-galaxy collection install my_namespace.my_collection:1.0.0

To install the 1.0.0-beta.1 version of the collection:

.. code-block:: bash

   ansible-galaxy collection install my_namespace.my_collection:==1.0.0-beta.1

To install the collections that are greater than or equal to 1.0.0 or less than 2.0.0:

.. code-block:: bash

   ansible-galaxy collection install my_namespace.my_collection:>=1.0.0,<2.0.0


You can specify multiple range identifiers which are split by ``,``. You can use the following range identifiers:

* ``*``: Any version, this is the default used when no range specified is set.
* ``!=``: Version is not equal to the one specified.
* ``==``: Version must be the one specified.
* ``>=``: Version is greater than or equal to the one specified.
* ``>``: Version is greater than the one specified.
* ``<=``: Version is less than or equal to the one specified.
* ``<``: Version is less than the one specified.

.. note::
    The ``ansible-galaxy`` command ignores any pre-release versions unless the ``==`` range identifier is used to
    explicitly set to that pre-release version.
