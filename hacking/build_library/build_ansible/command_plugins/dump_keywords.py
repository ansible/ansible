# coding: utf-8
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import importlib
import os.path
import pathlib
import re
from distutils.version import LooseVersion

import jinja2
import yaml
from jinja2 import Environment, FileSystemLoader

from ansible.module_utils._text import to_bytes

# Pylint doesn't understand Python3 namespace modules.
from ..change_detection import update_file_if_different  # pylint: disable=relative-beyond-top-level
from ..commands import Command  # pylint: disable=relative-beyond-top-level


DEFAULT_TEMPLATE_DIR = str(pathlib.Path(__file__).resolve().parents[4] / 'docs/templates')
TEMPLATE_FILE = 'playbooks_keywords.rst.j2'
PLAYBOOK_CLASS_NAMES = ['Play', 'Role', 'Block', 'Task']


def load_definitions(keyword_definitions_file):
    docs = {}
    with open(keyword_definitions_file) as f:
        docs = yaml.safe_load(f)

    return docs


def extract_keywords(keyword_definitions):
    pb_keywords = {}
    for pb_class_name in PLAYBOOK_CLASS_NAMES:
        if pb_class_name == 'Play':
            module_name = 'ansible.playbook'
        else:
            module_name = 'ansible.playbook.{0}'.format(pb_class_name.lower())
        module = importlib.import_module(module_name)
        playbook_class = getattr(module, pb_class_name, None)
        if playbook_class is None:
            raise ImportError("We weren't able to import the module {0}".format(module_name))

        # Maintain order of the actual class names for our output
        # Build up a mapping of playbook classes to the attributes that they hold
        pb_keywords[pb_class_name] = {k: v for (k, v) in playbook_class._valid_attrs.items()
                                      # Filter private attributes as they're not usable in playbooks
                                      if not v.private}

        # pick up definitions if they exist
        for keyword in tuple(pb_keywords[pb_class_name]):
            if keyword in keyword_definitions:
                pb_keywords[pb_class_name][keyword] = keyword_definitions[keyword]
            else:
                # check if there is an alias, otherwise undocumented
                alias = getattr(getattr(playbook_class, '_%s' % keyword), 'alias', None)
                if alias and alias in keyword_definitions:
                    pb_keywords[pb_class_name][alias] = keyword_definitions[alias]
                    del pb_keywords[pb_class_name][keyword]
                else:
                    pb_keywords[pb_class_name][keyword] = ' UNDOCUMENTED!! '

        # loop is really with_ for users
        if pb_class_name == 'Task':
            pb_keywords[pb_class_name]['with_<lookup_plugin>'] = (
                'The same as ``loop`` but magically adds the output of any lookup plugin to'
                ' generate the item list.')

        # local_action is implicit with action
        if 'action' in pb_keywords[pb_class_name]:
            pb_keywords[pb_class_name]['local_action'] = ('Same as action but also implies'
                                                          ' ``delegate_to: localhost``')

    return pb_keywords


def generate_page(pb_keywords, template_dir):
    env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True,)
    template = env.get_template(TEMPLATE_FILE)
    tempvars = {'pb_keywords': pb_keywords, 'playbook_class_names': PLAYBOOK_CLASS_NAMES}

    keyword_page = template.render(tempvars)
    if LooseVersion(jinja2.__version__) < LooseVersion('2.10'):
        # jinja2 < 2.10's indent filter indents blank lines.  Cleanup
        keyword_page = re.sub(' +\n', '\n', keyword_page)

    return keyword_page


class DocumentKeywords(Command):
    name = 'document-keywords'

    @classmethod
    def init_parser(cls, add_parser):
        parser = add_parser(cls.name, description='Generate playbook keyword documentation from'
                            ' code and descriptions')
        parser.add_argument("-T", "--template-dir", action="store", dest="template_dir",
                            default=DEFAULT_TEMPLATE_DIR,
                            help="directory containing Jinja2 templates")
        parser.add_argument("-o", "--output-dir", action="store", dest="output_dir",
                            default='/tmp/', help="Output directory for rst files")
        parser.add_argument("keyword_defs", metavar="KEYWORD-DEFINITIONS.yml", type=str,
                            help="Source for playbook keyword docs")

    @staticmethod
    def main(args):
        keyword_definitions = load_definitions(args.keyword_defs)
        pb_keywords = extract_keywords(keyword_definitions)

        keyword_page = generate_page(pb_keywords, args.template_dir)
        outputname = os.path.join(args.output_dir, TEMPLATE_FILE.replace('.j2', ''))
        update_file_if_different(outputname, to_bytes(keyword_page))

        return 0
