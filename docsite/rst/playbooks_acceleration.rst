Accelerated Mode
================

.. versionadded:: 1.3

You Might Not Need This!
````````````````````````

Are you running Ansible 1.5 or later?  If so, you may not need accelerated mode due to a new feature called "SSH pipelining" and should read the :ref:`pipelining` section of the documentation.

For users on 1.5 and later, accelerated mode only makes sense if you (A) are managing from an Enterprise Linux 6 or earlier host
   and still are on paramiko, or (B) can't enable TTYs with sudo as described in the pipelining docs.

If you can use pipelining, Ansible will reduce the amount of files transferred over the wire, 
making everything much more efficient, and performance will be on par with accelerated mode in nearly all cases, possibly excluding very large file transfer.   Because less moving parts are involved, pipelining is better than accelerated mode for nearly all use cases.

Accelerated moded remains around in support of EL6
control machines and other constrained environments.

Accelerated Mode Details
````````````````````````

While OpenSSH using the ControlPersist feature is quite fast and scalable, there is a certain small amount of overhead involved in
using SSH connections.  While many people will not encounter a need, if you are running on a platform that doesn't have ControlPersist support (such as an EL6 control machine), you'll probably be even more interested in tuning options.

Accelerated mode is there to help connections work faster, but still uses SSH for initial secure key exchange.  There is no
additional public key infrastructure to manage, and this does not require things like NTP or even DNS. 

Accelerated mode can be anywhere from 2-6x faster than SSH with ControlPersist enabled, and 10x faster than paramiko.

Accelerated mode works by launching a temporary daemon over SSH. Once the daemon is running, Ansible will connect directly
to it via a socket connection. Ansible secures this communication by using a temporary AES key that is exchanged during
the SSH connection (this key is different for every host, and is also regenerated periodically). 

By default, Ansible will use port 5099 for the accelerated connection, though this is configurable. Once running, the daemon will accept connections for 30 minutes, after which time it will terminate itself and need to be restarted over SSH.

Accelerated mode offers several improvements over the (deprecated) original fireball mode from which it was based:

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

As of Ansible version `1.6`, you can also allow the use of multiple keys for connections from multiple Ansible management nodes. To do so, add the following option
to your `ansible.cfg` configuration::

    accelerate_multi_key = yes

When enabled, the daemon will open a UNIX socket file (by default `$ANSIBLE_REMOTE_TEMP/.ansible-accelerate/.local.socket`). New connections over SSH can
use this socket file to upload new keys to the daemon.

