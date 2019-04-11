# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Docker doc fragment
    DOCUMENTATION = r'''

options:
    docker_host:
        description:
            - The URL or Unix socket path used to connect to the Docker API. To connect to a remote host, provide the
              TCP connection string. For example, C(tcp://192.0.2.23:2376). If TLS is used to encrypt the connection,
              the module will automatically replace C(tcp) in the connection URL with C(https).
            - If the value is not specified in the task, the value of environment variable C(DOCKER_HOST) will be used
              instead. If the environment variable is not set, the default value will be used.
        type: str
        default: unix://var/run/docker.sock
        aliases: [ docker_url ]
    tls_hostname:
        description:
            - When verifying the authenticity of the Docker Host server, provide the expected name of the server.
            - If the value is not specified in the task, the value of environment variable C(DOCKER_TLS_HOSTNAME) will
              be used instead. If the environment variable is not set, the default value will be used.
        type: str
        default: localhost
    api_version:
        description:
            - The version of the Docker API running on the Docker Host.
            - Defaults to the latest version of the API supported by Docker SDK for Python and the docker daemon.
            - If the value is not specified in the task, the value of environment variable C(DOCKER_API_VERSION) will be
              used instead. If the environment variable is not set, the default value will be used.
        type: str
        default: auto
        aliases: [ docker_api_version ]
    timeout:
        description:
            - The maximum amount of time in seconds to wait on a response from the API.
            - If the value is not specified in the task, the value of environment variable C(DOCKER_TIMEOUT) will be used
              instead. If the environment variable is not set, the default value will be used.
        type: int
        default: 60
    ca_cert:
        description:
            - Use a CA certificate when performing server verification by providing the path to a CA certificate file.
            - If the value is not specified in the task and the environment variable C(DOCKER_CERT_PATH) is set,
              the file C(ca.pem) from the directory specified in the environment variable C(DOCKER_CERT_PATH) will be used.
        type: path
        aliases: [ tls_ca_cert, cacert_path ]
    client_cert:
        description:
            - Path to the client's TLS certificate file.
            - If the value is not specified in the task and the environment variable C(DOCKER_CERT_PATH) is set,
              the file C(cert.pem) from the directory specified in the environment variable C(DOCKER_CERT_PATH) will be used.
        type: path
        aliases: [ tls_client_cert, cert_path ]
    client_key:
        description:
            - Path to the client's TLS key file.
            - If the value is not specified in the task and the environment variable C(DOCKER_CERT_PATH) is set,
              the file C(key.pem) from the directory specified in the environment variable C(DOCKER_CERT_PATH) will be used.
        type: path
        aliases: [ tls_client_key, key_path ]
    ssl_version:
        description:
            - Provide a valid SSL version number. Default value determined by ssl.py module.
            - If the value is not specified in the task, the value of environment variable C(DOCKER_SSL_VERSION) will be
              used instead.
        type: str
    tls:
        description:
            - Secure the connection to the API by using TLS without verifying the authenticity of the Docker host
              server. Note that if C(tls_verify) is set to C(yes) as well, it will take precedence.
            - If the value is not specified in the task, the value of environment variable C(DOCKER_TLS) will be used
              instead. If the environment variable is not set, the default value will be used.
        type: bool
        default: no
    validate_certs:
        description:
            - Secure the connection to the API by using TLS and verifying the authenticity of the Docker host server.
            - If the value is not specified in the task, the value of environment variable C(DOCKER_TLS_VERIFY) will be
              used instead. If the environment variable is not set, the default value will be used.
        type: bool
        default: no
        aliases: [ tls_verify ]
    debug:
        description:
            - Debug mode
        type: bool
        default: no

notes:
  - Connect to the Docker daemon by providing parameters with each task or by defining environment variables.
    You can define C(DOCKER_HOST), C(DOCKER_TLS_HOSTNAME), C(DOCKER_API_VERSION), C(DOCKER_CERT_PATH), C(DOCKER_SSL_VERSION),
    C(DOCKER_TLS), C(DOCKER_TLS_VERIFY) and C(DOCKER_TIMEOUT). If you are using docker machine, run the script shipped
    with the product that sets up the environment. It will set these variables for you. See
    U(https://docker-py.readthedocs.io/en/stable/machine/) for more details.
  - When connecting to Docker daemon with TLS, you might need to install additional Python packages.
    For the Docker SDK for Python, version 2.4 or newer, this can be done by installing C(docker[tls]) with M(pip).
  - Note that the Docker SDK for Python only allows to specify the path to the Docker configuration for very few functions.
    In general, it will use C($HOME/.docker/config.json) if the C(DOCKER_CONFIG) environment variable is not specified,
    and use C($DOCKER_CONFIG/config.json) otherwise.
'''

    # Additional, more specific stuff for minimal Docker SDK for Python version < 2.0

    DOCKER_PY_1_DOCUMENTATION = r'''
options: {}
requirements:
  - "Docker SDK for Python: Please note that the L(docker-py,https://pypi.org/project/docker-py/)
     Python module has been superseded by L(docker,https://pypi.org/project/docker/)
     (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
     For Python 2.6, C(docker-py) must be used. Otherwise, it is recommended to
     install the C(docker) Python module. Note that both modules should I(not)
     be installed at the same time. Also note that when both modules are installed
     and one of them is uninstalled, the other might no longer function and a
     reinstall of it is required."
'''

    # Additional, more specific stuff for minimal Docker SDK for Python version >= 2.0.
    # Note that Docker SDK for Python >= 2.0 requires Python 2.7 or newer.

    DOCKER_PY_2_DOCUMENTATION = r'''
options: {}
requirements:
  - "Python >= 2.7"
  - "Docker SDK for Python: Please note that the L(docker-py,https://pypi.org/project/docker-py/)
     Python module has been superseded by L(docker,https://pypi.org/project/docker/)
     (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
     This module does I(not) work with docker-py."
'''
