Windows Support
===============

.. contents:: Topics

.. _windows_how_does_it_work:

Windows: How Does It Work
`````````````````````````

As you may have already read, Ansible manages Linux/Unix machines using SSH by default.  

Starting in version 1.7, Ansible also contains support for managing Windows machines.  This uses
native powershell remoting, rather than SSH.

Ansible will still be run from a Linux control machine, and uses the "winrm" Python module to talk to remote hosts.

No additional software needs to be installed on the remote machines for Ansible to manage them, it still maintains the agentless properties that make it popular on Linux/Unix.

Note that it is expected you have a basic understanding of Ansible prior to jumping into this section, so if you haven't written a Linux playbook first, it might be worthwhile to dig in there first.

.. _windows_installing:

Installing on the Control Machine
`````````````````````````````````

On a Linux control machine::

   $ pip install http://github.com/diyan/pywinrm/archive/master.zip#egg=pywinrm

If you want to use windows domain user accounts, rather than local users, also install the following on the Linux control machine::

   $ yum install krb5-workstation krb5-libs
   $ pip install kerberos

or:: 

   $ sudo apt-get install krb5-user python-kerberos

.. note::

    What's a domain user?  Do I need this?
    
    Domain users, also known as Active Directory users can be set up on windows computers.
    This lets allows a user to log in on any machine that is part of the same group of computers 
    using the same username and password, regardless of which computer they are using.
    The group of computers is known as a domain or a realm.
    
    To make this work, a couple of things need to happen:
    1/ special machines are added to the network which store the usernames and password
    of anyone who is allowed to log into the realm.  These machines are called domain controllers and typically there is 
    a primary domain controller and a secondary one that keeps things going if the primary one fails.
    2/ a configuration change is made on each machine that needs to be a part of the realm, so that it knows 
    which machine to ask when someone attempts to log in.   Its worth knowing that a conversation happens between 
    machines on the domain and the domain controllers which results in something called a ticket being stored.
    A bit like a concert ticket, the ticket says that you, the ticket holder, are allowed in until a certain time, after which you either 
    need to leave or get another ticket.
    
    Fortunately, domain users were implemented using an existing technology called kerberos.  Since kerberos 
    is freely available, linux machines can also talk to domain controllers and make use of domain users.
    
    So, if you happen to have an existing windows domain you can store a single username and password in Ansible inventory
    and use it to control many computers.  

    For the purposes of controlling windows computers, Ansible only needs to be able to get hold of a ticket and present
    it when it starts talking to the windows machine, so the setup instructions below only cover this.  
    You can do other nice things, such as allowing users to log in to your Ansible controller using the domain password, 
    caching tickets so that you can log in when away from the network, creating home directories and 
    mapping network drives when users first log in, or even turning your linux host into a domain controller but 
    since none of this is necessary for Ansible it is not described here.

.. _windows_inventory:

Inventory
`````````

Ansible's windows support relies on a few standard variables to indicate the username, password, and connection type (windows) of the remote hosts.  These variables are most easily set up in inventory.  This is used instead of SSH-keys or passwords as normally fed into Ansible::

    [windows]
    winserver1.example.com
    winserver2.example.com

In group_vars/windows.yml, define the following inventory variables::

    # local user example
    # it is suggested that these be encrypted with ansible-vault:
    # ansible-vault edit group_vars/windows.yml

    ansible_ssh_user: Administrator
    ansible_ssh_pass: SekritPasswordGoesHere
    ansible_ssh_port: 5986
    ansible_connection: winrm

If you are using windows domain users, the user should be entered as user@fully.qualified.domain.com (not
fully\\user or user@fully ).  Also, set 'ansible_authorization_type: kerberos' so that ansible knows this is a domain user login::

    # domain user example
    # it is suggested that these be encrypted with ansible-vault:
    # ansible-vault edit group_vars/windows.yml

    ansible_ssh_user: domainuser@fully.qualified.domain.com
    ansible_ssh_pass: SekritDomainPasswordGoesHere
    ansible_ssh_port: 5986
    ansible_connection: winrm
    ansible_authorization_type: kerberos


Notice that the ssh_port is not actually for SSH, but this is a holdover variable name from how Ansible is mostly an SSH-oriented system.  Again, Windows management will not happen over SSH.

When using your playbook, don't forget to specify --ask-vault-pass to provide the password to unlock the file.

If using domain users, you will need to configure the linux control machine to be a Kerberos client.

Kerberos is configured using the file /etc/krb5.conf

This may be configured manually, but on debian-based system, you can use::

    $ sudo dpkg-reconfigure krb5-config

Centos and related distributions have a tool called 'authconfig-tui' which can also be used.::

    $ yum install authconfig; authconfig-tui  

Usually the defaults in the file are acceptable, but the [realms] section needs to be configured so that it shows your full domain name and the full name of the domain controller machines (ask your windows network adminstrator for these).  If your domain is called WORKPLACE.LOCAL and your domain controllers are called DC01 and DC02 then your [realms] section would need to look like the following::

   [realms] 
    WORKPLACE.LOCAL = {
     kdc = DC-01.WORKPLACE.LOCAL
     kdc = DC-02.WORKPLACE.LOCAL
    }

A full example /etc/krb5.conf file::

     [logging]
      default = FILE:/var/log/krb5libs.log
      kdc = FILE:/var/log/krb5kdc.log
      admin_server = FILE:/var/log/kadmind.log
     
     [libdefaults]
      default_realm = FULLY.QUALIFIED.DOMAIN.COM
      ticket_lifetime = 24h
      renew_lifetime = 7d
      forwardable = true
      udp_preference_limit = 1
     
     [realms]
      FULLY.QUALIFIED.DOMAIN.COM = {
       kdc = DOMAINCONTROLLER.fully.qualified.domain.com
       admin_server = DOMAINCONTROLLER.fully.qualified.domain.com
       default_domain = fully.qualified.domain.com
      }
     
     [appdefaults]
     validate=false
     
     [domain_realm]
      .domain.com = FULLY.QUALIFIED.DOMAIN.COM
      domain.com = FULLY.QUALIFIED.DOMAIN.COM


Please also make sure the hostnames given in ansible are available in both forward and reverse DNS lookups.  For best results ensure that the clock on your linux machine is as close as possible to being synchronized with the clocks on your domain controllers.  Typically this is done on linux by installing ntpdate.

Test you are able to log in to the domain using the kinit command::

    $ kinit user@fully.qualified.domain.com

Test your configuration like so, by trying to contact your Windows nodes.  Note this is not an ICMP ping, but tests the Ansible
communication channel that leverages Windows remoting::

    ansible windows [-i inventory] -m win_ping --ask-vault-pass

If you haven't done anything to prep your systems yet, this won't work yet.  This is covered in a later
section about how to enable powershell remoting - and if necessary - how to upgrade powershell to
a version that is 3 or higher.

You'll run this command again later though, to make sure everything is working.

.. _windows_system_prep:

Windows System Prep
```````````````````

In order for Ansible to manage your windows machines, you will have to enable Powershell remoting configured.

To automate setup of WinRM, you can run `this powershell script <https://github.com/ansible/ansible/blob/devel/examples/scripts/ConfigureRemotingForAnsible.ps1>`_ on the remote machine. 

Admins may wish to modify this setup slightly, for instance to increase the timeframe of
the certificate.

If you are using windows domain users, any domain user must be added to the group 'WinRMRemoteWMIUsers__' before they can be used for Powershell remoting.  They can be added from a DOS command window using the following command::

    C:\> net localgroup WinRMRemoteWMIUsers__ /add DOMAINNAME\\domainusername

(where DOMAINNAME is the name of your domain and domainusername is the domain user you want to use).
    
.. _getting_to_powershell_three_or_higher:

Getting to Powershell 3.0 or higher
```````````````````````````````````

Powershell 3.0 or higher is needed for most provided Ansible modules for Windows, and is also required to run the above setup script.

.. note::

   Powershell 3.0 and above depend on the .NET Framework.  Install .NET Framework 4 before attempting to upgrade to Powershell 3.0.  
   If you are going for Powershell 4.0, install .NET Framework 4.5.1 or later.  Either version can be found in the microsoft download center.

Looking at an ansible checkout, copy the `examples/scripts/upgrade_to_ps3.ps1 <https://github.com/cchurch/ansible/blob/devel/examples/scripts/upgrade_to_ps3.ps1>`_ script onto the remote host and run a powershell console as an administrator.  You will now be running Powershell 3 and can try connectivity again using the win_ping technique referenced above.

.. _what_windows_modules_are_available:

What modules are available
``````````````````````````

Most of the Ansible modules in core Ansible are written for a combination of Linux/Unix machines and arbitrary web services, though there are various 
Windows modules as listed in the `"windows" subcategory of the Ansible module index <http://docs.ansible.com/list_of_windows_modules.html>`_.  

Browse this index to see what is available.

In many cases, it may not be necessary to even write or use an Ansible module.

In particular, the "script" module can be used to run arbitrary powershell scripts, allowing Windows administrators familiar with powershell a very native way to do things, as in the following playbook::

    - hosts: windows
      tasks:
        - script: foo.ps1 --argument --other-argument

Note there are a few other Ansible modules that don't start with "win" that also function, including "slurp", "raw", and "setup" (which is how fact gathering works).

.. _developers_developers_developers:

Developers: Supported modules and how it works
``````````````````````````````````````````````

Developing ansible modules are covered in a `later section of the documentation <http://developing_modules.html>`_, with a focus on Linux/Unix.
What if you want to write Windows modules for ansible though?

For Windows, ansible modules are implemented in Powershell.  Skim those Linux/Unix module development chapters before proceeding.

Windows modules live in a "windows/" subfolder in the Ansible "library/" subtree.  For example, if a module is named
"library/windows/win_ping", there will be embedded documentation in the "win_ping" file, and the actual powershell code will live in a "win_ping.ps1" file.  Take a look at the sources and this will make more sense.

Modules (ps1 files) should start as follows::

    #!powershell
    # <license>

    # WANT_JSON
    # POWERSHELL_COMMON

    # code goes here, reading in stdin as JSON and outputting JSON

The above magic is necessary to tell Ansible to mix in some common code and also know how to push modules out.  The common code contains some nice wrappers around working with hash data structures and emitting JSON results, and possibly a few more useful things.  Regular Ansible has this same concept for reusing Python code - this is just the windows equivalent.

What modules you see in windows/ are just a start.  Additional modules may be submitted as pull requests to github.

.. _windows_and_linux_control_machine:

Reminder: You Must Have a Linux Control Machine
```````````````````````````````````````````````

Note running Ansible from a Windows control machine is NOT a goal of the project.  Refrain from asking for this feature,
as it limits what technologies, features, and code we can use in the main project in the future.  A Linux control machine
will be required to manage Windows hosts.

Cygwin is not supported, so please do not ask questions about Ansible running from Cygwin.

.. _windows_facts:

Windows Facts
`````````````

Just as with Linux/Unix, facts can be gathered for windows hosts, which will return things such as the operating system version.  To see what variables are available about a windows host, run the following::

    ansible winhost.example.com -m setup

Note that this command invocation is exactly the same as the Linux/Unix equivalent.

.. _windows_playbook_example:

Windows Playbook Examples
`````````````````````````

Look to the list of windows modules for most of what is possible, though also some modules like "raw" and "script" also work on Windows, as do "fetch" and "slurp".

Here is an example of pushing and running a powershell script::

    - name: test script module
      hosts: windows
      tasks:
        - name: run test script
          script: files/test_script.ps1

Running individual commands uses the 'raw' module, as opposed to the shell or command module as is common on Linux/Unix operating systems::

    - name: test raw module
      hosts: windows
      tasks:
        - name: run ipconfig
          raw: ipconfig
          register: ipconfig
        - debug: var=ipconfig

And for a final example, here's how to use the win_stat module to test for file existence.  Note that the data returned by the win_stat module is slightly different than what is provided by the Linux equivalent::

    - name: test stat module
      hosts: windows
      tasks:
        - name: test stat module on file
          win_stat: path="C:/Windows/win.ini"
          register: stat_file

        - debug: var=stat_file

        - name: check stat_file result
          assert:
              that:
                 - "stat_file.stat.exists"
                 - "not stat_file.stat.isdir"
                 - "stat_file.stat.size > 0"
                 - "stat_file.stat.md5"

Again, recall that the Windows modules are all listed in the Windows category of modules, with the exception that the "raw", "script", and "fetch" modules are also available.  These modules do not start with a "win" prefix.

.. _windows_contributions:

Windows Contributions
`````````````````````

Windows support in Ansible is still very new, and contributions are quite welcome, whether this is in the
form of new modules, tweaks to existing modules, documentation, or something else.  Please stop by the ansible-devel mailing list if you would like to get involved and say hi.

.. seealso::

   :doc:`developing_modules`
       How to write modules
   :doc:`playbooks`
       Learning ansible's configuration management language
   `List of Windows Modules <http://docs.ansible.com/list_of_windows_modules.html>`_
       Windows specific module list, all implemented in powershell
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


