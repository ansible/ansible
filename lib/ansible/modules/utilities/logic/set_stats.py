#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016 Ansible RedHat, Inc
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
author: "Brian Coca (@bcoca)"
module: set_stats
short_description: Set stats for the current ansible run
description:
     - This module allows setting/accumulating stats on the current ansible run, either per host of for all hosts in the run.
options:
  data:
    description:
      - A dictionary of which each key represents a stat (or variable) you want to keep track of
    required: true
  per_host:
    description:
        - boolean that indicates if the stats is per host or for all hosts in the run.
    required: no
    default: no
  aggregate:
    description:
        - boolean that indicates if the provided value is aggregated to the existing stat C(yes) or will replace it C(no)
    required: no
    default: yes
version_added: "2.3"
'''

EXAMPLES = '''
# Aggregating packages_installed stat per host
- set_stats:
    data:
      packages_installed: 31

# Aggregating random stats for all hosts using complex arguments
- set_stats:
    data:
      one_stat: 11
      other_stat: "{{ local_var * 2 }}"
      another_stat: "{{ some_registered_var.results | map(attribute='ansible_facts.some_fact') | list }}"
    per_host: no


# setting stats (not aggregating)
- set_stats:
    data:
      the_answer: 42
    aggregate: no
'''
