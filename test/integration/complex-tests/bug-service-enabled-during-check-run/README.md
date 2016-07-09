This is demonstration of a bug when playbook run in the check mode enables system service.

To demonstrate the issue we do following:
  - copy dummy service script
  - copy System V init script `ansible_test`
  - in the check mode run task `service: name=ansible_test enabled=yes`, this task actually
    enables service despite the fact that we run playbook in the check mode
  - in the check mode run task `service: name=ansible_test enabled=yes` again and check whether there are changes or not.  If ansible reports no changes, than the service was enabled the first time and the bug is actually present.  If Ansible does report changes, then there is no bug.

The bug is present on:
  - Debian 7
  - Ubuntu 12.04
  - Ubuntu 14.04
