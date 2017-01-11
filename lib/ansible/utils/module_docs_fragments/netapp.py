#
# (c) 2016, Sumit Kumar <sumit4@netapp.com>
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


class ModuleDocFragment(object):

    DOCUMENTATION = """
options:
  - See respective platform section for more details
requirements:
  - See respective platform section for more details
notes:
  - Ansible modules are available for the following NetApp Storage Platforms: E-Series, ONTAP, SolidFire
"""
    # Documentation fragment including attributes for E-Series/SANtricity
    SANTRICITY = """
options:
  - See respective modules for more details
requirements:
  - SANtricity Web Services Proxy*|1.4 or 2.0|
  - Ansible 2.2**
  - \* Not required for *E2800 with 11.30 OS*<br/>
  - \*\*The modules where developed with this version. Ansible forward and backward compatibility applies.

notes:
  - The modules prefixed with *netapp\_e* are built to support the SANtricity storage platform.
  - They require the SANtricity WebServices Proxy.
  - The WebServices Proxy is free software available at the [NetApp Software Download site](http://mysupport.netapp.com/NOW/download/software/eseries_webservices/1.40.X000.0009/).
  - Starting with the E2800 platform (11.30 OS), the modules will work directly with the storage array. Starting with this platform, REST API requests are handled directly on the box. This array can still be managed by proxy for large scale deployments.
  - The modules provide idempotent provisioning for volume groups, disk pools, standard volumes, thin volumes, LUN mapping,
    hosts, host groups (clusters), volume snapshots, consistency groups, and asynchronous mirroring.

"""
