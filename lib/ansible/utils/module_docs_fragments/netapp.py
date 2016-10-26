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

    # Documentation fragment for ONTAP
    ONTAP = """
options:
  hostname:
      required: true
      description:
      - The hostname or IP address of the ONTAP instance.
  username:
      required: true
      description:
      - Username
  password:
      required: true
      description:
      - Password

requirements:
  - A physical or virtual clustered Data ONTAP system. The modules were developed with Clustered Data ONTAP 8.3
  - Ansible 2.2
  - netapp-lib (2015.9.25). Install using 'pip install netapp-lib'

notes:
  - The modules prefixed with C(netapp\_cdot) are built to support the ONTAP storage platform.

example:
    - name: NetApp Sample Playbook
      hosts: localhost
      gather_facts: no
      connection: local
      vars:
        netapp_hostname: # Your hostname
        netapp_username: # Username
        netapp_password: # Password

      tasks:
        - name: License Manager
          na_cdot_license:
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"
            remove_unused: false
            remove_expired: true
            serial_number: #################
            licenses:
              nfs: #################
              # To remove a license, use the 'remove' keyword
              # nfs: remove
              cifs: #################
              iscsi: #################
              fcp: #################
              snaprestore: #################
              flexclone: #################

        - name: Aggregate Manager
          na_cdot_aggregate:
            state: absent
            name: ansibleAggr
            #new_name: ansibleAggrRenamed
            disk_count: 1
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"

        - name: SVM Manager
          na_cdot_svm:
            state: present
            name: ansibleVServer
            #new_name: ansibleVServerRenamed
            root_volume: vol1
            root_volume_aggregate: aggr1
            root_volume_security_style: mixed
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"

        - name: User Role Manager
          na_cdot_user_role:
            state: present
            name: ansibleRole
            command_directory_name: DEFAULT
            access_level: none
            vserver: ansibleVServer
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"

        - name: User Manager
          na_cdot_user:
            state: present
            name: Sample
            application: ssh
            authentication_method: password
            set_password: apn1242183u1298u41
            role_name: vsadmin
            vserver: ansibleVServer
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"

        - name: Volume Manager
          na_cdot_volume:
            state: present
            name: ansibleVolume
            #new_name: ansibleVolumeRenamed
            #is_infinite: False
            #is_online: True
            aggregate_name: aggr1
            size: 20
            size_unit: mb
            vserver: ansibleVServer
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"

        - name: QTree Manager
          na_cdot_qtree:
            state: present
            name: ansibleQTree
            #new_name: ansibleQTreeRenamed
            flexvol_name: ansibleVolume
            vserver: ansibleVServer
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"

        - name: LUN Manager
          na_cdot_lun:
            state: present
            name: ansibleLUN
            force_resize: True
            force_remove: False
            force_remove_fenced: False
            flexvol_name: ansibleVolume
            vserver: ansibleVServer
            size: 5
            size_unit: mb
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"
"""

# Documentation fragment for SolidFire
    SOLIDFIRE = """
options:
  hostname:
      required: true
      description:
      - The hostname or IP address of the SolidFire cluster
  username:
      required: true
      description:
      - Username
  password:
      required: true
      description:
      - Password

requirements:
  - solidfire-sdk-python (1.1.0.92)

notes:
  - The modules prefixed with C(sf\_) are built to support the SolidFire storage platform.

"""
