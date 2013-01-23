Best Practices
==============

Here are some tips for making the most of Ansible.

.. contents::
   :depth: 2
   :backlinks: top

Always Mention State
++++++++++++++++++++

The 'state' parameter is optional to a lot of modules.  Whether
'state=present' or 'state=absent', it's always best to leave that
parameter in your playbooks to make it clear, especially as some
modules support additional states.

Group By Roles
++++++++++++++

A system can be in multiple groups.  See :doc:`patterns`.   Having groups named after things like
*webservers* and *dbservers* is repeated in the examples because it's a very powerful concept.

This allows playbooks to target machines based on role, as well as to assign role specific variables
using the group variable system.

Directory Organization
++++++++++++++++++++++

Playbooks should be organized like this::

    # root of source control repository
    ├── acme/
    │   ├── files/
    │   │   └── some_file_path_foo.conf
    │   ├── handlers/
    │   │   └── main.yml
    │   ├── tasks/
    │   │   ├── setup.yml
    │   │   └── stop.yml
    │   ├── templates/
    │   │   ├── etc_acme_conf_acme.conf
    │   │   └── etc_other_conf_other.conf
    │   ├── vars/
    │   │   └── main.yml
    │   ├── setup.yml
    │   └── stop.yml
    └── global_vars.yml

Any directories or files not needed can be omitted.  Not all modules
may require 'vars' or 'files' sections, though most will require
'handlers', 'tasks', and 'templates'.  To review what each of
these sections do, see :doc:`playbooks` and :doc:`playbooks2`.

The acme/setup.yml playbook would be as simple as::

    ---
    - hosts: webservers
      user: root

      vars_files:
        - ../global_vars.yml
        - vars/main.yml
      tasks:
        - include: tasks/setup.yml
      handlers:
        - include: handlers/main.yml

The tasks are individually broken out in 'acme/tasks/setup.yml', and handlers, which are common to all task files,
are contained in 'acme/handlers/main.yml'.  As a reminder, handlers are mostly just used to notify services to restart
when things change, and these are described in :doc:`playbooks`.

Including more than one setup file or more than one handlers file is of course legal.

Bundling Ansible Modules With Playbooks
+++++++++++++++++++++++++++++++++++++++

.. versionadded:: 0.5

If a playbook has a "./library" directory relative to it's YAML file,
this directory can be used to add ansible modules that will
automatically be in the ansible module path.  This is a great way to
keep modules that go with a playbook together.

Miscellaneous Tips
++++++++++++++++++

When you can do something simply, do something simply.  Do not reach
to use every feature of Ansible together, all at once.  Use what works
for you.  For example, you should probably not need 'vars',
'vars_files', 'vars_prompt' and '--extra-vars' all at once,
while also using an external inventory file.

Optimize for readability.  Whitespace between sections of YAML
documents and in between tasks is strongly encouraged, as is usage of
YAML comments, which start with '#'.  It is also useful to comment
at the top of each file the purpose of the individual file and the
author, including email address.

It is possible to leave off the 'name' for a given task, though it
is recommended to provide a descriptive comment about why something is
being done instead.

Use version control.  Keep your playbooks and inventory file in git
(or another version control system), and commit when you make changes
to them.  This way you have an audit trail describing when and why you
changed the rules automating your infrastructure.

Resist the urge to write the same playbooks and configuration files
for heterogeneous distributions.  While lots of software packages
claim to make this easy on you, the configuration files are often
quite different, to the point where it would be easier to treat them
as different playbooks.  This is why, for example, Ansible has a
separate 'yum' and 'apt' module.  Yum and apt have different
capabilities, and we don't want to code for the least common
denominator.

Use variables for user tunable settings versus having constants in the
tasks file or templates, so that it is easy to reconfigure a playbook.
Think about this as exposing the knobs to things you would like to
tweak.

Since a system can be in more than one group, if you have multiple
datacenters or sites, consider putting systems into groups by role,
but also different groups by geography.  This allows you to assign
different variables to different geographies.

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
