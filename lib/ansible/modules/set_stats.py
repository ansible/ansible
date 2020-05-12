#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Ansible RedHat, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: set_stats
short_description: Set stats for the current ansible run
description:
     - This module allows setting/accumulating stats on the current ansible run, either per host or for all hosts in the run.
     - This module is also supported for Windows targets.
author: Brian Coca (@bcoca)
options:
  data:
    description:
      - A dictionary of which each key represents a stat (or variable) you want to keep track of.
    type: dict
    required: true
  per_host:
    description:
        - whether the stats are per host or for all hosts in the run.
    type: bool
    default: no
  aggregate:
    description:
        - Whether the provided value is aggregated to the existing stat C(yes) or will replace it C(no).
    type: bool
    default: yes
notes:
    - In order for custom stats to be displayed, you must set C(show_custom_stats) in C(ansible.cfg) or C(ANSIBLE_SHOW_CUSTOM_STATS) to C(yes).
    - This module is also supported for Windows targets.
version_added: "2.3"
'''

EXAMPLES = r'''
- name: Aggregating packages_installed stat per host
  set_stats:
    data:
      packages_installed: 31
    per_host: yes

- name: Aggregating random stats for all hosts using complex arguments
  set_stats:
    data:
      one_stat: 11
      other_stat: "{{ local_var * 2 }}"
      another_stat: "{{ some_registered_var.results | map(attribute='ansible_facts.some_fact') | list }}"
    per_host: no


- name: Setting stats (not aggregating)
  set_stats:
    data:
      the_answer: 42
    aggregate: no
'''
