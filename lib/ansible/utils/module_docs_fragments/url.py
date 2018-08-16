# (c) 2018, John Barker<gundalow@redhat.com>
#
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


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = """
options:
  url:
    description:
      - HTTP, HTTPS, or FTP URL in the form (http|https|ftp)://[user[:pass]]@host.domain[:port]/path
  force:
    description:
      - If C(yes) do not get a cached copy.
    aliases:
      - thirsty
    type: bool
    default: no
  http_agent:
    description:
      - Header to identify as, generally appears in web server logs.
    default: ansible-httpget
  use_proxy:
    description:
      - If C(no), it will not use a proxy, even if one is defined in an environment variable on the target hosts.
    type: bool
    default: yes
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    default: yes
    type: bool
  url_username:
    description:
      - The username for use in HTTP basic authentication.
      - This parameter can be used without I(url_password) for sites that allow empty passwords
  url_password:
    description:
      - The password for use in HTTP basic authentication.
      - If the I(url_username) parameter is not specified, the I(url_password) parameter will not be used.
  force_basic_auth:
    description:
      - Credentials specified with I(url_username) and I(url_password) should be passed in HTTP Header.
    default: no
    type: bool
  client_cert:
    description:
      - PEM formatted certificate chain file to be used for SSL client
        authentication. This file can also include the key as well, and if
        the key is included, C(client_key) is not required.
  client_key:
    description:
      - PEM formatted file that contains your private key to be used for SSL
        client authentication. If C(client_cert) contains both the certificate
        and key, this option is not required.
"""
