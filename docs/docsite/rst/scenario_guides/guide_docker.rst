Docker Guide
============

Ansible offers the following modules for orchestrating Docker containers:

    docker_compose
        Use your existing Docker compose files to orchestrate containers on a single Docker daemon or on
        Swarm. Supports compose versions 1 and 2.

    docker_container
        Manages the container lifecycle by providing the ability to create, update, stop, start and destroy a
        container.

    docker_image
        Provides full control over images, including: build, pull, push, tag and remove.

    docker_image_info
        Inspects one or more images in the Docker host's image cache, providing the information for making
        decision or assertions in a playbook.

    docker_login
        Authenticates with Docker Hub or any Docker registry and updates the Docker Engine config file, which
        in turn provides password-free pushing and pulling of images to and from the registry.

    docker (dynamic inventory)
        Dynamically builds an inventory of all the available containers from a set of one or more Docker hosts.


Ansible 2.1.0 includes major updates to the Docker modules, marking the start of a project to create a complete and
integrated set of tools for orchestrating containers. In addition to the above modules, we are also working on the
following:

Still using Dockerfile to build images? Check out `ansible-bender <https://github.com/ansible-community/ansible-bender>`_,
and start building images from your Ansible playbooks.

Use `Ansible Operator <https://learn.openshift.com/ansibleop/ansible-operator-overview/>`_
to launch your docker-compose file on `OpenShift <https://www.okd.io/>`_. Go from an app on your laptop to a fully
scalable app in the cloud with Kubernetes in just a few moments.

There's more planned. See the latest ideas and thinking at the `Ansible proposal repo <https://github.com/ansible/proposals/tree/master/docker>`_.

Requirements
------------

Using the docker modules requires having the `Docker SDK for Python <https://docker-py.readthedocs.io/en/stable/>`_
installed on the host running Ansible. You will need to have >= 1.7.0 installed. For Python 2.7 or
Python 3, you can install it as follows:

.. code-block:: bash

    $ pip install docker

For Python 2.6, you need a version before 2.0. For these versions, the SDK was called ``docker-py``,
so you need to install it as follows:

.. code-block:: bash

    $ pip install 'docker-py>=1.7.0'

Please note that only one of ``docker`` and ``docker-py`` must be installed. Installing both will result in
a broken installation. If this happens, Ansible will detect it and inform you about it::

    Cannot have both the docker-py and docker python modules installed together as they use the same
    namespace and cause a corrupt installation. Please uninstall both packages, and re-install only
    the docker-py or docker python module. It is recommended to install the docker module if no support
    for Python 2.6 is required. Please note that simply uninstalling one of the modules can leave the
    other module in a broken state.

The docker_compose module also requires `docker-compose <https://github.com/docker/compose>`_

.. code-block:: bash

   $ pip install 'docker-compose>=1.7.0'


Connecting to the Docker API
----------------------------

You can connect to a local or remote API using parameters passed to each task or by setting environment variables.
The order of precedence is command line parameters and then environment variables. If neither a command line
option or an environment variable is found, a default value will be used. The default values are provided under
`Parameters`_


Parameters
..........

Control how modules connect to the Docker API by passing the following parameters:

    docker_host
        The URL or Unix socket path used to connect to the Docker API. Defaults to ``unix://var/run/docker.sock``.
        To connect to a remote host, provide the TCP connection string. For example: ``tcp://192.0.2.23:2376``. If
        TLS is used to encrypt the connection to the API, then the module will automatically replace 'tcp' in the
        connection URL with 'https'.

    api_version
        The version of the Docker API running on the Docker Host. Defaults to the latest version of the API supported
        by docker-py.

    timeout
        The maximum amount of time in seconds to wait on a response from the API. Defaults to 60 seconds.

    tls
        Secure the connection to the API by using TLS without verifying the authenticity of the Docker host server.
        Defaults to False.

    tls_verify
        Secure the connection to the API by using TLS and verifying the authenticity of the Docker host server.
        Default is False.

    cacert_path
        Use a CA certificate when performing server verification by providing the path to a CA certificate file.

    cert_path
        Path to the client's TLS certificate file.

    key_path
        Path to the client's TLS key file.

    tls_hostname
        When verifying the authenticity of the Docker Host server, provide the expected name of the server. Defaults
        to 'localhost'.

    ssl_version
        Provide a valid SSL version number. Default value determined by docker-py, which at the time of this writing
        was 1.0


Environment Variables
.....................

Control how the modules connect to the Docker API by setting the following variables in the environment of the host
running Ansible:

    DOCKER_HOST
        The URL or Unix socket path used to connect to the Docker API.

    DOCKER_API_VERSION
        The version of the Docker API running on the Docker Host. Defaults to the latest version of the API supported
        by docker-py.

    DOCKER_TIMEOUT
        The maximum amount of time in seconds to wait on a response from the API.

    DOCKER_CERT_PATH
        Path to the directory containing the client certificate, client key and CA certificate.

    DOCKER_SSL_VERSION
        Provide a valid SSL version number.

    DOCKER_TLS
        Secure the connection to the API by using TLS without verifying the authenticity of the Docker Host.

    DOCKER_TLS_VERIFY
        Secure the connection to the API by using TLS and verify the authenticity of the Docker Host.


Dynamic Inventory Script
------------------------
The inventory script generates dynamic inventory by making API requests to one or more Docker APIs. It's dynamic
because the inventory is generated at run-time rather than being read from a static file. The script generates the
inventory by connecting to one or many Docker APIs and inspecting the containers it finds at each API. Which APIs the
script contacts can be defined using environment variables or a configuration file.

Groups
......
The script will create the following host groups:

 - container id
 - container name
 - container short id
 - image_name  (image_<image name>)
 - docker_host
 - running
 - stopped

Examples
........

You can run the script interactively from the command line or pass it as the inventory to a playbook. Here are few
examples to get you started:

.. code-block:: bash

    # Connect to the Docker API on localhost port 4243 and format the JSON output
    DOCKER_HOST=tcp://localhost:4243 ./docker.py --pretty

    # Any container's ssh port exposed on 0.0.0.0 will be mapped to
    # another IP address (where Ansible will attempt to connect via SSH)
    DOCKER_DEFAULT_IP=192.0.2.5 ./docker.py --pretty

    # Run as input to a playbook:
    ansible-playbook -i ~/projects/ansible/contrib/inventory/docker.py docker_inventory_test.yml

    # Simple playbook to invoke with the above example:

        - name: Test docker_inventory, this will not connect to any hosts
          hosts: all
          gather_facts: no
          tasks:
            - debug: msg="Container - {{ inventory_hostname }}"

Configuration
.............
You can control the behavior of the inventory script by defining environment variables, or
creating a docker.yml file (sample provided in ansible/contrib/inventory). The order of precedence is the docker.yml
file and then environment variables.


Environment Variables
;;;;;;;;;;;;;;;;;;;;;;

To connect to a single Docker API the following variables can be defined in the environment to control the connection
options. These are the same environment variables used by the Docker modules.

    DOCKER_HOST
        The URL or Unix socket path used to connect to the Docker API. Defaults to unix://var/run/docker.sock.

    DOCKER_API_VERSION:
        The version of the Docker API running on the Docker Host. Defaults to the latest version of the API supported
        by docker-py.

    DOCKER_TIMEOUT:
        The maximum amount of time in seconds to wait on a response from the API. Defaults to 60 seconds.

    DOCKER_TLS:
        Secure the connection to the API by using TLS without verifying the authenticity of the Docker host server.
        Defaults to False.

    DOCKER_TLS_VERIFY:
        Secure the connection to the API by using TLS and verifying the authenticity of the Docker host server.
        Default is False

    DOCKER_TLS_HOSTNAME:
        When verifying the authenticity of the Docker Host server, provide the expected name of the server. Defaults
        to localhost.

    DOCKER_CERT_PATH:
        Path to the directory containing the client certificate, client key and CA certificate.

    DOCKER_SSL_VERSION:
        Provide a valid SSL version number. Default value determined by docker-py, which at the time of this writing
        was 1.0

In addition to the connection variables there are a couple variables used to control the execution and output of the
script:

    DOCKER_CONFIG_FILE
        Path to the configuration file. Defaults to ./docker.yml.

    DOCKER_PRIVATE_SSH_PORT:
        The private port (container port) on which SSH is listening for connections. Defaults to 22.

    DOCKER_DEFAULT_IP:
        The IP address to assign to ansible_host when the container's SSH port is mapped to interface '0.0.0.0'.


Configuration File
;;;;;;;;;;;;;;;;;;

Using a configuration file provides a means for defining a set of Docker APIs from which to build an inventory.

The default name of the file is derived from the name of the inventory script. By default the script will look for
basename of the script (i.e. docker) with an extension of '.yml'.

You can also override the default name of the script by defining DOCKER_CONFIG_FILE in the environment.

Here's what you can define in docker_inventory.yml:

    defaults
        Defines a default connection. Defaults will be taken from this and applied to any values not provided
        for a host defined in the hosts list.

    hosts
        If you wish to get inventory from more than one Docker host, define a hosts list.

For the default host and each host in the hosts list define the following attributes:

.. code-block:: yaml

  host:
      description: The URL or Unix socket path used to connect to the Docker API.
      required: yes

  tls:
     description: Connect using TLS without verifying the authenticity of the Docker host server.
     default: false
     required: false

  tls_verify:
     description: Connect using TLS without verifying the authenticity of the Docker host server.
     default: false
     required: false

  cert_path:
     description: Path to the client's TLS certificate file.
     default: null
     required: false

  cacert_path:
     description: Use a CA certificate when performing server verification by providing the path to a CA certificate file.
     default: null
     required: false

  key_path:
     description: Path to the client's TLS key file.
     default: null
     required: false

  version:
     description: The Docker API version.
     required: false
     default: will be supplied by the docker-py module.

  timeout:
     description: The amount of time in seconds to wait on an API response.
     required: false
     default: 60

  default_ip:
     description: The IP address to assign to ansible_host when the container's SSH port is mapped to interface
     '0.0.0.0'.
     required: false
     default: 127.0.0.1

  private_ssh_port:
     description: The port containers use for SSH
     required: false
     default: 22
