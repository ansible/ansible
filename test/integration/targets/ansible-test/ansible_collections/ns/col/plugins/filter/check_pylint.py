"""
These test cases verify ansible-test version constraints for pylint and its dependencies across Python versions.
The initial test cases were discovered while testing various Python versions against ansible/ansible.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

# Python 3.8 fails with astroid 2.2.5 but works on 2.3.3
#   syntax-error: Cannot import 'string' due to syntax error 'invalid syntax (&lt;unknown&gt;, line 109)'
# Python 3.9 fails with astroid 2.2.5 but works on 2.3.3
#   syntax-error: Cannot import 'string' due to syntax error 'invalid syntax (&lt;unknown&gt;, line 104)'
import string

# Python 3.9 fails with pylint 2.3.1 or 2.4.4 with astroid 2.3.3 but works with pylint 2.5.0 and astroid 2.4.0
#   'Call' object has no attribute 'value'
result = {None: None}[{}.get('something')]

# pylint 2.3.1 and 2.4.4 report the following error but 2.5.0 and 2.6.0 do not
#   blacklisted-name: Black listed name "foo"
# see: https://github.com/PyCQA/pylint/issues/3701
# regression: documented as a known issue and removed from ignore.txt so pylint can be upgraded to 2.6.0
#             if future versions of pylint fix this issue then the ignore should be restored
foo = {}.keys()
