Tags
====

If you have a large playbook it may become useful to be able to run a 
specific part of the configuration without running the whole playbook.  

Both plays and tasks support a "tags:" attribute for this reason.

Example::

    tasks:

        - yum: name={{ item }} state=installed
          with_items:
             - httpd
             - memcached
          tags:
             - packages

        - template: src=templates/src.j2 dest=/etc/foo.conf
          tags:
             - configuration

If you wanted to just run the "configuration" and "packages" part of a very long playbook, you could do this::

    ansible-playbook example.yml --tags "configuration,packages"
    
On the other hand, if you want to run a playbook *without* certain tasks, you could do this::

    ansible-playbook example.yml --skip-tags "notification"

You may also apply tags to roles::

    roles:
      - { role: webserver, port: 5000, tags: [ 'web', 'foo' ] }

And you may also tag basic include statements::

    - include: foo.yml tags=web,foo

Both of these have the function of tagging every single task inside the include statement.

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_roles`
       Playbook organization by roles
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel




