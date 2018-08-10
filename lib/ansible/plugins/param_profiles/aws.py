# (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

def parameterize(squashed_vars, task_params):
    params = dict((k, v) for k, v in task_params.items())
    if 'aws_profile' in squashed_vars and 'profile' not in task_params:
        params['profile'] = squashed_vars['aws_profile']
    if 'aws_region' in squashed_vars and 'region' not in task_params:
        params['region'] = squashed_vars['aws_region']
    return params
