.. _collections_listing:

Listing collections
===================

To list installed collections, run ``ansible-galaxy collection list``. This shows all of the installed collections found in the configured collections search paths. It will also show collections under development which contain a galaxy.yml file instead of a MANIFEST.json. The path where the collections are located are displayed as well as version information. If no version information is available, a ``*`` is displayed for the version number.

.. code-block:: shell

      # /home/astark/.ansible/collections/ansible_collections
      Collection                 Version
      -------------------------- -------
      cisco.aci                  0.0.5
      cisco.mso                  0.0.4
      sandwiches.ham             *
      splunk.es                  0.0.5

      # /usr/share/ansible/collections/ansible_collections
      Collection        Version
      ----------------- -------
      fortinet.fortios  1.0.6
      pureport.pureport 0.0.8
      sensu.sensu_go    1.3.0

Run with ``-vvv`` to display more detailed information.
You may see additional collections here that were added as dependencies of your installed collections. Only use collections in your playbooks that you have directly installed.

To list a specific collection, pass a valid fully qualified collection name (FQCN) to the command ``ansible-galaxy collection list``. All instances of the collection will be listed.

.. code-block:: shell

      > ansible-galaxy collection list fortinet.fortios

      # /home/astark/.ansible/collections/ansible_collections
      Collection       Version
      ---------------- -------
      fortinet.fortios 1.0.1

      # /usr/share/ansible/collections/ansible_collections
      Collection       Version
      ---------------- -------
      fortinet.fortios 1.0.6

To search other paths for collections, use the ``-p`` option. Specify multiple search paths by separating them with a ``:``. The list of paths specified on the command line will be added to the beginning of the configured collections search paths.

.. code-block:: shell

      > ansible-galaxy collection list -p '/opt/ansible/collections:/etc/ansible/collections'

      # /opt/ansible/collections/ansible_collections
      Collection      Version
      --------------- -------
      sandwiches.club 1.7.2

      # /etc/ansible/collections/ansible_collections
      Collection     Version
      -------------- -------
      sandwiches.pbj 1.2.0

      # /home/astark/.ansible/collections/ansible_collections
      Collection                 Version
      -------------------------- -------
      cisco.aci                  0.0.5
      cisco.mso                  0.0.4
      fortinet.fortios           1.0.1
      sandwiches.ham             *
      splunk.es                  0.0.5

      # /usr/share/ansible/collections/ansible_collections
      Collection        Version
      ----------------- -------
      fortinet.fortios  1.0.6
      pureport.pureport 0.0.8
      sensu.sensu_go    1.3.0
