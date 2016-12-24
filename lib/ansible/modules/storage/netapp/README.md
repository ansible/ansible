#NetApp Storage Modules
This directory contains modules that support the storage platforms in the NetApp portfolio.

##SANtricity Modules
The modules prefixed with *netapp\_e* are built to support the SANtricity storage platform.  They require the SANtricity 
WebServices Proxy.  The WebServices Proxy is free software available at the [NetApp Software Download site](http://mysupport.netapp.com/NOW/download/software/eseries_webservices/1.40.X000.0009/).
Starting with the E2800 platform (11.30 OS), the modules will work directly with the storage array.  Starting with this
platform, REST API requests are handled directly on the box.  This array can still be managed by proxy for large scale deployments.
The modules provide idempotent provisioning for volume groups, disk pools, standard volumes, thin volumes, LUN mapping, 
hosts, host groups (clusters), volume snapshots, consistency groups, and asynchronous mirroring.
### Prerequisites
| Software | Version |
| -------- |:-------:|
| SANtricity Web Services Proxy*|1.4 or 2.0|
| Ansible | 2.2** |
\* Not required for *E2800 with 11.30 OS*<br/>
\*\*The modules where developed with this version.  Ansible forward and backward compatibility applies.

###Questions and Contribution
Please feel free to submit pull requests with improvements.  Issues for these modules should be routed to @hulquest but 
we also try to keep an eye on the list for issues specific to these modules.  General questions can be made to our [development team](mailto:ng-hsg-engcustomer-esolutions-support@netapp.com)

### Examples
These examples are not comprehensive but are intended to help you get started when integrating storage provisioning into 
your playbooks.
```yml
- name: NetApp Test All Modules
  hosts: proxy20
  gather_facts: yes
  connection: local
  vars:
    storage_systems:
      ansible1:
        address1: "10.251.230.41"
        address2: "10.251.230.42"
      ansible2:
        address1: "10.251.230.43"
        address2: "10.251.230.44"
      ansible3:
        address1: "10.251.230.45"
        address2: "10.251.230.46"
      ansible4:
        address1: "10.251.230.47"
        address2: "10.251.230.48"
    storage_pools:
      Disk_Pool_1:
        raid_level: raidDiskPool
        criteria_drive_count: 11
      Disk_Pool_2:
        raid_level: raidDiskPool
        criteria_drive_count: 11
      Disk_Pool_3:
        raid_level: raid0
        criteria_drive_count: 2
    volumes:
        vol_1:
          storage_pool_name: Disk_Pool_1
          size: 10
          thin_provision: false
          thin_volume_repo_size: 7
        vol_2:
          storage_pool_name: Disk_Pool_2
          size: 10
          thin_provision: false
          thin_volume_repo_size: 7
        vol_3:
          storage_pool_name: Disk_Pool_3
          size: 10
          thin_provision: false
          thin_volume_repo_size: 7
        thin_vol_1:
          storage_pool_name: Disk_Pool_1
          size: 10
          thin_provision: true
          thin_volume_repo_size: 7
    hosts:
      ANSIBLE-1:
        host_type: 1
        index: 1
        ports:
          - type: 'fc'
            label: 'fpPort1'
            port: '2100000E1E191B01'

    netapp_api_host: 10.251.230.29
    netapp_api_url: http://{{ netapp_api_host }}/devmgr/v2
    netapp_api_username: rw
    netapp_api_password: rw
    ssid: ansible1
    auth: no
    lun_mapping: no
    netapp_api_validate_certs: False
    snapshot: no
    gather_facts: no
    amg_create: no
    remove_volume: no
    make_volume: no
    check_thins: no
    remove_storage_pool: yes
    check_storage_pool: yes
    remove_storage_system: no
    check_storage_system: yes
    change_role: no
    flash_cache: False
    configure_hostgroup: no
    configure_async_mirror: False
    configure_snapshot: no
    copy_volume: False
    volume_copy_source_volume_id:
    volume_destination_source_volume_id:
    snapshot_volume_storage_pool_name: Disk_Pool_3
    snapshot_volume_image_id: 3400000060080E5000299B640063074057BC5C5E
    snapshot_volume: no
    snapshot_volume_name: vol_1_snap_vol
    host_type_index: 1
    host_name: ANSIBLE-1
    set_host: no
    remove_host: no
    amg_member_target_array:
    amg_member_primary_pool:
    amg_member_secondary_pool:
    amg_member_primary_volume:
    amg_member_secondary_volume:
    set_amg_member: False
    amg_array_name: foo
    amg_name: amg_made_by_ansible
    amg_secondaryArrayId: ansible2
    amg_sync_name: foo
    amg_sync: no

  tasks:

    - name: Get array facts
      netapp_e_facts:
        ssid: "{{ item.key }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
      with_dict: "{{ storage_systems }}"
      when: gather_facts

    - name:  Presence of storage system
      netapp_e_storage_system:
        ssid: "{{ item.key }}"
        state: present
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
        controller_addresses:
          - "{{ item.value.address1 }}"
          - "{{ item.value.address2 }}"
      with_dict: "{{ storage_systems }}"
      when: check_storage_system

    - name: Create Snapshot
      netapp_e_snapshot_images:
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
        snapshot_group: "ansible_snapshot_group"
        state: 'create'
      when: snapshot
      
    - name: Auth Module Example
      netapp_e_auth:
        ssid: "{{ ssid }}"
        current_password: 'Infinit2'
        new_password: 'Infinit1'
        set_admin: yes
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
      when: auth

    - name: No disk groups
      netapp_e_storagepool:
        ssid: "{{ ssid }}"
        name: "{{ item }}"
        state: absent
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
        remove_volumes: yes
      with_items:
        - Disk_Pool_1
        - Disk_Pool_2
        - Disk_Pool_3
      when: remove_storage_pool

    - name: Make disk groups
      netapp_e_storagepool:
        ssid: "{{ ssid }}"
        name: "{{ item.key }}"
        state: present
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
        raid_level: "{{ item.value.raid_level }}"
        criteria_drive_count: "{{ item.value.criteria_drive_count }}"
      with_dict: " {{ storage_pools }}"
      when: check_storage_pool

    - name: No thin volume
      netapp_e_volume:
        ssid: "{{ ssid }}"
        name: NewThinVolumeByAnsible
        state: absent
        thin_provision: yes
        log_path: /tmp/volume.log
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
      when: check_thins

    - name: Make a thin volume
      netapp_e_volume:
        ssid: "{{ ssid }}"
        name: NewThinVolumeByAnsible
        state: present
        thin_provision: yes
        thin_volume_repo_size: 7
        size: 10 
        log_path: /tmp/volume.log
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
        storage_pool_name: Disk_Pool_1
      when: check_thins

    - name: Remove standard/thick volumes
      netapp_e_volume:
        ssid: "{{ ssid }}"
        name: "{{ item.key }}"
        state: absent
        log_path: /tmp/volume.log
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
      with_dict: "{{ volumes }}"
      when: remove_volume

    - name: Make a volume
      netapp_e_volume:
        ssid: "{{ ssid }}"
        name: "{{ item.key }}"
        state: present
        storage_pool_name: "{{ item.value.storage_pool_name }}"
        size: "{{ item.value.size }}"
        thin_provision: "{{ item.value.thin_provision }}"
        thin_volume_repo_size: "{{ item.value.thin_volume_repo_size }}"
        log_path: /tmp/volume.log
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
      with_dict: "{{ volumes }}"
      when: make_volume

    - name: No storage system
      netapp_e_storage_system:
        ssid: "{{ item.key }}"
        state: absent
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
      with_dict: "{{ storage_systems }}"
      when: remove_storage_system

    - name: Update the role of a storage array
      netapp_e_amg_role:
        name: "{{ amg_name }}"
        role: primary
        force: true
        noSync: true
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
      when: change_role

    - name: Flash Cache
      netapp_e_flashcache:
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
        name: SSDCacheBuiltByAnsible
      when: flash_cache

    - name: Configure Hostgroup
      netapp_e_hostgroup:
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
        state: absent
        name: "ansible-host-group"
      when: configure_hostgroup

    - name: Configure Snapshot group
      netapp_e_snapshot_group:
        ssid: "{{ ssid }}"
        state: present
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
        base_volume_name: vol_3
        name: ansible_snapshot_group
        repo_pct: 20
        warning_threshold: 85
        delete_limit: 30
        full_policy: purgepit
        storage_pool_name: Disk_Pool_3
        rollback_priority: medium
      when: configure_snapshot

    - name: Copy volume
      netapp_e_volume_copy:
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        status: present
        source_volume_id: "{{ volume_copy_source_volume_id }}"
        destination_volume_id: "{{ volume_destination_source_volume_id }}"
      when: copy_volume

    - name: Snapshot volume
      netapp_e_snapshot_volume:
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        state: present
        storage_pool_name: "{{ snapshot_volume_storage_pool_name }}"
        snapshot_image_id: "{{ snapshot_volume_image_id }}"
        name: "{{ snapshot_volume_name }}"
      when: snapshot_volume

    - name: Remove hosts
      netapp_e_host:
        ssid: "{{ ssid }}"
        state: absent
        name: "{{ item.key }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        host_type_index: "{{ host_type_index }}"
      with_dict: "{{hosts}}"
      when: remove_host

    - name: Ensure/add hosts
      netapp_e_host:
        ssid: "{{ ssid }}"
        state: present
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        name: "{{ item.key }}"
        host_type_index: "{{ item.value.index }}"
        ports:
          - type: 'fc'
            label: 'fpPort1'
            port: '2100000E1E191B01'
      with_dict: "{{hosts}}"
      when: set_host

    - name: Unmap a volume
      netapp_e_lun_mapping:
        state: absent
        ssid: "{{ ssid }}"
        lun: 2
        target: "{{ host_name }}"
        volume_name: "thin_vol_1"
        target_type: host
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
      when: lun_mapping

    - name: Map a volume
      netapp_e_lun_mapping:
        state: present
        ssid: "{{ ssid }}"
        lun: 16
        target: "{{ host_name }}"
        volume_name: "thin_vol_1"
        target_type: host
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
      when: lun_mapping

    - name: Update LUN Id
      netapp_e_lun_mapping:
        state: present
        ssid: "{{ ssid }}"
        lun: 2
        target: "{{ host_name }}"
        volume_name: "thin_vol_1"
        target_type: host
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
      when: lun_mapping

    - name: AMG removal
      netapp_e_amg:
        state: absent
        ssid: "{{ ssid }}"
        secondaryArrayId: "{{amg_secondaryArrayId}}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        new_name: "{{amg_array_name}}"
        name: "{{amg_name}}"
      when: amg_create

    - name: AMG create
      netapp_e_amg:
        state: present
        ssid: "{{ ssid }}"
        secondaryArrayId: "{{amg_secondaryArrayId}}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        new_name: "{{amg_array_name}}"
        name: "{{amg_name}}"
      when: amg_create

    - name: start AMG async
      netapp_e_amg_sync:
        name: "{{ amg_name }}"
        state: running
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
      when: amg_sync
```
