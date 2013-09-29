Variables
=========

All of your systems are likely not the same.  On some systems you may want to set some behavior
or configuration that is slightly different from others. Also, some of the observed behavior or state 
of remote systems might need to influence how you configure those systems.

You might have some templates for configuration files that are mostly the same, but slightly different
based on those variables.  

Variables in Ansible are how we manage with differences between systems.  Once understanding variables you'll
also want to dig into `playbooks_conditionals` and `playbooks_loops`.

.. contents::
   :depth: 2

Variables Defined in Inventory
``````````````````````````````

Often you'll want to set variables based on what groups a machine is in.  For instance, maybe machines in Boston
want to use 'boston.ntp.example.com' as an NTP server.

See the `intro_inventory` document for multiple ways on how to define variables in inventory.  

Variables Defined in a Playbook
```````````````````````````````

In a playbook, it's possible to define variables directly inline like so::

   - hosts: webservers
     vars:
       http_port: 80

This can be nice as it's right there when you are reading the playbook.

Variables defined from includes
-------------------------------

As described in `intro_roles`, variables can also be included in the playbook via include files, which may or may
not be part of an "Ansible Role".  Usage of roles is preferred as it provides a nice organizational system.

Using Variables: About Jinja2
`````````````````````````````

We've referenced various ways to define variables above, but how do you reference them?  Ansible allows you to
reference variables in your playbooks using the Jinja2 templating system.  While you can do a lot of complex
things in Jinja, only the basics are things you really need to learn.

For instance, in a simple template, you can do something like

    My amp goes to {{ max_amp_value }}

And that will provide the most basic form of variable substitution.

This is also valid directly in playbooks, and you'll occasionally want to do things like:

    template: src=foo.cfg.j2 dest={{ remote_install_path}}/foo.cfg

.. note:: ansible allows Jinja2 loops and conditionals in templates, but in playbooks, we do not use them.  Ansible
   templates are pure machine-parseable YAML.

.. note:: YAML syntax requires that if you start a value with {{ foo }} you quote the whole line, since it wants to be
   sure you aren't trying to start a YAML dictionary.  This is covered on the `YAMLSyntax` page.

Information discovered from systems: Facts
``````````````````````````````````````````

Facts are information derived from speaking with your remote systems.

An example of this might be the ip address of the remote host, or what the operating system is. 

To see what information is available, try the following::

    ansible hostname -m setup

The results of this can be used to create dynamic groups of hosts that match particular critera, see the :doc:`group_by` for details,
as well as in generalized conditional statements as discussed in the `playbook_conditionals` chapter.

Turning Off Facts
`````````````````

If you know you don't need any fact data about your hosts, and know everything about your systems centrally, you
can turn off fact gathering.  This has advantages in scaling Ansible in push mode with very large numbers of
systems, mainly, or if you are using Ansible on experimental platforms.   In any play, just do this::

    - hosts: whatever
      gather_facts: no

Local Facts (Facts.d)
`````````````````````

.. versionadded:: 1.3

As discussed in the playbooks chapter, Ansible facts are a way of getting data about remote systems for use in playbook variables.
Usually these are discovered automatically by the 'setup' module in Ansible. Users can also write custom facts modules, as described
in the API guide.  However, what if you want to have a simple way to provide system or user
provided data for use in Ansible variables, without writing a fact module?  For instance, what if you want users to be able to control some aspect about how their systems are managed? "Facts.d" is one such mechanism.

If a remotely managed system has an "/etc/ansible/facts.d" directory, any files in this directory
ending in ".fact", can be JSON, INI, or executable files returning JSON, and these can supply local facts in Ansible.

For instance assume a /etc/ansible/facts.d/preferences.fact::

    [general]
    asdf=1
    bar=2

This will produce a hash variable fact named "general" with 'asdf' and 'bar' as members.
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

And this data can be accessed in a template/playbook as::

     {{ ansible_local.preferences.general.asdf }}

The local namespace prevents any user supplied fact from overriding system facts
or variables defined elsewhere in the playbook.


Registered Variables
````````````````````

The value of a task being executed in ansible can be saved in a variable and used later.  See some examples of this in the
`playbooks_conditionals` chapter.

Accessing Complex Variable Data
```````````````````````````````

Some provided facts, like networking information, are made available as nested data structures.  To access
them a simple {{ foo }} is not sufficient, but it is still easy to do.   Here's how we get an IP address::

    {{ ansible_eth0["ipv4"]["address"] }}

Similarly, this is how we access the first element of an array::

    {{ foo[0] }}

Magic Variables, and How To Access Information About Other Hosts
````````````````````````````````````````````````````````````````

Even if you didn't define them yourself, Ansible provides a few variables for you automatically.
The most important of these are 'hostvars', 'group_names', and 'groups'.  Users should not use
these names themselves as they are reserved.  'environment' is also reserved.

Hostvars lets you ask about the variables of another host, including facts that have been gathered
about that host.  If, at this point, you haven't talked to that host yet in any play in the playbook
or set of playbooks, you can get at the variables, but you will not be able to see the facts.

If your database server wants to use the value of a 'fact' from another node, or an inventory variable
assigned to another node, it's easy to do so within a template or even an action line::

    {{ hostvars['test.example.com']['ansible_distribution'] }}

Additionally, *group_names* is a list (array) of all the groups the current host is in.  This can be used in templates using Jinja2 syntax to make template source files that vary based on the group membership (or role) of the host::

   {% if 'webserver' in group_names %}
      # some part of a configuration file that only applies to webservers
   {% endif %}

*groups* is a list of all the groups (and hosts) in the inventory.  This can be used to enumerate all hosts within a group.
For example::

   {% for host in groups['app_servers'] %}
      # something that applies to all app servers.
   {% endfor %}

A frequently used idiom is walking a group to find all IP addresses in that group::

   {% for host in groups['app_servers'] %}
      {{ hostvars[host]['ansible_eth0']['ipv4']['address'] }}
   {% endfor %}

An example of this could include pointing a frontend proxy server to all of the app servers, setting up the correct firewall rules between servers, etc.

Just a few other 'magic' variables are available...  There aren't many.

Additionally, *inventory_hostname* is the name of the hostname as configured in Ansible's inventory host file.  This can
be useful for when you don't want to rely on the discovered hostname `ansible_hostname` or for other mysterious
reasons.  If you have a long FQDN, *inventory_hostname_short* also contains the part up to the first
period, without the rest of the domain.

Don't worry about any of this unless you think you need it.  You'll know when you do.

Also available, *inventory_dir* is the pathname of the directory holding Ansible's inventory host file, *inventory_file* is the pathname and the filename pointing to the Ansible's inventory host file.

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
   similar files, this is covered in :ref:`patterns`.

Prompting For Sensitive Data
````````````````````````````

You may wish to prompt the user for certain input, and can
do so with the similarly named 'vars_prompt' section.  This has uses
beyond security, for instance, you may use the same playbook for all
software releases and would prompt for a particular release version
in a push-script::

    ---
    - hosts: all
      remote_user: root
      vars:
        from: "camelot"
      vars_prompt:
        name: "what is your name?"
        quest: "what is your quest?"
        favcolor: "what is your favorite color?"

There are full examples of both of these items in the github examples/playbooks directory.

If you have a variable that changes infrequently, it might make sense to
provide a default value that can be overridden.  This can be accomplished using
the default argument::

   vars_prompt:
     - name: "release_version"
       prompt: "Product release version"
       default: "1.0"

An alternative form of vars_prompt allows for hiding input from the user, and may later support
some other options, but otherwise works equivalently::

   vars_prompt:
     - name: "some_password"
       prompt: "Enter password"
       private: yes
     - name: "release_version"
       prompt: "Product release version"
       private: no

If `Passlib <http://pythonhosted.org/passlib/>`_ is installed, vars_prompt can also crypt the
entered value so you can use it, for instance, with the user module to define a password::

   vars_prompt:
     - name: "my_password2"
       prompt: "Enter password2"
       private: yes
       encrypt: "md5_crypt"
       confirm: yes
       salt_size: 7

You can use any crypt scheme supported by 'Passlib':

- *des_crypt* - DES Crypt
- *bsdi_crypt* - BSDi Crypt
- *bigcrypt* - BigCrypt
- *crypt16* - Crypt16
- *md5_crypt* - MD5 Crypt
- *bcrypt* - BCrypt
- *sha1_crypt* - SHA-1 Crypt
- *sun_md5_crypt* - Sun MD5 Crypt
- *sha256_crypt* - SHA-256 Crypt
- *sha512_crypt* - SHA-512 Crypt
- *apr_md5_crypt* - Apache’s MD5-Crypt variant
- *phpass* - PHPass’ Portable Hash
- *pbkdf2_digest* - Generic PBKDF2 Hashes
- *cta_pbkdf2_sha1* - Cryptacular’s PBKDF2 hash
- *dlitz_pbkdf2_sha1* - Dwayne Litzenberger’s PBKDF2 hash
- *scram* - SCRAM Hash
- *bsd_nthash* - FreeBSD’s MCF-compatible nthash encoding

However, the only parameters accepted are 'salt' or 'salt_size'. You can use you own salt using
'salt', or have one generated automatically using 'salt_size'. If nothing is specified, a salt
of size 8 will be generated.

Passing Variables On The Command Line
`````````````````````````````````````

In addition to `vars_prompt` and `vars_files`, it is possible to send variables over
the Ansible command line.  This is particularly useful when writing a generic release playbook
where you may want to pass in the version of the application to deploy::

    ansible-playbook release.yml --extra-vars "version=1.23.45 other_variable=foo"

This is useful, for, among other things, setting the hosts group or the user for the playbook.

Example::

    ---
    - remote_user: '{{ user }}'
      hosts: '{{ hosts }}'
      tasks:
         - ...

    ansible-playbook release.yml --extra-vars "hosts=vipers user=starbuck"

As of Ansible 1.2, you can also pass in extra vars as quoted JSON, like so::

    --extra-vars '{"pacman":"mrs","ghosts":["inky","pinky","clyde","sue"]}'

The key=value form is obviously simpler, but it's there if you need it!

As of Ansible 1.3, extra vars can be loaded from a JSON file with the "@" syntax::

    --extra-vars "@some_file.json"

Also as of Ansible 1.3, extra vars can be formatted as YAML, either on the command line
or in a file as above.

Conditional Imports
```````````````````

.. note: this behavior is infrequently used in Ansible.  You may wish to skip this section.  The 'group_by' module as described in the module documentation is a better way to achieve this behavior in most cases.

Sometimes you will want to do certain things differently in a playbook based on certain criteria.
Having one playbook that works on multiple platforms and OS versions is a good example.

As an example, the name of the Apache package may be different between CentOS and Debian,
but it is easily handled with a minimum of syntax in an Ansible Playbook::

    ---
    - hosts: all
      remote_user: root
      vars_files:
        - "vars/common.yml"
        - [ "vars/{{ ansible_os_family }}.yml", "vars/os_defaults.yml" ]
      tasks:
      - name: make sure apache is running
        service: name={{ apache }} state=running

.. note::
   The variable 'ansible_os_family' is being interpolated into
   the list of filenames being defined for vars_files.

As a reminder, the various YAML files contain just keys and values::

    ---
    # for vars/CentOS.yml
    apache: httpd
    somethingelse: 42

How does this work?  If the operating system was 'CentOS', the first file Ansible would try to import
would be 'vars/CentOS.yml', followed by '/vars/os_defaults.yml' if that file
did not exist.   If no files in the list were found, an error would be raised.
On Debian, it would instead first look towards 'vars/Debian.yml' instead of 'vars/CentOS.yml', before
falling back on 'vars/os_defaults.yml'. Pretty simple.

To use this conditional import feature, you'll need facter or ohai installed prior to running the playbook, but
you can of course push this out with Ansible if you like::

    # for facter
    ansible -m yum -a "pkg=facter ensure=installed"
    ansible -m yum -a "pkg=ruby-json ensure=installed"

    # for ohai
    ansible -m yum -a "pkg=ohai ensure=installed"

Ansible's approach to configuration -- separating variables from tasks, keeps your playbooks
from turning into arbitrary code with ugly nested ifs, conditionals, and so on - and results
in more streamlined & auditable configuration rules -- especially because there are a
minimum of decision points to track.

