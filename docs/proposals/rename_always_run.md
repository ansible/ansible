# Rename always_run to ignore_checkmode

*Author*: René Moser <@resmo>

*Date*: 02/03/2016

## Motivation

The task argument `always_run` is misleading.

Ansible is known to be readable by users without deep knowledge of creating playbooks, they do not understand
what `always_run` does at the first glance.

### Problems

The following looks scary if you have no idea, what `always_run` does:

```
- shell: dangerous_cleanup.sh
  when: cleanup == "yes"
  always_run: yes
```

You have a conditional but also a word that says `always`. This is a conflict in terms of understanding.

## Solution Proposal

Deprecate `always_run` by rename it to `ignore_checkmode`:

```
- shell: dangerous_cleanup.sh
  when: cleanup == "yes"
  ignore_checkmode: yes
```
