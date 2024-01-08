# -*- coding: utf-8 -*-

# Copyright: (c) 2018, John Barker <gundalow@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


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
      - If V(yes) do not get a cached copy.
    type: bool
    default: no
  http_agent:
    description:
      - Header to identify as, generally appears in web server logs.
    type: str
    default: ansible-httpget
  use_proxy:
    description:
      - If V(no), it will not use a proxy, even if one is defined in an environment variable on the target hosts.
    type: bool
    default: yes
  validate_certs:
    description:
      - If V(no), SSL certificates will not be validated.
      - This should only be used on personally controlled sites using self-signed certificates.
    type: bool
    default: yes
  url_username:
    description:
      - The username for use in HTTP basic authentication.
      - This parameter can be used without O(url_password) for sites that allow empty passwords
    type: str
  url_password:
    description:
      - The password for use in HTTP basic authentication.
      - If the O(url_username) parameter is not specified, the O(url_password) parameter will not be used.
    type: str
  force_basic_auth:
    description:
      - Credentials specified with O(url_username) and O(url_password) should be passed in HTTP Header.
    type: bool
    default: no
  client_cert:
    description:
      - PEM formatted certificate chain file to be used for SSL client authentication.
      - This file can also include the key as well, and if the key is included, O(client_key) is not required.
    type: path
  client_key:
    description:
      - PEM formatted file that contains your private key to be used for SSL client authentication.
      - If O(client_cert) contains both the certificate and key, this option is not required.
    type: path
  use_gssapi:
    description:
      - Use GSSAPI to perform the authentication, typically this is for Kerberos or Kerberos through Negotiate
        authentication.
      - Requires the Python library L(gssapi,https://github.com/pythongssapi/python-gssapi) to be installed.
      - Credentials for GSSAPI can be specified with O(url_username)/O(url_password) or with the GSSAPI env var
        C(KRB5CCNAME) that specified a custom Kerberos credential cache.
      - NTLM authentication is B(not) supported even if the GSSAPI mech for NTLM has been installed.
    type: bool
    default: no
    version_added: '2.11'
'''

    URL_REDIRECT = r'''
options:
  follow_redirects:
    description:
      - Whether or not redirects should be followed. V(all) will follow all redirects.
        V(safe) will follow only "safe" redirects, where "safe" means that the client is only
        doing a GET or HEAD on the URI to which it is being redirected. V(none) will not follow
        any redirects. Note that V(true) and V(false) choices are accepted for backwards compatibility,
        where V(true) is the equivalent of V(all) and V(false) is the equivalent of V(safe). V(true) and V(false)
        are deprecated and will be removed in some future version of Ansible.
    type: str
    choices: ['all', 'no', 'none', 'safe', 'urllib2', 'yes']
    default: safe
'''