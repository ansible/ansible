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
            - URL or Unix socket path used to connect to the Docker daemon.
        required: false
        default: null
    tls_hostname:
        description:
            - If verifying the name of the host found in the TLS certs, provide the expected host name.
        default: null
        required: false
    api_version:
        description:
            - Version of the Docker API the client will use.
        required: false
        default: default provided by docker-py
    timeout:
        description:
            - Amount of time in seconds to wait on response from the API.
        required: false
        default: null
    cacert_path:
        description:
            - Path to the client TLS Certificate Authority .pem file.
        required: false
        default: null
    cert_path:
        description:
            - Path to the client TLS certificate .pem file.
        required: false
        default: null
    key_path:
        description:
            - Path to the client .pem key file.
        required: false
        default: null
    ssl_version:
        description:
            - SSL version number to use for TLS encryption.
        required: false
        default: null
    tls:
        description:
            - Use TLS encryption without verifying the host certificates.
        default: false
    tls_verify:
        description:
            - Use TLS encryption and verify the host certificates.
        default: false

notes:
    - Connect to the Docker daemon by providing parameters with each task or by defining environment variables.
      You can define DOCKER_HOST, DOCKER_TLS_HOSTNAME, DOCKER_API_VERSION, DOCKER_CERT_PATH, DOCKER_SSL_VERSION,
      DOCKER_TLS, DOCKER_TLS_VERIFY and DOCKER_TIMEOUT. If you are using docker machine, run the script shipped
      with the product that sets up the environment. It will set these variables for you. See
      https://docker-py.readthedocs.org/en/stable/machine/ for more details.
'''