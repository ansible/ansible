# (c) 2017, Yassine Azzouz <yassine.azzouz@gmail.com>
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = """
options:
  user:
    required: false
    default: null
    description:
      - Identity of the user running the query, (applies only to C(authentication=local)).
      - When security is off the authenticated user is the username specified in the user.name query parameter, specified by this parameter.
      - Defaults to the current user (as determined by I(whoami)).
  authentication:
    required: false
    default: none
    choices: [ none, kerberos, token ]
    description:
      - The authentication type to use
      - if C(local) the user issuing the requests will be the current user.
      - if C(kerberos), the C(principal) and C(keytab) or C(password) will be used to kinit.
      - if C(token), the C(token) will be used to authenticate the user.
  principal:
    required: false
    default: null
    description:
      - When security is on, the authentication is performed against a kerberos server with the principal, specified by this parameter.
      - This applies only to C(authentication=kerberos)
  proxy:
    required: false
    default: null
    description:
      - User to proxy as, theorically make sense only with C(authentication=kerberos) or C(authentication=token) but works for both secure and Insecure.
  password:
    required: false
    default: null
    description:
      - The kerberos password used to authenticate the principle, this is only valid with C(authentication=kerberos).
  keytab:
    required: false
    default: null
    description:
      - The keytab used to authenticate the principle, this is only valid with C(authentication=kerberos)
      - Only one credentials type can be used so this is mutually exclusive with C(password).
  token:
    required: false
    default: null
    description:
      - When security is on you can use a delegation token instead of having to authenticate every time with kerberos.
  nameservices:
    required: true
    default: null
    description:
      - A json list of nameservices to connect to, each nameservice is a dict having a list of namenodes urls and the associated mount points.
      - You can create the spec in yml then use the to_json filter.
  verify:
    required: false
    default: false
    type: bool
    description:
      - For secure connections whether to verify or not the server certificate.
  truststore:
    required: false
    default: null
    description:
      - For secure connections the server certificate file(trust store) to trust.
  timeout:
    required: false
    default: null
    description:
      - Connection timeouts, forwarded to the request handler. This determines how long to wait for the server to send data before giving up.
  root:
    required: false
    default: null
    description:
      - Root path, this will be prefixed to all HDFS paths passed. If the root is relative, the path will be assumed relative to the user home directory.
"""
