Frequently Asked Questions
==========================

Here are some commonly-asked questions and their answers.

.. contents::
   :depth: 2
   :backlinks: top

How do I handle different machines needing different user accounts or ports to log in with?
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Setting inventory variables in the inventory file is the easiest way.

For instance, suppose these hosts have different usernames and ports::

    [webservers]
    asdf.example.com  ansible_ssh_port=5000   ansible_ssh_user=alice
    jkl.example.com   ansible_ssh_port=5001   ansible_ssh_user=bob

You can also dictate the connection type to be used, if you want::

    [testcluster]
    localhost           ansible_connection=local
    /path/to/chroot1    ansible_connection=chroot
    foo.example.com
    bar.example.com 

You may also wish to keep these in group variables instead, or file in them in a group_vars/<groupname> file.
See the rest of the documentation for more information about how to organize variables.


How do I get ansible to reuse connections, enable Kerberized SSH, or have Ansible pay attention to my local SSH config file?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Switch your default connectiont type in the configuration file to 'ssh', or use '-c ssh' to use
Native OpenSSH for connections instead of the python paramiko library.

Paramiko is great for starting out, but the OpenSSH type offers many advanced options.  You will want to run Ansible
from a machine new enough to support ControlPersist, if you are using this connection type.  You can still manage
older clients.  If you are using RHEL 6, CentOS 6, SLES 10 or SLES 11 the version of OpenSSH is still a bit old, so 
consider managing from a Fedora or openSUSE client even though you are managing older nodes, or just use paramiko.

We keep paramiko as the default as if you are first installing Ansible on an EL box, it offers a better experience
for new users.

How do I speed up management inside EC2?
++++++++++++++++++++++++++++++++++++++++

Don't try to manage a fleet of EC2 machines from your laptop.  Connect to a management node inside EC2 first
and run Ansible from there.

How do I handle python pathing not having a Python 2.X in /usr/bin/python on a remote machine?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

While you can write ansible modules in any language, most ansible modules are written in Python, and some of these
are important core ones.

By default Ansible assumes it can find a /usr/bin/python on your remote system that is a 2.X version of Python, specifically
2.4 or higher.

Setting of an inventory variable 'ansible_python_interpreter' on any host will allow Ansible to auto-replace the interpreter
used when executing python modules.   Thus, you can point to any python you want on the system if /usr/bin/python on your
system does not point to a Python 2.X interpreter.  

Some Linux operating systems, such as Arch, may only have Python 3 installed by default.  This is not sufficient and you will
get syntax errors trying to run modules with Python 3.  Python 3 is essentially not the same
language as Python 2.  Ansible modules currently need to support older Pythons for users that  still have Enterprise Linux 5 deployed, so they are not yet ported to run under Python 3.0.  This is not a problem though as you can just install Python 2 also on a managed host.

Python 3.0 support will likely be addressed at a later point in time when usage becomes more mainstream.

Do not replace the shebang lines of your python modules.  Ansible will do this for you automatically at deploy time.

What is the best way to make content reusable/redistributable?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

If you have not done so already, read all about "Roles" in the playbooks documentation.  This helps you make playbook content
self contained, and works will with things like git submodules for sharing content with others.

If some of these plugin types look strange to you, see the API documentation for more details about ways Ansible can be extended.

Where does the configuration file live and what can I configure in it?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Technically ansible doesn't need a configuration file, but OS packages are likely to include a default one in /etc/ansible/ansible.cfg
that you may customize.  You can also install your own copy in ~/.ansible.cfg or keep a copy in a directory relative to your playbook named "ansible.cfg".

For what values you can use in this file, see `the configuration file on github <https://github.com/ansible/ansible/blob/devel/examples/ansible.cfg>`_.

Generally you would configure the default module path or connection type here, among other things, though the defaults are usually
good enough for starting out.

How do I disable cowsay?
++++++++++++++++++++++++

If cowsay is installed, Ansible takes it upon itself to make your day happier when running playbooks.  If you decide
that you would like to work in a professional cow-free environment, you can either uninstall cowsay, or set an environment variable::

    export ANSIBLE_NOCOWS=1

How do I see a list of all of the ansible\_ variables?
++++++++++++++++++++++++++++++++++++++++++++++++++++++

Ansible by default gathers "facts" about the machines under management, and these facts can be accessed in Playbooks and in templates. To see a list of all of the facts that are available about a machine, you can run the "setup" module as an ad-hoc action::

    ansible -m setup hostname

This will print out a dictionary of all of the facts that are available for that particular host.

How do I loop over a list of hosts in a group, inside of a template?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

A pretty common pattern is to iterate over a list of hosts inside of a host group, perhaps to populate a template configuration
file with a list of servers. To do this, you can just access the "$groups" dictionary in your template, like this::

    {% for host in groups['db_servers'] %}
        {{ host }}
    {% endfor %}

If you need to access facts about these hosts, for instance, the IP address of each hostname, you need to make sure that the facts have been populated. For example, make sure you have a play that talks to db_servers::

    - hosts:  db_servers
      tasks:
        - # doesn't matter what you do, just that they were talked to previously.

Then you can use the facts inside your template, like this::

    {% for host in groups['db_servers'] %}
       {{ hostvars[host]['ansible_eth0']['ipv4']['address'] }}
    {% endfor %}

How do I copy files recursively onto a target host?
+++++++++++++++++++++++++++++++++++++++++++++++++++

The "copy" module doesn't handle recursive copies of directories. A common solution to do this is to use a local action to call 'rsync' to recursively copy files to the managed servers.

Here is an example::

    ---
    # ...
      tasks:
      - name: recursively copy files from management server to target
        local_action: command rsync -a /path/to/files $inventory_hostname:/path/to/target/

Note that you'll need passphrase-less SSH or ssh-agent set up to let rsync copy without prompting for a passphase or password.

How do I access shell environment variables?
++++++++++++++++++++++++++++++++++++++++++++

If you just need to access existing variables, use the 'env' lookup plugin.  For example, to access the value of the HOME
environment variable on management machine::

   ---
   # ...
     vars:
        local_home: "{{ lookup('env','HOME') }}"

If you need to set environment variables, see the Advanced Playbooks section about environments.

Can I get training on Ansible or find commerical support?
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Yes!  See `AnsibleWorks.com <http://ansibleworks.com>`_ or email `info@ansibleworks.com <mailto:info@ansibleworks.com>`_.

How do I submit a change to the documentation?
++++++++++++++++++++++++++++++++++++++++++++++

Great question!  Documentation for the Ansible project is kept in `Github <https://github.com/ansible/ansible/tree/devel/docsite/latest/rst>`_ in restructured text format.  Simply send in a pull request for changes, or file a ticket if you found an error but do not have time to submit
a change request.   Thanks!

I don't see my question here
++++++++++++++++++++++++++++

See the "Resources" section of the documentation for a link to the IRC and Google Group.



