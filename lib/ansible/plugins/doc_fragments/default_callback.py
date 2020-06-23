# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
    options:
      display_skipped_hosts:
        name: Show skipped hosts
        description: "Toggle to control displaying skipped task/host results in a task"
        type: bool
        default: yes
        env:
          - name: DISPLAY_SKIPPED_HOSTS
            deprecated:
              why: environment variables without "ANSIBLE_" prefix are deprecated
              version: "2.12"
              alternatives: the "ANSIBLE_DISPLAY_SKIPPED_HOSTS" environment variable
          - name: ANSIBLE_DISPLAY_SKIPPED_HOSTS
        ini:
          - key: display_skipped_hosts
            section: defaults
      display_ok_hosts:
        name: Show 'ok' hosts
        description: "Toggle to control displaying 'ok' task/host results in a task"
        type: bool
        default: yes
        env:
          - name: ANSIBLE_DISPLAY_OK_HOSTS
        ini:
          - key: display_ok_hosts
            section: defaults
        version_added: '2.7'
      display_failed_stderr:
        name: Use STDERR for failed and unreachable tasks
        description: "Toggle to control whether failed and unreachable tasks are displayed to STDERR (vs. STDOUT)"
        type: bool
        default: no
        env:
          - name: ANSIBLE_DISPLAY_FAILED_STDERR
        ini:
          - key: display_failed_stderr
            section: defaults
        version_added: '2.7'
      show_custom_stats:
        name: Show custom stats
        description: 'This adds the custom stats set via the set_stats plugin to the play recap'
        type: bool
        default: no
        env:
          - name: ANSIBLE_SHOW_CUSTOM_STATS
        ini:
          - key: show_custom_stats
            section: defaults
      show_per_host_start:
        name: Show per host task start
        description: 'This adds output that shows when a task is started to execute for each host'
        type: bool
        default: no
        env:
          - name: ANSIBLE_SHOW_PER_HOST_START
        ini:
          - key: show_per_host_start
            section: defaults
        version_added: '2.9'
      check_mode_markers:
        name: Show markers when running in check mode
        description:
        - Toggle to control displaying markers when running in check mode.
        - "The markers are C(DRY RUN) at the beggining and ending of playbook execution (when calling C(ansible-playbook --check))
        and C(CHECK MODE) as a suffix at every play and task that is run in check mode."
        type: bool
        default: no
        version_added: '2.9'
        env:
          - name: ANSIBLE_CHECK_MODE_MARKERS
        ini:
          - key: check_mode_markers
            section: defaults
'''
