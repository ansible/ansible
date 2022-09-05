.. _collections_installing:

Installing collections
======================

.. note::

  If you install a collection manually as described in this paragraph, the collection will not be upgraded automatically when you upgrade the ``ansible`` package or ``ansible-core``.

Installing collections with ``ansible-galaxy``
----------------------------------------------

.. include:: ../shared_snippets/installing_collections.txt

.. _installing_signed_collections:

Installing collections with signature verification
---------------------------------------------------

If a collection has been signed by a :term:`distribution server`, the server will provide ASCII armored, detached signatures to verify the authenticity of the ``MANIFEST.json`` before using it to verify the collection's contents. This option is not available on all distribution servers. See :ref:`distributing_collections` for a table listing which servers support collection signing.

To use signature verification for signed collections:

1. :ref:`Configured a GnuPG keyring <galaxy_gpg_keyring>` for ``ansible-galaxy``, or provide the path to the keyring with the ``--keyring`` option when you install the signed collection.
   

2. Import the public key from the distribution server into that keyring.
   
   .. code-block:: bash

     gpg --import --no-default-keyring --keyring ~/.ansible/pubring.kbx my-public-key.asc


3. Verify the signature when you install the collection.
   
   .. code-block:: bash

     ansible-galaxy collection install my_namespace.my_collection --keyring ~/.ansible/pubring.kbx

   The ``--keyring`` option is not necessary if you have :ref:`configured a GnuPG keyring <galaxy_gpg_keyring>`. 

4. Optionally, verify the signature at any point after installation to prove the collection has not been tampered with. See :ref:`verify_signed_collections` for details.


You can also include signatures in addition to those provided by the distribution server. Use the ``--signature`` option to verify the collection's ``MANIFEST.json`` with these additional signatures. Supplemental signatures should be provided as URIs.

.. code-block:: bash

   ansible-galaxy collection install my_namespace.my_collection --signature https://examplehost.com/detached_signature.asc --keyring ~/.ansible/pubring.kbx

GnuPG verification only occurs for collections installed from a distribution server. User-provided signatures are not used to verify collections installed from git repositories, source directories, or URLs/paths to tar.gz files.

You can also include additional signatures in the collection ``requirements.yml`` file under the ``signatures`` key.

.. code-block:: yaml

   # requirements.yml
   collections:
     - name: ns.coll
       version: 1.0.0
       signatures:
         - https://examplehost.com/detached_signature.asc
         - file:///path/to/local/detached_signature.asc

See :ref:`collection requirements file <collection_requirements_file>` for details on how to install collections with this file.

By default, verification is considered successful if a minimum of 1 signature successfully verifies the collection. The number of required signatures can be configured with ``--required-valid-signature-count`` or :ref:`GALAXY_REQUIRED_VALID_SIGNATURE_COUNT`. All signatures can be required by setting the option to ``all``. To fail signature verification if no valid signatures are found, prepend the value with ``+``, such as ``+all`` or ``+1``.

.. code-block:: bash

   export ANSIBLE_GALAXY_GPG_KEYRING=~/.ansible/pubring.kbx
   export ANSIBLE_GALAXY_REQUIRED_VALID_SIGNATURE_COUNT=2
   ansible-galaxy collection install my_namespace.my_collection --signature https://examplehost.com/detached_signature.asc --signature file:///path/to/local/detached_signature.asc

Certain GnuPG errors can be ignored with ``--ignore-signature-status-code`` or :ref:`GALAXY_REQUIRED_VALID_SIGNATURE_COUNT`. :ref:`GALAXY_REQUIRED_VALID_SIGNATURE_COUNT` should be a list, and ``--ignore-signature-status-code`` can be provided multiple times to ignore multiple additional error status codes.

This example requires any signatures provided by the distribution server to verify the collection except if they fail due to NO_PUBKEY:

.. code-block:: bash

   export ANSIBLE_GALAXY_GPG_KEYRING=~/.ansible/pubring.kbx
   export ANSIBLE_GALAXY_REQUIRED_VALID_SIGNATURE_COUNT=all
   ansible-galaxy collection install my_namespace.my_collection --ignore-signature-status-code NO_PUBKEY

If verification fails for the example above, only errors other than NO_PUBKEY will be displayed.

If verification is unsuccessful, the collection will not be installed. GnuPG signature verification can be disabled with ``--disable-gpg-verify`` or by configuring :ref:`GALAXY_DISABLE_GPG_VERIFY`.


.. _collections_older_version:

Installing an older version of a collection
-------------------------------------------

.. include:: ../shared_snippets/installing_older_collection.txt

.. _collection_requirements_file:

Install multiple collections with a requirements file
-----------------------------------------------------

.. include:: ../shared_snippets/installing_multiple_collections.txt

.. _collection_offline_download:

Downloading a collection for offline use
-----------------------------------------

.. include:: ../shared_snippets/download_tarball_collections.txt

Installing a collection from source files
-----------------------------------------

.. include:: ../shared_snippets/installing_collections_file.rst

Installing a collection from a git repository
---------------------------------------------

.. include:: ../shared_snippets/installing_collections_git_repo.txt

.. _galaxy_server_config:

Configuring the ``ansible-galaxy`` client
------------------------------------------

.. include:: ../shared_snippets/galaxy_server_list.txt