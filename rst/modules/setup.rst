.. _setup:

setup
`````

This module is automatically called by playbooks to gather useful variables about remote hosts that can be used
in playbooks.  It can also be executed directly by /usr/bin/ansible to check what variables are available
to a host.

Ansible provides many 'facts' about the system, automatically.

Some of the variables that are supplied are listed below.  These in particular
are from a VMWare Fusion 4 VM running CentOS 6.2::

  "ansible_facts": {
        "ansible_all_ipv4_addresses": [
            "192.168.144.180", 
            "192.168.122.1"
        ], 
        "ansible_all_ipv6_addresses": [
            "ffff::fff:ffff:ffff:ffff"
        ], 
        "ansible_architecture": "x86_64", 
        "ansible_bios_date": "06/02/2011", 
        "ansible_bios_version": "6.00", 
        "ansible_default_ipv4": {
            "address": "192.168.144.180", 
            "alias": "eth0", 
            "gateway": "192.168.144.2", 
            "interface": "eth0", 
            "macaddress": "AA:BB:CC:DD:EE:FF",
            "mtu": "1500", 
            "netmask": "255.255.255.0", 
            "network": "192.168.144.0", 
            "type": "ether"
        }, 
        "ansible_default_ipv6": {}, 
        "ansible_distribution": "CentOS", 
        "ansible_distribution_release": "Final", 
        "ansible_distribution_version": "6.2", 
        "ansible_eth0": {
            "device": "eth0", 
            "ipv4": {
                "address": "192.168.144.180", 
                "netmask": "255.255.255.0", 
                "network": "192.16.144.0"
            }, 
            "ipv6": [
                {
                    "address": "ffff::fff:ffff:ffff:ffff", 
                    "prefix": "64", 
                    "scope": "link"
                }
            ], 
            "macaddress": "00:0c:29:b6:a2:62", 
            "mtu": "1500", 
            "type": "ether"
        }, 
        "ansible_form_factor": "Other", 
        "ansible_fqdn": "localhost.localdomain", 
        "ansible_hostname": "localhost", 
        "ansible_interfaces": [
            "lo", 
            "virbr0", 
            "eth0"
        ], 
        "ansible_kernel": "2.6.32-220.2.1.el6.x86_64", 
        "ansible_lo": {
            "device": "lo", 
            "ipv4": {
                "address": "127.0.0.1", 
                "netmask": "255.0.0.0", 
                "network": "127.0.0.0"
            }, 
            "ipv6": [
                {
                    "address": "::1", 
                    "prefix": "128", 
                    "scope": "host"
                }
            ], 
            "macaddress": "00:00:00:00:00:00", 
            "mtu": "16436", 
            "type": "loopback"
        }, 
        "ansible_machine": "x86_64", 
        "ansible_memfree_mb": 166, 
        "ansible_memtotal_mb": 993, 
        "ansible_processor": [
            "Intel(R) Core(TM) i7-2677M CPU @ 1.80GHz"
        ], 
        "ansible_processor_cores": "NA", 
        "ansible_processor_count": 1, 
        "ansible_product_name": "VMware Virtual Platform", 
        "ansible_product_serial": "REDACTED",
        "ansible_product_uuid": "REDACTED",
        "ansible_product_version": "None", 
        "ansible_python_version": "2.6.6", 
        "ansible_selinux": {
            "config_mode": "enforcing", 
            "mode": "permissive", 
            "policyvers": 24, 
            "status": "enabled", 
            "type": "targeted"
        }, 
        "ansible_ssh_host_key_dsa_public": "REDACTED",
        "ansible_ssh_host_key_rsa_public": "REDACTED",
        "ansible_swapfree_mb": 1933, 
        "ansible_swaptotal_mb": 2015, 
        "ansible_system": "Linux", 
        "ansible_system_vendor": "VMware, Inc.", 
        "ansible_virbr0": {
            "device": "virbr0", 
            "ipv4": {
                "address": "192.168.122.1", 
                "netmask": "255.255.255.0", 
                "network": "192.168.122.0"
            }, 
            "macaddress": "AA:BB:CC:DD:EE:FF",
            "mtu": "1500", 
            "type": "ether"
        }, 
        "ansible_virtualization_role": "guest", 
        "ansible_virtualization_type": "VMware", 

More ansible facts will be added with successive releases.

If facter or ohai are installed, variables from these programs will
also be snapshotted into the JSON file for usage in templating. These
variables are prefixed with ``facter_`` and ``ohai_`` so it's easy to
tell their source.

All variables are bubbled up to the caller.  Using the ansible facts and choosing
to not install facter and ohai means you can avoid ruby-dependencies
on your remote systems.

Example action from `/usr/bin/ansible`::

    ansible testserver -m setup
