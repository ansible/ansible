# Proposal: Re-run handlers cli option

*Author*: René Moser <@resmo>

*Date*: 07/03/2016

- Status: New

## Motivation

The most annoying thing users face using ansible in production is running handlers manually after a task failed after a notified handler.

### Problems

Handler notifications get lost after a task failed and there is no help from ansible to catch up the notified handlers in a next ansible playbook run.

~~~yaml
- hosts: localhost
  gather_facts: no
  tasks:
    - name: simple task
      shell: echo foo
      notify: get msg out

    - name: this tasks fails
      fail: msg="something went wrong"

  handlers:
    - name: get msg out
      shell: echo handler run
~~~

Result:

~~~
$ ansible-playbook test.yml

PLAY ***************************************************************************

TASK [simple task] *************************************************************
changed: [localhost]

TASK [this tasks fails] ********************************************************
fatal: [localhost]: FAILED! => {"changed": false, "failed": true, "msg": "something went wrong"}

NO MORE HOSTS LEFT *************************************************************

RUNNING HANDLER [get msg out] **************************************************
	to retry, use: --limit @test.retry

PLAY RECAP *********************************************************************
localhost                  : ok=1    changed=1    unreachable=0    failed=1
~~~

## Solution proposal

Similar to retry, ansible should provide a way to manully invoke a list of handlers additionaly to the notified handlers in the plays:

~~~
 $ ansible-playbook test.yml --notify-handlers <handler>,<handler>,<handler>
 $ ansible-playbook test.yml --notify-handlers @test.handlers
~~~

Example:

~~~
 $ ansible-playbook test.yml --notify-handlers "get msg out"
~~~

The stdout of a failed play should provide an example how to run notified handlers in the next run:

~~~
...
RUNNING HANDLER [get msg out] **************************************************
	to retry, use: --limit @test.retry --notify-handlers @test.handlers
~~~

