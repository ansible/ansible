*************
Network Tests
*************

.. contents:: Topics



Overview of Network Testing
===========================

This page details the specifics around testing Ansible Networking modules.


.. important:: Network testing requirements for Ansible 2.4

   From Ansible 2.4 all network modules MUST include corrisponding unit tests to defend functionality.
   The unit tests must be added in the same PR that includes the new network module, or extends functionality.
   Integration tests, although not required, are a welcome addition.
   How to do this is explained in the rest of this document.






```
$ ANSIBLE_ROLES_PATH=targets ansible-playbook network-all.yaml
```

*NOTE* To run the network tests you will need a number of test machines and suitably configured inventory file, a sample is included in `test/integration/inventory.network`

*NOTE* As with the rest of the integration tests, they can be found grouped by module in `test/integration/targets/MODULENAME/`

To filter a set of test cases set `limit_to` to the name of the group, generally this is the name of the module:

```
$ ANSIBLE_ROLES_PATH=targets ansible-playbook -i inventory.network network-all.yaml -e "limit_to=eos_command"
```

To filter a singular test case set the tags options to eapi or cli, set limit_to to the test group,
and test_cases to the name of the test:

```
$ ANSIBLE_ROLES_PATH=targets ansible-playbook -i inventory.network network-all.yaml --tags="cli" -e "limit_to=eos_command test_case=notequal"
```


Integration Tests
------------------
Test cases are added to roles based on the module being testing. Test cases
should include both `cli` and `eapi` test cases. Cli test cases should be
added to `test/integration/targets/modulename/tests/cli` and eapi tests should be added to
`test/integration/targets/modulename/tests/eapi`.

In addition to positive testing, negative tests are required to ensure user friendly warnings & errors are generated, rather than backtraces, for example:

.. code-block: yaml

   - name: test invalid subset (foobar)
     eos_facts:
       provider: "{{ cli }}"
       gather_subset:
         - "foobar"
     register: result
     ignore_errors: true

   - assert:
       that:
         # Failures shouldn't return changes
         - "result.changed == false"
         # It's a failure
         - "result.failed == true"
         # Sensible Failure message
         - "'Subset must be one of' in result.msg"


Conventions
```````````

- Each test case should generally follow the pattern:

  >setup —> test —> assert —> test again (idempotent) —> assert —> -teardown (if needed) -> done

  This keeps test playbooks from becoming monolithic and difficult to
  troubleshoot.

- Include a name for each task that is not an assertion. (It's OK to add names
  to assertions too. But to make it easy to identify the broken task within a failed
  test, at least provide a helpful name for each task.)

- Files containing test cases must end in `.yaml`


Adding a new Network Platform
`````````````````````````````

A top level playbook is required such as `ansible/test/integration/eos.yaml` which needs to be references by `ansible/test/integration/network-all.yaml`

Where to find out more
======================

FIXME Details of Network Meetings

FIXME
=====
In an effort to ensure the highest quality of network modules, all contributions must include unit tests to exercise each feature of the module. Additionally, do to the nature of mocked interfaces unit tests use, network modules should also include integration tests. The integration tests should be runnable against supported versions of network devices as well as their virtual machine images or containers if available.

Examples of existing unit tests can be found in ansible/test/units
Examples of existing integration tests can be found in ansible/test/integration
