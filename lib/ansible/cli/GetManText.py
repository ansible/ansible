from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ansible.plugins.loader as plugin_loader

import datetime
import json
import os
import textwrap
import traceback
import yaml
import sys

from ansible import constants as C
from ansible import context
from ansible.cli import CLI
from ansible.cli.arguments import option_helpers as opt_help
from ansible.collections.list import list_collection_dirs, get_collection_name_from_path
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils._text import to_native
from ansible.module_utils.common._collections_compat import Container, Sequence
from ansible.module_utils.six import string_types
from ansible.parsing.metadata import extract_metadata
from ansible.parsing.plugin_docs import read_docstub
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.plugins.loader import action_loader, fragment_loader
from ansible.utils.collection_loader import set_collection_playbook_paths
from ansible.utils.display import Display
from ansible.utils.plugin_docs import BLACKLIST, get_docstring, get_versioned_doclink
sys.path.append('/ansible/cli/GetManText.py')


class GetManText:


    def __init__(self, doc, display, DocCLI):
        self.doc = doc
        self.DocCLI = DocCLI
        self.pad = display.columns * 0.20
        self.limit = max(self.display.columns - int(self.pad), 70)
        self.DocCLI.IGNORE = self.DocCLI.IGNORE + (context.CLIARGS['type'],)
        self.text = []
        self.opt_indent = "        "

    def isInstance(self):
        if isinstance(self.doc['description'], list):
            desc = " ".join(self.doc.pop('description'))
        else:
            desc = self.doc.pop('description')
        self.text.append("%s\n" % textwrap.fill(self.DocCLI.tty_ify(desc), self.limit, initial_indent=self.opt_indent,
                                           subsequent_indent=self.opt_indent))

    def isDeprecated(self):
        if 'deprecated' in self.doc and self.doc['deprecated'] is not None and len(self.doc['deprecated']) > 0:
            self.text.append("DEPRECATED: \n")
            if isinstance(self.doc['deprecated'], dict):
                if 'version' in self.doc['deprecated'] and 'removed_in' not in self.doc['deprecated']:
                    self.doc['deprecated']['removed_in'] = self.doc['deprecated']['version']
                self.text.append("\tReason: %(why)s\n\tWill be removed in: Ansible %(removed_in)s\n\tAlternatives: %(alternative)s" % 
                            self.doc.pop('deprecated'))
            else:
                self.text.append("%s" % self.doc.pop('deprecated'))
            self.text.append("\n")

        try:
            support_block = self.DocCLI.get_support_block(self.doc)
            if support_block:
                self.text.extend(support_block)
        except Exception:
            pass  # FIXME: not suported by plugins

    def isPop(self):
        if self.doc.pop('action', False):
            self.text.append("  * note: %s\n" % "This module has a corresponding action plugin.")

    def isOptions(self):
        if 'options' in self.doc and self.doc['options']:
            self.text.append("OPTIONS (= is mandatory):\n")
            self.DocCLI.add_fields(self.text, self.doc.pop('options'), self.limit, self.opt_indent)
            self.text.append('')

    def isNotes(self):
        if 'notes' in self.doc and self.doc['notes'] and len(self.doc['notes']) > 0:
            self.text.append("NOTES:")
            for note in self.doc['notes']:
                self.text.append(textwrap.fill(self.DocCLI.tty_ify(note), self.limit - 6,
                                          initial_indent=self.opt_indent[:-2] + "* ", subsequent_indent=self.opt_indent))
            self.text.append('')
            self.text.append('')
            del self.doc['notes']

    def isSeeAlso(self):
        if 'seealso' in self.doc and self.doc['seealso']:
            self.text.append("SEE ALSO:")
            for item in self.doc['seealso']:
                if 'module' in item:
                    self.text.append(textwrap.fill(self.DocCLI.tty_ify('Module %s' % item['module']),
                                self.limit - 6, initial_indent=self.opt_indent[:-2] + "* ", subsequent_indent=self.opt_indent))
                    description = item.get('description', 'The official documentation on the %s module.' % item['module'])
                    self.text.append(textwrap.fill(self.DocCLI.tty_ify(description), self.limit - 6, initial_indent=self.opt_indent + '   ', 
                                subsequent_indent=self.opt_indent + '   '))
                    self.text.append(textwrap.fill(self.DocCLI.tty_ify(get_versioned_doclink('modules/%s_module.html' % item['module'])),
                                self.limit - 6, initial_indent=self.opt_indent + '   ', subsequent_indent=self.opt_indent))
                elif 'name' in item and 'link' in item and 'description' in item:
                    self.text.append(textwrap.fill(self.DocCLI.tty_ify(item['name']),
                                self.limit - 6, initial_indent=self.opt_indent[:-2] + "* ", subsequent_indent=self.opt_indent))
                    self.text.append(textwrap.fill(self.DocCLI.tty_ify(item['description']),
                                self.limit - 6, initial_indent=self.opt_indent + '   ', subsequent_indent=self.opt_indent + '   '))
                    self.text.append(textwrap.fill(self.DocCLI.tty_ify(item['link']),
                                self.limit - 6, initial_indent=self.opt_indent + '   ', subsequent_indent=self.opt_indent + '   '))
                elif 'ref' in item and 'description' in item:
                    self.text.append(textwrap.fill(self.DocCLI.tty_ify('Ansible documentation [%s]' % item['ref']),
                                self.limit - 6, initial_indent=self.opt_indent[:-2] + "* ", subsequent_indent=self.opt_indent))
                    self.text.append(textwrap.fill(self.DocCLI.tty_ify(item['description']),
                                self.limit - 6, initial_indent=self.opt_indent + '   ', subsequent_indent=self.opt_indent + '   '))
                    self.text.append(textwrap.fill(self.DocCLI.tty_ify(get_versioned_doclink('/#stq=%s&stp=1' % item['ref'])), 
                    self.limit - 6,
                    initial_indent=self.opt_indent + '   ', subsequent_indent=self.opt_indent + '   '))

            self.text.append('')
            self.text.append('')
            del self.doc['seealso']

    def isRequirements(self):
        if 'requirements' in self.doc and self.doc['requirements'] is not None and len(self.doc['requirements']) > 0:
            req = ", ".join(self.doc.pop('requirements'))
            self.text.append("REQUIREMENTS:%s\n" % textwrap.fill(self.DocCLI.tty_ify(req), self.limit - 16, initial_indent="  ",
                        subsequent_indent=self.opt_indent))
        # Generic handler
        for k in sorted(self.doc):
            if k in self.DocCLI.IGNORE or not self.doc[k]:
                continue
            if isinstance(self.doc[k], string_types):
                self.text.append('%s: %s' % (k.upper(), textwrap.fill(self.DocCLI.tty_ify(self.doc[k]), self.limit - (len(k) + 2),
                            subsequent_indent=self.opt_indent)))
            elif isinstance(self.doc[k], (list, tuple)):
                self.text.append('%s: %s' % (k.upper(), ', '.join(self.doc[k])))
            else:
                self.text.append(self.DocCLI._dump_yaml({k.upper(): self.doc[k]}, self.opt_indent))
            del self.doc[k]
        self.text.append('')

    def isPlainText(self):
        if 'plainexamples' in self.doc and self.doc['plainexamples'] is not None:
            self.text.append("EXAMPLES:")
            self.text.append('')
            if isinstance(self.doc['plainexamples'], string_types):
                self.text.append(self.doc.pop('plainexamples').strip())
            else:
                self.text.append(yaml.dump(self.doc.pop('plainexamples'), indent=2, default_flow_style=False))
            self.text.append('')
            self.text.append('')

    def isReturnDocs(self):
        if 'returndocs' in self.doc and self.doc['returndocs'] is not None:
            self.text.append("RETURN VALUES:")
            if isinstance(self.doc['returndocs'], string_types):
                self.text.append(self.doc.pop('returndocs'))
            else:
                self.text.append(yaml.dump(self.doc.pop('returndocs'), indent=2, default_flow_style=False))
        self.text.append('')

        try:
            metadata_block = self.DocCLI.get_metadata_block(self.doc)
            if metadata_block:
                self.text.extend(metadata_block)
                self.text.append('')
        except Exception:
            pass  # metadata is optional

    def generate(self):
        GetManText.isInstance
        GetManText.isDeprecated
        GetManText.isPop
        GetManText.isOptions
        GetManText.isNotes
        GetManText.isSeeAlso
        GetManText.isRequirements
        GetManText.isPlainText
        GetManText.isReturnDocs
        return "\n".join(self.text)
