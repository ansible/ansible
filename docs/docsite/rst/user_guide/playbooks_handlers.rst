.. _handlers:

Handlers: running operations on change
======================================

Sometimes you want a task to run only when a change is made on a machine. For example, you may want to restart a service if a task updates the configuration of that service, but not if the configuration is unchanged. Ansible uses handlers to address this use case. Handlers are tasks that only run when notified. Each handler should have a globally unique name.

.. contents::
   :local:

Handler example
---------------

This playbook, ``verify-apache.yml``, contains a single play with a handler::

    ---
    - name: verify apache installation
      hosts: webservers
      vars:
        http_port: 80
        max_clients: 200
      remote_user: root
      tasks:
      - name: ensure apache is at the latest version
        yum:
          name: httpd
          state: latest
      - name: write the apache config file
        template:
          src: /srv/httpd.j2
          dest: /etc/httpd.conf
        notify:
        - restart apache
      - name: ensure apache is running
        service:
          name: httpd
          state: started
      handlers:
        - name: restart apache
          service:
            name: httpd
            state: restarted

In this example playbook, the second task notifies the handler. A single task can notify more than one handler::

    - name: template configuration file
      template:
        src: template.j2
        dest: /etc/foo.conf
      notify:
        - restart memcached
        - restart apache
      handlers:
        - name: restart memcached
          service:
            name: memcached
            state: restarted
        - name: restart apache
          service:
            name: apache
            state: restarted

Controlling when handlers run
-----------------------------

By default, handlers run after all the tasks in a particular play have been completed. This approach is efficient, because the handler only runs once, regardless of how many tasks notify it. For example, if multiple tasks update a configuration file and notify a handler to restart Apache, Ansible only bounces Apache once to avoid unnecessary restarts.

If you need handlers to run before the end of the play, add a task to flush them using the :ref:`meta module <meta_module>`, which executes Ansible actions::

    tasks:
      - shell: some tasks go here
      - meta: flush_handlers
      - shell: some other tasks

The ``meta: flush_handlers`` task triggers any handlers that have been notified at that point in the play.

Using variables with handlers
-----------------------------

You may want your Ansible handlers to use variables. For example, if the name of a service varies slightly by distribution, you want your output to show the exact name of the restarted service for each target machine. Avoid placing variables in the name of the handler. Since handler names are templated early on, Ansible may not have a value available for a handler name like this::

    handlers:
    # this handler name may cause your play to fail!
    - name: restart "{{ web_service_name }}"

If the variable used in the handler name is not available, the entire play fails. Changing that variable mid-play **will not** result in newly created handler.

Instead, place variables in the task parameters of your handler. You can load the values using ``include_vars`` like this:

  .. code-block:: yaml+jinja

    tasks:
      - name: Set host variables based on distribution
        include_vars: "{{ ansible_facts.distribution }}.yml"

    handlers:
      - name: restart web service
        service:
          name: "{{ web_service_name | default('httpd') }}"
          state: restarted

Handlers can also "listen" to generic topics, and tasks can notify those topics as follows::

    handlers:
      - name: restart memcached
        service:
          name: memcached
          state: restarted
        listen: "restart web services"
      - name: restart apache
        service:
          name: apache
          state: restarted
        listen: "restart web services"

    tasks:
      - name: restart everything
        command: echo "this task will restart the web services"
        notify: "restart web services"

This use makes it much easier to trigger multiple handlers. It also decouples handlers from their names,
making it easier to share handlers among playbooks and roles (especially when using 3rd party roles from
a shared source like Galaxy).

.. note::
   * Handlers always run in the order they are defined, not in the order listed in the notify-statement. This is also the case for handlers using `listen`.
   * Handler names and `listen` topics live in a global namespace.
   * Handler names are templatable and `listen` topics are not.
   * Use unique handler names. If you trigger more than one handler with the same name, the first one(s) get overwritten. Only the last one defined will run.
   * You can notify a handler defined inside a static include.
   * You cannot notify a handler defined inside a dynamic include.

When using handlers within roles, note that:

* handlers notified within ``pre_tasks``, ``tasks``, and ``post_tasks`` sections are automatically flushed in the end of section where they were notified.
* handlers notified within ``roles`` section are automatically flushed in the end of ``tasks`` section, but before any ``tasks`` handlers.
* handlers are play scoped and as such can be used outside of the role they are defined in.
