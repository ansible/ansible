unwrap-unsafe
=============

Use of ``unwrap_var`` is strictly monitored for improper use, that could
cause future security issues.

Unsafe designations are very important to Ansible, to ensure that unsafe data
is not templated. Allowing unsafe data to be templated could cause adverse
security issues.

``unwrap_var`` should be used minimally, and only in very specific cases,
such as when passing data to a remote Python API where the receiving python
code does not understand our subclasses, potentially due to performing type
checks like ``if type(value) == 'str':``

Use of ``unwrap_var`` is not required to convert values to JSON, as the
default JSON encoder will implicitly ignore the subclass.
