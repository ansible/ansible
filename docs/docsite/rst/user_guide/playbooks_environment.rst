.. _playbooks_environment:

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

You can also use it at a play level::

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


Working With Language-Specific Version Managers
===============================================

Some language-specific version managers (such as rbenv and nvm) require environment variables be set while these tools are in use. When using these tools manually, they usually require sourcing some environment variables via a script or lines added to your shell configuration file. In Ansible, you can instead use the environment directive::

    ---
    ### A playbook demonstrating a common npm workflow:
    # - Check for package.json in the application directory
    # - If package.json exists:
    #   * Run npm prune
    #   * Run npm install

    - hosts: application
      become: false

      vars:
        node_app_dir: /var/local/my_node_app

      environment:
        NVM_DIR: /var/local/nvm
        PATH: /var/local/nvm/versions/node/v4.2.1/bin:{{ ansible_env.PATH }}

      tasks:
      - name: check for package.json
        stat:
          path: '{{ node_app_dir }}/package.json'
        register: packagejson

      - name: npm prune
        command: npm prune
        args:
          chdir: '{{ node_app_dir }}'
        when: packagejson.stat.exists

      - name: npm install
        npm:
          path: '{{ node_app_dir }}'
        when: packagejson.stat.exists

You might also want to simply specify the environment for a single task::

    ---
    - name: install ruby 2.3.1
      command: rbenv install {{ rbenv_ruby_version }}
      args:
        creates: '{{ rbenv_root }}/versions/{{ rbenv_ruby_version }}/bin/ruby'
      vars:
        rbenv_root: /usr/local/rbenv
        rbenv_ruby_version: 2.3.1
      environment:
        CONFIGURE_OPTS: '--disable-install-doc'
        RBENV_ROOT: '{{ rbenv_root }}'
        PATH: '{{ rbenv_root }}/bin:{{ rbenv_root }}/shims:{{ rbenv_plugins }}/ruby-build/bin:{{ ansible_env.PATH }}'

.. note::
   ``environment:`` is not currently supported for Windows targets

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


