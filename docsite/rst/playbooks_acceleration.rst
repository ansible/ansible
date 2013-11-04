Accelerated Mode
================

.. contents::
   :depth: 2

.. versionadded:: 1.3

While OpenSSH using the ControlPersist feature is quite fast and scalable, there is a certain small amount of overhead involved in
using SSH connections.  While many people will not encounter a need, if you are running on a platform that doesn't have ControlPersist support (such as an EL6 control machine), you'll probably be even more interested in tuning options.

Accelerate mode is there to help connections work faster, but still uses SSH for initial secure key exchange.  There is no
additional public key infrastructure to manage, and this does not require things like NTP or even DNS. 

Accelerated mode can be anywhere from 2-6x faster than SSH with ControlPersist enabled, and 10x faster than paramiko.

Accelerated mode works by launching a temporary daemon over SSH. Once the daemon is running, Ansible will connect directly
to it via a socket connection. Ansible secures this communication by using a temporary AES key that is exchanged during
the SSH connection (this key is different for every host, and is also regenerated periodically). 

By default, Ansible will use port 5099 for the accelerated connection, though this is configurable. Once running, the daemon will accept connections for 30 minutes, after which time it will terminate itself and need to be restarted over SSH.

Accelerated mode offers several improvements over the original fireball mode from which it was based:

* No bootstrapping is required, only a single line needs to be added to each play you wish to run in accelerated mode.
* Support for sudo commands (see below for more details and caveats) is available.
* There are fewer requirements. ZeroMQ is no longer required, nor are there any special packages beyond python-keyczar 
* python 2.5 or higher is required.

In order to use accelerated mode, simply add `accelerate: true` to your play::

    ---
    - hosts: all
      accelerate: true
      tasks:
      - name: some task
        command: echo {{ item }}
        with_items:
        - foo
        - bar
        - baz

If you wish to change the port Ansible will use for the accelerated connection, just add the `accelerated_port` option::

    ---
    - hosts: all
      accelerate: true
      # default port is 5099
      accelerate_port: 10000

The `accelerate_port` option can also be specified in the environment variable ACCELERATE_PORT, or in your `ansible.cfg` configuration::

    [accelerate]
    accelerate_port = 5099

As noted above, accelerated mode also supports running tasks via sudo, however there are two important caveats:

* You must remove requiretty from your sudoers options.
* Prompting for the sudo password is not yet supported, so the NOPASSWD option is required for sudo'ed commands.

.. _fireball_mode:

Fireball Mode
`````````````

.. versionadded:: 0.8 (deprecated as of 1.3)

.. note::

    The following section has been deprecated as of Ansible 1.3 in favor of the accelerated mode described above. This
    documentation is here for users who may still be using the original fireball connection method only, and should not
    be used for any new deployments.

Ansible's core connection types of 'local', 'paramiko', and 'ssh' are augmented in version 0.8 and later by a new extra-fast
connection type called 'fireball'.  It can only be used with playbooks and does require some additional setup
outside the lines of Ansible's normal "no bootstrapping" philosophy.  You are not required to use fireball mode
to use Ansible, though some users may appreciate it.

Fireball mode works by launching a temporary 0mq daemon from SSH that by default lives for only 30 minutes before
shutting off.  Fireball mode, once running, uses temporary AES keys to encrypt a session, and requires direct
communication to given nodes on the configured port.  The default is 5099.  The fireball daemon runs as any user you
set it down as.  So it can run as you, root, or so on.  If multiple users are running Ansible as the same batch of hosts,
take care to use unique ports.

Fireball mode is roughly 10 times faster than paramiko for communicating with nodes and may be a good option
if you have a large number of hosts::

    ---

    # set up the fireball transport
    - hosts: all
      gather_facts: no
      connection: ssh # or paramiko
      sudo: yes
      tasks:
          - action: fireball

    # these operations will occur over the fireball transport
    - hosts: all
      connection: fireball
      tasks:
          - shell: echo "Hello {{ item }}"
            with_items:
                - one
                - two

In order to use fireball mode, certain dependencies must be installed on both ends.   You can use this playbook as a basis for initial bootstrapping on
any platform.  You will also need gcc and zeromq-devel installed from your package manager, which you can of course also get Ansible to install::

    ---
    - hosts: all
      sudo: yes
      gather_facts: no
      connection: ssh
      tasks:
          - easy_install: name=pip
          - pip: name={{ item }} state=present
            with_items:
              - pyzmq
              - pyasn1
              - PyCrypto
              - python-keyczar

Fedora and EPEL also have Ansible RPM subpackages available for fireball-dependencies.

Also see the module documentation section.

.. seealso::

   :doc:`playbooks`
       Introductory playbook information
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

