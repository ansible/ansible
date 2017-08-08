# ansible-infoblox
Awesome infobox module for ansible

## Dependencies

- Python "requests" module is required
```
sudo pip install requests
```

## Extensible Attributes

Extensible attributes are supported in this client.  It should be noted that in WAPI versions before 1.2,  the field is named "extensible_attributes", whereas in version 1.2 and later, it is named "extattrs". 

## Infoblox Version Compatibility

This gem is known to be compatible with Infoblox versions 1.0 through 2.3.  While Infoblox claims that their API is backwards-compatible, one caveat remains with the Extensible Attributes (see elsewhere in this document).  Some features are only available in newer versions (such as FixedAddress and AAAARecord).

## Usage
### Actions
- get_network [network]
- get_ipv6network [network]
- get_range [start_addr, end_addr]
- get_next_available_ip [network] | [start_addr, end_addr] 
- get_host [hostname]
- add_host [hostname, network] | [hostname, start_addr, end_addr]
- add_ipv6host [hostname, network]
- delete_host [hostname]
- set_extattr [hostname, attirbule name, attribute value]
- get_a_record [name]
- set_a_record [name, address | addresses, ttl=None] (this will change existing records if they exist)
- delete_a_record [name]

### Networks vs Ranges

get_next_available_ip and add_host can be used in either a Network or a Range on the Infoblox environment. Use the network parameter in the 192.168.1.0/24 or 192.168.1.0 format to reference a Network. Use the start_addr and end_addr parameters in the 192.168.0.1 format to reference a Range.

### Playbook example
```
---
- hosts: localhost
  connection: local
  gather_facts: False

  tasks:
    - name: "Add host"
      infoblox:
        server: 192.168.1.100
        username: admin
        password: admin
        action: add_host
        network: 192.168.1.0/24
        host: "{{ item }}"
      with_items:
        - test01.internal
        - test02.internal
      register: result

    - name: "Do awesome stuff with the result"
      debug:
        var: result
```
## Contributing

1. Fork it
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create new Pull Request
