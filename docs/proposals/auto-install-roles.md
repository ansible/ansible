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

### Problems

- The most likely step in this process to be forgotten is the middle step. While we can improve processes and documentation to try and ensure that this step is not skipped, we can improve ansible-playbook so that the step is not required.
- Ansible-galaxy does ot sufficiently handle versioning. 
- There is not a consistent format for specifying a role in a playbook or a dependent role in meta/main.yml.

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


### Approach 3:  

*Author*: chouseknecht<@chouseknecht>

*Date*: 24/02/2016

This is a combination of ideas taken from IRC, the ansible development group, and conversations at the recent contributor's summit. It also incorporates most of the ideas from Approach 1 (above) with two notable texceptions: 1) it elmintates maintaing a roles file (or what we think of today as requirements.yml); and 2) it does not include the definition of rolesdir in the playbook.

Here's the approach:

- Share the role install logic between ansible-playbook and ansible-galaxy so that ansible-playbook can resolve and install missing roles at playbook run time simply by evaluating the playbook.
- Ansible-galaxy installs or preloads roles also by examining a playbook.
- Deprecate support for requirements.yaml (the two points above make it unnecessary).
- Make ansible-playbook auto-downloading of roles configurable in ansible.cfg. In certain circumstance it may be desirable to disable auto-download.
- Provide one format for specifying a role whether in a playbook or in meta/main.yml. Suggested format: 

    ```
    {
        'scm': 'git',
        'src': 'http://git.example.com/repos/repo.git',
        'version': 'v1.0',
        'name': 'repo’
    }
    ```
- For roles installed from Galaxy, Galaxy should provide some measure of security against version change. Galaxy should track the commit related to a version. If the role owner changes historical versions (today tags) and thus changes the commit hash, the affected version would become un-installable.

- Refactor the install process to encompass the following :

    - Idempotency - If a role version is already installed, don’t attempt to install it again. If symlinks are present (see below), don’t break or remove them.
    - Provide a --force option that overrides idempotency.
    - Install roles via tree-ish references, not just tags or commits (PR exists for this).
    - Support a whitelist of role sources. Galaxy should not be automatically assumed to be part of the whitelist.
    - Continue to be recursive, allowing roles to have dependencies specified in meta/main.yml.
    - Continue to install roles in the roles_path.
    - Use a symlink approach to managing role versions in the roles_path. Example:

        ```
        roles/
           briancoca.oracle_java7.v1.0
           briancoca.oracle_java7.v2.2
           briancoca.oracle_java7.qs3ih6x
           briancoca.oracle_java7 =>  briancoca.oracle_java7.qs3ih6x
        ```
    
## Conclusion

Feedback is requested to improve any of the above approaches, or provide further approaches to solve this problem.
