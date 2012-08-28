API & Integrations
==================

There are two major ways to use Ansible from an API perspective.   The primary way
is to use the Ansible python API to control nodes.  Ansible is written in its own
API so you have a considerable amount of power there.  

Also covered here, Ansible's
list of hosts, groups, and variables assigned to each host can be driven from
external sources.   We'll start with the Python API.

.. contents:: `Table of contents`
   :depth: 2
   :backlinks: top

Python API
----------

The Python API is very powerful, and is how the ansible CLI and ansible-playbook
are implemented.  

It's pretty simple::

    import ansible.runner

    runner = ansible.runner.Runner(
       module_name='ping',
       module_args='',
       pattern='web*',
       forks=10
    )
    datastructure = runner.run()

The run method returns results per host, grouped by whether they
could be contacted or not.  Return types are module specific, as
expressed in the 'ansible-modules' documentation.::

    {
        "dark" : {
           "web1.example.com" : "failure message"
        }
        "contacted" : {
           "web2.example.com" : 1
        }
    }

A module can return any type of JSON data it wants, so Ansible can
be used as a framework to rapidly build powerful applications and scripts.

Detailed API Example
````````````````````

The following script prints out the uptime information for all hosts::

    #!/usr/bin/python

    import ansible.runner
    import sys

    # construct the ansible runner and execute on all hosts
    results = ansible.runner.Runner(
        pattern='*', forks=10,
        module_name='command', module_args='/usr/bin/uptime',
    ).run()

    if results is None:
       print "No hosts found"
       sys.exit(1)

    print "UP ***********"
    for (hostname, result) in results['contacted'].items():
        if not 'failed' in result:
            print "%s >>> %s" % (hostname, result['stdout'])

    print "FAILED *******"
    for (hostname, result) in results['contacted'].items():
        if 'failed' in result:
            print "%s >>> %s" % (hostname, result['msg'])

    print "DOWN *********"
    for (hostname, result) in results['dark'].items():
        print "%s >>> %s" % (hostname, result)

Advanced programmers may also wish to read the source to ansible itself, for
it uses the Runner() API (with all available options) to implement the
command line tools ``ansible`` and ``ansible-playbook``.

External Inventory
------------------

Often a user of a configuration management system will want to keep inventory
in a different system.  Frequent examples include LDAP, `Cobbler <http://cobbler.github.com>`_, 
or a piece of expensive enterprisey CMDB software.   Ansible easily supports all
of these options via an external inventory system.  The `ansible-plugins <http://github.com/ansible/ansible-plugins>`_ repo contains some of these already.

It's possible to write an external inventory script in any language.  If you are familiar with Puppet terminology, this concept is basically the same as 'external nodes', with the slight difference that it also defines which hosts are managed.

Script Conventions
``````````````````

When the external node script is called with the single argument '--list', the script must return a JSON hash/dictionary of all the groups to be managed, with a list of each host/IP as the value for each hash/dictionary element, like so::

    {
        'databases'  : [ 'host1.example.com', 'host2.example.com' ],
        'webservers' : [ 'host2.example.com', 'host3.example.com' ],
        'atlanta'    : [ 'host1.example.com', 'host4.example.com', 'host5.example.com' ] 
    }

When called with the arguments '--host <hostname>' (where <hostname> is a host from above), the script must return either an empty JSON
hash/dictionary, or a list of key/value variables to make available to templates or playbooks.  Returning variables is optional,
if the script does not wish to do this, returning an empty hash/dictionary is the way to go::

    {
        'favcolor'   : 'red',
        'ntpserver'  : 'wolf.example.com',
        'monitoring' : 'pack.example.com'
    }

Example: The Cobbler External Inventory Script
``````````````````````````````````````````````

It is expected that many Ansible users will also be `Cobbler <http://cobbler.github.com>`_ users.  Cobbler has a generic
layer that allows it to represent data for multiple configuration management systems (even at the same time), and has
been referred to as a 'lightweight CMDB' by some admins.   This particular script will communicate with Cobbler
using Cobbler's XMLRPC API.

To tie Ansible's inventory to Cobbler (optional), copy `this script <https://github.com/ansible/ansible-plugins/blob/master/inventory/cobbler.py>`_ to /etc/ansible/hosts and `chmod +x` the file.  cobblerd will now need
to be running when you are using Ansible.

Test the file by running `./etc/ansible/hosts` directly.   You should see some JSON data output, but it may not have
anything in it just yet.

Let's explore what this does.  In cobbler, assume a scenario somewhat like the following::

    cobbler profile add --name=webserver --distro=CentOS6-x86_64
    cobbler profile edit --name=webserver --mgmt-classes="webserver" --ksmeta="a=2 b=3"
    cobbler system edit --name=foo --dns-name="foo.example.com" --mgmt-classes="atlanta" --ksmeta="c=4"
    cobbler system edit --name=bar --dns-name="bar.example.com" --mgmt-classes="atlanta" --ksmeta="c=5"

In the example above, the system 'foo.example.com' will be addressable by ansible directly, but will also be addressable when using the group names 'webserver' or 'atlanta'.  Since Ansible uses SSH, we'll try to contract system foo over 'foo.example.com', only, never just 'foo'.  Similarly, if you try "ansible foo" it wouldn't find the system... but "ansible 'foo*'" would, because the system DNS name starts with 'foo'.

The script doesn't just provide host and group info.  In addition, as a bonus, when the 'setup' module is run (which happens automatically when using playbooks), the variables 'a', 'b', and 'c' will all be auto-populated in the templates::

    # file: /srv/motd.j2
    Welcome, I am templated with a value of a={{ a }}, b={{ b }}, and c={{ c }}

Which could be executed just like this::

    ansible webserver -m setup
    ansible webserver -m template -a "src=/tmp/motd.j2 dest=/etc/motd"

.. note::
   The name 'webserver' came from cobbler, as did the variables for
   the config file.  You can still pass in your own variables like
   normal in Ansible, but variables from the external inventory script
   will override any that have the same name.

So, with the template above (motd.j2), this would result in the following data being written to /etc/motd for system 'foo'::

    Welcome, I am templated with a value of a=2, b=3, and c=4

And on system 'bar' (bar.example.com)::

    Welcome, I am templated with a value of a=2, b=3, and c=5

And technically, though there is no major good reason to do it, this also works too::

    ansible webserver -m shell -a "echo {{ a }}"

So in other words, you can use those variables in arguments/actions as well.  You might use this to name
a conf.d file appropriately or something similar.  Who knows?

So that's the Cobbler integration support -- using the cobbler script as an example, it should be trivial to adapt Ansible to pull inventory, as well as variable information, from any data source.  If you create anything interesting, please share with the mailing list, and we can keep it in the source code tree for others to use.

Example: AWS EC2 External Inventory Script
``````````````````````````````````````````

If you use Amazon Web Services EC2, maintaining an inventory file might not be the best approach. For this reason, you can use the `EC2 external inventory  <https://github.com/ansible/ansible-plugins/blob/master/inventory/ec2.py>`_ script.

You can use this script in one of two ways. The easiest is to use Ansible's ``-i`` command line option and specify the path to the script.

    ansible -i ec2.py -u ubuntu us-east-1d -m ping

The second option is to copy the script to `/etc/ansible/hosts` and `chmod +x` it. You will also need to copy the ``ec2.ini`` file to `/etc/ansible/ec2.ini`. Then you can run ansible as you would normally.

To successfully make an API call to AWS, you will need to configure Boto (the Python interface to AWS). There are a `variety of methods <http://docs.pythonboto.org/en/latest/boto_config_tut.html>`_ available, but the simplest is just to export two environment variables:

    export AWS_ACCESS_KEY_ID='AK123'
    export AWS_SECRET_ACCESS_KEY='abc123'

You can test the script by itself to make sure your config is correct

    cd examples/scripts
    ./ec2_external_inventory.py --list

After a few moments, you should see your entire EC2 inventory across all regions in JSON.

Since each region requires its own API call, if you are only using a small set of regions, feel free to edit ``ec2.ini`` and list only the regions you are interested in. There are other config options in ``ec2.ini`` including cache control, and destination variables.

At their heart, inventory files are simply a mapping from some name to a destination address. The default ``ec2.ini`` settings are configured for running Ansible from outside EC2 (from your laptop for example). If you are running Ansible from within EC2, internal DNS names and IP addresses may make more sense than public DNS names. In this case, you can modify the ``destination_variable`` in ``ec2.ini`` to be the private DNS name of an instance. This is particularly important when running Ansible within a private subnet inside a VPC, where the only way to access an instance is via its private IP address. For VPC instances, `vpc_destination_variable` in ``ec2.ini`` provides a means of using which ever `boto.ec2.instance variable <http://docs.pythonboto.org/en/latest/ref/ec2.html#module-boto.ec2.instance>`_ makes the most sense for your use case.

The EC2 external inventory provides mappings to instances from several groups:

Instance ID
  These are groups of one since instance IDs are unique.
  e.g.
  ``i-00112233``
  ``i-a1b1c1d1`` 

Region
  A group of all instances in an AWS region.
  e.g.
  ``us-east-1``
  ``us-west-2``

Availability Zone
  A group of all instances in an availability zone.
  e.g.
  ``us-east-1a``
  ``us-east-1b``

Security Group
  Instances belong to one or more security groups. A group is created for each security group, with all characters except alphanumerics, dashes (-) converted to underscores (_). Each group is prefixed by ``security_group_``
  e.g.
  ``security_group_default``
  ``security_group_webservers``
  ``security_group_Pete_s_Fancy_Group``

Tags
  Each instance can have a variety of key/value pairs associated with it called Tags. The most common tag key is 'Name', though anything is possible. Each key/value pair is its own group of instances, again with special characters converted to underscores, in the format ``tag_KEY_VALUE``
  e.g.
  ``tag_Name_Web``
  ``tag_Name_redis-master-001``
  ``tag_aws_cloudformation_logical-id_WebServerGroup``

When the Ansible is interacting with a specific server, the EC2 inventory script is called again with the ``--host HOST`` option. This looks up the HOST in the index cache to get the instance ID, and then makes an API call to AWS to get information about that specific instance. It then makes information about that instance available as variables to your playbooks. Each variable is prefixed by ``ec2_``. Here are some of the variables available:

- ec2_architecture
- ec2_description
- ec2_dns_name
- ec2_id
- ec2_image_id
- ec2_instance_type
- ec2_ip_address
- ec2_kernel
- ec2_key_name
- ec2_launch_time
- ec2_monitored
- ec2_ownerId
- ec2_placement
- ec2_platform
- ec2_previous_state
- ec2_private_dns_name
- ec2_private_ip_address
- ec2_public_dns_name
- ec2_ramdisk
- ec2_region
- ec2_root_device_name
- ec2_root_device_type
- ec2_security_group_ids
- ec2_security_group_names
- ec2_spot_instance_request_id
- ec2_state
- ec2_state_code
- ec2_state_reason
- ec2_status
- ec2_subnet_id
- ec2_tag_Name
- ec2_tenancy
- ec2_virtualization_type
- ec2_vpc_id

Both ``ec2_security_group_ids`` and ``ec2_security_group_names`` are comma-separated lists of all security groups. Each EC2 tag is a variable in the format ``ec2_tag_KEY``.

To see the complete list of variables available for an instance, run the script by itself::

    cd examples/scripts
    ./ec2_external_inventory.py --host ec2-12-12-12-12.compute-1.amazonaws.com


.. seealso::

   :doc:`modules`
       List of built-in modules
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

