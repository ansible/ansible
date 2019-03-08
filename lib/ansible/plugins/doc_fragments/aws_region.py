# -*- coding: utf-8 -*-

# Copyright: (c) 2017,  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Plugin option for AWS region
    DOCUMENTATION = r'''
options:
  region:
    description: The region for which to create the connection.
    type: str
    env:
      - name: EC2_REGION
      - name: AWS_REGION
'''
