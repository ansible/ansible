# Copyright 2013 Dale Sedivec
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# prune@lecentre.net - 20150813

from __future__ import absolute_import
from ansible import errors
import os
import hashlib

def to_ssha (term):
    """ This filter transform a term in a  SSHA value
        It is used to compute LDAP passwords
        Usage:
          set_fact: ldap_user_password="{{ ldap_clear_user_password|ssha }}"

    """
    salt = os.urandom(4)
    sha = hashlib.sha1(term)
    sha.update(salt)
    digest_salt_b64 = '{}{}'.format(sha.digest(), salt).encode('base64').strip()

    return '{{SSHA}}{}'.format(digest_salt_b64)

class FilterModule(object):
    ''' Ansible ssha jinja2 filters '''

    def filters(self):
        return {
            # ssha password encoding
            'to_ssha' : to_ssha,

        }
