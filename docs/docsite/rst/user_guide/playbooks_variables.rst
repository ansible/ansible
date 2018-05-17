.. _playbooks_variables:

Variables
=========

.. contents:: Topics

While automation exists to make it easier to make things repeatable, all systems are not exactly alike; some may require configuration that is slightly different from others. In some instances, the observed behavior or state of one system might influence how you configure other systems. For example, you might need to find out the IP address of a system and use it as a configuration value on another system.

Ansible uses *variables* to help deal with differences between systems.

To understand variables you'll also want to read :doc:`playbooks_conditionals` and :doc:`playbooks_loops`.
Useful things like the **group_by** module
and the ``when`` conditional can also be used with variables, and to help manage differences between systems.

The ansible-examples github repository contains many examples of how variables are used in Ansible.

For advice on best practices, refer to :ref:`best_practices_for_variables_and_vaults` in the *Best Practices* chapter.

.. _valid_variable_names:

What Makes A Valid Variable Name
````````````````````````````````

Before we start using variables, it's important to know what are valid variable names.

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

Variables Defined in Inventory
``````````````````````````````

We've actually already covered a lot about variables in another section, so far this shouldn't be terribly new, but
a bit of a refresher.

Often you'll want to set variables based on what groups a machine is in.  For instance, maybe machines in Boston
want to use 'boston.ntp.example.com' as an NTP server.

See the :doc:`intro_inventory` document for multiple ways on how to define variables in inventory.

.. _playbook_variables:

Variables Defined in a Playbook
```````````````````````````````

In a playbook, it's possible to define variables directly inline like so::

   - hosts: webservers
     vars:
       http_port: 80

This can be nice as it's right there when you are reading the playbook.

.. _included_variables:

Variables defined from included files and roles
```````````````````````````````````````````````

It turns out we've already talked about variables in another place too.

As described in :doc:`playbooks_reuse_roles`, variables can also be included in the playbook via include files, which may or may
not be part of an "Ansible Role".  Usage of roles is preferred as it provides a nice organizational system.

.. _about_jinja2:

Using Variables: About Jinja2
`````````````````````````````

It's nice enough to know about how to define variables, but how do you use them?

Ansible allows you to reference variables in your playbooks using the Jinja2 templating system.  While you can do a lot of complex things in Jinja, only the basics are things you really need to learn at first.

For example, in a simple template, you can do something like::

    My amp goes to {{ max_amp_value }}

And that will provide the most basic form of variable substitution.

This is also valid directly in playbooks, and you'll occasionally want to do things like::

    template: src=foo.cfg.j2 dest={{ remote_install_path }}/foo.cfg

In the above example, we used a variable to help decide where to place a file.

Inside a template you automatically have access to all of the variables that are in scope for a host.  Actually
it's more than that -- you can also read variables about other hosts.  We'll show how to do that in a bit.

.. note:: ansible allows Jinja2 loops and conditionals in templates, but in playbooks, we do not use them.  Ansible
   playbooks are pure machine-parseable YAML.  This is a rather important feature as it means it is possible to code-generate
   pieces of files, or to have other ecosystem tools read Ansible files.  Not everyone will need this but it can unlock
   possibilities.

.. seealso::

    :doc:`playbooks_templating`
        More information about Jinja2 templating

.. _jinja2_filters:

Jinja2 Filters
``````````````

.. note:: These are infrequently utilized features.  Use them if they fit a use case you have, but this is optional knowledge.

Filters in Jinja2 are a way of transforming template expressions from one kind of data into another.  Jinja2
ships with many of these. See `builtin filters`_ in the official Jinja2 template documentation.

In addition to those, Ansible supplies many more. See the :doc:`playbooks_filters` document
for a list of available filters and example usage guide.

.. _yaml_gotchas:

Hey Wait, A YAML Gotcha
```````````````````````

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

Information discovered from systems: Facts
``````````````````````````````````````````

There are other places where variables can come from, but these are a type of variable that are discovered, not set by the user.

Facts are information derived from speaking with your remote systems.

An example of this might be the IP address of the remote host, or what the operating system is.

To see what information is available, try the following::

    ansible hostname -m setup

This will return a large amount of variable data, which may look like this, as taken from Ansible 1.4 running on a Ubuntu 12.04 system

.. code-block:: json

    {
        "ansible_all_ipv4_addresses": [
            "REDACTED IP ADDRESS"
        ],
        "ansible_all_ipv6_addresses": [
            "REDACTED IPV6 ADDRESS"
        ],
        "ansible_architecture": "x86_64",
        "ansible_bios_date": "09/20/2012",
        "ansible_bios_version": "6.00",
        "ansible_cmdline": {
            "BOOT_IMAGE": "/boot/vmlinuz-3.5.0-23-generic",
            "quiet": true,
            "ro": true,
            "root": "UUID=4195bff4-e157-4e41-8701-e93f0aec9e22",
            "splash": true
        },
        "ansible_date_time": {
            "date": "2013-10-02",
            "day": "02",
            "epoch": "1380756810",
            "hour": "19",
            "iso8601": "2013-10-02T23:33:30Z",
            "iso8601_micro": "2013-10-02T23:33:30.036070Z",
            "minute": "33",
            "month": "10",
            "second": "30",
            "time": "19:33:30",
            "tz": "EDT",
            "year": "2013"
        },
        "ansible_default_ipv4": {
            "address": "REDACTED",
            "alias": "eth0",
            "gateway": "REDACTED",
            "interface": "eth0",
            "macaddress": "REDACTED",
            "mtu": 1500,
            "netmask": "255.255.255.0",
            "network": "REDACTED",
            "type": "ether"
        },
        "ansible_default_ipv6": {},
        "ansible_devices": {
            "fd0": {
                "holders": [],
                "host": "",
                "model": null,
                "partitions": {},
                "removable": "1",
                "rotational": "1",
                "scheduler_mode": "deadline",
                "sectors": "0",
                "sectorsize": "512",
                "size": "0.00 Bytes",
                "support_discard": "0",
                "vendor": null
            },
            "sda": {
                "holders": [],
                "host": "SCSI storage controller: LSI Logic / Symbios Logic 53c1030 PCI-X Fusion-MPT Dual Ultra320 SCSI (rev 01)",
                "model": "VMware Virtual S",
                "partitions": {
                    "sda1": {
                        "sectors": "39843840",
                        "sectorsize": 512,
                        "size": "19.00 GB",
                        "start": "2048"
                    },
                    "sda2": {
                        "sectors": "2",
                        "sectorsize": 512,
                        "size": "1.00 KB",
                        "start": "39847934"
                    },
                    "sda5": {
                        "sectors": "2093056",
                        "sectorsize": 512,
                        "size": "1022.00 MB",
                        "start": "39847936"
                    }
                },
                "removable": "0",
                "rotational": "1",
                "scheduler_mode": "deadline",
                "sectors": "41943040",
                "sectorsize": "512",
                "size": "20.00 GB",
                "support_discard": "0",
                "vendor": "VMware,"
            },
            "sr0": {
                "holders": [],
                "host": "IDE interface: Intel Corporation 82371AB/EB/MB PIIX4 IDE (rev 01)",
                "model": "VMware IDE CDR10",
                "partitions": {},
                "removable": "1",
                "rotational": "1",
                "scheduler_mode": "deadline",
                "sectors": "2097151",
                "sectorsize": "512",
                "size": "1024.00 MB",
                "support_discard": "0",
                "vendor": "NECVMWar"
            }
        },
        "ansible_distribution": "Ubuntu",
        "ansible_distribution_release": "precise",
        "ansible_distribution_version": "12.04",
        "ansible_domain": "",
        "ansible_env": {
            "COLORTERM": "gnome-terminal",
            "DISPLAY": ":0",
            "HOME": "/home/mdehaan",
            "LANG": "C",
            "LESSCLOSE": "/usr/bin/lesspipe %s %s",
            "LESSOPEN": "| /usr/bin/lesspipe %s",
            "LOGNAME": "root",
            "LS_COLORS": "rs=0:di=01;34:ln=01;36:mh=00:pi=40;33:so=01;35:do=01;35:bd=40;33;01:cd=40;33;01:or=40;31;01:su=37;41:sg=30;43:ca=30;41:tw=30;42:ow=34;42:st=37;44:ex=01;32:*.tar=01;31:*.tgz=01;31:*.arj=01;31:*.taz=01;31:*.lzh=01;31:*.lzma=01;31:*.tlz=01;31:*.txz=01;31:*.zip=01;31:*.z=01;31:*.Z=01;31:*.dz=01;31:*.gz=01;31:*.lz=01;31:*.xz=01;31:*.bz2=01;31:*.bz=01;31:*.tbz=01;31:*.tbz2=01;31:*.tz=01;31:*.deb=01;31:*.rpm=01;31:*.jar=01;31:*.war=01;31:*.ear=01;31:*.sar=01;31:*.rar=01;31:*.ace=01;31:*.zoo=01;31:*.cpio=01;31:*.7z=01;31:*.rz=01;31:*.jpg=01;35:*.jpeg=01;35:*.gif=01;35:*.bmp=01;35:*.pbm=01;35:*.pgm=01;35:*.ppm=01;35:*.tga=01;35:*.xbm=01;35:*.xpm=01;35:*.tif=01;35:*.tiff=01;35:*.png=01;35:*.svg=01;35:*.svgz=01;35:*.mng=01;35:*.pcx=01;35:*.mov=01;35:*.mpg=01;35:*.mpeg=01;35:*.m2v=01;35:*.mkv=01;35:*.webm=01;35:*.ogm=01;35:*.mp4=01;35:*.m4v=01;35:*.mp4v=01;35:*.vob=01;35:*.qt=01;35:*.nuv=01;35:*.wmv=01;35:*.asf=01;35:*.rm=01;35:*.rmvb=01;35:*.flc=01;35:*.avi=01;35:*.fli=01;35:*.flv=01;35:*.gl=01;35:*.dl=01;35:*.xcf=01;35:*.xwd=01;35:*.yuv=01;35:*.cgm=01;35:*.emf=01;35:*.axv=01;35:*.anx=01;35:*.ogv=01;35:*.ogx=01;35:*.aac=00;36:*.au=00;36:*.flac=00;36:*.mid=00;36:*.midi=00;36:*.mka=00;36:*.mp3=00;36:*.mpc=00;36:*.ogg=00;36:*.ra=00;36:*.wav=00;36:*.axa=00;36:*.oga=00;36:*.spx=00;36:*.xspf=00;36:",
            "MAIL": "/var/mail/root",
            "OLDPWD": "/root/ansible/docsite",
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "PWD": "/root/ansible",
            "SHELL": "/bin/bash",
            "SHLVL": "1",
            "SUDO_COMMAND": "/bin/bash",
            "SUDO_GID": "1000",
            "SUDO_UID": "1000",
            "SUDO_USER": "mdehaan",
            "TERM": "xterm",
            "USER": "root",
            "USERNAME": "root",
            "XAUTHORITY": "/home/mdehaan/.Xauthority",
            "_": "/usr/local/bin/ansible"
        },
        "ansible_eth0": {
            "active": true,
            "device": "eth0",
            "ipv4": {
                "address": "REDACTED",
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
            "module": "e1000",
            "mtu": 1500,
            "type": "ether"
        },
        "ansible_form_factor": "Other",
        "ansible_fqdn": "ubuntu2.example.com",
        "ansible_hostname": "ubuntu2",
        "ansible_interfaces": [
            "lo",
            "eth0"
        ],
        "ansible_kernel": "3.5.0-23-generic",
        "ansible_lo": {
            "active": true,
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
            "mtu": 16436,
            "type": "loopback"
        },
        "ansible_lsb": {
            "codename": "precise",
            "description": "Ubuntu 12.04.2 LTS",
            "id": "Ubuntu",
            "major_release": "12",
            "release": "12.04"
        },
        "ansible_machine": "x86_64",
        "ansible_memfree_mb": 74,
        "ansible_memtotal_mb": 991,
        "ansible_mounts": [
            {
                "device": "/dev/sda1",
                "fstype": "ext4",
                "mount": "/",
                "options": "rw,errors=remount-ro",
                "size_available": 15032406016,
                "size_total": 20079898624
            }
        ],
        "ansible_nodename": "ubuntu2.example.com",
        "ansible_os_family": "Debian",
        "ansible_pkg_mgr": "apt",
        "ansible_processor": [
            "Intel(R) Core(TM) i7 CPU         860  @ 2.80GHz"
        ],
        "ansible_processor_cores": 1,
        "ansible_processor_count": 1,
        "ansible_processor_threads_per_core": 1,
        "ansible_processor_vcpus": 1,
        "ansible_product_name": "VMware Virtual Platform",
        "ansible_product_serial": "REDACTED",
        "ansible_product_uuid": "REDACTED",
        "ansible_product_version": "None",
        "ansible_python_version": "2.7.3",
        "ansible_selinux": false,
        "ansible_ssh_host_key_dsa_public": "REDACTED KEY VALUE",
        "ansible_ssh_host_key_ecdsa_public": "REDACTED KEY VALUE",
        "ansible_ssh_host_key_rsa_public": "REDACTED KEY VALUE",
        "ansible_swapfree_mb": 665,
        "ansible_swaptotal_mb": 1021,
        "ansible_system": "Linux",
        "ansible_system_vendor": "VMware, Inc.",
        "ansible_user_id": "root",
        "ansible_userspace_architecture": "x86_64",
        "ansible_userspace_bits": "64",
        "ansible_virtualization_role": "guest",
        "ansible_virtualization_type": "VMware"
    }

In the above the model of the first harddrive may be referenced in a template or playbook as::

    {{ ansible_devices.sda.model }}

Similarly, the hostname as the system reports it is::

    {{ ansible_nodename }}

and the unqualified hostname shows the string before the first period(.)::

    {{ ansible_hostname }}

Facts are frequently used in conditionals (see :doc:`playbooks_conditionals`) and also in templates.

Facts can be also used to create dynamic groups of hosts that match particular criteria, see the :doc:`modules` documentation on **group_by** for details, as well as in generalized conditional statements as discussed in the :doc:`playbooks_conditionals` chapter.

.. _disabling_facts:

Turning Off Facts
`````````````````

If you know you don't need any fact data about your hosts, and know everything about your systems centrally, you
can turn off fact gathering.  This has advantages in scaling Ansible in push mode with very large numbers of
systems, mainly, or if you are using Ansible on experimental platforms.   In any play, just do this::

    - hosts: whatever
      gather_facts: no

.. _local_facts:

Local Facts (Facts.d)
`````````````````````

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

     {{ ansible_local.preferences.general.asdf }}

The local namespace prevents any user supplied fact from overriding system facts or variables defined elsewhere in the playbook.

.. note:: The key part in the key=value pairs will be converted into lowercase inside the ansible_local variable. Using the example above, if the ini file contained ``XYZ=3`` in the ``[general]`` section, then you should expect to access it as: ``{{ ansible_local.preferences.general.xyz }}`` and not ``{{ ansible_local.preferences.general.XYZ }}``. This is because Ansible uses Python's `ConfigParser`_ which passes all option names through the `optionxform`_ method and this method's default implementation converts option names to lower case.

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
```````````````

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

Fact Caching
````````````

.. versionadded:: 1.8

As shown elsewhere in the docs, it is possible for one server to reference variables about another, like so::

    {{ hostvars['asdf.example.com']['ansible_os_family'] }}

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

Registered Variables
````````````````````

Another major use of variables is running a command and using the result of that command to save the result into a variable. Results will vary from module to module. Use of ``-v`` when executing playbooks will show possible values for the results.

The value of a task being executed in ansible can be saved in a variable and used later.  See some examples of this in the
:doc:`playbooks_conditionals` chapter.

While it's mentioned elsewhere in that document too, here's a quick syntax example::

   - hosts: web_servers

     tasks:

        - shell: /usr/bin/foo
          register: foo_result
          ignore_errors: True

        - shell: /usr/bin/bar
          when: foo_result.rc == 5

Registered variables are valid on the host the remainder of the playbook run, which is the same as the lifetime of "facts"
in Ansible.  Effectively registered variables are just like facts.

When using ``register`` with a loop the data structure placed in the variable during a loop, will contain a ``results`` attribute, that is a list of all responses from the module. For a more in-depth example of how this works, see the :doc:`playbooks_loops` section on using register with a loop.

.. note:: If a task fails or is skipped, the variable still is registered with a failure or skipped status, the only way to avoid registering a variable is using tags.

.. _accessing_complex_variable_data:

Accessing Complex Variable Data
````````````````````````````````

We already described facts a little higher up in the documentation.

Some provided facts, like networking information, are made available as nested data structures.  To access
them a simple ``{{ foo }}`` is not sufficient, but it is still easy to do.   Here's how we get an IP address::

    {{ ansible_eth0["ipv4"]["address"] }}

OR alternatively::

    {{ ansible_eth0.ipv4.address }}

Similarly, this is how we access the first element of an array::

    {{ foo[0] }}

.. _magic_variables_and_hostvars:

Magic Variables, and How To Access Information About Other Hosts
````````````````````````````````````````````````````````````````

Even if you didn't define them yourself, Ansible provides a few variables for you automatically.
The most important of these are ``hostvars``, ``group_names``, and ``groups``.  Users should not use
these names themselves as they are reserved.  ``environment`` is also reserved.

``hostvars`` lets you ask about the variables of another host, including facts that have been gathered
about that host.  If, at this point, you haven't talked to that host yet in any play in the playbook
or set of playbooks, you can still get the variables, but you will not be able to see the facts.

If your database server wants to use the value of a 'fact' from another node, or an inventory variable
assigned to another node, it's easy to do so within a template or even an action line::

    {{ hostvars['test.example.com']['ansible_distribution'] }}

Additionally, ``group_names`` is a list (array) of all the groups the current host is in.  This can be used in templates using Jinja2 syntax to make template source files that vary based on the group membership (or role) of the host

.. code-block:: jinja

   {% if 'webserver' in group_names %}
      # some part of a configuration file that only applies to webservers
   {% endif %}


``groups`` is a list of all the groups (and hosts) in the inventory.  This can be used to enumerate all hosts within a group.
For example:

.. code-block:: jinja

   {% for host in groups['app_servers'] %}
      # something that applies to all app servers.
   {% endfor %}

A frequently used idiom is walking a group to find all IP addresses in that group

.. code-block:: jinja

   {% for host in groups['app_servers'] %}
      {{ hostvars[host]['ansible_eth0']['ipv4']['address'] }}
   {% endfor %}

An example of this could include pointing a frontend proxy server to all of the app servers, setting up the correct firewall rules between servers, etc.
You need to make sure that the facts of those hosts have been populated before though, for example by running a play against them if the facts have not been cached recently (fact caching was added in Ansible 1.8).

Additionally, ``inventory_hostname`` is the name of the hostname as configured in Ansible's inventory host file.  This can
be useful for when you don't want to rely on the discovered hostname ``ansible_hostname`` or for other mysterious
reasons.  If you have a long FQDN, ``inventory_hostname_short`` also contains the part up to the first
period, without the rest of the domain.

``play_hosts`` has been deprecated in 2.2, it was the same as the new ``ansible_play_batch`` variable.

.. versionadded:: 2.2

``ansible_play_hosts`` is the full list of all hosts still active in the current play.

.. versionadded:: 2.2

``ansible_play_batch`` is available as a list of hostnames that are in scope for the current 'batch' of the play. The batch size is defined by ``serial``, when not set it is equivalent to the whole play (making it the same as ``ansible_play_hosts``).

.. versionadded:: 2.3

``ansible_playbook_python`` is the path to the python executable used to invoke the Ansible command line tool.

These vars may be useful for filling out templates with multiple hostnames or for injecting the list into the rules for a load balancer.

Don't worry about any of this unless you think you need it.  You'll know when you do.

Also available, ``inventory_dir`` is the pathname of the directory holding Ansible's inventory host file, ``inventory_file`` is the pathname and the filename pointing to the Ansible's inventory host file.

``playbook_dir`` contains the playbook base directory.

We then have ``role_path`` which will return the current role's pathname (since 1.8). This will only work inside a role.

And finally, ``ansible_check_mode`` (added in version 2.1), a boolean magic variable which will be set to ``True`` if you run Ansible with ``--check``.

.. _variable_file_separation_details:

Variable File Separation
````````````````````````

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

Passing Variables On The Command Line
`````````````````````````````````````

In addition to ``vars_prompt`` and ``vars_files``, it is possible to set variables at the
command line using the ``--extra-vars`` (or ``-e``) argument.  Variables can be defined using
a single quoted string (containing one or more variables) using one of the formats below

key=value format::

    ansible-playbook release.yml --extra-vars "version=1.23.45 other_variable=foo"

.. note:: Values passed in using the ``key=value`` syntax are interpreted as strings.
          Use the JSON format if you need to pass in anything that shouldn't be a string (Booleans, integers, floats, lists etc).

.. versionadded:: 1.2

JSON string format::

    ansible-playbook release.yml --extra-vars '{"version":"1.23.45","other_variable":"foo"}'
    ansible-playbook arcade.yml --extra-vars '{"pacman":"mrs","ghosts":["inky","pinky","clyde","sue"]}'

.. versionadded:: 1.3

YAML string format::

    ansible-playbook release.yml --extra-vars '
    version: "1.23.45"
    other_variable: foo'

    ansible-playbook arcade.yml --extra-vars '
    pacman: mrs
    ghosts:
    - inky
    - pinky
    - clyde
    - sue'

.. versionadded:: 1.3

vars from a JSON or YAML file::

    ansible-playbook release.yml --extra-vars "@some_file.json"

This is useful for, among other things, setting the hosts group or the user for the playbook.

Escaping quotes and other special characters:

.. versionadded:: 1.2

Ensure you're escaping quotes appropriately for both your markup (e.g. JSON), and for
the shell you're operating in.::

    ansible-playbook arcade.yml --extra-vars "{\"name\":\"Conan O\'Brien\"}"
    ansible-playbook arcade.yml --extra-vars '{"name":"Conan O'\\\''Brien"}'
    ansible-playbook script.yml --extra-vars "{\"dialog\":\"He said \\\"I just can\'t get enough of those single and double-quotes"\!"\\\"\"}"

.. versionadded:: 1.3

In these cases, it's probably best to use a JSON or YAML file containing the variable
definitions.

.. _ansible_variable_precedence:

Variable Precedence: Where Should I Put A Variable?
````````````````````````````````````````````````````

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

  * role defaults [1]_
  * inventory file or script group vars [2]_
  * inventory group_vars/all [3]_
  * playbook group_vars/all [3]_
  * inventory group_vars/* [3]_
  * playbook group_vars/* [3]_
  * inventory file or script host vars [2]_
  * inventory host_vars/*
  * playbook host_vars/*
  * host facts / cached set_facts [4]_
  * inventory host_vars/* [3]_
  * playbook host_vars/* [3]_
  * host facts
  * play vars
  * play vars_prompt
  * play vars_files
  * role vars (defined in role/vars/main.yml)
  * block vars (only for tasks in block)
  * task vars (only for the task)
  * include_vars
  * set_facts / registered vars
  * role (and include_role) params
  * include params
  * extra vars (always win precedence)

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
.. note:: Group loading follows parent/child relationships. Groups of the same 'patent/child' level are then merged following alphabetical order.
          This last one can be superceeded by the user via ``ansible_group_priority``, which defaults to 0 for all groups.


Another important thing to consider (for all versions) is that connection variables override config, command line and play/role/task specific options and keywords.  For example::

    ansible -u lola myhost

This will still connect as ``ramon`` because ``ansible_ssh_user`` is set to ``ramon`` in inventory for myhost.
For plays/tasks this is also true for ``remote_user``::

 - hosts: myhost
   tasks:
    - command: i'll connect as ramon still
      remote_user: lola

This is done so host-specific settings can override the general settings. These variables are normally defined per host or group in inventory,
but they behave like other variables. If you want to override the remote user globally (even over inventory) you can use extra vars::

    ansible... -e "ansible_user=<user>"

You can also override as a normal variable in a play::

    - hosts: all
      vars:
        ansible_user: lola
      tasks:
        - command: i'll connect as lola!

.. _variable_scopes:

Variable Scopes
````````````````

Ansible has three main scopes:

 * Global: this is set by config, environment variables and the command line
 * Play: each play and contained structures, vars entries (vars; vars_files; vars_prompt), role defaults and vars.
 * Host: variables directly associated to a host, like inventory, include_vars, facts or registered task outputs

.. _variable_examples:

Variable Examples
`````````````````

 Let's show some examples and where you would choose to put what based on the kind of control you might want over values.

First off, group variables are powerful.

Site wide defaults should be defined as a ``group_vars/all`` setting.  Group variables are generally placed alongside
your inventory file.  They can also be returned by a dynamic inventory script (see :doc:`intro_dynamic_inventory`) or defined
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
See :doc:`playbooks_reuse_roles` for more info about this::

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

If you found that a little hard to understand, take a look at the `ansible-examples`_ repo on our github for a bit more about
how all of these things can work together.

.. _ansible-examples: https://github.com/ansible/ansible-examples
.. _builtin filters: http://jinja.pocoo.org/docs/templates/#builtin-filters

Advanced Syntax
```````````````

For information about advanced YAML syntax used to declare variables and have more control over the data placed in YAML files used by Ansible, see :doc:`playbooks_advanced_syntax`.

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_conditionals`
       Conditional statements in playbooks
   :doc:`playbooks_filters`
       Jinja2 filters and their uses
   :doc:`playbooks_loops`
       Looping in playbooks
   :doc:`playbooks_reuse_roles`
       Playbook organization by roles
   :doc:`playbooks_best_practices`
       Best practices in playbooks
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


