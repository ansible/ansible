# (c) 2017 Red Hat Inc.
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

# (c) 2017 Red Hat Inc.

from ansible.modules.cloud.amazon.aws_acm import pem_compare


# TODO: hook this into the test framework
def test_pem_compare():
  
    #original
    a = """
-----BEGIN CERTIFICATE REQUEST-----
ABC123
-----END CERTIFICATE REQUEST-----
"""
    # newline in body
    b = """
-----BEGIN CERTIFICATE REQUEST-----
ABC
123
-----END CERTIFICATE REQUEST-----
"""

    # trailing space
    c = """
-----BEGIN CERTIFICATE REQUEST-----
ABC
123
-----END CERTIFICATE REQUEST-----

"""

    d = """
-----OTHER HEADER-----
ABC123
-----OTHER HEADER-----
"""
  
    # different number of dashes
    e = """
---BEGIN CERTIFICATE REQUEST---
ABC
123
---END CERTIFICATE REQUEST---
"""

    assert(pem_compare(a,b))
    
    assert(pem_compare(a,c))
    assert(pem_compare(b,c))
    
    assert(not pem_compare(a,d))
    assert(not pem_compare(b,d))
    assert(not pem_compare(c,d))
    
    assert(pem_compare(a,e))
    assert(pem_compare(b,e))
    assert(not pem_compare(d,e))
    assert(pem_compare(c,e))
    
    assert(pem_compare(None,None))
    assert(not pem_compare(None,a))
   