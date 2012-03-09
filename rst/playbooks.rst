Playbooks
=========

.. seealso::

   :doc:`YAMLScripts`
       Learn about YAML syntax
   :doc:`modules`
       Learn about available modules and writing your own
   :doc:`patterns`
       Learn about how to select hosts


Playbooks are a completely different way to use ansible and are
particularly awesome.

They are the basis for a really simple configuration management and
multi-machine deployment system, unlike any that already exist, and
one that is very well suited to deploying complex applications.

While you might run the main /usr/bin/ansible program for ad-hoc
tasks, playbooks are more likely to be kept in source control and used
to push out your configuration or assure the configurations of your
remote systems are in spec.


Playbook Example
````````````````

Playbooks are expressed in YAML format and have a minimum of syntax.
Each playbook is composed of one or more 'plays' in a list.  By
composing a playbook of multiple 'plays', it is possible to
orchestrate multi-machine deployments, running certain steps on all
machines in the webservers group, then certain steps on the database
server group, then more commands back on the webservers group, etc::

    ---
    - hosts: webservers
      vars:
        http_port: 80
        max_clients: 200
      user: root
      tasks:
      - include: base.yml somevar=3 othervar=4
      - name: write the apache config file
        action: template src=/srv/httpd.j2 dest=/etc/httpd.conf
        notify:
        - restart apache
      - name: ensure apache is running
        action: service name=httpd state=started
      handlers:
        - include: handlers.yml

Hosts line
``````````

The hosts line is a list of one or more groups or host patterns,
separated by colons, as described in the :ref:`patterns`
documentation.  This is just like the first parameter to
`/usr/bin/ansible`.

Vars section
````````````

A list of variables and values that can be used in the plays.  These
can be used in templates or 'action' lines and are dereferenced using
`jinja2` syntax like this::

   {{ varname }}

Further, if there are discovered variables about the system (say, if
facter or ohai were installed) these variables bubble up back into the
playbook, and can be used on each system just like explicitly set
variables.  Facter variables are prefixed with ``facter_`` and Ohai
variables are prefixed with ``ohai_``.  So for instance, if I wanted
to write the hostname into the /etc/motd file, I could say::

   - name: write the motd
   - action: template src=/srv/templates/motd.j2 dest=/etc/motd

And in /srv/templates/motd.j2::

   You are logged into {{ facter_hostname }}

But we're getting ahead of ourselves.  Let's talk about tasks.

Tasks list
``````````

Each play contains a list of tasks.  Tasks are executed in order, one
at a time, against all machines matched by the playbooks host pattern,
before moving on to the next task.

Hosts with failed tasks are taken out of the rotation for the entire
playbook.  If things fail, simply correct the playbook file and rerun.

Modules other than command are idempotent, meaning if you run them
again, they will make the changes they are told to make to bring the
system to the desired state.

Task name and action
`````````````````````

Every task must have a name, which is included in the output from
running the playbook.

The action line is the name of an ansible module followed by
parameters.  Usually these are expressed in ``key=value`` form, except
for the command module, which looks just like a Linux/Unix command
line.  See the module documentation for more info.

Variables, as mentioned above, can be used in action lines.  So if,
hypothetically, you wanted to make a directory on each system named
after the hostname ... yeah, that's I know silly ... you could do it
like so::

   - name: make a directory
   - action: mkdir /tmp/{{ facter_hostname }}

Notify statements
`````````````````

Nearly all modules are written to be 'idempotent' and can signal when
they have affected a change on the remote system.  If a notify
statement is used, the named handler will be run against each system
where a change was effected, but NOT on systems where no change
occurred.  This happens after all of the tasks are run.  For example,
if notifying Apache and potentially replacing lots of configuration
files, you could have Apache restart just once, at the end of a run.
If you need Apache restarted in the middle of a run, you could just
make a task for it, no harm done.  Notifiers are optional.

Handlers
````````

Handlers are lists of tasks, not really any different from regular
tasks, that are referenced by name.  Handlers are what notifiers
notify.  If nothing notifies a handler, it will not run.  Regardless
of how many things notify a handler, it will run only once, after all
of the tasks complete in a particular play.

Includes
````````

Not all tasks have to be listed directly in the main file.  An include
file can contain a list of tasks (in YAML) as well, optionally passing
extra variables into the file.  Variables passed in can be deferenced
like this (assume a variable named 'user')::

   {{ user }}

For instance, if deploying multiple wordpress instances, I could
contain all of my tasks in a wordpress.yml file, and use it like so::

   - tasks:
      - include: wordpress.yml user=timmy 
      - include: wordpress.yml user=alice
      - include: wordpress.yml user=bob

In addition to the explicitly passed in parameters, all variables from
the vars section are also available.

The format of an included list of tasks or handlers looks just like a
flat list of tasks.  Here is an example of what base.yml might look
like::

    ---
    - name: no selinux
      action: command /usr/sbin/setenforce 0
    - name: no iptables
      action: service name=iptables state=stopped
    - name: this is just to show variables work here, favcolor={{ favcolor }}
      action: command /bin/true

As you can see above, variables in include files work just like they
do in the main file.  Including a variable in the name of a task is a
contrived example, you could also pass them to the action command line
or use them inside a template file.

.. note::
    Note that include statements are only usable from the top level
    playbook file.  At this time, includes can not include other
    includes.

Using Includes To Assign Classes of Systems
```````````````````````````````````````````

Include files are best used to reuse logic between playbooks.  You
could imagine a playbook describing your entire infrastructure like
this::

    ---
    - hosts: atlanta-webservers
      vars:
        datacenter: atlanta
      tasks:
      - include: base.yml
      - include: webservers.yml database=db.atlanta.com
      handlers:
        - include: generic-handlers.yml
    - hosts: atlanta-dbservers
      vars:
        datacenter: atlanta
      tasks:
      - include: base.yml
      - include: dbservers.yml
      handlers:
        - include: generic-handlers.yml

There is one (or more) play defined for each group of systems, and
each play maps each group includes one or more 'class definitions'
telling the systems what they are supposed to do or be.

Using a common handlers file could allow one task in 'webservers' to
define 'restart apache', and it could be reused between multiple
plays.

Variables like 'database' above can be used in templates referenced
from the configuration file to generate machine specific variables.

Asynchronous Actions and Polling
````````````````````````````````

(Information on this feature is pending)


Executing A Playbook
````````````````````

To run a playbook::

    ansible-playbook playbook.yml

