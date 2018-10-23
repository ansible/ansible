#
# (c) 2018, Sumit Kumar <sumit4@netapp.com>, chris Archibald <carchi@netapp.com>
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

    # Documentation fragment for ONTAP (na_ontap)
    NA_ONTAP = """
options:
  hostname:
      required: true
      description:
      - The hostname or IP address of the ONTAP instance.
  username:
      required: true
      description:
      - This can be a Cluster-scoped or SVM-scoped account, depending on whether a Cluster-level or SVM-level API is required.
        For more information, please read the documentation U(https://mysupport.netapp.com/NOW/download/software/nmsdk/9.4/).
      aliases: ['user']
  password:
      required: true
      description:
      - Password for the specified user.
      aliases: ['pass']
  https:
      description:
      - Enable and disable https
      type: bool
      default: false
  validate_certs:
      description:
      - If set to C(False), the SSL certificates will not be validated.
      - This should only set to C(False) used on personally controlled sites using self-signed certificates.
      default: true
      type: bool
  http_port:
      description:
      - Override the default port (80 or 443) with this port
      type: int


requirements:
  - A physical or virtual clustered Data ONTAP system. The modules were developed with Clustered Data ONTAP 9.3
  - Ansible 2.6
  - netapp-lib (2017.10.30). Install using 'pip install netapp-lib'
  - To enable http on the cluster you must run the following commands 'set -privilege advanced;' 'system services web modify -http-enabled true;'

notes:
  - The modules prefixed with na\\_ontap are built to support the ONTAP storage platform.

    """

    # Documentation fragment for ONTAP (na_cdot)
    ONTAP = """
options:
  hostname:
      required: true
      description:
      - The hostname or IP address of the ONTAP instance.
  username:
      required: true
      description:
      - This can be a Cluster-scoped or SVM-scoped account, depending on whether a Cluster-level or SVM-level API is required.
        For more information, please read the documentation U(https://mysupport.netapp.com/NOW/download/software/nmsdk/9.4/).
      aliases: ['user']
  password:
      required: true
      description:
      - Password for the specified user.
      aliases: ['pass']
requirements:
  - A physical or virtual clustered Data ONTAP system. The modules were developed with Clustered Data ONTAP 8.3
  - Ansible 2.2
  - netapp-lib (2015.9.25). Install using 'pip install netapp-lib'

notes:
  - The modules prefixed with na\\_cdot are built to support the ONTAP storage platform.

"""

    # Documentation fragment for SolidFire
    SOLIDFIRE = """
options:
  hostname:
      required: true
      description:
      - The hostname or IP address of the SolidFire cluster.
  username:
      required: true
      description:
      - Please ensure that the user has the adequate permissions. For more information, please read the official documentation
        U(https://mysupport.netapp.com/documentation/docweb/index.html?productID=62636&language=en-US).
      aliases: ['user']
  password:
      required: true
      description:
      - Password for the specified user.
      aliases: ['pass']

requirements:
  - The modules were developed with SolidFire 10.1
  - solidfire-sdk-python (1.1.0.92) or greater. Install using 'pip install solidfire-sdk-python'

notes:
  - The modules prefixed with na\\_elementsw are built to support the SolidFire storage platform.

"""

    # Documentation fragment for E-Series
    ESERIES = """
options:
  api_username:
    required: true
    description:
    - The username to authenticate with the SANtricity Web Services Proxy or Embedded Web Services API.
  api_password:
    required: true
    description:
    - The password to authenticate with the SANtricity Web Services Proxy or Embedded Web Services API.
  api_url:
    required: true
    description:
    - The url to the SANtricity Web Services Proxy or Embedded Web Services API.
    example:
    - https://prod-1.wahoo.acme.com/devmgr/v2
  validate_certs:
    required: false
    default: true
    description:
        - Should https certificates be validated?
    type: bool
  ssid:
    required: true
    description:
    - The ID of the array to manage. This value must be unique for each array.

notes:
  - The E-Series Ansible modules require either an instance of the Web Services Proxy (WSP), to be available to manage
    the storage-system, or an E-Series storage-system that supports the Embedded Web Services API.
  - Embedded Web Services is currently available on the E2800, E5700, EF570, and newer hardware models.
  - M(netapp_e_storage_system) may be utilized for configuring the systems managed by a WSP instance.
    """
