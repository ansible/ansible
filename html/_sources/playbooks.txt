Playbooks: Ansible for Deployment, Configuration Management, and Orchestration
==============================================================================

.. seealso::

   :doc:`YAMLScripts`
       Learn about YAML syntax
   :doc:`modules`
       Learn about available modules and writing your own
   :doc:`patterns`
       Learn about how to select hosts


Playbooks are a completely different way to use ansible and are particularly awesome.  They are the basis for a really simple configuration management and deployment system, unlike any that already exist, and one that is very well suited to deploying complex multi-machine applications. While you might run the main ansible program for ad-hoc tasks, playbooks are more likely to be kept in source control and used to push out your configuration or assure the configurations of your remote systems are in spec.


Playbook Example
````````````````

Playbooks are expressed in YAML format and have a minimum of syntax.  Each playbook is composed
of one or more 'plays' in a list.  By composing a playbook of multiple 'plays', it is possible
to orchestrate multi-machine deployments, running certain steps on all machines in
the webservers group, then certain steps on the database server group, then more commands
back on the webservers group, etc::

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

The hosts line is alist of one or more groups or host patterns, seperated by colons, as
described in the 'patterns' documentation.

Vars section
````````````

A list of variables that can be used in the templates, action lines, or included files.
Variables are deferenced using ``jinja2`` syntax like this::

   {{ varname }}

These variables will be pushed down to the managed systems for use in templating operations, where
the way to dereference them in templates is exactly the same.

Further, if there are discovered variables about the system (say, if facter or ohai were
installed) these variables bubble up back into the playbook, and can be used on each
system just like explicitly set variables.  Facter variables are prefixed with 'facter_'
and Ohai variables are prefixed with 'ohai_'.

Tasks list
``````````

Each play contains a list of tasks.  Tasks are executed in order, one at a time, against 
all machines matched by the play's host pattern, before moving on to the next task.  
Hosts with failed tasks are taken out of the rotation for the entire playbook.  If things fail, 
correct the problem and rerun.  Modules other than command are idempotent, meaning if you
run them again, they will make the changes they are told to make to bring the system to
the desired state.

Task name and action
`````````````````````

Every task must have a name, which is included in the output from running the playbook.

The action line is the name of an ansible module followed by parameters.  Usually these
are expressed in key=value form, except for the command module, which looks just like a Linux/Unix
command line.  See the module documentation for more info.

Notify statements
`````````````````

Nearly all modules are written to be 'idempotent' and can signal when they have affected a change
on the remote system.  If a notify statement is used, the named handler will be run against
each system where a change was effected, but NOT on systems where no change occurred.

Handlers
````````

Handlers are lists of tasks, not really any different from regular tasks, that are referenced
by name.  

Includes
````````

Not all tasks have to be listed directly in the main file.  An include file can contain
a list of tasks (in YAML) as well, optionally passing extra variables into the file.
Variables passed in can be deferenced like this:

   {{ variable }}

Asynchronous Actions and Polling
````````````````````````````````

(Information on this feature is pending)

Executing A Playbook
````````````````````

To run a playbook::

    ansible-playbook playbook.yml

