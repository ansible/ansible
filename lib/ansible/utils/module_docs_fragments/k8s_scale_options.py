#
#  Copyright 2018 Red Hat | Ansible
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

# Options used by scale modules.


class ModuleDocFragment(object):

    DOCUMENTATION = '''
options:
  replicas:
    description:
      - The desired number of replicas.
  current_replicas:
    description:
      - For Deployment, ReplicaSet, Replication Controller, only scale, if the number of existing replicas
        matches. In the case of a Job, update parallelism only if the current parallelism value matches.
    type: int
  resource_version:
    description:
      - Only attempt to scale, if the current object version matches.
    type: str
  wait:
    description:
      - For Deployment, ReplicaSet, Replication Controller, wait for the status value of I(ready_replicas) to change
        to the number of I(replicas). In the case of a Job, this option is ignored.
    type: bool
    default: true
  wait_timeout:
    description:
      - When C(wait) is I(True), the number of seconds to wait for the I(ready_replicas) status to equal  I(replicas).
        If the status is not reached within the allotted time, an error will result. In the case of a Job, this option
        is ignored.
    type: int
    default: 20
'''
