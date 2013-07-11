Best Practices
==============

Here are some tips for making the most of Ansible.

You can find some example playbooks illustrating these best practices in our `ansible-examples repository <https://github.com/ansible/ansible-examples>`_.  (NOTE: These may not use all of the features in the latest release just yet).

.. contents::
   :depth: 2
   :backlinks: top

Content Organization
++++++++++++++++++++++

The following section shows one of many possible ways to organize content.   Your usage of Ansible should fit your needs,
so feel free to modify this approach and organize as you see fit.

(One thing you will definitely want to do though, is use the "roles" organization feature, which is documented as part
of the main playbooks page)

Directory Layout
````````````````

The top level of the directory would contain files and directories like so::

    production                # inventory file for production servers
    stage                     # inventory file for stage environment 

    group_vars/
       group1                 # here we assign variables to particular groups
       group2                 # ""
    host_vars/
       hostname1              # if systems need specific variables, put them here
       hostname2              # ""

    site.yml                  # master playbook
    webservers.yml            # playbook for webserver tier
    dbservers.yml             # playbook for dbserver tier

    roles/
        common/               # this hierarchy represents a "role"
            tasks/            #
                main.yml      #  <-- tasks file can include smaller files if warranted
            handlers/         # 
                main.yml      #  <-- handlers file
            templates/        #  <-- files for use with the template resource
                ntp.conf.j2   #  <------- templates end in .j2
            files/            #
                bar.txt       #  <-- files for use with the copy resource
                foo.sh        #  <-- script files for use with the script resource

        webtier/              # same kind of structure as "common" was above, done for the webtier role
        monitoring/           # ""
        fooapp/               # "" 

How to Arrange Inventory, Stage vs Production
`````````````````````````````````````````````

In this example, the *production* file contains the inventory of all of your production hosts.  Of course you can pull inventory from an external
data source as well, but this is just a basic example.  Define groups based on purpose of the host (roles) and also geography or datacenter location::

    # file: production

    [atlanta-webservers]
    www-atl-1.example.com
    www-atl-2.example.com

    [boston-webservers]
    www-bos-1.example.com
    www-bos-2.example.com

    [atlanta-dbservers]
    db-atl-1.example.com
    db-atl-2.example.com

    [boston-dbservers]
    db-bos-1.example.com

    # webservers in all geos
    [webservers:children]
    atlanta-webservers
    boston-webservers

    # dbservers in all geos
    [dbservers:children]
    atlanta-dbservers
    boston-dbservers

    # everything in the atlanta geo
    [atlanta:children]
    atlanta-webservers
    atlanta-dbservers

    # everything in the boston geo
    [boston:children]
    boston-webservers
    boston-dbservers

Group And Host Variables
````````````````````````

Now, groups are nice for organization, but that's not all groups are good for.  You can also assign variables to them!  For instance, atlanta
has it's own NTP servers, so when settings up ntp.conf, we should use them.  Let's set those now::

    ---
    # file: group_vars/atlanta
    ntp: ntp-atlanta.example.com
    backup: backup-atlanta.example.com

Variables aren't just for geographic information either!  Maybe the webservers have some configuration that doesn't make sense for the database
servers::

    ---
    # file: group_vars/webservers
    apacheMaxRequestsPerChild: 3000
    apacheMaxClients: 900

If we had any default values, or values that were universally true, we would put them in a file called group_vars/all::

    ---
    # file: group_vars/all
    ntp: ntp-boston.example.com
    backup: backup-boston.example.com 

We can define specific hardware variance in systems in a host_vars file, but avoid doing this unless you need to::

    ---
    # file: host_vars/db-bos-1.example.com
    foo_agent_port: 86
    bar_agent_port: 99

Top Level Playbooks Are Separated By Role
`````````````````````````````````````````

In site.yml, we include a playbook that defines our entire infrastructure.  Note this is SUPER short, because it's just including
some other playbooks.  Remember playbooks are nothing more than lists of plays::

    ---
    # file: site.yml
    - include: webservers.yml
    - include: dbservers.yml

In a file like webservers.yml (also at the top level), we simply map the configuration of the webservers group to the roles performed by the webservers group.  Also notice this is incredibly short.  For example::

    ---
    # file: webservers.yml
    - hosts: webservers
      roles:
        - common
        - webtier

Task And Handler Organization For A Role
````````````````````````````````````````

Below is an example tasks file, that explains how a role works.  Our common role here just sets up NTP, but it could do more if we wanted::

    ---
    # file: roles/common/tasks/main.yml

    - name: be sure ntp is installed
      yum: pkg=ntp state=installed
      tags: ntp

    - name: be sure ntp is configured
      template: src=ntp.conf.j2 dest=/etc/ntp.conf
      notify:
        - restart ntpd
      tags: ntp

    - name: be sure ntpd is running and enabled
      service: name=ntpd state=running enabled=yes
      tags: ntp

Here is an example handlers file.  As a review, handlers are only fired when certain tasks report changes, and are run at the end
of each play::

    ---
    # file: roles/common/handlers/main.yml
    - name: restart ntpd
      service: name=ntpd state=restarted

What This Organization Enables (Examples)
`````````````````````````````````````````

So that's our basic organizational structure.

Now what sort of use cases does this layout enable?  Lots!  If I want to reconfigure my whole infrastructure, it's just::

    ansible-playbook -i production site.yml

What about just reconfiguring NTP on everything?  Easy.::

    ansible-playbook -i production site.yml --tags ntp

What about just reconfiguring my webservers?::

    ansible-playbook -i production webservers.yml

What about just my webservers in Boston?::

    ansible-playbook -i production webservers.yml --limit boston

What about just the first 10, and then the next 10?::
   
    ansible-playbook -i production webservers.yml --limit boston[0-10]
    ansible-playbook -i production webservers.yml --limit boston[10-20]

And of course just basic ad-hoc stuff is also possible.::

    ansible -i production -m ping
    ansible -i production -m command -a '/sbin/reboot' --limit boston 

And there are some useful commands (at least in 1.1 to know)::

    # confirm what task names would be run if I ran this command and said "just ntp tasks"
    ansible-playbook -i production webservers.yml --tags ntp --list-tasks

    # confirm what hostnames might be communicated with if I said "limit to boston"
    ansible-playbook -i production webservers.yml --limit boston --list-hosts

Deployment vs Configuration Organization
````````````````````````````````````````

The above setup models a typical OS configuration topology.  When doing multi-tier deployments, there are going
to be some additional playbooks that hop between tiers to roll out an application.  In this case, 'site.yml'
may be augmented by playbooks like 'deploy_exampledotcom.yml' but the general concepts can still apply.

Ansible allows you to deploy and configure using the same tool, so you would likely reuse groups and just
keep the OS configuration in separate playbooks from the app deployment.

Stage vs Production
+++++++++++++++++++

As also mentioned above, a good way to keep your stage (or testing) and production environments separate is to use a separate inventory file for stage and production.   This way you pick with -i what you are targetting.  Keeping them all in one file can lead to surprises!

Testing things in a stage environment before trying in production is always a great idea.  Your environments need not be the same
size and you can use group variables to control the differences between those environments.

Rolling Updates
+++++++++++++++

Understand the 'serial' keyword.  If updating a webserver farm you really want to use it to control how many machines you are
updating at once in the batch.

Always Mention The State
++++++++++++++++++++++++

The 'state' parameter is optional to a lot of modules.  Whether 'state=present' or 'state=absent', it's always best to leave that
parameter in your playbooks to make it clear, especially as some modules support additional states.

Group By Roles
++++++++++++++

A system can be in multiple groups.  See :doc:`patterns`.   Having groups named after things like
*webservers* and *dbservers* is repeated in the examples because it's a very powerful concept.

This allows playbooks to target machines based on role, as well as to assign role specific variables
using the group variable system.

Operating System and Distribution Variance
++++++++++++++++++++++++++++++++++++++++++

When dealing with a parameter that is different between two different operating systems, the best way to handle this is
by using the group_by module.

This makes a dynamic group of hosts matching certain criteria, even if that group is not defined in the inventory file::

   ---

   # talk to all hosts just so we can learn about them 

   - hosts: all
     tasks:
        - group_by: key=${ansible_distribution}

   # now just on the CentOS hosts...

   - hosts: CentOS
     gather_facts: False
     tasks:
        - # tasks that only happen on CentOS go here

If group specific settings are needed, this can also be done, for example::

    ---
    # file: group_vars/all
    asdf: 10

    ---
    # file: group_vars/CentOS
    asdf: 42

In the above example, CentOS machines get the value of '42' for asdf, but other machines get 10.


Bundling Ansible Modules With Playbooks
+++++++++++++++++++++++++++++++++++++++

.. versionadded:: 0.5

If a playbook has a "./library" directory relative to it's YAML file, this directory can be used to add ansible modules that will
automatically be in the ansible module path.  This is a great way to keep modules that go with a playbook together.

Whitespace and Comments
+++++++++++++++++++++++

Generous use of whitespace to break things up, and use of comments (which start with '#'), is encouraged.

Always Name Tasks
+++++++++++++++++

It is possible to leave off the 'name' for a given task, though it is recommended to provide a description 
about why something is being done instead.  This name is shown when the playbook is run.

Keep It Simple
++++++++++++++

When you can do something simply, do something simply.  Do not reach
to use every feature of Ansible together, all at once.  Use what works
for you.  For example, you should probably not need 'vars',
'vars_files', 'vars_prompt' and '--extra-vars' all at once,
while also using an external inventory file.

Version Control
+++++++++++++++

Use version control.  Keep your playbooks and inventory file in git
(or another version control system), and commit when you make changes
to them.  This way you have an audit trail describing when and why you
changed the rules automating your infrastructure.

.. seealso::

   :doc:`YAMLSyntax`
       Learn about YAML syntax
   :doc:`playbooks`
       Review the basic playbook features
   :doc:`modules`
       Learn about available modules
   :doc:`moduledev`
       Learn how to extend Ansible by writing your own modules
   :doc:`patterns`
       Learn about how to select hosts
   `Github examples directory <https://github.com/ansible/ansible/tree/devel/examples/playbooks>`_
       Complete playbook files from the github project source
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
