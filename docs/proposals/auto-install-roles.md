# Auto Install Ansible roles

*Author*: Will Thames <@willthames>

*Date*: 19/02/2016

## Motivation

To use the latest (or even a specific) version of a playbook with the
appropriate roles, the following steps are typically required:

```
git pull upstream branch
ansible-galaxy install -r path/to/rolesfile.yml -p path/to/rolesdir -f
ansible-playbook run-the-playbook.yml
```

The most likely step in this process to be forgotten is the middle step. While
we can improve processes and documentation to try and ensure that this step is
not skipped, we can improve ansible-playbook so that the step is not required.

## Approaches

### Approach 1: Specify rolesfile and rolesdir in playbook

Provide new `rolesdir` and `rolesfile` keywords:

```
- hosts: application-env
  become: True
  rolesfile: path/to/rolesfile.yml
  rolesdir: path/to/rolesdir
  roles:
  - roleA
  - { role: roleB, tags: role_roleB }
```

Running ansible-playbook against such a playbook would cause the roles listed in
`rolesfile` to be installed in `rolesdir`.

Add new configuration to allow default rolesfile, default rolesdir and
whether or not to auto update roles (defaulting to False)

#### Advantages

- Existing mechanism for roles management is maintained
- Playbooks are not polluted with roles 'meta' information (version, source)

#### Disadvantage

- Adds two new keywords
- Adds three new configuration variables for defaults

### Approach 2: Allow rolesfile inclusion

Allow the `roles` section to include a roles file:

```
- hosts: application-env
  become: True
  roles:
  - include: path/to/rolesfile.yml
```

Running this playbook would cause the roles to be updated from the included
roles file.

This would also be functionally equivalent to specifying the roles file
content within the playbook:

```
- hosts: application-env
  become: True
  roles:
  - src: https://git.example.com/roleA.git
    scm: git
    version: 0.1
  - src: https://git.example.com/roleB.git
    scm: git
    version: 0.3
    tags: role_roleB
```

#### Advantages

- The existing rolesfile mechanism is maintained
- Uses familiar inclusion mechanism

#### Disadvantage

- Separate playbooks would need separate rolesfiles. For example, a provision
  playbook and upgrade playbook would likely have some overlap - currently
  you can use the same rolesfile with ansible-galaxy so that the same
  roles are available but only a subset of roles is used by the smaller
  playbook.
- The roles file would need to be able to include playbook features such
  as role tagging.
- New configuration defaults would likely still be required (and possibly
  an override keyword for rolesdir and role auto update)

## Conclusion

The author's preferred approach is currently Approach 1.

Feedback is requested to improve either approach, or provide further
approaches to solve this problem.
