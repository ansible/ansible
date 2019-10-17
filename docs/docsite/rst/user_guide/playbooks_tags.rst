Tags
====

If you have a large playbook, it may become useful to be able to run only
a specific part of it rather than running *everything* in the playbook.
Ansible supports a "tags:" attribute for this reason.

Tags can be applied to *many* structures in Ansible (see "tag inheritance",
below), but its simplest use is with individual tasks. Here is an example
that tags two tasks with different tags::

    tasks:
    - yum:
        name:
        - httpd
        - memcached
        state: present
      tags:
      - packages

    - template:
        src: templates/src.j2
        dest: /etc/foo.conf
      tags:
      - configuration

When you execute a playbook, you can filter tasks based on tags in two ways:

- On the command line, with the ``--tags`` or ``--skip-tags`` options
- In Ansible configuration settings, with the ``TAGS_RUN``
  and ``TAGS_SKIP`` options

For example, if you wanted to just run the "configuration" and "packages" part
of a very long playbook, you can use the ``--tags`` option on the command line::

    ansible-playbook example.yml --tags "configuration,packages"

On the other hand, if you want to run a playbook *without* certain tagged
tasks, you can use the ``--skip-tags`` command-line option::

    ansible-playbook example.yml --skip-tags "packages"

You can see which tasks will be executed with ``--tags`` or ``--skip-tags`` by
combining it with ``--list-tasks``::

    ansible-playbook example.yml --tags "configuration,packages" --list-tasks

.. warning::
    * Fact gathering is tagged with 'always' by default. It is ONLY skipped if
      you apply a tag and then use a different tag in ``--tags`` or the same
      tag in ``--skip-tags``.

.. _tag_reuse:

Tag Reuse
```````````````
You can apply the same tag to more than one task. When a play is run using
the ``--tags`` command-line option, all tasks with that tag name will be run.

This example tags several tasks with one tag, "ntp"::

    ---
    # file: roles/common/tasks/main.yml

    - name: be sure ntp is installed
      yum:
        name: ntp
        state: present
      tags: ntp

    - name: be sure ntp is configured
      template:
        src: ntp.conf.j2
        dest: /etc/ntp.conf
      notify:
      - restart ntpd
      tags: ntp

    - name: be sure ntpd is running and enabled
      service:
        name: ntpd
        state: started
        enabled: yes
      tags: ntp

.. _tag_inheritance:

Tag Inheritance
```````````````

Adding ``tags:`` to a play, or to statically imported tasks and roles, adds
those tags to all of the contained tasks. This is referred to as *tag
inheritance*. Tag inheritance is *not* applicable to dynamic inclusions
such as ``include_role`` and ``include_tasks``.

When you apply ``tags:`` attributes to structures other than tasks,
Ansible processes the tag attribute to apply ONLY to the tasks they contain.
Applying tags anywhere other than tasks is just a convenience so you don't
have to tag tasks individually.

This example tags all tasks in the two plays. The first play has all its tasks
tagged with 'bar', and the second has all its tasks tagged with 'foo'::

    - hosts: all
      tags:
      - bar
      tasks:
        ...

    - hosts: all
      tags: [ foo ]
      tasks:
        ...

You may also apply tags to the tasks imported by ``roles``::

    roles:
      - role: webserver
        vars:
          port: 5000
        tags: [ web, foo ]

And to ``import_role:`` and ``import_tasks:`` statements::

    - import_role:
        name: myrole
      tags: [ web, foo ]

    - import_tasks: foo.yml
      tags: [ web, foo ]


All of these apply the specified tags to EACH task inside the play, imported
file, or role, so that these tasks can be selectively run when the playbook
is invoked with the corresponding tags.

Tags are applied *down* the dependency chain. In order for a tag to be
inherited to a dependent role's tasks, the tag should be applied to the
role declaration or static import, not to all the tasks within the role.

There is no way to 'import only these tags'; you probably want to split
into smaller roles/includes if you find yourself looking for such a feature.

The above information does not apply to `include_tasks` or other dynamic
includes, as the attributes applied to an include, only affect the include
itself.

You can see which tags are applied to tasks, roles, and static imports
by running ``ansible-playbook`` with the ``--list-tasks`` option. You can
display all tags available with the ``--list-tags`` option.

.. note::
    The above information does not apply to `include_tasks`, `include_roles`,
    or other dynamic includes. Tags applied to either of these only tag the
    include itself.

To use tags with tasks and roles intended for dynamic inclusions,
all needed tasks should be explicitly tagged at the task level; or
``block:`` may be used to tag more than one task at once. The include
itself should also be tagged.

Here is an example of tagging role tasks with the tag ``mytag``, using a
``block`` statement, to then be used with a dynamic include:

Playbook file::

    - hosts: all
      tasks:
      - include_role:
          name: myrole
        tags: mytag

Role tasks file::

    - block:
      - name: First task to run
        ...
      - name: Second task to run
        ...
      tags:
      - mytag


.. _special_tags:

Special Tags
````````````

There is a special ``always`` tag that will always run a task, unless
specifically skipped (``--skip-tags always``)

Example::

    tasks:
    - debug:
        msg: "Always runs"
      tags:
      - always

    - debug:
        msg: "runs when you use tag1"
      tags:
      - tag1

.. versionadded:: 2.5

Another special tag is ``never``, which will prevent a task from running unless
a tag is specifically requested.

Example::

    tasks:
      - debug: msg="{{ showmevar }}"
        tags: [ never, debug ]

In this example, the task will only run when the ``debug`` or ``never`` tag
is explicitly requested.


There are another 3 special keywords for tags: ``tagged``, ``untagged`` and
``all``, which run only tagged, only untagged
and all tasks respectively.

By default, Ansible runs as if ``--tags all`` had been specified.

.. seealso::

   :ref:`playbooks_intro`
       An introduction to playbooks
   :ref:`playbooks_reuse_roles`
       Playbook organization by roles
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
