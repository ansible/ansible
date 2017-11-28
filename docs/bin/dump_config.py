#!/usr/bin/env python

import optparse
import os
import sys
import yaml

from jinja2 import Environment, FileSystemLoader

DEFAULT_TEMPLATE_FILE = 'config.rst.j2'


def generate_parser():
    p = optparse.OptionParser(
        version='%prog 1.0',
        usage='usage: %prog [options]',
        description='Generate module documentation from metadata',
    )
    p.add_option("-t", "--template-file", action="store", dest="template_file", default=DEFAULT_TEMPLATE_FILE, help="directory containing Jinja2 templates")
    p.add_option("-o", "--output-dir", action="store", dest="output_dir", default='/tmp/', help="Output directory for rst files")
    p.add_option("-d", "--docs-source", action="store", dest="docs", default=None, help="Source for attribute docs")

    (options, args) = p.parse_args()

    return p


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


def main(args):

    parser = generate_parser()
    (options, args) = parser.parse_args()

    output_dir = os.path.abspath(options.output_dir)
    template_file_full_path = os.path.abspath(options.template_file)
    template_file = os.path.basename(template_file_full_path)
    template_dir = os.path.dirname(os.path.abspath(template_file_full_path))

    if options.docs:
        with open(options.docs) as f:
            docs = yaml.safe_load(f)
    else:
        docs = {}

    config_options = docs
    config_options = fix_description(config_options)

    env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True,)
    template = env.get_template(template_file)
    output_name = os.path.join(output_dir, template_file.replace('.j2', ''))
    temp_vars = {'config_options': config_options}

    with open(output_name, 'wb') as f:
        f.write(template.render(temp_vars).encode('utf-8'))

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[:]))
