# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#


class ModuleDocFragment(object):

    # Docker doc fragment
    DOCUMENTATION = '''

options:
    docker_host:
        description:
            - "The URL or Unix socket path used to connect to the Docker API. To connect to a remote host, provide the
              TCP connection string. For example, 'tcp://192.0.2.23:2376'. If TLS is used to encrypt the connection,
              the module will automatically replace 'tcp' in the connection URL with 'https'."
        default: "unix://var/run/docker.sock"
        aliases:
            - docker_url
    tls_hostname:
        description:
            - When verifying the authenticity of the Docker Host server, provide the expected name of the server.
        default: localhost
    api_version:
        description:
            - The version of the Docker API running on the Docker Host. Defaults to the latest version of the API
              supported by docker-py.
        default: 'auto'
        aliases:
            - docker_api_version
    timeout:
        description:
            - The maximum amount of time in seconds to wait on a response from the API.
        default: 60
    cacert_path:
        description:
            - Use a CA certificate when performing server verification by providing the path to a CA certificate file.
        aliases:
            - tls_ca_cert
    cert_path:
        description:
            - Path to the client's TLS certificate file.
        aliases:
            - tls_client_cert
    key_path:
        description:
            - Path to the client's TLS key file.
        aliases:
            - tls_client_key
    ssl_version:
        description:
            - Provide a valid SSL version number. Default value determined by ssl.py module.
    tls:
        description:
            -  Secure the connection to the API by using TLS without verifying the authenticity of the Docker host
               server.
        default: false
        type: bool
    tls_verify:
        description:
            - Secure the connection to the API by using TLS and verifying the authenticity of the Docker host server.
        default: false
        type: bool
    debug:
        description:
            - Debug mode
        default: false
        type: bool

notes:
    - Connect to the Docker daemon by providing parameters with each task or by defining environment variables.
      You can define DOCKER_HOST, DOCKER_TLS_HOSTNAME, DOCKER_API_VERSION, DOCKER_CERT_PATH, DOCKER_SSL_VERSION,
      DOCKER_TLS, DOCKER_TLS_VERIFY and DOCKER_TIMEOUT. If you are using docker machine, run the script shipped
      with the product that sets up the environment. It will set these variables for you. See
      https://docker-py.readthedocs.org/en/stable/machine/ for more details.
'''
