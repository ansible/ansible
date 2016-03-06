Setting the Environment (and Working With Proxies)
==================================================

.. versionadded:: 1.1

It is quite possible that you may need to get package updates through a proxy, or even get some package
updates through a proxy and access other packages not through a proxy.  Or maybe a script you might wish to 
call may also need certain environment variables set to run properly.

Ansible makes it easy for you to configure your environment by using the 'environment' keyword.  Here is an example::

    - hosts: all
      remote_user: root

      tasks:

        - apt: name=cobbler state=installed
          environment:
            http_proxy: http://proxy.example.com:8080

The environment can also be stored in a variable, and accessed like so::

    - hosts: all
      remote_user: root

      # here we make a variable named "proxy_env" that is a dictionary
      vars:
        proxy_env:
          http_proxy: http://proxy.example.com:8080

      tasks:

        - apt: name=cobbler state=installed
          environment: "{{proxy_env}}"

You can also use it at a playbook level::

    - hosts: testhost

      roles:
         - php
         - nginx

      environment:
        http_proxy: http://proxy.example.com:8080

While just proxy settings were shown above, any number of settings can be supplied.  The most logical place
to define an environment hash might be a group_vars file, like so::

    ---
    # file: group_vars/boston

    ntp_server: ntp.bos.example.com
    backup: bak.bos.example.com
    proxy_env:
      http_proxy: http://proxy.bos.example.com:8080
      https_proxy: http://proxy.bos.example.com:8080

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


