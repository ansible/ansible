# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Peter Sagerson <psagers@ignorare.net>
# Copyright: (c) 2016, Jiri Tyr <jiri.tyr@gmail.com>
# Copyright: (c) 2017-2018 Keller Fuchs (@kellerfuchs) <kellerfuchs@hashbang.sh>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Standard LDAP documentation fragment
    DOCUMENTATION = '''
options:
  bind_dn:
    description:
      - A DN to bind with. If this is omitted, we'll try a SASL bind with the EXTERNAL mechanism.
      - If this is blank, we'll use an anonymous bind.
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
      - A URI to the LDAP server.
      - The default value lets the underlying LDAP client library look for a UNIX domain socket in its default location.
  start_tls:
    default: 'no'
    type: bool
    description:
      - If true, we'll use the START_TLS LDAP extension.
  validate_certs:
    default: 'yes'
    type: bool
    description:
      - If set to C(no), SSL certificates will not be validated.
      - This should only be used on sites using self-signed certificates.
    version_added: "2.4"
'''
