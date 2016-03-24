# Publish / Subscribe for Handlers

*Author*: René Moser <@resmo>

*Date*: 07/03/2016

## Motivation

In some use cases a publish/subscribe kind of event to run a handler is more convenient, e.g. restart services after replacing SSL certs.

However, ansible does not provide a built-in way to handle it yet.


### Problem

If your SSL cert changes, you usually have to reload/restart services to use the new certificate.

However, If you have a ssl role or a generic ssl play, you usually don't want to add specific handlers to it.
Instead it would be much more convenient to use a publish/subscribe kind of paradigm in the roles where the services are configured in.

The way we implemented it currently:

I use notify to set a fact where later (in different plays) we act on a fact using notify again.

~~~yaml
---
- hosts: localhost
  gather_facts: no
  tasks:
  - name: copy an ssl cert
    shell: echo cert has been changed
    notify: publish ssl cert change
  handlers:
  - name: publish ssl cert change
    set_fact:
      ssl_cert_changed: true

- hosts: localhost
  gather_facts: no
  tasks:
  - name: subscribe for ssl cert change
    shell: echo cert changed
    notify: service restart one
    when: ssl_cert_changed is defined and ssl_cert_changed
  handlers:
  - name: service restart one
    shell: echo service one restarted

- hosts: localhost
  gather_facts: no
  tasks:
  - name: subscribe for ssl cert change
    shell: echo cert changed
    when: ssl_cert_changed is defined and ssl_cert_changed
    notify: service restart two
  handlers:
  - name: service restart two
    shell: echo service two restarted
~~~

However, this looks like a workaround of a feature that ansible should provide in a much cleaner way.

## Approaches

### Approach 1:

Provide new `subscribe` keyword on handlers:

~~~yaml
- hosts: localhost
  gather_facts: no
  tasks:
  - name: copy an ssl cert
    shell: echo cert has been changed


- hosts: localhost
  gather_facts: no
  handlers:
  - name: service restart one
    shell: echo service one restarted
    subscribe: copy an ssl cert


- hosts: localhost
  gather_facts: no
  handlers:
  - name: service restart two
    shell: echo service two restarted
    subscribe: copy an ssl cert
~~~

### Approach 2:

Provide new `subscribe` on handlers and `publish` keywords in tasks:

~~~yaml
- hosts: localhost
  gather_facts: no
  tasks:
  - name: copy an ssl cert
    shell: echo cert has been changed
    publish: yes


- hosts: localhost
  gather_facts: no
  handlers:
  - name: service restart one
    shell: echo service one restarted
    subscribe: copy an ssl cert


- hosts: localhost
  gather_facts: no
  handlers:
  - name: service restart two
    shell: echo service two restarted
    subscribe: copy an ssl cert
~~~

### Approach 3:

Provide new `subscribe` module:

A subscribe module could consume the results of a task by name, optionally the value to react on could be specified (default: `changed`)

~~~yaml
- hosts: localhost
  gather_facts: no
  tasks:
  - name: copy an ssl cert
    shell: echo cert has been changed


- hosts: localhost
  gather_facts: no
  tasks:
  - subscribe:
      name: copy an ssl cert
    notify: service restart one
  handlers:
  - name: service restart one
    shell: echo service one restarted


- hosts: localhost
  gather_facts: no
  tasks:
  - subscribe:
      name: copy an ssl cert
      react_on: changed
    notify: service restart two
  handlers:
  - name: service restart two
    shell: echo service two restarted
~~~


### Approach 4:

Provide new `subscribe` module (same as Approach 3) and `publish` keyword:

~~~yaml
- hosts: localhost
  gather_facts: no
  tasks:
  - name: copy an ssl cert
    shell: echo cert has been changed
    publish: yes


- hosts: localhost
  gather_facts: no
  tasks:
  - subscribe:
      name: copy an ssl cert
    notify: service restart one
  handlers:
  - name: service restart one
    shell: echo service one restarted


- hosts: localhost
  gather_facts: no
  tasks:
  - subscribe:
      name: copy an ssl cert
    notify: service restart two
  handlers:
  - name: service restart two
    shell: echo service two restarted
~~~

### Clarifications about role dependencies and publish

When using service roles having the subscription handlers and the publish task (e.g. cert change) is defined in a depended role (SSL role) only the first service role running the "cert change" task as dependency will trigger the publish.

In any other service role in the playbook having "SSL role" as dependency, the task won't be `changed` anymore.

Therefore a once published "message" should not be overwritten or so called "unpublished" by running the same task in a followed role in the playbook.

## Conclusion

Feedback is requested to improve any of the above approaches, or provide further approaches to solve this problem.
