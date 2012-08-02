Playbooks
=========

Playbooks are a completely different way to use ansible and are
particularly awesome.   They are the basis for a really simple 
configuration management and multi-machine deployment system, 
unlike any that already exist, and
one that is very well suited to deploying complex applications.

Playbooks can declare configurations, but they can also orchestrate steps of
any manual ordered process, even as different steps must bounce back and forth
between sets of machines in particular orders.  They can launch tasks 
synchronously or asynchronously.

While you might run the main /usr/bin/ansible program for ad-hoc
tasks, playbooks are more likely to be kept in source control and used
to push out your configuration or assure the configurations of your
remote systems are in spec.

Let's dive in and see how they work.  As you go, you may wish to open 
the `github examples directory <https://github.com/ansible/ansible/tree/master/examples/playbooks>`_ in
another tab, so you can apply the theory to what things look like in practice.

Playbook Example
````````````````

Playbooks are expressed in YAML format and have a minimum of syntax.
Each playbook is composed of one or more 'plays' in a list.  

By composing a playbook of multiple 'plays', it is possible to
orchestrate multi-machine deployments, running certain steps on all
machines in the webservers group, then certain steps on the database
server group, then more commands back on the webservers group, etc. 

For starters, here's a playbook that contains just one play::

    ---
    - hosts: webservers
      vars:
        http_port: 80
        max_clients: 200
      user: root
      tasks:
      - name: ensure apache is at the latest version
        action: yum pkg=httpd state=latest
      - name: write the apache config file
        action: template src=/srv/httpd.j2 dest=/etc/httpd.conf
        notify:
        - restart apache
      - name: ensure apache is running
        action: service name=httpd state=started
      handlers:
        - name: restart apache
          action: service name=apache state=restarted

Below, we'll break down what the various features of the playbook language are.

Basics
``````

Hosts and Users
+++++++++++++++

For each play in a playbook, you get to choose which machines in your infrastructure
to target and what remote user to complete the steps (called tasks) as.

The `hosts` line is a list of one or more groups or host patterns,
separated by colons, as described in the :ref:`patterns`
documentation.  The `user` is just the name of the user account::

    ---
    - hosts: webservers
      user: root


Support for running things from sudo is also available::
    
    ---
    - hosts: webservers
      user: yourname
      sudo: True

You can also login as you, and then sudo to different users than root::

    ---
    - hosts: webservers
      user: yourname
      sudo: True
      sudo_user: postgres

If you need to specify a password to sudo, run `ansible-playbook` with ``--ask-sudo-pass`` (`-K`).
If you run a sudo playbook and the playbook seems to hang, it's probably stuck at the sudo prompt.
Just `Control-C` to kill it and run it again with `-K`.

NOTE:  When using `sudo_user` to a user other than root, the module arguments are briefly written into 
a random tempfile in /tmp.  These are deleted immediately after the command is executed.  This only
occurs when sudoing from a user like 'bob' to 'timmy', not when going from 'bob' to 'root', or
logging in directly as 'bob' or 'root'.  If this concerns you that this data is briefly readable
(not writeable), avoid transferring uncrypted passwords with `sudo_user` set.  In other cases, '/tmp' is not used and
this does not come into play. Ansible also takes care to not log password parameters.

Vars section
++++++++++++

The `vars` section contains a list of variables and values that can be used in the plays, like this::

    ---
    - hosts: webservers
      users: root
      vars:
         http_port: 80
         van_halen_port: 5150
         other: 'magic'       

These variables can be used later in the playbook like this::

    $varname or ${varname}

The later is useful in the event you need to do something like ${other}_concatenated_value.

The full power of the Jinja2 templating language is also available (note: in 0.4, this is only true inside of templates), which looks like this::

    {{ varname }}

The Jinja2 documentation provides information about how to construct loops and conditionals for those
who which to use more advanced templating.  This is optional and the $varname format still works in template
files.

If there are discovered variables about the system (ansible provides some of these,
plus we include ones taken from facter or ohai if installed) these variables bubble up back into the
playbook, and can be used on each system just like explicitly set
variables.  

Facter variables are prefixed with ``facter_`` and Ohai
variables are prefixed with ``ohai_``.  Ansible variables (0.3 and later) 
are not surprisingly prefixed with ``ansible_`` (See the :ref:`setup` module
documentation for a list of Ansible variables).

So for instance, if I wanted
to write the hostname into the /etc/motd file, I could say::

   - name: write the motd
     action: template src=/srv/templates/motd.j2 dest=/etc/motd

And in /srv/templates/motd.j2::

   You are logged into {{ facter_hostname }}

But we're getting ahead of ourselves.  Let's talk about tasks.

Tasks list
++++++++++

Each play contains a list of tasks.  Tasks are executed in order, one
at a time, against all machines matched by the host pattern,
before moving on to the next task.

Hosts with failed tasks are taken out of the rotation for the entire
playbook.  If things fail, simply correct the playbook file and rerun.

The goal of each task is to execute a module, with very specific arguments.
Variables, as mentioned above, can be used in arguments to modules.

Modules other than `command` and `shell` are 'idempotent', meaning if you run them
again, they will make the changes they are told to make to bring the
system to the desired state.  This makes it very safe to rerun
the same playbook multiple times.  They won't change things
unless they have to change things.  

The `command` and `shell` modules will actually rerun the same command again, 
which is totally ok if the command is something like 
'chmod' or 'setsebool', etc.

Every task should have a `name`, which is included in the output from
running the playbook.   This is output for humans, so it is
nice to have reasonably good descriptions of each task step.  If the name
is not provided though, the string fed to 'action' will be used for
output.

Here is what a basic task looks like, as with most modules,
the service module takes key=value arguments::

   tasks:
     - name: make sure apache is running
       action: service name=httpd state=running

The `command` and `shell` modules are the one modules that just takes a list
of arguments, and don't use the key=value form.  This makes
them work just like you would expect. Simple::

   tasks:
     - name: disable selinux 
       action: command /sbin/setenforce 0

Variables can be used in action lines.   Suppose you defined
a variable called 'vhost' in the 'vars' section, you could do this::

   tasks:
     - name: create a virtual host file for $vhost
       action: template src=somefile.j2 dest=/etc/httpd/conf.d/$vhost

Those same variables are usable in templates, which we'll get to later.


Running Operations On Change
````````````````````````````

As we've mentioned, nearly all modules are written to be 'idempotent' and can relay  when
they have made a change on the remote system.   Playbooks recognize this and
have a basic event system that can be used to respond to change.

These 'notify' actions are triggered at the end of each 'play' in a playbook, and
trigger only once each.  For instance, multiple resources may indicate
that apache needs to be restarted, but apache will only be bounced once.

Here's an example of restarting two services when the contents of a file
change, but only if the file changes::

   - name: template configuration file
     action: template src=template.j2 dest=/etc/foo.conf
     notify:
        - restart memcached
        - restart apache

The things listed in the 'notify' section of a task are called
handlers.  

Handlers are lists of tasks, not really any different from regular
tasks, that are referenced by name.  Handlers are what notifiers
notify.  If nothing notifies a handler, it will not run.  Regardless
of how many things notify a handler, it will run only once, after all
of the tasks complete in a particular play.  

Here's an example handlers section::

    handlers:
        - name: restart memcached
          action: service name=memcached state=restarted
        - name: restart apache
          action: service name=apache state=restarted

Handlers are best used to restart services and trigger reboots.  You probably
won't need them for much else.

.. note::
   Notify handlers are always run in the order written.


Include Files And Reuse
```````````````````````

Suppose you want to reuse lists of tasks between plays or playbooks.  You can use
include files to do this.

An include file simply contains a flat list of tasks, like so::

    ---
    # possibly saved as tasks/foo.yml
    - name: placeholder foo
      action: command /bin/foo
    - name: placeholder bar
      action: command /bin/bar

Include directives look like this::

   tasks:
    - include: tasks/foo.yml

You can also pass variables into includes directly.  We might call this a 'parameterized include'.

For instance, if deploying multiple wordpress instances, I could
contain all of my wordpress tasks in a single wordpress.yml file, and use it like so::

   tasks:
     - include: wordpress.yml user=timmy 
     - include: wordpress.yml user=alice
     - include: wordpress.yml user=bob

Variables passed in can be used in the included files.  You can reference them like this::
   
   $user

In addition to the explicitly passed in parameters, all variables from
the vars section are also available for use here as well.  

.. note::
   Include statements are only usable from the top level
   playbook file.  This means includes can not include other
   includes.  This may be implemented in a later release.

Includes can also be used in the 'handlers' section, for instance, if you
want to define how to restart apache, you only have to do that once for all
of your playbooks.  You might make a handlers.yml that looks like::

   ----
   # this might be in a file like handlers/handlers.yml
   - name: restart apache
     action: service name=apache state=restarted

And in your main playbook file, just include it like so, at the bottom
of a play::

   handlers:
     - include: handlers/handlers.yml

You can mix in includes along with your regular non-included tasks and handlers.

Note that you can not conditionally path the location to an include file, like you can
with 'vars_files'.  If you find yourself needing to do this, consider how you can
restructure your playbook to be more class/role oriented.  


Executing A Playbook
````````````````````

Now that you've learned playbook syntax, how do you run a playbook?  It's simple.
Let's run a playbook using a parallelism level of 10::

    ansible-playbook playbook.yml -f 10

Tips and Tricks
```````````````

Look at the bottom of the playbook execution for a summary of the nodes that were executed
and how they performed.   General failures and fatal "unreachable" communication attempts are 
kept seperate in the counts.

If you ever want to see detailed output from successful modules as well as unsuccessful ones,
use the '--verbose' flag.  This is available in Ansible 0.5 and later.

Also, in version 0.5 and later, Ansible playbook output is vastly upgraded if the cowsay 
package is installed.  Try it!

.. seealso::

   :doc:`YAMLSyntax`
       Learn about YAML syntax
   :doc:`playbooks`
       Review the basic Playbook language features
   :doc:`playbooks2`
       Learn about Advanced Playbook Features
   :doc:`bestpractices`
       Various tips about managing playbooks in the real world
   :doc:`modules`
       Learn about available modules
   :doc:`moduledev`
       Learn how to extend Ansible by writing your own modules
   :doc:`patterns`
       Learn about how to select hosts
   `Github examples directory <https://github.com/ansible/ansible/tree/master/examples/playbooks>`_
       Complete playbook files from the github project source
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups


