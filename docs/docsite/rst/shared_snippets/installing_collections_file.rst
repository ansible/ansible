Ansible can also install from a source directory in several ways:

.. code-block:: yaml

    collections:
      # directory containing the collection
      - source: ./my_namespace/my_collection/
        type: dir

      # directory containing a namespace, with collections as subdirectories
      - source: ./my_namespace/
        type: subdirs

Ansible can also install a collection collected with ``ansible-galaxy collection build`` or downloaded from Galaxy for offline use by specifying the output file directly:

.. code-block:: yaml

    collections:
      - source: /tmp/my_namespace-my_collection-1.0.0.tar.gz
        type: file

.. note::

    Relative paths are calculated from the current working directory (where you are invoking ``ansible-galaxy install -r`` from). They are not taken relative to the ``requirements.yml`` file.