#!/usr/bin/python
# -*- coding: utf-8 -*-

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
                    'status': ['deprecated'],
                    'supported_by': 'curated'}

DOCUMENTATION = '''
---
module: ec2_facts
deprecated: Use ec2_metadata_facts instead.
short_description: Gathers facts (instance metadata) about remote hosts within ec2
version_added: "1.0"
author:
    - Silviu Dicu (@silviud)
    - Vinay Dandekar (@roadmapper)
description:
    - This module fetches data from the instance metadata endpoint in ec2 as per
      http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html.
      The module must be called from within the EC2 instance itself.
notes:
    - Parameters to filter on ec2_metadata_facts may be added later.
'''

from ec2_metadata_facts import *

if __name__ == '__main__':
    main()
