# coding: utf-8
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import os.path
import pathlib

import yaml
from jinja2 import Environment, FileSystemLoader
from ansible.module_utils._text import to_bytes

# Pylint doesn't understand Python3 namespace modules.
from ..change_detection import update_file_if_different  # pylint: disable=relative-beyond-top-level
from ..commands import Command  # pylint: disable=relative-beyond-top-level


DEFAULT_TEMPLATE_FILE = 'config.rst.j2'
DEFAULT_TEMPLATE_DIR = pathlib.Path(__file__).parents[4] / 'docs/templates'


def fix_description(config_options):
    '''some descriptions are strings, some are lists. workaround it...'''

    for config_key in config_options:
        description = config_options[config_key].get('description', [])
        if isinstance(description, list):
            desc_list = description
        else:
            desc_list = [description]
        config_options[config_key]['description'] = desc_list
    return config_options


class DocumentConfig(Command):
    name = 'document-config'

    @classmethod
    def init_parser(cls, add_parser):
        parser = add_parser(cls.name, description='Generate module documentation from metadata')
        parser.add_argument("-t", "--template-file", action="store", dest="template_file",
                            default=DEFAULT_TEMPLATE_FILE,
                            help="Jinja2 template to use for the config")
        parser.add_argument("-T", "--template-dir", action="store", dest="template_dir",
                            default=DEFAULT_TEMPLATE_DIR,
                            help="directory containing Jinja2 templates")
        parser.add_argument("-o", "--output-dir", action="store", dest="output_dir", default='/tmp/',
                            help="Output directory for rst files")
        parser.add_argument("config_defs", metavar="CONFIG-OPTION-DEFINITIONS.yml", type=str,
                            help="Source for config option docs")

    @staticmethod
    def main(args):
        output_dir = os.path.abspath(args.output_dir)
        template_file_full_path = os.path.abspath(os.path.join(args.template_dir, args.template_file))
        template_file = os.path.basename(template_file_full_path)
        template_dir = os.path.dirname(template_file_full_path)

        with open(args.config_defs) as f:
            config_options = yaml.safe_load(f)

        config_options = fix_description(config_options)

        env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True,)
        template = env.get_template(template_file)
        output_name = os.path.join(output_dir, template_file.replace('.j2', ''))
        temp_vars = {'config_options': config_options}

        data = to_bytes(template.render(temp_vars))
        update_file_if_different(output_name, data)

        return 0
