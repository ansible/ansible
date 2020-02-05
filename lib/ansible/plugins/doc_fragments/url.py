# -*- coding: utf-8 -*-

# Copyright: (c) 2018, John Barker <gundalow@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  url:
    description:
      - HTTP, HTTPS, or FTP URL in the form (http|https|ftp)://[user[:pass]]@host.domain[:port]/path
    type: str
  force:
    description:
      - If C(yes) do not get a cached copy.
      - Alias C(thirsty) has been deprecated and will be removed in 2.13.
    type: bool
    default: no
    aliases: [ thirsty ]
  http_agent:
    description:
      - Header to identify as, generally appears in web server logs.
    type: str
    default: ansible-httpget
  use_proxy:
    description:
      - If C(no), it will not use a proxy, even if one is defined in an environment variable on the target hosts.
    type: bool
    default: yes
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated.
      - This should only be used on personally controlled sites using self-signed certificates.
    type: bool
    default: yes
  url_username:
    description:
      - The username for use in HTTP basic authentication.
      - This parameter can be used without I(url_password) for sites that allow empty passwords
    type: str
  url_password:
    description:
      - The password for use in HTTP basic authentication.
      - If the I(url_username) parameter is not specified, the I(url_password) parameter will not be used.
    type: str
  force_basic_auth:
    description:
      - Credentials specified with I(url_username) and I(url_password) should be passed in HTTP Header.
    type: bool
    default: no
  client_cert:
    description:
      - PEM formatted certificate chain file to be used for SSL client authentication.
      - This file can also include the key as well, and if the key is included, C(client_key) is not required.
    type: path
  client_key:
    description:
      - PEM formatted file that contains your private key to be used for SSL client authentication.
      - If C(client_cert) contains both the certificate and key, this option is not required.
    type: path
'''
