.. _ansible_faq:

Frequently Asked Questions
==========================

Here are some commonly asked questions and their answers.


.. _set_environment:

How can I set the PATH or any other environment variable for a task or entire playbook?
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Setting environment variables can be done with the `environment` keyword. It can be used at the task or the play level::

    environment:
      PATH: "{{ ansible_env.PATH }}:/thingy/bin"
      SOME: value

.. note:: starting in 2.0.1 the setup task from gather_facts also inherits the environment directive from the play, you might need to use the `|default` filter to avoid errors if setting this at play level.

.. _faq_setting_users_and_ports:

How do I handle different machines needing different user accounts or ports to log in with?
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Setting inventory variables in the inventory file is the easiest way.

For instance, suppose these hosts have different usernames and ports:

.. code-block:: ini

    [webservers]
    asdf.example.com  ansible_port=5000   ansible_user=alice
    jkl.example.com   ansible_port=5001   ansible_user=bob

You can also dictate the connection type to be used, if you want:

.. code-block:: ini

    [testcluster]
    localhost           ansible_connection=local
    /path/to/chroot1    ansible_connection=chroot
    foo.example.com     ansible_connection=paramiko

You may also wish to keep these in group variables instead, or file them in a group_vars/<groupname> file.
See the rest of the documentation for more information about how to organize variables.

.. _use_ssh:

How do I get ansible to reuse connections, enable Kerberized SSH, or have Ansible pay attention to my local SSH config file?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Switch your default connection type in the configuration file to 'ssh', or use '-c ssh' to use
Native OpenSSH for connections instead of the python paramiko library.  In Ansible 1.2.1 and later, 'ssh' will be used
by default if OpenSSH is new enough to support ControlPersist as an option.

Paramiko is great for starting out, but the OpenSSH type offers many advanced options.  You will want to run Ansible
from a machine new enough to support ControlPersist, if you are using this connection type.  You can still manage
older clients.  If you are using RHEL 6, CentOS 6, SLES 10 or SLES 11 the version of OpenSSH is still a bit old, so
consider managing from a Fedora or openSUSE client even though you are managing older nodes, or just use paramiko.

We keep paramiko as the default as if you are first installing Ansible on an EL box, it offers a better experience
for new users.

.. _use_ssh_jump_hosts:

How do I configure a jump host to access servers that I have no direct access to?
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

You can set a `ProxyCommand` in the
`ansible_ssh_common_args` inventory variable. Any arguments specified in
this variable are added to the sftp/scp/ssh command line when connecting
to the relevant host(s). Consider the following inventory group:

..  code-block:: ini

    [gatewayed]
    foo ansible_host=192.0.2.1
    bar ansible_host=192.0.2.2

You can create `group_vars/gatewayed.yml` with the following contents::

    ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p -q user@gateway.example.com"'

Ansible will append these arguments to the command line when trying to
connect to any hosts in the group `gatewayed`. (These arguments are used
in addition to any `ssh_args` from `ansible.cfg`, so you do not need to
repeat global `ControlPersist` settings in `ansible_ssh_common_args`.)

Note that `ssh -W` is available only with OpenSSH 5.4 or later. With
older versions, it's necessary to execute `nc %h:%p` or some equivalent
command on the bastion host.

With earlier versions of Ansible, it was necessary to configure a
suitable `ProxyCommand` for one or more hosts in `~/.ssh/config`,
or globally by setting `ssh_args` in `ansible.cfg`.

.. _ec2_cloud_performance:

How do I speed up management inside EC2?
++++++++++++++++++++++++++++++++++++++++

Don't try to manage a fleet of EC2 machines from your laptop.  Connect to a management node inside EC2 first
and run Ansible from there.

.. _python_interpreters:

How do I handle python not having a Python interpreter at /usr/bin/python on a remote machine?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

While you can write Ansible modules in any language, most Ansible modules are written in Python,
including the ones central to letting Ansible work.

By default, Ansible assumes it can find a :command:`/usr/bin/python` on your remote system that is
either Python2, version 2.6 or higher or Python3, 3.5 or higher.

Setting the inventory variable ``ansible_python_interpreter`` on any host will tell Ansible to
auto-replace the Python interpreter with that value instead. Thus, you can point to any Python you
want on the system if :command:`/usr/bin/python` on your system does not point to a compatible
Python interpreter.

Some platforms may only have Python 3 installed by default. If it is not installed as
:command:`/usr/bin/python`, you will need to configure the path to the interpreter via
``ansible_python_interpreter``. Although most core modules will work with Python 3, there may be some
special purpose ones which do not or you may encounter a bug in an edge case. As a temporary
workaround you can install Python 2 on the managed host and configure Ansible to use that Python via
``ansible_python_interpreter``. If there's no mention in the module's documentation that the module
requires Python 2, you can also report a bug on our `bug tracker
<https://github.com/ansible/ansible/issues>`_ so that the incompatibility can be fixed in a future release.

Do not replace the shebang lines of your python modules.  Ansible will do this for you automatically at deploy time.

Common Platform Issues
++++++++++++++++++++++

Running in a virtualenv
-----------------------

You can install Ansible into a virtualenv on the controller quite simply:

.. code-block:: shell

    $ virtualenv ansible
    $ source ./ansible/bin/activate
    $ pip install ansible

If you want to run under Python 3 instead of Python 2 you may want to change that slightly:

.. code-block:: shell

    $ virtualenv ansible
    $ source ./ansible/bin/activate
    $ pip3 install ansible

If you need to use any libraries which are not available via pip (for instance, SELinux Python
bindings on systems such as Red Hat Enterprise Linux or Fedora that have SELinux enabled) then you
need to install them into the virtualenv.  There are two methods:

* When you create the virtualenv, specify ``--system-site-packages`` to make use of any libraries
  installed in the system's Python:

  .. code-block:: shell

      $ virtualenv ansible --system-site-packages

* Copy those files in manually from the system.  For instance, for SELinux bindings you might do:

  .. code-block:: shell

      $ virtualenv ansible --system-site-packages
      $ cp -r -v /usr/lib64/python3.*/site-packages/selinux/ ./py3-ansible/lib64/python3.*/site-packages/
      $ cp -v /usr/lib64/python3.*/site-packages/*selinux*.so ./py3-ansible/lib64/python3.*/site-packages/


Running on BSD
--------------

.. seealso:: :ref:`working_with_bsd`


Running on Solaris
------------------

By default, Solaris 10 and earlier run a non-POSIX shell which does not correctly expand the default
tmp directory Ansible uses ( :file:`~/.ansible/tmp`). If you see module failures on Solaris machines, this
is likely the problem. There are several workarounds:

* You can set ``remote_tmp`` to a path that will expand correctly with the shell you are using (see the plugin documentation for :ref:`C shell<csh_shell>`, :ref:`fish shell<fish_shell>`, and :ref:`Powershell<powershell_shell>`).  For
  example, in the ansible config file you can set::

    remote_tmp=$HOME/.ansible/tmp

  In Ansible 2.5 and later, you can also set it per-host in inventory like this::

    solaris1 ansible_remote_tmp=$HOME/.ansible/tmp

* You can set :ref:`ansible_shell_executable<ansible_shell_executable>` to the path to a POSIX compatible shell.  For
  instance, many Solaris hosts have a POSIX shell located at :file:`/usr/xpg4/bin/sh` so you can set
  this in inventory like so::

    solaris1 ansible_shell_executable=/usr/xpg4/bin/sh

  (bash, ksh, and zsh should also be POSIX compatible if you have any of those installed).


.. _use_roles:

What is the best way to make content reusable/redistributable?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

If you have not done so already, read all about "Roles" in the playbooks documentation.  This helps you make playbook content
self-contained, and works well with things like git submodules for sharing content with others.

If some of these plugin types look strange to you, see the API documentation for more details about ways Ansible can be extended.

.. _configuration_file:

Where does the configuration file live and what can I configure in it?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


See :doc:`../installation_guide/intro_configuration`.

.. _who_would_ever_want_to_disable_cowsay_but_ok_here_is_how:

How do I disable cowsay?
++++++++++++++++++++++++

If cowsay is installed, Ansible takes it upon itself to make your day happier when running playbooks.  If you decide
that you would like to work in a professional cow-free environment, you can either uninstall cowsay, or set the :envvar:`ANSIBLE_NOCOWS` environment variable:

.. code-block:: shell-session

    export ANSIBLE_NOCOWS=1

.. _browse_facts:

How do I see a list of all of the ansible\_ variables?
++++++++++++++++++++++++++++++++++++++++++++++++++++++

Ansible by default gathers "facts" about the machines under management, and these facts can be accessed in Playbooks and in templates. To see a list of all of the facts that are available about a machine, you can run the "setup" module as an ad-hoc action:

.. code-block:: shell-session

    ansible -m setup hostname

This will print out a dictionary of all of the facts that are available for that particular host. You might want to pipe the output to a pager.

.. _browse_inventory_vars:

How do I see all the inventory vars defined for my host?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

By running the following command, you can see vars resulting from what you've defined in the inventory:

.. code-block:: shell-session

    ansible -m debug -a "var=hostvars['hostname']" localhost

.. _host_loops:

How do I loop over a list of hosts in a group, inside of a template?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

A pretty common pattern is to iterate over a list of hosts inside of a host group, perhaps to populate a template configuration
file with a list of servers. To do this, you can just access the "$groups" dictionary in your template, like this:

.. code-block:: jinja

    {% for host in groups['db_servers'] %}
        {{ host }}
    {% endfor %}

If you need to access facts about these hosts, for instance, the IP address of each hostname, you need to make sure that the facts have been populated. For example, make sure you have a play that talks to db_servers::

    - hosts:  db_servers
      tasks:
        - debug: msg="doesn't matter what you do, just that they were talked to previously."

Then you can use the facts inside your template, like this:

.. code-block:: jinja

    {% for host in groups['db_servers'] %}
       {{ hostvars[host]['ansible_eth0']['ipv4']['address'] }}
    {% endfor %}

.. _programatic_access_to_a_variable:

How do I access a variable name programmatically?
+++++++++++++++++++++++++++++++++++++++++++++++++

An example may come up where we need to get the ipv4 address of an arbitrary interface, where the interface to be used may be supplied
via a role parameter or other input.  Variable names can be built by adding strings together, like so:

.. code-block:: jinja

    {{ hostvars[inventory_hostname]['ansible_' + which_interface]['ipv4']['address'] }}

The trick about going through hostvars is necessary because it's a dictionary of the entire namespace of variables.  'inventory_hostname'
is a magic variable that indicates the current host you are looping over in the host loop.

.. _first_host_in_a_group:

How do I access a variable of the first host in a group?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

What happens if we want the ip address of the first webserver in the webservers group?  Well, we can do that too.  Note that if we
are using dynamic inventory, which host is the 'first' may not be consistent, so you wouldn't want to do this unless your inventory
is static and predictable.  (If you are using :doc:`../reference_appendices/tower`, it will use database order, so this isn't a problem even if you are using cloud
based inventory scripts).

Anyway, here's the trick:

.. code-block:: jinja

    {{ hostvars[groups['webservers'][0]]['ansible_eth0']['ipv4']['address'] }}

Notice how we're pulling out the hostname of the first machine of the webservers group.  If you are doing this in a template, you
could use the Jinja2 '#set' directive to simplify this, or in a playbook, you could also use set_fact::

    - set_fact: headnode={{ groups[['webservers'][0]] }}

    - debug: msg={{ hostvars[headnode].ansible_eth0.ipv4.address }}

Notice how we interchanged the bracket syntax for dots -- that can be done anywhere.

.. _file_recursion:

How do I copy files recursively onto a target host?
+++++++++++++++++++++++++++++++++++++++++++++++++++

The "copy" module has a recursive parameter.  However, take a look at the "synchronize" module if you want to do something more efficient for a large number of files.  The "synchronize" module wraps rsync.  See the module index for info on both of these modules.

.. _shell_env:

How do I access shell environment variables?
++++++++++++++++++++++++++++++++++++++++++++

If you just need to access existing variables, use the 'env' lookup plugin.  For example, to access the value of the HOME
environment variable on the management machine::

   ---
   # ...
     vars:
        local_home: "{{ lookup('env','HOME') }}"

If you need to set environment variables, see the Advanced Playbooks section about environments.

Remote environment variables are available via facts in the 'ansible_env' variable:

.. code-block:: jinja

   {{ ansible_env.SOME_VARIABLE }}

.. _user_passwords:

How do I generate crypted passwords for the user module?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The mkpasswd utility that is available on most Linux systems is a great option:

.. code-block:: shell-session

    mkpasswd --method=sha-512
    

If this utility is not installed on your system (e.g. you are using OS X) then you can still easily
generate these passwords using Python. First, ensure that the `Passlib <https://bitbucket.org/ecollins/passlib/wiki/Home>`_
password hashing library is installed:

.. code-block:: shell-session

    pip install passlib

Once the library is ready, SHA512 password values can then be generated as follows:

.. code-block:: shell-session

    python -c "from passlib.hash import sha512_crypt; import getpass; print(sha512_crypt.using(rounds=5000).hash(getpass.getpass()))"

Use the integrated :ref:`hash_filters` to generate a hashed version of a password.
You shouldn't put plaintext passwords in your playbook or host_vars; instead, use :doc:`../user_guide/playbooks_vault` to encrypt sensitive data.

In OpenBSD, a similar option is available in the base system called encrypt(1):

.. code-block:: shell-session

    encrypt

.. _commercial_support:

Ansible supports dot notation and array notation for variables. Which notation should I use?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The dot notation comes from Jinja and works fine for variables without special
characters. If your variable contains dots (.), colons (:), or dashes (-) it is
safer to use the array notation for variables.

.. code-block:: jinja

    item[0]['checksum:md5']
    item['section']['2.1']
    item['region']['Mid-Atlantic']
    It is {{ temperature['Celsius']['-3'] }} outside.

Can I get training on Ansible?
++++++++++++++++++++++++++++++

Yes!  See our `services page <https://www.ansible.com/consulting>`_ for information on our services and training offerings. Email `info@ansible.com <mailto:info@ansible.com>`_ for further details.

We also offer free web-based training classes on a regular basis. See our `webinar page <https://www.ansible.com/webinars-training>`_ for more info on upcoming webinars.

.. _web_interface:

Is there a web interface / REST API / etc?
++++++++++++++++++++++++++++++++++++++++++

Yes!  Ansible, Inc makes a great product that makes Ansible even more powerful
and easy to use. See :doc:`../reference_appendices/tower`.

.. _docs_contributions:

How do I submit a change to the documentation?
++++++++++++++++++++++++++++++++++++++++++++++

Great question!  Documentation for Ansible is kept in the main project git repository, and complete instructions for contributing can be found in the docs README `viewable on GitHub <https://github.com/ansible/ansible/blob/devel/docs/docsite/README.md>`_.  Thanks!

.. _keep_secret_data:

How do I keep secret data in my playbook?
+++++++++++++++++++++++++++++++++++++++++

If you would like to keep secret data in your Ansible content and still share it publicly or keep things in source control, see :doc:`../user_guide/playbooks_vault`.

If you have a task that you don't want to show the results or command given to it when using -v (verbose) mode, the following task or playbook attribute can be useful::

    - name: secret task
      shell: /usr/bin/do_something --value={{ secret_value }}
      no_log: True

This can be used to keep verbose output but hide sensitive information from others who would otherwise like to be able to see the output.

The no_log attribute can also apply to an entire play::

    - hosts: all
      no_log: True

Though this will make the play somewhat difficult to debug.  It's recommended that this
be applied to single tasks only, once a playbook is completed. Note that the use of the
no_log attribute does not prevent data from being shown when debugging Ansible itself via
the :envvar:`ANSIBLE_DEBUG` environment variable.


.. _when_to_use_brackets:
.. _dynamic_variables:
.. _interpolate_variables:

When should I use {{ }}? Also, how to interpolate variables or dynamic variable names
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

A steadfast rule is 'always use ``{{ }}`` except when ``when:``'.
Conditionals are always run through Jinja2 as to resolve the expression,
so ``when:``, ``failed_when:`` and ``changed_when:`` are always templated and you should avoid adding ``{{ }}``.

In most other cases you should always use the brackets, even if previously you could use variables without specifying (like ``loop`` or ``with_`` clauses),
as this made it hard to distinguish between an undefined variable and a string.

Another rule is 'moustaches don't stack'. We often see this:

.. code-block:: jinja

     {{ somevar_{{other_var}} }}

The above DOES NOT WORK, if you need to use a dynamic variable use the hostvars or vars dictionary as appropriate:

.. code-block:: jinja

    {{ hostvars[inventory_hostname]['somevar_' + other_var] }}

Why don't you ship in X format?
+++++++++++++++++++++++++++++++

Several reasons, in most cases it has to do with maintainability, there are tons of ways to ship software and it is a herculean task to try to support them all.
In other cases there are technical issues, for example, for python wheels, our dependencies are not present so there is little to no gain.

.. _i_dont_see_my_question:

I don't see my question here
++++++++++++++++++++++++++++

Please see the section below for a link to IRC and the Google Group, where you can ask your question there.

.. seealso::

   :doc:`../user_guide/playbooks`
       An introduction to playbooks
   :doc:`../user_guide/playbooks_best_practices`
       Best practices advice
   `User Mailing List <http://groups.google.com/group/ansible-project>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
