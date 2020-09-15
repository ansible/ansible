# coding: utf-8
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import argparse
import os.path
import sys

from jinja2 import Environment, DictLoader

# Pylint doesn't understand Python3 namespace modules.
from ..commands import Command  # pylint: disable=relative-beyond-top-level


PORTING_GUIDE_TEMPLATE = """
.. _porting_{{ ver }}_guide:

*************************
Ansible {{ ver }} Porting Guide
*************************

This section discusses the behavioral changes between Ansible {{ prev_ver }} and Ansible {{ ver }}.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for {{ ver }} <https://github.com/ansible/ansible/blob/devel/changelogs/CHANGELOG-v{{ ver }}.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics


Playbook
========

No notable changes


Command Line
============

No notable changes


Deprecated
==========

No notable changes


Modules
=======

No notable changes


Modules removed
---------------

The following modules no longer exist:

* No notable changes


Deprecation notices
-------------------

No notable changes


Noteworthy module changes
-------------------------

No notable changes


Plugins
=======

No notable changes


Porting custom scripts
======================

No notable changes


Networking
==========

No notable changes

"""  # noqa for E501 (line length).
# jinja2 is horrid about getting rid of extra newlines so we have to have a single line per
# paragraph for proper wrapping to occur

JINJA_ENV = Environment(
    loader=DictLoader({'porting_guide': PORTING_GUIDE_TEMPLATE,
                       }),
    extensions=['jinja2.ext.i18n'],
    trim_blocks=True,
    lstrip_blocks=True,
)


def generate_porting_guide(version):
    template = JINJA_ENV.get_template('porting_guide')

    version_list = version.split('.')
    version_list[-1] = str(int(version_list[-1]) - 1)
    previous_version = '.'.join(version_list)

    content = template.render(ver=version, prev_ver=previous_version)
    return content


def write_guide(version, guide_content):
    filename = 'porting_guide_{0}.rst'.format(version)
    with open(filename, 'w') as out_file:
        out_file.write(guide_content)


class PortingGuideCommand(Command):
    name = 'porting-guide'

    @classmethod
    def init_parser(cls, add_parser):
        parser = add_parser(cls.name, description="Generate a fresh porting guide template")
        parser.add_argument("--version", dest="version", type=str, required=True, action='store',
                            help="Version of Ansible to write the porting guide for")

    @staticmethod
    def main(args):
        guide_content = generate_porting_guide(args.version)
        write_guide(args.version, guide_content)
        return 0
