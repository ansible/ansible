# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Peter Sagerson <psagers@ignorare.net>
# Copyright: (c) 2016, Jiri Tyr <jiri.tyr@gmail.com>
# Copyright: (c) 2017-2018 Keller Fuchs (@KellerFuchs) <kellerfuchs@hashbang.sh>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Standard LDAP documentation fragment
    DOCUMENTATION = r'''
options:
  bind_dn:
    description:
      - A DN to bind with. If this is omitted, we'll try a SASL bind with the EXTERNAL mechanism.
      - If this is blank, we'll use an anonymous bind.
    type: str
  bind_pw:
    description:
      - The password to use with I(bind_dn).
    type: str
  dn:
    required: true
    description:
      - The DN of the entry to add or remove.
    type: str
  server_uri:
    description:
      - A URI to the LDAP server.
      - The default value lets the underlying LDAP client library look for a UNIX domain socket in its default location.
    type: str
    default: ldapi:///
  start_tls:
    description:
      - If true, we'll use the START_TLS LDAP extension.
    type: bool
    default: no
  validate_certs:
    description:
      - If set to C(no), SSL certificates will not be validated.
      - This should only be used on sites using self-signed certificates.
    type: bool
    default: yes
    version_added: "2.4"
'''
