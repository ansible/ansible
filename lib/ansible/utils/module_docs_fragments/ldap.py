# -*- coding: utf-8 -*-

# Copyright 2017-2018 Keller Fuchs (@kellerfuchs) <kellerfuchs@hashbang.sh>
# Copyright 2016      Peter Sagerson <psagers@ignorare.net>
# Copyright 2016      Jiri Tyr <jiri.tyr@gmail.com>

# This file is part of Ansible by Red Hat
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
    DOCUMENTATION = '''
options:
  bind_dn:
    description:
      - A DN to bind with. If this is omitted, we'll try a SASL bind with
        the EXTERNAL mechanism. If this is blank, we'll use an anonymous
        bind.
  bind_pw:
    description:
      - The password to use with I(bind_dn).
  dn:
    required: true
    description:
      - The DN of the entry to add or remove.
  server_uri:
    default: ldapi:///
    description:
      - A URI to the LDAP server. The default value lets the underlying
        LDAP client library look for a UNIX domain socket in its default
        location.
  start_tls:
    default: 'no'
    type: bool
    description:
      - If true, we'll use the START_TLS LDAP extension.
  validate_certs:
    default: 'yes'
    type: bool
    description:
      - If C(no), SSL certificates will not be validated. This should only be
        used on sites using self-signed certificates.
    version_added: "2.4"
'''
