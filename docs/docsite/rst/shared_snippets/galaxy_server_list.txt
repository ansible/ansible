


By default running ``ansible-galaxy`` will use the :ref:`galaxy_server` config value or the ``--server`` command line
argument when it performs an action against a Galaxy server. The ``ansible-galaxy collection install`` supports
installing collections from multiple servers as defined in the :ref:`ansible_configuration_settings_locations` file
using the :ref:`galaxy_server_list` configuration option. To define multiple Galaxy servers you have to create the
following entries like so:

.. code-block:: ini

    [galaxy]
    server_list = automation_hub, my_org_hub, release_galaxy, test_galaxy

    [galaxy_server.automation_hub]
    url=https://ci.cloud.redhat.com/api/automation-hub/
    auth_url=https://sso.qa.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
    token=my_token

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
* ``auth_url``: The URL of a Keycloak server 'token_endpoint' if using SSO auth (Automation Hub for ex). This is mutually exclusive with ``username``. ``auth_url`` requires ``token``.

As well as being defined in the ``ansible.cfg`` file, these server options can be defined as an environment variable.
The environment variable is in the form ``ANSIBLE_GALAXY_SERVER_{{ id }}_{{ key }}`` where ``{{ id }}`` is the upper
case form of the server identifier and ``{{ key }}`` is the key to define. For example I can define ``token`` for
``release_galaxy`` by setting ``ANSIBLE_GALAXY_SERVER_RELEASE_GALAXY_TOKEN=secret_token``.

For operations where only one Galaxy server is used, i.e. ``publish``, ``info``, ``login`` then the first entry in the
``server_list`` is used unless an explicit server was passed in as a command line argument.

.. note::
    Once a collection is found, any of its requirements are only searched within the same Galaxy instance as the parent
    collection. The install process will not search for a collection requirement in a different Galaxy instance.
