Network Getting Started: Intermediate Concepts
======================================================

Ansible Configuration: Setting global defaults

Ansible Vault: Protecting Sensitive Data

Privilege Escalation: `authorize` and `become`

Jinja2: Using Data with Filters and Tests

Conditional Comparison in Network Modules
```````````````````````````````````````````````````````````````

Conditional statements in Ansible evaluate the output from a managed node to determine what happens next in a playbook. Linux/Unix and Windows modules use mathematical symbols (for example, `==`, `<`, and `>`) for comparison. However, network modules use different conditional comparisons. The conditional tests for network modules are:

- eq - Equal
- neq - Not equal
- gt - Greater than
- ge - Greater than or equal
- lt - Less than
- le - Less than or equal
- contains - Object contains specified item

