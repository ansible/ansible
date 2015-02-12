- hosts: localhost
  gather_facts: no
  tasks:
  - debug: msg="the date is {{ lookup('pipe', 'date') }}"
