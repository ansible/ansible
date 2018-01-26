# Proposal: Add the ability to use route targets in the ios_vrf module.

*Author*: Trebuchet Clement <@clementtrebuchet> IRC: handle (if different)

*Date*: 2017/12/26

- Status: New
- Proposal type: core design
- Targeted Release: 2.5
- Associated PR: https://github.com/ansible/ansible/pull/34248
- Estimated time to implement: one day


## Motivation
- Add the ability for the ios_vrf module to apply route targets to a VRF to control the import and export of routes between other VRFs.

### Problems
What problems exist that this proposal will solve?
- The ios_vrf module can not configure route targets

## Solution proposal
- Creates a route-target extended community for a VRF.

  - The route_import keyword specifies to import routing information from the target VPN extended community.
  - The route_export keyword specifies to export routing information to the target VPN extended community.
  - The route_both keyword specifies to import both import and export routing information to the target VPN extended community.
  - The route-target-ext-community argument adds the route-target extended community attributes to the VRF’s list of import, export, or both (import and export) 


```yaml

---
- hosts: all
  gather_facts: no
  connection: local
  vars_files:
     - group_vars/all
  tasks:
  - name: Set the test provider
    set_fact:
     provider:
      host: "{{ inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      authorize: yes
      auth_pass: "{{ auth_pass }}"
      timeout: 30


  - name: Add Test_vrf
    ios_vrf:
      name: Test_vrf
      rd: 2:100
      route_both:
       - 2:100
       - 3:100
      provider: "{{ provider }}"


  - name: Add Test_vrf1
    ios_vrf:
      name: Test_vrf1
      rd: 1:100
      route_export:
        - 1:100
        - 3:100
      route_import:
        - 1:100
        - 3:100
      provider: "{{ provider }}"

  - name: Add interface Ethernet0/2
    ios_vrf:
      name: Test_vrf1
      interfaces:
        - Ethernet0/2
      provider: "{{ provider }}"
```

```bash
    (venv) [clement@clemo vrf_playbooks]$ ansible-playbook -i hosts export_import_both.yml 

    PLAY [all] *********************************************************************************************************************************************************************
    
    TASK [Set the test provider] ***************************************************************************************************************************************************
    ok: [30.1.0.31]
    
    TASK [Add Test_vrf] ************************************************************************************************************************************************************
    changed: [30.1.0.31]
    
    TASK [Add Test_vrf1] ***********************************************************************************************************************************************************
    changed: [30.1.0.31]
    
    TASK [Add interface Ethernet0/2] ***********************************************************************************************************************************************
    ok: [30.1.0.31]
    
    PLAY RECAP *********************************************************************************************************************************************************************
    30.1.0.31                  : ok=4    changed=2    unreachable=0    failed=0   

```

```bash
clementroutertest> sh ip vrf      
  Name                             Default RD            Interfaces
  Test_vrf                         2:100                 
  Test_vrf1                        1:100                 Et0/2
  management                       <not set>             Et0/3
  reseau_priv_001                  6500:1                Et0/1.1401
  reseau_priv_002                  6500:20               Et0/1.1402

clementroutertest> sh ip vrf detail 
VRF Test_vrf (VRF Id = 8); default RD 2:100; default VPNID <not set>
  New CLI format, supports multiple address-families
  Flags: 0x180C
  No interfaces
Address family ipv4 unicast (Table ID = 0x8):
  Flags: 0x0
  Export VPN route-target communities
    RT:2:100                 RT:3:100                
  Import VPN route-target communities
    RT:2:100                 RT:3:100                
  No import route-map
  No global export route-map
  No export route-map
  VRF label distribution protocol: not configured
  VRF label allocation mode: per-prefix

VRF Test_vrf1 (VRF Id = 7); default RD 1:100; default VPNID <not set>
  New CLI format, supports multiple address-families
  Flags: 0x180C
  Interfaces:
    Et0/2                   
Address family ipv4 unicast (Table ID = 0x7):
  Flags: 0x0
  Export VPN route-target communities
    RT:1:100                 RT:3:100                
  Import VPN route-target communities
    RT:1:100                 RT:3:100                
  No import route-map
  No global export route-map
  No export route-map
  VRF label distribution protocol: not configured
  VRF label allocation mode: per-prefix

```

## Testing (optional)
- unittest and functional tests are welcomed.

```xml
<testcase classname="test.units.modules.network.ios.test_ios_vrf.TestIosVrfModule" file="test/units/modules/network/ios/test_ios_vrf.py" line="127" name="test_ios_vrf_route_both" time="10.020341157913208"/>
<testcase classname="test.units.modules.network.ios.test_ios_vrf.TestIosVrfModule" file="test/units/modules/network/ios/test_ios_vrf.py" line="145" name="test_ios_vrf_route_both_exclusive" time="0.008541107177734375"/>
<testcase classname="test.units.modules.network.ios.test_ios_vrf.TestIosVrfModule" file="test/units/modules/network/ios/test_ios_vrf.py" line="139" name="test_ios_vrf_route_export" time="10.025418043136597"/>
<testcase classname="test.units.modules.network.ios.test_ios_vrf.TestIosVrfModule" file="test/units/modules/network/ios/test_ios_vrf.py" line="133" name="test_ios_vrf_route_import"
```

## Documentation (optional)
- Documentation would be welcomed.