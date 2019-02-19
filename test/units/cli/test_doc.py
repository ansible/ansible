# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.cli.doc import DocCLI


def test_parsing_all_option():
    doc_cli = DocCLI(['/n/ansible-doc', '-a'])
    doc_cli.parse()
