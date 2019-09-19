
.. _collections:

*****************
Using collections
*****************

Collections are a distribution format for Ansible content that can include playbooks, roles, modules, and plugins.
You can install and use collections through `Ansible Galaxy <https://galaxy.ansible.com>`_.

.. contents::
   :local:
   :depth: 2

Installing collections
======================

You can use the ``ansible-galaxy collection install`` command to install a collection on your system. You must specify an installation location using the ``-p`` option.

To install a collection hosted in Galaxy:

.. code-block:: bash

   ansible-galaxy collection install my_namespace.my_collection -p /collections

You can also directly use the tarball from your build:

.. code-block:: bash

   ansible-galaxy collection install my_namespace-my_collection-1.0.0.tar.gz -p ./collections

.. note::
    The install command automatically appends the path ``ansible_collections`` to the one specified  with the ``-p`` option unless the
    parent directory is already in a folder called ``ansible_collections``.


You should use one of the values configured in :ref:`COLLECTIONS_PATHS` for your path. This is also where Ansible itself will expect to find collections when attempting to use them.

You can also keep a collection adjacent to the current playbook, under a ``collections/ansible_collections/`` directory structure.

::

    play.yml
    ├── collections/
    │   └── ansible_collections/
    │               └── my_namespace/
    │                   └── my_collection/<collection structure lives here>


Installing an older version of a collection
-------------------------------------------

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


.. _collection_requirements_file:

Install multiple collections with a requirements file
-----------------------------------------------------

You can also setup a ``requirements.yml`` file to install multiple collections in one command. This file is a YAML file in the format:

.. code-block:: yaml+jinja

   ---
   collections:
   # With just the collection name
   - my_namespace.my_collection

   # With the collection name, version, and source options
   - name: my_namespace.my_other_collection
     version: 'version range identifiers (default: ``*``)'
     source: 'The Galaxy URL to pull the collection from (default: ``--api-server`` from cmdline)'

The ``version`` key can take in the same range identifier format documented above.

Roles can also be specified and placed under the ``roles`` key. The values follow the same format as a requirements
file used in older Ansible releases.

.. note::
    While both roles and collections can be specified in one requirements file, they need to be installed separately.
    The ``ansible-galaxy role install -r requirements.yml`` will only install roles and
    ``ansible-galaxy collection install -r requirements.yml -p ./`` will only install collections.

.. _galaxy_server_config:

Galaxy server configuration list
--------------------------------

By default running ``ansible-galaxy`` will use the :ref:`galaxy_server` config value or the ``--server`` command line
argument when it performs an action against a Galaxy server. The ``ansible-galaxy collection install`` supports
installing collections from multiple servers as defined in the :ref:`ansible_configuration_settings_locations` file
using the :ref:`galaxy_server_list` configuration option. To define multiple Galaxy servers you have to create the
following entries like so:

.. code-block:: ini

    [galaxy]
    server_list = my_org_hub, release_galaxy, test_galaxy

    [galaxy_server.my_org_hub]
    url=https://automation.my_org/
    username=my_user
    password=my_pass

    [galaxy_server.release_galaxy]
    url=https://galaxy.ansible.com/
    token=my_token

    [galaxy_server.test_galaxy]
    url=https://galaxy-dev.ansible.com/
    token=my_token

.. note::
    You can use the ``--server`` command line argument to select an explicit Galaxy server in the ``server_list`` and
    the value of this arg should match the name of the server. If the value of ``--server`` is not a pre-defined server
    in ``ansible.cfg`` then the value specified will be the URL used to access that server and all pre-defined servers
    are ignored. Also the ``--api-key`` argument is not applied to any of the pre-defined servers, it is only applied
    if no server list is defined or a URL was specified by ``--server``.


The :ref:`galaxy_server_list` option is a list of server identifiers in a prioritized order. When searching for a
collection, the install process will search in that order, e.g. ``my_org_hub`` first, then ``release_galaxy``, and
finally ``test_galaxy`` until the collection is found. The actual Galaxy instance is then defined under the section
``[galaxy_server.{{ id }}]`` where ``{{ id }}`` is the server identifier defined in the list. This section can then
define the following keys:

* ``url``: The URL of the galaxy instance to connect to, this is required.
* ``token``: A token key to use for authentication against the Galaxy instance, this is mutually exclusive with ``username``
* ``username``: The username to use for basic authentication against the Galaxy instance, this is mutually exclusive with ``token``
* ``password``: The password to use for basic authentication

As well as being defined in the ``ansible.cfg`` file, these server options can be defined as an environment variable.
The environment variable is in the form ``ANSIBLE_GALAXY_SERVER_{{ id }}_{{ key }}`` where ``{{ id }}`` is the upper
case form of the server identifier and ``{{ key }}`` is the key to define. For example I can define ``token`` for
``release_galaxy`` by setting ``ANSIBLE_GALAXY_SERVER_RELEASE_GALAXY_TOKEN=secret_token``.

For operations where only one Galaxy server is used, i.e. ``publish``, ``info``, ``login`` then the first entry in the
``server_list`` is used unless an explicit server was passed in as a command line argument.

.. note::
    Once a collection is found, any of its requirements are only searched within the same Galaxy instance as the parent
    collection. The install process will not search for a collection requirement in a different Galaxy instance.


.. _using_collections:

Using collections in a Playbook
===============================

Once installed, you can reference a collection content by its fully qualified collection name (FQCN):

.. code-block:: yaml

     - hosts: all
       tasks:
         - my_namespace.my_collection.mymodule:
             option1: value

This works for roles or any type of plugin distributed within the collection:

.. code-block:: yaml

     - hosts: all
       tasks:
         - import_role:
             name: my_namespace.my_collection.role1

         - my_namespace.mycollection.mymodule:
             option1: value

         - debug:
             msg: '{{ lookup("my_namespace.my_collection.lookup1", 'param1')| my_namespace.my_collection.filter1 }}'


To avoid a lot of typing, you can use the ``collections`` keyword added in Ansible 2.8:


.. code-block:: yaml

     - hosts: all
       collections:
        - my_namespace.my_collection
       tasks:
         - import_role:
             name: role1

         - mymodule:
             option1: value

         - debug:
             msg: '{{ lookup("my_namespace.my_collection.lookup1", 'param1')| my_namespace.my_collection.filter1 }}'

This keyword creates a 'search path' for non namespaced plugin references. It does not import roles or anything else.
Notice that you still need the FQCN for non-action or module plugins.

.. seealso::

  :ref:`developing_collections`
      Develop or modify a collection.
  :ref:`collections_galaxy_meta`
       Understand the collections metadata structure.
  `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
  `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
