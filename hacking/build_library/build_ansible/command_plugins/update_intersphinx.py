# -*- coding: utf-8 -*-
# (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import argparse
import importlib
import os
import pathlib
import time
import urllib.parse

from collections import defaultdict

from ansible.module_utils.common.collections import is_iterable
from ansible.module_utils.urls import Request

# Pylint doesn't understand Python3 namespace modules.
from ..commands import Command  # pylint: disable=relative-beyond-top-level
from .. import errors  # pylint: disable=relative-beyond-top-level


EXAMPLE_CONF = """
A proper intersphinx_mapping entry should look like:
    intersphinx_mapping = {
        'python3': ('https://docs.python.org/3', (None, 'python3.inv'))
    }

See the intersphinx docs for more info:
    https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#confval-intersphinx_mapping
"""


class UpdateIntersphinxCache(Command):
    name = 'update-intersphinx-cache'

    @classmethod
    def init_parser(cls, add_parser):
        parser = add_parser(cls.name, description='Update cached intersphinx mappings.  This'
                            ' updates the cached intersphinx mappings for docs to reference'
                            ' documentation from other projects.')
        parser.add_argument('-o', '--output-dir', action='store',
                            help='Path to directory the cached objects.inv files are stored in')
        parser.add_argument('-c', '--conf-file', action='store',
                            help='Path to a sphinx config file to retrieve intersphinx config from')

    @staticmethod
    def main(args):
        # Retrieve the intersphinx information from the sphinx config file
        conf_dir = pathlib.Path(args.conf_file).parent

        conf_module_spec = importlib.util.spec_from_file_location('sphinxconf', args.conf_file)
        conf_module = importlib.util.module_from_spec(conf_module_spec)
        conf_module_spec.loader.exec_module(conf_module)
        intersphinx_mapping = conf_module.intersphinx_mapping

        for intersphinx_name, inventory in intersphinx_mapping.items():
            if not is_iterable(inventory) or len(inventory) != 2:
                print('WARNING: The intersphinx entry for {0} must be'
                      ' a two-tuple.\n{1}'.format(intersphinx_name, EXAMPLE_CONF))
                continue

            url = cache_file = None
            for inv_source in inventory:
                if isinstance(inv_source, str) and url is None:
                    url = inv_source
                elif is_iterable(inv_source) and cache_file is None:
                    if len(inv_source) != 2:
                        print('WARNING: The fallback entry for {0} should be a tuple of (None,'
                              ' filename).\n{1}'.format(intersphinx_name, EXAMPLE_CONF))
                        continue
                    cache_file = inv_source[1]
                else:
                    print('WARNING: The configuration for {0} should be a tuple of one url and one'
                          ' tuple for a fallback filename.\n{1}'.format(intersphinx_name,
                                                                        EXAMPLE_CONF))
                    continue

            if url is None or cache_file is None:
                print('WARNING: Could not figure out the url or fallback'
                      ' filename for {0}.\n{1}'.format(intersphinx_name, EXAMPLE_CONF))
                continue

            url = urllib.parse.urljoin(url, 'objects.inv')
            # Resolve any relative cache files to be relative to the conf file
            cache_file = conf_dir / cache_file

            # Retrieve the inventory and cache it
            # The jinja CDN seems to be blocking the default urllib User-Agent
            requestor = Request(headers={'User-Agent': 'Definitely Not Python ;-)'})
            with requestor.open('GET', url) as source_file:
                with open(cache_file, 'wb') as f:
                    f.write(source_file.read())

        print('Download of new cache files complete.  Remember to git commit -a the changes')

        return 0
