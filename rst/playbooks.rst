Playbooks
=========

.. seealso::

   :doc:`YAMLSyntax`
       Learn about YAML syntax
   :doc:`modules`
       Learn about available modules and writing your own
   :doc:`patterns`
       Learn about how to select hosts
   `Github examples directory <https://github.com/ansible/ansible/tree/master/examples/playbooks>`_
       Complete playbook files from the github project source


Playbooks are a completely different way to use ansible and are
particularly awesome.

They are the basis for a really simple configuration management and
multi-machine deployment system, unlike any that already exist, and
one that is very well suited to deploying complex applications.

Playbooks can declare configurations, or they can automate steps of
a manual ordered process.  They can launch tasks synchronously or asynchronously.

While you might run the main /usr/bin/ansible program for ad-hoc
tasks, playbooks are more likely to be kept in source control and used
to push out your configuration or assure the configurations of your
remote systems are in spec.

Let's dive in and see how they work.


Playbook Example
````````````````

Playbooks are expressed in YAML format and have a minimum of syntax.
Each playbook is composed of one or more 'plays' in a list.  

By composing a playbook of multiple 'plays', it is possible to
orchestrate multi-machine deployments, running certain steps on all
machines in the webservers group, then certain steps on the database
server group, then more commands back on the webservers group, etc. 

For starters, here's a playbook that contains just one play.::

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


Hosts line
```````````

The `hosts` line is a list of one or more groups or host patterns,
separated by colons, as described in the :ref:`patterns`
documentation.  This is just like the first parameter to
`/usr/bin/ansible`. 

Each play gets to designate it's own choice of patterns.

User line
`````````

Playbook steps on the remote system can be executed as any user.  The default is root,
but you can specify others.  Sudo support is pending.::

    user: mdehaan

Vars section
````````````

The `vars' section contains a list of variables and values that can be used in the plays.  These
can be used in templates or tasks and are dereferenced using
`jinja2` syntax like this::

    {{ varname }}

Further, if there are discovered variables about the system (say, if
facter or ohai were installed) these variables bubble up back into the
playbook, and can be used on each system just like explicitly set
variables.  Facter variables are prefixed with ``facter_`` and Ohai
variables are prefixed with ``ohai_``.  So for instance, if I wanted
to write the hostname into the /etc/motd file, I could say::

   - name: write the motd
     action: template src=/srv/templates/motd.j2 dest=/etc/motd

And in /srv/templates/motd.j2::

   You are logged into {{ facter_hostname }}

But we're getting ahead of ourselves.  Let's talk about tasks.

Tasks list
``````````

Each play contains a list of tasks.  Tasks are executed in order, one
at a time, against all machines matched by the host pattern,
before moving on to the next task.

Hosts with failed tasks are taken out of the rotation for the entire
playbook.  If things fail, simply correct the playbook file and rerun.

Modules other than `command` are 'idempotent', meaning if you run them
again, they will make the changes they are told to make to bring the
system to the desired state.  This makes it very safe to rerun
the same playbook multiple times.  They won't change things
unless they have to change things.  Command will actually rerun the
same command again, which is totally ok if the command is something
like 'chmod' or 'setsebool', etc.


Task name and action
`````````````````````

Every task must have a name, which is included in the output from
running the playbook.

The action line is the name of an ansible module followed by
parameters in key=value form::

   - name: make sure apache is running
     action: service name=httpd state=running

The command module is the one module that just takes a list
of arguments, and doesn't use the key=value form.  Simple::

   - name: disable selinux 
     action: command /sbin/setenforce 0

Variables can be used in action lines.   Suppose you defined
a variable called 'vhost' in the 'vars' section, you could do this::

   - name: make a directory
     action: template src=somefile.j2 dest=/etc/httpd/conf.d/{{ vhost }}

Those same variables are usable in templates, which we'll get to later.

Notify statements
`````````````````

As we've mentioned, nearly all modules are written to be 'idempotent' and can signal when
they have affected a change on the remote system.   Playbooks recognize this and
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

Next up, we'll show what a handler looks like.

.. note::
   Notify handlers are always run in the order written.

Handlers
````````

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


Power Tricks
````````````

Now that you have the basics down, let's learn some more advanced
things you can do with playbooks.


External Variables And Sensitive Data
+++++++++++++++++++++++++++++++++++++

It's a great idea to keep your playbooks under source control, but
you may wish to make the playbook source public while keeping certain
important variables private.  You can do this by using an external
variables file, or files, just like this::

    ---
    - hosts: all
      user: root
      vars:
        favcolor: blue
      vars_files:
        - /vars/external_vars.yml
      tasks:
      - name: this is just a placeholder
        action: command /bin/echo foo

This removes the risk of sharing sensitive data with others when
sharing your playbook source with them.

The contents of each variables file is a simple YAML dictionary, like this::

    ---
    # in the above example, this would be vars/external_vars.yml
    somevar: somevalue
    password: magic


Include Files And Reuse
+++++++++++++++++++++++

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

   - tasks:
      - include: tasks/foo.yml

Variables passed in can be used in the include files too.  Assume a variable named 'user'. Using
`jinja2` syntax, anywhere in the included file, you can say::

   {{ user }}

I can also pass variables into includes directly.  We might call this a 'parameterized include'.

For instance, if deploying multiple wordpress instances, I could
contain all of my wordpress tasks in a single wordpress.yml file, and use it like so::

   - tasks:
     - include: wordpress.yml user=timmy 
     - include: wordpress.yml user=alice
     - include: wordpress.yml user=bob

In addition to the explicitly passed in parameters, all variables from
the vars section are also available for use here as well.  Variables that bubble
up from tools like facter and ohai are not usable here though -- but they ARE available for use
inside 'action' lines and in templates.

.. note::
   Include statements are only usable from the top level
   playbook file.  This means includes can not include other
   includes.

Includes can also be used in the 'handlers' section, for instance, if you
want to define how to restart apache, you only have to do that once for all
of your playbooks.  You might make a notifiers.yaml that looked like::

   ----
   # this might be in a file like handlers/handlers.yml
   - name: restart apache
     action: service name=apache state=restarted

And in your main playbook file, just include it like so, at the bottom
of a play::

   handlers:
     - include: handlers/handlers.yml

You can mix in includes along with your regular non-included tasks and handlers.


Using Includes To Assign Classes of Systems
+++++++++++++++++++++++++++++++++++++++++++

Include files are really powerful when used to reuse logic between playbooks.  You
could imagine a playbook describing your entire infrastructure like
this, in a list of just a few plays::

    ---
    - hosts: atlanta-webservers
      vars:
        datacenter: atlanta
      tasks:
      - include: tasks/base.yml
      - include: tasks/webservers.yml database=db.atlanta.com
      handlers:
        - include: handlers/common.yml
    - hosts: atlanta-dbservers
      vars:
        datacenter: atlanta
      tasks:
      - include: tasks/base.yml
      - include: tasks/dbservers.yml
      handlers:
        - include: handlers/common.yml

There is one (or more) play defined for each group of systems, and
each play maps each group to several includes.  These includes represent
'class definitions', telling the systems what they are supposed to do or be.
In the above example, all hosts get the base configuration first and further
customize it depending on what class or nature of machines they are.

.. note::
   Playbooks do not always have to be declarative; you can do something
   similar to model a push process for a multi-tier web application.  This is
   actually one of the things playbooks were invented to do.


Asynchronous Actions and Polling
++++++++++++++++++++++++++++++++

By default tasks in playbooks block, meaning the connections stay open
until the task is done on each node.  If executing playbooks with
a small parallelism value (aka `--forks`), you may wish that long
running operations can go faster.  The easiest way to do this is
to kick them off all at once and then poll until they are done.  

You will also want to use asynchronous mode on very long running 
operations that might be subject to timeout.

To launch a task asynchronously, specify it's maximum runtime
and how frequently you would like to poll for status.  The default
poll value is 10 seconds if you do not specify a value for `poll`::

    ---
    - hosts: all
      user: root
      tasks:
      - name: simulate long running op (15 sec), wait for up to 45, poll every 5
        action: command /bin/sleep 15
        async: 45
        poll: 5

.. note::
   There is no default for the async time limit.  If you leave off the
   'async' keyword, the task runs synchronously, which is Ansible's
   default.

Alternatively, if you do not need to wait on the task to complete, you may
"fire and forget" by specifying a poll value of 0::

    ---
    - hosts: all
      user: root
      tasks:
      - name: simulate long running op, allow to run for 45, fire and forget
        action: command /bin/sleep 15
        async: 45
        poll: 0

.. note::
   You shouldn't "fire and forget" with operations that require 
   exclusive locks, such as yum transactions, if you expect to run other
   commands later in the playbook against those same resources.  

.. note::
   Using a higher value for `--forks` will result in kicking off asynchronous
   tasks even faster.  This also increases the efficiency of polling.

Executing A Playbook
````````````````````

Now that you've learned playbook syntax, how do you run a playbook?  It's simple.
Let's run a playbook using a parallelism level of 10::

    ansible-playbook playbook.yml -f 10

.. note::
    Don't forget to check out the `Github examples directory <https://github.com/ansible/ansible/tree/master/examples/playbooks>`_ for examples of playbooks in action, so you can see how all of these features can be put together.


