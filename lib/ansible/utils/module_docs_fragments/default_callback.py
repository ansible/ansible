# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    DOCUMENTATION = """
    options:
      show_skipped_hosts:
        name: Show skipped hosts
        description: "Toggle to control displaying skipped task/host results in a task"
        default: True
        env:
          - name: DISPLAY_SKIPPED_HOSTS
        ini:
          - key: display_skipped_hosts
            section: defaults
        type: boolean
      show_custom_stats:
        name: Show custom stats
        description: 'This adds the custom stats set via the set_stats plugin to the play recap'
        default: False
        env:
          - name: ANSIBLE_SHOW_CUSTOM_STATS
        ini:
          - key: show_custom_stats
            section: defaults
        type: bool
"""
