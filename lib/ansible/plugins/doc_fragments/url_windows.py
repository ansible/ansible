# -*- coding: utf-8 -*-

# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


class ModuleDocFragment:

    # Common options for Ansible.ModuleUtils.WebRequest
    DOCUMENTATION = r'''
options:
  method:
    description:
    - The HTTP Method of the request.
    type: str
  follow_redirects:
    description:
    - Whether or the module should follow redirects.
    - V(all) will follow all redirect.
    - V(none) will not follow any redirect.
    - V(safe) will follow only "safe" redirects, where "safe" means that the
      client is only doing a C(GET) or C(HEAD) on the URI to which it is being
      redirected.
    - When following a redirected URL, the C(Authorization) header and any
      credentials set will be dropped and not redirected.
    choices:
    - all
    - none
    - safe
    default: safe
    type: str
  headers:
    description:
    - Extra headers to set on the request.
    - This should be a dictionary where the key is the header name and the
      value is the value for that header.
    type: dict
  http_agent:
    description:
    - Header to identify as, generally appears in web server logs.
    - This is set to the C(User-Agent) header on a HTTP request.
    default: ansible-httpget
    type: str
  maximum_redirection:
    description:
    - Specify how many times the module will redirect a connection to an
      alternative URI before the connection fails.
    - If set to V(0) or O(follow_redirects) is set to V(null), or V(safe) when
      not doing a C(GET) or C(HEAD) it prevents all redirection.
    default: 50
    type: int
  timeout:
    description:
    - Specifies how long the request can be pending before it times out (in
      seconds).
    - Set to V(0) to specify an infinite timeout.
    default: 30
    type: int
  validate_certs:
    description:
    - If V(no), SSL certificates will not be validated.
    - This should only be used on personally controlled sites using self-signed
      certificates.
    default: yes
    type: bool
  client_cert:
    description:
    - The path to the client certificate C(.pfx) that is used for X509
      authentication. This path can either be the path to the C(.pfx) on the
      filesystem or the PowerShell certificate path
      C(Cert:\CurrentUser\My\<thumbprint>).
    - The WinRM connection must be authenticated with C(CredSSP) or C(become)
      is used on the task if the certificate file is not password protected.
    - Other authentication types can set O(client_cert_password) when the cert
      is password protected.
    type: str
  client_cert_password:
    description:
    - The password for O(client_cert) if the cert is password protected.
    type: str
  force_basic_auth:
    description:
    - By default the authentication header is only sent when a webservice
      responses to an initial request with a 401 status. Since some basic auth
      services do not properly send a 401, logins will fail.
    - This option forces the sending of the Basic authentication header upon
      the original request.
    default: no
    type: bool
  url_username:
    description:
    - The username to use for authentication.
    type: str
  url_password:
    description:
    - The password for O(url_username).
    type: str
  use_default_credential:
    description:
    - Uses the current user's credentials when authenticating with a server
      protected with C(NTLM), C(Kerberos), or C(Negotiate) authentication.
    - Sites that use C(Basic) auth will still require explicit credentials
      through the O(url_username) and O(url_password) options.
    - The module will only have access to the user's credentials if using
      C(become) with a password, you are connecting with SSH using a password,
      or connecting with WinRM using C(CredSSP) or C(Kerberos with delegation).
    - If not using C(become) or a different auth method to the ones stated
      above, there will be no default credentials available and no
      authentication will occur.
    default: no
    type: bool
  use_proxy:
    description:
    - If V(no), it will not use the proxy defined in IE for the current user.
    default: yes
    type: bool
  proxy_url:
    description:
    - An explicit proxy to use for the request.
    - By default, the request will use the IE defined proxy unless O(use_proxy=no).
    type: str
  proxy_username:
    description:
    - The username to use for proxy authentication.
    type: str
  proxy_password:
    description:
    - The password for O(proxy_username).
    type: str
  proxy_use_default_credential:
    description:
    - Uses the current user's credentials when authenticating with a proxy host
      protected with C(NTLM), C(Kerberos), or C(Negotiate) authentication.
    - Proxies that use C(Basic) auth will still require explicit credentials
      through the O(proxy_username) and O(proxy_password) options.
    - The module will only have access to the user's credentials if using
      C(become) with a password, you are connecting with SSH using a password,
      or connecting with WinRM using C(CredSSP) or C(Kerberos with delegation).
    - If not using C(become) or a different auth method to the ones stated
      above, there will be no default credentials available and no proxy
      authentication will occur.
    default: no
    type: bool
seealso:
- module: community.windows.win_inet_proxy
'''
