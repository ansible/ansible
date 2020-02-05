:orphan:

no-tests-as-filters
===================

Using Ansible provided Jinja2 tests as filters will be removed in Ansible 2.9.

Prior to Ansible 2.5, Jinja2 tests included within Ansible were most often used as filters. The large difference in use is that filters are referenced as ``variable | filter_name`` while Jinja2 tests are referenced as ``variable is test_name``.

Jinja2 tests are used for comparisons, whereas filters are used for data manipulation, and have different applications in Jinja2. This change is to help differentiate the concepts for a better understanding of Jinja2, and where each can be appropriately used.

As of Ansible 2.5 using an Ansible provided Jinja2 test with filter syntax will display a deprecation error.
