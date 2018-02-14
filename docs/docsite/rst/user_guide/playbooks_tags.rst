Tags
====

If you have a large playbook it may become useful to be able to run a specific part of the configuration without running the whole playbook.

Both plays and tasks support a "tags:" attribute for this reason.
You can **ONLY** filter tasks based on tags from the command line with ``--tags`` or ``--skip-tags``.
Adding "tags:" in any part of a play (including roles) adds those tags to the contained tasks.

Example::

    tasks:

        - yum:
            name: "{{ item }}"
            state: installed
          loop:
             - httpd
             - memcached
          tags:
             - packages

        - template:
            src: templates/src.j2
            dest: /etc/foo.conf
          tags:
             - configuration

If you wanted to just run the "configuration" and "packages" part of a very long playbook, you could do this::

    ansible-playbook example.yml --tags "configuration,packages"

On the other hand, if you want to run a playbook *without* certain tasks, you could do this::

    ansible-playbook example.yml --skip-tags "notification"


.. _tag_reuse:

Tag Reuse
```````````````
You can apply the same tag name to more than one task, in the same file
or included files. This will run all tasks with that tag.

Example::

    ---
    # file: roles/common/tasks/main.yml

    - name: be sure ntp is installed
      yum:
        name: ntp
        state: installed
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

You can apply tags to more than tasks, but they ONLY affect the tasks themselves. Applying tags anywhere else is just a convenience so you don't have to write it on every task::

    - hosts: all
      tags:
        - bar
      tasks:
        ...

    - hosts: all
      tags: ['foo']
      tasks:
        ...

You may also apply tags to roles::

    roles:
      - { role: webserver, port: 5000, tags: [ 'web', 'foo' ] }

And import statements::

    - import_tasks: foo.yml
      tags: [web,foo]

All of these apply the specified tags to EACH task inside the play, imported
file, or role, so that these tasks can be selectively run when the playbook
is invoked with the corresponding tags.

The above information does not apply to `include_tasks` or other dynamic includes,
as the attributes applied to an include, only affect the include itself.

Tags are inherited *down* the dependency chain. In order for tags to be applied to a role and all its dependencies,
the tag should be applied to the role, not to all the tasks within a role.

You can see which tags are applied to tasks by running ``ansible-playbook`` with the ``--list-tasks`` option. You can display all tags using the ``--list-tags`` option.

.. _special_tags:

Special Tags
````````````

There is a special ``always`` tag that will always run a task, unless specifically skipped (``--skip-tags always``)

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

Another special tag is ``never``, which will prevent a task from running unless a tag is specifically requested.

Example::

    tasks:
      - debug: msg='{{ showmevar}}'
        tags: [ 'never', 'debug' ]

In this example, the task will only run when the ``debug`` or ``never`` tag is explicitly requested.


There are another 3 special keywords for tags: ``tagged``, ``untagged`` and ``all``, which run only tagged, only untagged
and all tasks respectively.

By default, Ansible runs as if ``--tags all`` had been specified.

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_reuse_roles`
       Playbook organization by roles
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel




