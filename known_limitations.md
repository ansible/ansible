# tacp_instance Ansible module

## Known Limitations

### Major:
- only able to create shutdown VMs, need to add other power states
- only supports the base vNIC that comes with the template
    - Set static MAC address
- disk size input doesn't do anything right now, the disk size is baked into the template at the moment
    - change the disk in the vm once it has been created, before finishing the play
- need to add fields
    - Description
    - firewall options to vnic
    - options for other settings
    - tags 
    - compute constraints
    - Instancemode 
- No graceful failure for incorrect storage pool, datacenter, mz, etc.
- Monolithic code, need to move utility functions that will be shared among 
    tacp_instance/tacp_info/other? modules into module_utils/
- Add fixed mac address to vnics

# tacp_info


# tacp_vnet 
VNET static bindings



Bin Depdendencies 
- Static MAC address
- Attach two vNICs at creation
- Look into attaching ISO to VM from REST API 
