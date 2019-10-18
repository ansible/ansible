# -*- coding: utf-8 -*-

# Copyright: (c) 2018,  Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Options used by scale modules.


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
  replicas:
    description:
      - The desired number of replicas.
    type: int
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
    default: yes
  wait_timeout:
    description:
      - When C(wait) is I(True), the number of seconds to wait for the I(ready_replicas) status to equal  I(replicas).
        If the status is not reached within the allotted time, an error will result. In the case of a Job, this option
        is ignored.
    type: int
    default: 20
'''
