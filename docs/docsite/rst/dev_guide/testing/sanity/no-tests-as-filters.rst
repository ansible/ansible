Sanity Tests » no-tests-as-filters
==================================

Using Ansible provided jinja tests as filters will be removed in Ansible 2.9.

Prior to Ansible 2.5, jinja tests included within Ansible were most often used as filters. The large difference in use is that filters are referenced as ``variable | filter_name`` where as jinja tests are refereced as ``variable is test_name``.

Jinja tests are used for comparisons, whereas filters are used for data manipulation, and have different applications in jinja. This change is to help differentiate the concepts for a better understanding of jinja, and where each can be appropriately used.

As of Ansible 2.5 using an Ansible provided jinja test with filter syntax, will display a deprecation error.
