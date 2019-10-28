.. _playbooks_variables:

***************
Using Variables
***************

.. contents::
   :local:

While automation exists to make it easier to make things repeatable, all systems are not exactly alike; some may require configuration that is slightly different from others. In some instances, the observed behavior or state of one system might influence how you configure other systems. For example, you might need to find out the IP address of a system and use it as a configuration value on another system.

Ansible uses *variables* to help deal with differences between systems.

To understand variables you'll also want to read :ref:`playbooks_conditionals` and :ref:`playbooks_loops`.
Useful things like the **group_by** module
and the ``when`` conditional can also be used with variables, and to help manage differences between systems.

The `ansible-examples github repository <https://github.com/ansible/ansible-examples>`_ contains many examples of how variables are used in Ansible.

.. _valid_variable_names:

Creating valid variable names
=============================

Before you start using variables, it's important to know what are valid variable names.

Variable names should be letters, numbers, and underscores.  Variables should always start with a letter.

``foo_port`` is a great variable.  ``foo5`` is fine too.

``foo-port``, ``foo port``, ``foo.port`` and ``12`` are not valid variable names.

YAML also supports dictionaries which map keys to values.  For instance::

  foo:
    field1: one
    field2: two

You can then reference a specific field in the dictionary using either bracket
notation or dot notation::

  foo['field1']
  foo.field1

These will both reference the same value ("one").  However, if you choose to
use dot notation be aware that some keys can cause problems because they
collide with attributes and methods of python dictionaries.  You should use
bracket notation instead of dot notation if you use keys which start and end
with two underscores (Those are reserved for special meanings in python) or
are any of the known public attributes:

``add``, ``append``, ``as_integer_ratio``, ``bit_length``, ``capitalize``, ``center``, ``clear``, ``conjugate``, ``copy``, ``count``, ``decode``, ``denominator``, ``difference``, ``difference_update``, ``discard``, ``encode``, ``endswith``, ``expandtabs``, ``extend``, ``find``, ``format``, ``fromhex``, ``fromkeys``, ``get``, ``has_key``, ``hex``, ``imag``, ``index``, ``insert``, ``intersection``, ``intersection_update``, ``isalnum``, ``isalpha``, ``isdecimal``, ``isdigit``, ``isdisjoint``, ``is_integer``, ``islower``, ``isnumeric``, ``isspace``, ``issubset``, ``issuperset``, ``istitle``, ``isupper``, ``items``, ``iteritems``, ``iterkeys``, ``itervalues``, ``join``, ``keys``, ``ljust``, ``lower``, ``lstrip``, ``numerator``, ``partition``, ``pop``, ``popitem``, ``real``, ``remove``, ``replace``, ``reverse``, ``rfind``, ``rindex``, ``rjust``, ``rpartition``, ``rsplit``, ``rstrip``, ``setdefault``, ``sort``, ``split``, ``splitlines``, ``startswith``, ``strip``, ``swapcase``, ``symmetric_difference``, ``symmetric_difference_update``, ``title``, ``translate``, ``union``, ``update``, ``upper``, ``values``, ``viewitems``, ``viewkeys``, ``viewvalues``, ``zfill``.

.. _variables_in_inventory:

Defining variables in inventory
===============================

Often you'll want to set variables for an individual host, or for a group of hosts in your inventory. For instance, machines in Boston
may all use 'boston.ntp.example.com' as an NTP server. The :ref:`intro_inventory` page has details on setting :ref:`host_variables` and :ref:`group_variables` in inventory.

.. _playbook_variables:

Defining variables in a playbook
================================

You can define variables directly in a playbook::

   - hosts: webservers
     vars:
       http_port: 80

This can be nice as it's right there when you are reading the playbook.

.. _included_variables:

Defining variables in included files and roles
==============================================

As described in :ref:`playbooks_reuse_roles`, variables can also be included in the playbook via include files, which may or may
not be part of an Ansible Role.  Usage of roles is preferred as it provides a nice organizational system.

.. _about_jinja2:

Using variables with Jinja2
===========================

Once you've defined variables, you can use them in your playbooks using the Jinja2 templating system.  Here's a simple Jinja2 template::

    My amp goes to {{ max_amp_value }}

This expression provides the most basic form of variable substitution.

You can use the same syntax in playbooks. For example::

    template: src=foo.cfg.j2 dest={{ remote_install_path }}/foo.cfg

Here the variable defines the location of a file, which can vary from one system to another.

Inside a template you automatically have access to all variables that are in scope for a host.  Actually
it's more than that -- you can also read variables about other hosts.  We'll show how to do that in a bit.

.. note:: ansible allows Jinja2 loops and conditionals in templates, but in playbooks, we do not use them.  Ansible
   playbooks are pure machine-parseable YAML.  This is a rather important feature as it means it is possible to code-generate
   pieces of files, or to have other ecosystem tools read Ansible files.  Not everyone will need this but it can unlock
   possibilities.

.. seealso::

    :ref:`playbooks_templating`
        More information about Jinja2 templating

.. _jinja2_filters:

Transforming variables with Jinja2 filters
==========================================

Jinja2 filters let you transform the value of a variable within a template expression. For example, the ``capitalize`` filter capitalizes any value passed to it; the ``to_yaml`` and ``to_json`` filters change the format of your variable values. Jinja2 includes many `built-in filters <http://jinja.pocoo.org/docs/templates/#builtin-filters>`_ and Ansible supplies :ref:`many more filters <playbooks_filters>`.

.. _yaml_gotchas:

Hey wait, a YAML gotcha
=======================

YAML syntax requires that if you start a value with ``{{ foo }}`` you quote the whole line, since it wants to be
sure you aren't trying to start a YAML dictionary.  This is covered on the :ref:`yaml_syntax` documentation.

This won't work::

    - hosts: app_servers
      vars:
          app_path: {{ base_path }}/22

Do it like this and you'll be fine::

    - hosts: app_servers
      vars:
           app_path: "{{ base_path }}/22"

.. _vars_and_facts:

Variables discovered from systems: Facts
========================================

There are other places where variables can come from, but these are a type of variable that are discovered, not set by the user.

Facts are information derived from speaking with your remote systems. You can find a complete set under the ``ansible_facts`` variable,
most facts are also 'injected' as top level variables preserving the ``ansible_`` prefix, but some are dropped due to conflicts.
This can be disabled via the :ref:`INJECT_FACTS_AS_VARS` setting.

An example of this might be the IP address of the remote host, or what the operating system is.

To see what information is available, try the following in a play::

    - debug: var=ansible_facts

To see the 'raw' information as gathered::

    ansible hostname -m setup

This will return a large amount of variable data, which may look like this on Ansible 2.7:

.. code-block:: json

    {
        "ansible_all_ipv4_addresses": [
            "REDACTED IP ADDRESS"
        ],
        "ansible_all_ipv6_addresses": [
            "REDACTED IPV6 ADDRESS"
        ],
        "ansible_apparmor": {
            "status": "disabled"
        },
        "ansible_architecture": "x86_64",
        "ansible_bios_date": "11/28/2013",
        "ansible_bios_version": "4.1.5",
        "ansible_cmdline": {
            "BOOT_IMAGE": "/boot/vmlinuz-3.10.0-862.14.4.el7.x86_64",
            "console": "ttyS0,115200",
            "no_timer_check": true,
            "nofb": true,
            "nomodeset": true,
            "ro": true,
            "root": "LABEL=cloudimg-rootfs",
            "vga": "normal"
        },
        "ansible_date_time": {
            "date": "2018-10-25",
            "day": "25",
            "epoch": "1540469324",
            "hour": "12",
            "iso8601": "2018-10-25T12:08:44Z",
            "iso8601_basic": "20181025T120844109754",
            "iso8601_basic_short": "20181025T120844",
            "iso8601_micro": "2018-10-25T12:08:44.109968Z",
            "minute": "08",
            "month": "10",
            "second": "44",
            "time": "12:08:44",
            "tz": "UTC",
            "tz_offset": "+0000",
            "weekday": "Thursday",
            "weekday_number": "4",
            "weeknumber": "43",
            "year": "2018"
        },
        "ansible_default_ipv4": {
            "address": "REDACTED",
            "alias": "eth0",
            "broadcast": "REDACTED",
            "gateway": "REDACTED",
            "interface": "eth0",
            "macaddress": "REDACTED",
            "mtu": 1500,
            "netmask": "255.255.255.0",
            "network": "REDACTED",
            "type": "ether"
        },
        "ansible_default_ipv6": {},
        "ansible_device_links": {
            "ids": {},
            "labels": {
                "xvda1": [
                    "cloudimg-rootfs"
                ],
                "xvdd": [
                    "config-2"
                ]
            },
            "masters": {},
            "uuids": {
                "xvda1": [
                    "cac81d61-d0f8-4b47-84aa-b48798239164"
                ],
                "xvdd": [
                    "2018-10-25-12-05-57-00"
                ]
            }
        },
        "ansible_devices": {
            "xvda": {
                "holders": [],
                "host": "",
                "links": {
                    "ids": [],
                    "labels": [],
                    "masters": [],
                    "uuids": []
                },
                "model": null,
                "partitions": {
                    "xvda1": {
                        "holders": [],
                        "links": {
                            "ids": [],
                            "labels": [
                                "cloudimg-rootfs"
                            ],
                            "masters": [],
                            "uuids": [
                                "cac81d61-d0f8-4b47-84aa-b48798239164"
                            ]
                        },
                        "sectors": "83883999",
                        "sectorsize": 512,
                        "size": "40.00 GB",
                        "start": "2048",
                        "uuid": "cac81d61-d0f8-4b47-84aa-b48798239164"
                    }
                },
                "removable": "0",
                "rotational": "0",
                "sas_address": null,
                "sas_device_handle": null,
                "scheduler_mode": "deadline",
                "sectors": "83886080",
                "sectorsize": "512",
                "size": "40.00 GB",
                "support_discard": "0",
                "vendor": null,
                "virtual": 1
            },
            "xvdd": {
                "holders": [],
                "host": "",
                "links": {
                    "ids": [],
                    "labels": [
                        "config-2"
                    ],
                    "masters": [],
                    "uuids": [
                        "2018-10-25-12-05-57-00"
                    ]
                },
                "model": null,
                "partitions": {},
                "removable": "0",
                "rotational": "0",
                "sas_address": null,
                "sas_device_handle": null,
                "scheduler_mode": "deadline",
                "sectors": "131072",
                "sectorsize": "512",
                "size": "64.00 MB",
                "support_discard": "0",
                "vendor": null,
                "virtual": 1
            },
            "xvde": {
                "holders": [],
                "host": "",
                "links": {
                    "ids": [],
                    "labels": [],
                    "masters": [],
                    "uuids": []
                },
                "model": null,
                "partitions": {
                    "xvde1": {
                        "holders": [],
                        "links": {
                            "ids": [],
                            "labels": [],
                            "masters": [],
                            "uuids": []
                        },
                        "sectors": "167770112",
                        "sectorsize": 512,
                        "size": "80.00 GB",
                        "start": "2048",
                        "uuid": null
                    }
                },
                "removable": "0",
                "rotational": "0",
                "sas_address": null,
                "sas_device_handle": null,
                "scheduler_mode": "deadline",
                "sectors": "167772160",
                "sectorsize": "512",
                "size": "80.00 GB",
                "support_discard": "0",
                "vendor": null,
                "virtual": 1
            }
        },
        "ansible_distribution": "CentOS",
        "ansible_distribution_file_parsed": true,
        "ansible_distribution_file_path": "/etc/redhat-release",
        "ansible_distribution_file_variety": "RedHat",
        "ansible_distribution_major_version": "7",
        "ansible_distribution_release": "Core",
        "ansible_distribution_version": "7.5.1804",
        "ansible_dns": {
            "nameservers": [
                "127.0.0.1"
            ]
        },
        "ansible_domain": "",
        "ansible_effective_group_id": 1000,
        "ansible_effective_user_id": 1000,
        "ansible_env": {
            "HOME": "/home/zuul",
            "LANG": "en_US.UTF-8",
            "LESSOPEN": "||/usr/bin/lesspipe.sh %s",
            "LOGNAME": "zuul",
            "MAIL": "/var/mail/zuul",
            "PATH": "/usr/local/bin:/usr/bin",
            "PWD": "/home/zuul",
            "SELINUX_LEVEL_REQUESTED": "",
            "SELINUX_ROLE_REQUESTED": "",
            "SELINUX_USE_CURRENT_RANGE": "",
            "SHELL": "/bin/bash",
            "SHLVL": "2",
            "SSH_CLIENT": "REDACTED 55672 22",
            "SSH_CONNECTION": "REDACTED 55672 REDACTED 22",
            "USER": "zuul",
            "XDG_RUNTIME_DIR": "/run/user/1000",
            "XDG_SESSION_ID": "1",
            "_": "/usr/bin/python2"
        },
        "ansible_eth0": {
            "active": true,
            "device": "eth0",
            "ipv4": {
                "address": "REDACTED",
                "broadcast": "REDACTED",
                "netmask": "255.255.255.0",
                "network": "REDACTED"
            },
            "ipv6": [
                {
                    "address": "REDACTED",
                    "prefix": "64",
                    "scope": "link"
                }
            ],
            "macaddress": "REDACTED",
            "module": "xen_netfront",
            "mtu": 1500,
            "pciid": "vif-0",
            "promisc": false,
            "type": "ether"
        },
        "ansible_eth1": {
            "active": true,
            "device": "eth1",
            "ipv4": {
                "address": "REDACTED",
                "broadcast": "REDACTED",
                "netmask": "255.255.224.0",
                "network": "REDACTED"
            },
            "ipv6": [
                {
                    "address": "REDACTED",
                    "prefix": "64",
                    "scope": "link"
                }
            ],
            "macaddress": "REDACTED",
            "module": "xen_netfront",
            "mtu": 1500,
            "pciid": "vif-1",
            "promisc": false,
            "type": "ether"
        },
        "ansible_fips": false,
        "ansible_form_factor": "Other",
        "ansible_fqdn": "centos-7-rax-dfw-0003427354",
        "ansible_hostname": "centos-7-rax-dfw-0003427354",
        "ansible_interfaces": [
            "lo",
            "eth1",
            "eth0"
        ],
        "ansible_is_chroot": false,
        "ansible_kernel": "3.10.0-862.14.4.el7.x86_64",
        "ansible_lo": {
            "active": true,
            "device": "lo",
            "ipv4": {
                "address": "127.0.0.1",
                "broadcast": "host",
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
            "mtu": 65536,
            "promisc": false,
            "type": "loopback"
        },
        "ansible_local": {},
        "ansible_lsb": {
            "codename": "Core",
            "description": "CentOS Linux release 7.5.1804 (Core)",
            "id": "CentOS",
            "major_release": "7",
            "release": "7.5.1804"
        },
        "ansible_machine": "x86_64",
        "ansible_machine_id": "2db133253c984c82aef2fafcce6f2bed",
        "ansible_memfree_mb": 7709,
        "ansible_memory_mb": {
            "nocache": {
                "free": 7804,
                "used": 173
            },
            "real": {
                "free": 7709,
                "total": 7977,
                "used": 268
            },
            "swap": {
                "cached": 0,
                "free": 0,
                "total": 0,
                "used": 0
            }
        },
        "ansible_memtotal_mb": 7977,
        "ansible_mounts": [
            {
                "block_available": 7220998,
                "block_size": 4096,
                "block_total": 9817227,
                "block_used": 2596229,
                "device": "/dev/xvda1",
                "fstype": "ext4",
                "inode_available": 10052341,
                "inode_total": 10419200,
                "inode_used": 366859,
                "mount": "/",
                "options": "rw,seclabel,relatime,data=ordered",
                "size_available": 29577207808,
                "size_total": 40211361792,
                "uuid": "cac81d61-d0f8-4b47-84aa-b48798239164"
            },
            {
                "block_available": 0,
                "block_size": 2048,
                "block_total": 252,
                "block_used": 252,
                "device": "/dev/xvdd",
                "fstype": "iso9660",
                "inode_available": 0,
                "inode_total": 0,
                "inode_used": 0,
                "mount": "/mnt/config",
                "options": "ro,relatime,mode=0700",
                "size_available": 0,
                "size_total": 516096,
                "uuid": "2018-10-25-12-05-57-00"
            }
        ],
        "ansible_nodename": "centos-7-rax-dfw-0003427354",
        "ansible_os_family": "RedHat",
        "ansible_pkg_mgr": "yum",
        "ansible_processor": [
            "0",
            "GenuineIntel",
            "Intel(R) Xeon(R) CPU E5-2670 0 @ 2.60GHz",
            "1",
            "GenuineIntel",
            "Intel(R) Xeon(R) CPU E5-2670 0 @ 2.60GHz",
            "2",
            "GenuineIntel",
            "Intel(R) Xeon(R) CPU E5-2670 0 @ 2.60GHz",
            "3",
            "GenuineIntel",
            "Intel(R) Xeon(R) CPU E5-2670 0 @ 2.60GHz",
            "4",
            "GenuineIntel",
            "Intel(R) Xeon(R) CPU E5-2670 0 @ 2.60GHz",
            "5",
            "GenuineIntel",
            "Intel(R) Xeon(R) CPU E5-2670 0 @ 2.60GHz",
            "6",
            "GenuineIntel",
            "Intel(R) Xeon(R) CPU E5-2670 0 @ 2.60GHz",
            "7",
            "GenuineIntel",
            "Intel(R) Xeon(R) CPU E5-2670 0 @ 2.60GHz"
        ],
        "ansible_processor_cores": 8,
        "ansible_processor_count": 8,
        "ansible_processor_threads_per_core": 1,
        "ansible_processor_vcpus": 8,
        "ansible_product_name": "HVM domU",
        "ansible_product_serial": "REDACTED",
        "ansible_product_uuid": "REDACTED",
        "ansible_product_version": "4.1.5",
        "ansible_python": {
            "executable": "/usr/bin/python2",
            "has_sslcontext": true,
            "type": "CPython",
            "version": {
                "major": 2,
                "micro": 5,
                "minor": 7,
                "releaselevel": "final",
                "serial": 0
            },
            "version_info": [
                2,
                7,
                5,
                "final",
                0
            ]
        },
        "ansible_python_version": "2.7.5",
        "ansible_real_group_id": 1000,
        "ansible_real_user_id": 1000,
        "ansible_selinux": {
            "config_mode": "enforcing",
            "mode": "enforcing",
            "policyvers": 31,
            "status": "enabled",
            "type": "targeted"
        },
        "ansible_selinux_python_present": true,
        "ansible_service_mgr": "systemd",
        "ansible_ssh_host_key_ecdsa_public": "REDACTED KEY VALUE",
        "ansible_ssh_host_key_ed25519_public": "REDACTED KEY VALUE",
        "ansible_ssh_host_key_rsa_public": "REDACTED KEY VALUE",
        "ansible_swapfree_mb": 0,
        "ansible_swaptotal_mb": 0,
        "ansible_system": "Linux",
        "ansible_system_capabilities": [
            ""
        ],
        "ansible_system_capabilities_enforced": "True",
        "ansible_system_vendor": "Xen",
        "ansible_uptime_seconds": 151,
        "ansible_user_dir": "/home/zuul",
        "ansible_user_gecos": "",
        "ansible_user_gid": 1000,
        "ansible_user_id": "zuul",
        "ansible_user_shell": "/bin/bash",
        "ansible_user_uid": 1000,
        "ansible_userspace_architecture": "x86_64",
        "ansible_userspace_bits": "64",
        "ansible_virtualization_role": "guest",
        "ansible_virtualization_type": "xen",
        "gather_subset": [
            "all"
        ],
        "module_setup": true
    }

In the above the model of the first disk may be referenced in a template or playbook as::

    {{ ansible_facts['devices']['xvda']['model'] }}

Similarly, the hostname as the system reports it is::

    {{ ansible_facts['nodename'] }}

Facts are frequently used in conditionals (see :ref:`playbooks_conditionals`) and also in templates.

Facts can be also used to create dynamic groups of hosts that match particular criteria, see the :ref:`modules` documentation on **group_by** for details, as well as in generalized conditional statements as discussed in the :ref:`playbooks_conditionals` chapter.

.. _disabling_facts:

Disabling facts
---------------

If you know you don't need any fact data about your hosts, and know everything about your systems centrally, you
can turn off fact gathering.  This has advantages in scaling Ansible in push mode with very large numbers of
systems, mainly, or if you are using Ansible on experimental platforms.   In any play, just do this::

    - hosts: whatever
      gather_facts: no

.. _local_facts:

Local facts (facts.d)
---------------------

.. versionadded:: 1.3

As discussed in the playbooks chapter, Ansible facts are a way of getting data about remote systems for use in playbook variables.

Usually these are discovered automatically by the ``setup`` module in Ansible. Users can also write custom facts modules, as described in the API guide. However, what if you want to have a simple way to provide system or user provided data for use in Ansible variables, without writing a fact module?

"Facts.d" is one mechanism for users to control some aspect of how their systems are managed.

.. note:: Perhaps "local facts" is a bit of a misnomer, it means "locally supplied user values" as opposed to "centrally supplied user values", or what facts are -- "locally dynamically determined values".

If a remotely managed system has an ``/etc/ansible/facts.d`` directory, any files in this directory
ending in ``.fact``, can be JSON, INI, or executable files returning JSON, and these can supply local facts in Ansible.
An alternate directory can be specified using the ``fact_path`` play keyword.

For example, assume ``/etc/ansible/facts.d/preferences.fact`` contains::

    [general]
    asdf=1
    bar=2

This will produce a hash variable fact named ``general`` with ``asdf`` and ``bar`` as members.
To validate this, run the following::

    ansible <hostname> -m setup -a "filter=ansible_local"

And you will see the following fact added::

    "ansible_local": {
            "preferences": {
                "general": {
                    "asdf" : "1",
                    "bar"  : "2"
                }
            }
     }

And this data can be accessed in a ``template/playbook`` as::

     {{ ansible_local['preferences']['general']['asdf'] }}

The local namespace prevents any user supplied fact from overriding system facts or variables defined elsewhere in the playbook.

.. note:: The key part in the key=value pairs will be converted into lowercase inside the ansible_local variable. Using the example above, if the ini file contained ``XYZ=3`` in the ``[general]`` section, then you should expect to access it as: ``{{ ansible_local['preferences']['general']['xyz'] }}`` and not ``{{ ansible_local['preferences']['general']['XYZ'] }}``. This is because Ansible uses Python's `ConfigParser`_ which passes all option names through the `optionxform`_ method and this method's default implementation converts option names to lower case.

.. _ConfigParser: https://docs.python.org/2/library/configparser.html
.. _optionxform: https://docs.python.org/2/library/configparser.html#ConfigParser.RawConfigParser.optionxform

If you have a playbook that is copying over a custom fact and then running it, making an explicit call to re-run the setup module
can allow that fact to be used during that particular play.  Otherwise, it will be available in the next play that gathers fact information.
Here is an example of what that might look like::

  - hosts: webservers
    tasks:
      - name: create directory for ansible custom facts
        file: state=directory recurse=yes path=/etc/ansible/facts.d
      - name: install custom ipmi fact
        copy: src=ipmi.fact dest=/etc/ansible/facts.d
      - name: re-read facts after adding custom fact
        setup: filter=ansible_local

In this pattern however, you could also write a fact module as well, and may wish to consider this as an option.

.. _ansible_version:

Ansible version
---------------

.. versionadded:: 1.8

To adapt playbook behavior to specific version of ansible, a variable ansible_version is available, with the following
structure::

    "ansible_version": {
        "full": "2.0.0.2",
        "major": 2,
        "minor": 0,
        "revision": 0,
        "string": "2.0.0.2"
    }

.. _fact_caching:

Caching Facts
-------------

.. versionadded:: 1.8

As shown elsewhere in the docs, it is possible for one server to reference variables about another, like so::

    {{ hostvars['asdf.example.com']['ansible_facts']['os_family'] }}

With "Fact Caching" disabled, in order to do this, Ansible must have already talked to 'asdf.example.com' in the
current play, or another play up higher in the playbook.  This is the default configuration of ansible.

To avoid this, Ansible 1.8 allows the ability to save facts between playbook runs, but this feature must be manually
enabled.  Why might this be useful?

With a very large infrastructure with thousands of hosts, fact caching could be configured to run nightly. Configuration of a small set of servers could run ad-hoc or periodically throughout the day. With fact caching enabled, it would
not be necessary to "hit" all servers to reference variables and information about them.

With fact caching enabled, it is possible for machine in one group to reference variables about machines in the other group, despite the fact that they have not been communicated with in the current execution of /usr/bin/ansible-playbook.

To benefit from cached facts, you will want to change the ``gathering`` setting to ``smart`` or ``explicit`` or set ``gather_facts`` to ``False`` in most plays.

Currently, Ansible ships with two persistent cache plugins: redis and jsonfile.

To configure fact caching using redis, enable it in ``ansible.cfg`` as follows::

    [defaults]
    gathering = smart
    fact_caching = redis
    fact_caching_timeout = 86400
    # seconds

To get redis up and running, perform the equivalent OS commands::

    yum install redis
    service redis start
    pip install redis

Note that the Python redis library should be installed from pip, the version packaged in EPEL is too old for use by Ansible.

In current embodiments, this feature is in beta-level state and the Redis plugin does not support port or password configuration, this is expected to change in the near future.

To configure fact caching using jsonfile, enable it in ``ansible.cfg`` as follows::

    [defaults]
    gathering = smart
    fact_caching = jsonfile
    fact_caching_connection = /path/to/cachedir
    fact_caching_timeout = 86400
    # seconds

``fact_caching_connection`` is a local filesystem path to a writeable
directory (ansible will attempt to create the directory if one does not exist).

``fact_caching_timeout`` is the number of seconds to cache the recorded facts.

.. _registered_variables:

Registering variables
=====================

Another major use of variables is running a command and registering the result of that command as a variable. When you execute a task and save the return value in a variable for use in later tasks, you create a registered variable. There are more examples of this in the
:ref:`playbooks_conditionals` chapter.

For example::

   - hosts: web_servers

     tasks:

        - shell: /usr/bin/foo
          register: foo_result
          ignore_errors: True

        - shell: /usr/bin/bar
          when: foo_result.rc == 5

Results will vary from module to module. Each module's documentation includes a ``RETURN`` section describing that module's return values. To see the values for a particular task, run your playbook with ``-v``.

Registered variables are similar to facts, with a few key differences. Like facts, registered variables are host-level variables. However, registered variables are only stored in memory. (Ansible facts are backed by whatever cache plugin you have configured.) Registered variables are only valid on the host for the rest of the current playbook run. Finally, registered variables and facts have different :ref:`precedence levels <ansible_variable_precedence>`.

When you register a variable in a task with a loop, the registered variable contains a value for each item in the loop. The data structure placed in the variable during the loop will contain a ``results`` attribute, that is a list of all responses from the module. For a more in-depth example of how this works, see the :ref:`playbooks_loops` section on using register with a loop.

.. note:: If a task fails or is skipped, the variable still is registered with a failure or skipped status, the only way to avoid registering a variable is using tags.

.. _accessing_complex_variable_data:

Accessing complex variable data
===============================

We already described facts a little higher up in the documentation.

Some provided facts, like networking information, are made available as nested data structures.  To access
them a simple ``{{ foo }}`` is not sufficient, but it is still easy to do.   Here's how we get an IP address::

    {{ ansible_facts["eth0"]["ipv4"]["address"] }}

OR alternatively::

    {{ ansible_facts.eth0.ipv4.address }}

Similarly, this is how we access the first element of an array::

    {{ foo[0] }}

.. _magic_variables_and_hostvars:

Accessing information about other hosts with magic variables
============================================================

Whether or not you define any variables, you can access information about your hosts with the :ref:`special_variables` Ansible provides, including "magic" variables, facts, and connection variables. Magic variable names are reserved - do not set variables with these names. The variable ``environment`` is also reserved.

The most commonly used magic variables are ``hostvars``, ``groups``, ``group_names``, and ``inventory_hostname``.

``hostvars`` lets you access variables for another host, including facts that have been gathered about that host. You can access host variables at any point in a playbook. Even if you haven't connected to that host yet in any play in the playbook or set of playbooks, you can still get the variables, but you will not be able to see the facts.

If your database server wants to use the value of a 'fact' from another node, or an inventory variable
assigned to another node, it's easy to do so within a template or even an action line::

    {{ hostvars['test.example.com']['ansible_facts']['distribution'] }}

``groups`` is a list of all the groups (and hosts) in the inventory.  This can be used to enumerate all hosts within a group. For example:

.. code-block:: jinja

   {% for host in groups['app_servers'] %}
      # something that applies to all app servers.
   {% endfor %}

A frequently used idiom is walking a group to find all IP addresses in that group.

.. code-block:: jinja

   {% for host in groups['app_servers'] %}
      {{ hostvars[host]['ansible_facts']['eth0']['ipv4']['address'] }}
   {% endfor %}

You can use this idiom to point a frontend proxy server to all of the app servers, to set up the correct firewall rules between servers, etc.
You need to make sure that the facts of those hosts have been populated before though, for example by running a play against them if the facts have not been cached recently (fact caching was added in Ansible 1.8).

``group_names`` is a list (array) of all the groups the current host is in.  This can be used in templates using Jinja2 syntax to make template source files that vary based on the group membership (or role) of the host:

.. code-block:: jinja

   {% if 'webserver' in group_names %}
      # some part of a configuration file that only applies to webservers
   {% endif %}

``inventory_hostname`` is the name of the hostname as configured in Ansible's inventory host file.  This can
be useful when you've disabled fact-gathering, or you don't want to rely on the discovered hostname ``ansible_hostname``.  If you have a long FQDN, you can use ``inventory_hostname_short``, which contains the part up to the first
period, without the rest of the domain.

Other useful magic variables refer to the current play or playbook, including:

.. versionadded:: 2.2

``ansible_play_hosts`` is the full list of all hosts still active in the current play.

.. versionadded:: 2.2

``ansible_play_batch`` is available as a list of hostnames that are in scope for the current 'batch' of the play. The batch size is defined by ``serial``, when not set it is equivalent to the whole play (making it the same as ``ansible_play_hosts``).

.. versionadded:: 2.3

``ansible_playbook_python`` is the path to the python executable used to invoke the Ansible command line tool.

These vars may be useful for filling out templates with multiple hostnames or for injecting the list into the rules for a load balancer.

Also available, ``inventory_dir`` is the pathname of the directory holding Ansible's inventory host file, ``inventory_file`` is the pathname and the filename pointing to the Ansible's inventory host file.

``playbook_dir`` contains the playbook base directory.

We then have ``role_path`` which will return the current role's pathname (since 1.8). This will only work inside a role.

And finally, ``ansible_check_mode`` (added in version 2.1), a boolean magic variable which will be set to ``True`` if you run Ansible with ``--check``.

.. _variable_file_separation_details:

Defining variables in files
===========================

It's a great idea to keep your playbooks under source control, but
you may wish to make the playbook source public while keeping certain
important variables private.  Similarly, sometimes you may just
want to keep certain information in different files, away from
the main playbook.

You can do this by using an external variables file, or files, just like this::

    ---

    - hosts: all
      remote_user: root
      vars:
        favcolor: blue
      vars_files:
        - /vars/external_vars.yml

      tasks:

      - name: this is just a placeholder
        command: /bin/echo foo

This removes the risk of sharing sensitive data with others when
sharing your playbook source with them.

The contents of each variables file is a simple YAML dictionary, like this::

    ---
    # in the above example, this would be vars/external_vars.yml
    somevar: somevalue
    password: magic

.. note::
   It's also possible to keep per-host and per-group variables in very
   similar files, this is covered in :ref:`splitting_out_vars`.

.. _passing_variables_on_the_command_line:

Passing variables on the command line
=====================================

In addition to ``vars_prompt`` and ``vars_files``, it is possible to set variables at the
command line using the ``--extra-vars`` (or ``-e``) argument.  Variables can be defined using
a single quoted string (containing one or more variables) using one of the formats below

key=value format::

    ansible-playbook release.yml --extra-vars "version=1.23.45 other_variable=foo"

.. note:: Values passed in using the ``key=value`` syntax are interpreted as strings.
          Use the JSON format if you need to pass in anything that shouldn't be a string (Booleans, integers, floats, lists etc).

JSON string format::

    ansible-playbook release.yml --extra-vars '{"version":"1.23.45","other_variable":"foo"}'
    ansible-playbook arcade.yml --extra-vars '{"pacman":"mrs","ghosts":["inky","pinky","clyde","sue"]}'

vars from a JSON or YAML file::

    ansible-playbook release.yml --extra-vars "@some_file.json"

This is useful for, among other things, setting the hosts group or the user for the playbook.

Escaping quotes and other special characters:

Ensure you're escaping quotes appropriately for both your markup (e.g. JSON), and for
the shell you're operating in.::

    ansible-playbook arcade.yml --extra-vars "{\"name\":\"Conan O\'Brien\"}"
    ansible-playbook arcade.yml --extra-vars '{"name":"Conan O'\\\''Brien"}'
    ansible-playbook script.yml --extra-vars "{\"dialog\":\"He said \\\"I just can\'t get enough of those single and double-quotes"\!"\\\"\"}"

In these cases, it's probably best to use a JSON or YAML file containing the variable
definitions.

.. _ansible_variable_precedence:

Variable precedence: Where should I put a variable?
===================================================

A lot of folks may ask about how variables override another.  Ultimately it's Ansible's philosophy that it's better
you know where to put a variable, and then you have to think about it a lot less.

Avoid defining the variable "x" in 47 places and then ask the question "which x gets used".
Why?  Because that's not Ansible's Zen philosophy of doing things.

There is only one Empire State Building. One Mona Lisa, etc.  Figure out where to define a variable, and don't make
it complicated.

However, let's go ahead and get precedence out of the way!  It exists.  It's a real thing, and you might have
a use for it.

If multiple variables of the same name are defined in different places, they get overwritten in a certain order.

Here is the order of precedence from least to greatest (the last listed variables winning prioritization):

  #. command line values (eg "-u user")
  #. role defaults [1]_
  #. inventory file or script group vars [2]_
  #. inventory group_vars/all [3]_
  #. playbook group_vars/all [3]_
  #. inventory group_vars/* [3]_
  #. playbook group_vars/* [3]_
  #. inventory file or script host vars [2]_
  #. inventory host_vars/* [3]_
  #. playbook host_vars/* [3]_
  #. host facts / cached set_facts [4]_
  #. play vars
  #. play vars_prompt
  #. play vars_files
  #. role vars (defined in role/vars/main.yml)
  #. block vars (only for tasks in block)
  #. task vars (only for the task)
  #. include_vars
  #. set_facts / registered vars
  #. role (and include_role) params
  #. include params
  #. extra vars (always win precedence)

Basically, anything that goes into "role defaults" (the defaults folder inside the role) is the most malleable and easily overridden. Anything in the vars directory of the role overrides previous versions of that variable in namespace.  The idea here to follow is that the more explicit you get in scope, the more precedence it takes with command line ``-e`` extra vars always winning.  Host and/or inventory variables can win over role defaults, but not explicit includes like the vars directory or an ``include_vars`` task.

.. rubric:: Footnotes

.. [1] Tasks in each role will see their own role's defaults. Tasks defined outside of a role will see the last role's defaults.
.. [2] Variables defined in inventory file or provided by dynamic inventory.
.. [3] Includes vars added by 'vars plugins' as well as host_vars and group_vars which are added by the default vars plugin shipped with Ansible.
.. [4] When created with set_facts's cacheable option, variables will have the high precedence in the play,
       but will be the same as a host facts precedence when they come from the cache.

.. note:: Within any section, redefining a var will overwrite the previous instance.
          If multiple groups have the same variable, the last one loaded wins.
          If you define a variable twice in a play's ``vars:`` section, the second one wins.
.. note:: The previous describes the default config ``hash_behaviour=replace``, switch to ``merge`` to only partially overwrite.
.. note:: Group loading follows parent/child relationships. Groups of the same 'parent/child' level are then merged following alphabetical order.
          This last one can be superseded by the user via ``ansible_group_priority``, which defaults to ``1`` for all groups.
          This variable, ``ansible_group_priority``, can only be set in the inventory source and not in group_vars/ as the variable is used in the loading of group_vars/.

Another important thing to consider (for all versions) is that connection variables override config, command line and play/role/task specific options and keywords. See :ref:`general_precedence_rules` for more details. For example, if your inventory specifies ``ansible_user: ramon`` and you run::

    ansible -u lola myhost

This will still connect as ``ramon`` because the value from the variable takes priority (in this case, the variable came from the inventory, but the same would be true no matter where the variable was defined).

For plays/tasks this is also true for ``remote_user``. Assuming the same inventory config, the following play::

 - hosts: myhost
   tasks:
    - command: I'll connect as ramon still
      remote_user: lola

will have the value of ``remote_user`` overwritten by ``ansible_user`` in the inventory.

This is done so host-specific settings can override the general settings. These variables are normally defined per host or group in inventory,
but they behave like other variables.

If you want to override the remote user globally (even over inventory) you can use extra vars. For instance, if you run::

    ansible... -e "ansible_user=maria" -u lola

the ``lola`` value is still ignored, but ``ansible_user=maria`` takes precedence over all other places where ``ansible_user`` (or ``remote_user``) might be set.

A connection-specific version of a variable takes precedence over more generic
versions.  For example, ``ansible_ssh_user`` specified as a group_var would have
a higher precedence than ``ansible_user`` specified as a host_var.

You can also override as a normal variable in a play::

    - hosts: all
      vars:
        ansible_user: lola
      tasks:
        - command: I'll connect as lola!

.. _variable_scopes:

Scoping variables
-----------------

You can decide where to set a variable based on the scope you want that value to have. Ansible has three main scopes:

 * Global: this is set by config, environment variables and the command line
 * Play: each play and contained structures, vars entries (vars; vars_files; vars_prompt), role defaults and vars.
 * Host: variables directly associated to a host, like inventory, include_vars, facts or registered task outputs

.. _variable_examples:

Examples of where to set a variable
-----------------------------------

 Let's show some examples and where you would choose to put what based on the kind of control you might want over values.

First off, group variables are powerful.

Site-wide defaults should be defined as a ``group_vars/all`` setting.  Group variables are generally placed alongside
your inventory file.  They can also be returned by a dynamic inventory script (see :ref:`intro_dynamic_inventory`) or defined
in things like :ref:`ansible_tower` from the UI or API::

    ---
    # file: /etc/ansible/group_vars/all
    # this is the site wide default
    ntp_server: default-time.example.com

Regional information might be defined in a ``group_vars/region`` variable.  If this group is a child of the ``all`` group (which it is, because all groups are), it will override the group that is higher up and more general::

    ---
    # file: /etc/ansible/group_vars/boston
    ntp_server: boston-time.example.com

If for some crazy reason we wanted to tell just a specific host to use a specific NTP server, it would then override the group variable!::

    ---
    # file: /etc/ansible/host_vars/xyz.boston.example.com
    ntp_server: override.example.com

So that covers inventory and what you would normally set there.  It's a great place for things that deal with geography or behavior.  Since groups are frequently the entity that maps roles onto hosts, it is sometimes a shortcut to set variables on the group instead of defining them on a role.  You could go either way.

Remember:  Child groups override parent groups, and hosts always override their groups.

Next up: learning about role variable precedence.

We'll pretty much assume you are using roles at this point.  You should be using roles for sure.  Roles are great.  You are using
roles aren't you?  Hint hint.

If you are writing a redistributable role with reasonable defaults, put those in the ``roles/x/defaults/main.yml`` file.  This means
the role will bring along a default value but ANYTHING in Ansible will override it.
See :ref:`playbooks_reuse_roles` for more info about this::

    ---
    # file: roles/x/defaults/main.yml
    # if not overridden in inventory or as a parameter, this is the value that will be used
    http_port: 80

If you are writing a role and want to ensure the value in the role is absolutely used in that role, and is not going to be overridden
by inventory, you should put it in ``roles/x/vars/main.yml`` like so, and inventory values cannot override it.  ``-e`` however, still will::

    ---
    # file: roles/x/vars/main.yml
    # this will absolutely be used in this role
    http_port: 80

This is one way to plug in constants about the role that are always true.  If you are not sharing your role with others,
app specific behaviors like ports is fine to put in here.  But if you are sharing roles with others, putting variables in here might
be bad. Nobody will be able to override them with inventory, but they still can by passing a parameter to the role.

Parameterized roles are useful.

If you are using a role and want to override a default, pass it as a parameter to the role like so::

    roles:
       - role: apache
         vars:
            http_port: 8080

This makes it clear to the playbook reader that you've made a conscious choice to override some default in the role, or pass in some
configuration that the role can't assume by itself.  It also allows you to pass something site-specific that isn't really part of the
role you are sharing with others.

This can often be used for things that might apply to some hosts multiple times. For example::

    roles:
       - role: app_user
         vars:
            myname: Ian
       - role: app_user
         vars:
           myname: Terry
       - role: app_user
         vars:
           myname: Graham
       - role: app_user
         vars:
           myname: John

In this example, the same role was invoked multiple times.  It's quite likely there was
no default for ``name`` supplied at all.  Ansible can warn you when variables aren't defined -- it's the default behavior in fact.

There are a few other things that go on with roles.

Generally speaking, variables set in one role are available to others.  This means if you have a ``roles/common/vars/main.yml`` you
can set variables in there and make use of them in other roles and elsewhere in your playbook::

     roles:
        - role: common_settings
        - role: something
          vars:
            foo: 12
        - role: something_else

.. note:: There are some protections in place to avoid the need to namespace variables.
          In the above, variables defined in common_settings are most definitely available to 'something' and 'something_else' tasks, but if
          "something's" guaranteed to have foo set at 12, even if somewhere deep in common settings it set foo to 20.

So, that's precedence, explained in a more direct way.  Don't worry about precedence, just think about if your role is defining a
variable that is a default, or a "live" variable you definitely want to use.  Inventory lies in precedence right in the middle, and
if you want to forcibly override something, use ``-e``.

If you found that a little hard to understand, take a look at the `ansible-examples <https://github.com/ansible/ansible-examples>`_ repo on GitHub for a bit more about how all of these things can work together.

Using advanced variable syntax
==============================

For information about advanced YAML syntax used to declare variables and have more control over the data placed in YAML files used by Ansible, see :ref:`playbooks_advanced_syntax`.

.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :ref:`playbooks_conditionals`
       Conditional statements in playbooks
   :ref:`playbooks_filters`
       Jinja2 filters and their uses
   :ref:`playbooks_loops`
       Looping in playbooks
   :ref:`playbooks_reuse_roles`
       Playbook organization by roles
   :ref:`playbooks_best_practices`
       Best practices in playbooks
   :ref:`special_variables`
       List of special variables
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
