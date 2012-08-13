.. _setup:

setup
`````

This module is automatically called by playbooks to gather useful variables about remote hosts that can be used
in playbooks.  It can also be executed directly by /usr/bin/ansible to check what variables are available
to a host.

Ansible provides many 'facts' about the system, automatically.

Some of the variables that are supplied are listed below.  These in particular
are from a VMWare Fusion 4 VM running CentOS 6.2::

    "ansible_architecture": "x86_64",
    "ansible_distribution": "CentOS",
    "ansible_distribution_release": "Final",
    "ansible_distribution_version": "6.2",
    "ansible_eth0": {
        "ipv4": {
            "address": "REDACTED",
            "netmask": "255.255.255.0"
        },
        "ipv6": [
            {
                "address": "REDACTED",
                "prefix": "64",
                "scope": "link"
            }
        ],
        "macaddress": "REDACTED"
    },
    "ansible_form_factor": "Other",
    "ansible_fqdn": "localhost.localdomain",
    "ansible_hostname": "localhost",
    "ansible_interfaces": [
        "lo",
        "eth0"
    ],
    "ansible_kernel": "2.6.32-220.2.1.el6.x86_64",
    "ansible_lo": {
        "ipv4": {
            "address": "127.0.0.1",
            "netmask": "255.0.0.0"
        },
        "ipv6": [
            {
                "address": "::1",
                "prefix": "128",
                "scope": "host"
            }
        ],
    "ansible_machine": "x86_64",
    "ansible_memfree_mb": 89,
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
    "ansible_product_version": "None",
    "ansible_python_version": "2.6.6",
    "ansible_ssh_host_key_dsa_public": REDACTED",
    "ansible_ssh_host_key_rsa_public": "REDACTED",
    "ansible_swapfree_mb": 1822,
    "ansible_swaptotal_mb": 2015,
    "ansible_system": "Linux",
    "ansible_system_vendor": "VMware, Inc.",
    "ansible_virtualization_role": "None",
    "ansible_virtualization_type": "None",

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
