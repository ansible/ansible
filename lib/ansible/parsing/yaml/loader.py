# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    from _yaml import CParser, CEmitter
    HAVE_PYYAML_C = True
except ImportError:
    HAVE_PYYAML_C = False

from yaml.resolver import Resolver

from ansible.parsing.yaml.constructor import AnsibleConstructor

if HAVE_PYYAML_C:

    class AnsibleLoader(CParser, AnsibleConstructor, Resolver):
        def __init__(self, stream, file_name=None, vault_secrets=None):
            CParser.__init__(self, stream)
            AnsibleConstructor.__init__(self, file_name=file_name, vault_secrets=vault_secrets)
            Resolver.__init__(self)
else:
    from yaml.composer import Composer
    from yaml.reader import Reader
    from yaml.scanner import Scanner
    from yaml.parser import Parser

    class AnsibleLoader(Reader, Scanner, Parser, Composer, AnsibleConstructor, Resolver):
        def __init__(self, stream, file_name=None, vault_secrets=None):
            Reader.__init__(self, stream)
            Scanner.__init__(self)
            Parser.__init__(self)
            Composer.__init__(self)
            AnsibleConstructor.__init__(self, file_name=file_name, vault_secrets=vault_secrets)
            Resolver.__init__(self)
