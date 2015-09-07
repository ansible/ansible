# -*- coding: utf-8 -*-
# (c) 2015, Taneli Leppä <rosmo@rosmo.fi>
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
#
# Based of ipaddr.py filter

from functools import partial
try:
    import pyotp
except ImportError:
    # in this case, we'll make the filters return error messages (see bottom)
    pyotp = None

from ansible import errors

def _need_pyotp(f_name, *args, **kwargs):
    raise errors.AnsibleFilterError('The {0} filter requires PyOTP be'
            ' installed on the ansible controller'.format(f_name))

def totp_token(value):
    ''' Generate a TOTP '''
    _otp = pyotp.TOTP(value)
    return _otp.now()

def hotp_token(value, at = 0):
    ''' Generate a HOTP '''
    _otp = pyotp.HOTP(value)
    return _otp.at(at)

class FilterModule(object):
    ''' Generate One Time Password tokens '''
    filter_map =  {
        'totp_token': totp_token,
        'hotp_token': hotp_token
    }

    def filters(self):
        if pyotp:
            return self.filter_map
        else:
            # Need to install python-netaddr for these filters to work
            return dict((f, partial(_need_pyotp, f)) for f in self.filter_map)
