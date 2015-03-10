Jinja2 filters
==============

.. contents:: Topics

Filters in Jinja2 are a way of transforming template expressions from one kind of data into another.  Jinja2
ships with many of these. See `builtin filters`_ in the official Jinja2 template documentation.

In addition to those, Ansible supplies many more.

.. _filters_for_formatting_data:

Filters For Formatting Data
---------------------------

The following filters will take a data structure in a template and render it in a slightly different format.  These
are occasionally useful for debugging::

    {{ some_variable | to_nice_json }}
    {{ some_variable | to_nice_yaml }}

.. _filters_used_with_conditionals:

Filters Often Used With Conditionals
------------------------------------

The following tasks are illustrative of how filters can be used with conditionals::

    tasks:

      - shell: /usr/bin/foo
        register: result
        ignore_errors: True

      - debug: msg="it failed"
        when: result|failed

      # in most cases you'll want a handler, but if you want to do something right now, this is nice
      - debug: msg="it changed"
        when: result|changed

      - debug: msg="it succeeded"
        when: result|success

      - debug: msg="it was skipped"
        when: result|skipped

.. _forcing_variables_to_be_defined:

Forcing Variables To Be Defined
-------------------------------

The default behavior from ansible and ansible.cfg is to fail if variables are undefined, but you can turn this off.

This allows an explicit check with this feature off::

    {{ variable | mandatory }}

The variable value will be used as is, but the template evaluation will raise an error if it is undefined.


.. _defaulting_undefined_variables:

Defaulting Undefined Variables
------------------------------

Jinja2 provides a useful 'default' filter, that is often a better approach to failing if a variable is not defined::

    {{ some_variable | default(5) }}

In the above example, if the variable 'some_variable' is not defined, the value used will be 5, rather than an error
being raised.


.. _omitting_undefined_variables:

Omitting Undefined Variables and Parameters
-------------------------------------------

As of Ansible 1.8, it is possible to use the default filter to omit variables and module parameters using the special
`omit` variable::

    - name: touch files with an optional mode
      file: dest={{item.path}} state=touch mode={{item.mode|default(omit)}}
      with_items:
        - path: /tmp/foo
        - path: /tmp/bar
        - path: /tmp/baz
          mode: "0444"

For the first two files in the list, the default mode will be determined by the umask of the system as the `mode=`
parameter will not be sent to the file module while the final file will receive the `mode=0444` option.


.. _list_filters:

List Filters
------------

These filters all operate on list variables.

.. versionadded:: 1.8

To get the minimum value from list of numbers::

    {{ list1 | min }}

To get the maximum value from a list of numbers::

    {{ [3, 4, 2] | max }}

.. _set_theory_filters:

Set Theory Filters
------------------
All these functions return a unique set from sets or lists.

.. versionadded:: 1.4

To get a unique set from a list::

    {{ list1 | unique }}

To get a union of two lists::

    {{ list1 | union(list2) }}

To get the intersection of 2 lists (unique list of all items in both)::

    {{ list1 | intersect(list2) }}

To get the difference of 2 lists (items in 1 that don't exist in 2)::

    {{ list1 | difference(list2) }}

To get the symmetric difference of 2 lists (items exclusive to each list)::

    {{ list1 | symmetric_difference(list2) }}

.. _version_comparison_filters:

Version Comparison Filters
--------------------------

.. versionadded:: 1.6

To compare a version number, such as checking if the ``ansible_distribution_version``
version is greater than or equal to '12.04', you can use the ``version_compare`` filter.

The ``version_compare`` filter can also be used to evaluate the ``ansible_distribution_version``::

    {{ ansible_distribution_version | version_compare('12.04', '>=') }}

If ``ansible_distribution_version`` is greater than or equal to 12, this filter will return True, otherwise it will return False.

The ``version_compare`` filter accepts the following operators::

    <, lt, <=, le, >, gt, >=, ge, ==, =, eq, !=, <>, ne

This filter also accepts a 3rd parameter, ``strict`` which defines if strict version parsing should
be used.  The default is ``False``, and if set as ``True`` will use more strict version parsing::

    {{ sample_version_var | version_compare('1.0', operator='lt', strict=True) }}

.. _random_filter:

Random Number Filter
--------------------

.. versionadded:: 1.6

This filter can be used similar to the default jinja2 random filter (returning a random item from a sequence of
items), but can also generate a random number based on a range.

To get a random item from a list::

    {{ ['a','b','c']|random }} => 'c'

To get a random number from 0 to supplied end::

    {{ 59 |random}} * * * * root /script/from/cron

Get a random number from 0 to 100 but in steps of 10::

    {{ 100 |random(step=10) }}  => 70

Get a random number from 1 to 100 but in steps of 10::

    {{ 100 |random(1, 10) }}    => 31
    {{ 100 |random(start=1, step=10) }}    => 51


Shuffle Filter
--------------

.. versionadded:: 1.8

This filter will randomize an existing list, giving a different order every invocation.

To get a random list from an existing  list::

    {{ ['a','b','c']|shuffle }} => ['c','a','b']
    {{ ['a','b','c']|shuffle }} => ['b','c','a']

note that when used with a non 'listable' item it is a noop, otherwise it always returns a list


.. _math_stuff:

Math
--------------------
.. versionadded:: 1.9


To see if something is actually a number::

    {{ myvar | isnan }}

Get the logarithm (default is e)::

    {{ myvar | log }}

Get the base 10 logarithm::

    {{ myvar | log(10) }}

Give me the power of 2! (or 5)::

    {{ myvar | pow(2) }}
    {{ myvar | pow(5) }}

Square root, or the 5th::

    {{ myvar | root }}
    {{ myvar | root(5) }}

Note that jinja2 already provides some like abs() and round().

.. _ipaddr_filter:

IP address filter
-----------------
.. versionadded:: 1.9

To test if a string is a valid IP address::

  {{ myvar | ipaddr }}

You can also require a specific IP protocol version::

  {{ myvar | ipv4 }}
  {{ myvar | ipv6 }}

IP address filter can also be used to extract specific information from an IP
address. For example, to get the IP address itself from a CIDR, you can use::

  {{ '192.0.2.1/24' | ipaddr('address') }}

More information about ``ipaddr`` filter and complete usage guide can be found
in :doc:`playbooks_filters_ipaddr`.

.. _hash_filters:

Hashing filters
--------------------
.. versionadded:: 1.9

To get the sha1 hash of a string::

    {{ 'test1'|hash('sha1') }}

To get the md5 hash of a string::

    {{ 'test1'|hash('md5') }}

Get a string checksum::

    {{ 'test2'|checksum }}

Other hashes (platform dependant)::

    {{ 'test2'|hash('blowfish') }}

To get a sha512 password hash (random salt)::

    {{ 'passwordsaresecret'|password_hash('sha512') }}

To get a sha256 password hash with a specific salt::

    {{ 'secretpassword'|password_hash('sha256', 'mysecretsalt') }}


Hash types available depend on the master system running ansible,
'hash' depends on hashlib password_hash depends on crypt.


.. _other_useful_filters:

Other Useful Filters
--------------------

To use one value on true and another on false (since 1.9)::

   {{ name == "John" | ternary('Mr','Ms') }}

To concatenate a list into a string::

   {{ list | join(" ") }}

To get the last name of a file path, like 'foo.txt' out of '/etc/asdf/foo.txt'::

    {{ path | basename }}

To get the directory from a path::

    {{ path | dirname }}

To expand a path containing a tilde (`~`) character (new in version 1.5)::

    {{ path | expanduser }}

To get the real path of a link (new in version 1.8)::

   {{ path | realpath }}

To work with Base64 encoded strings::

    {{ encoded | b64decode }}
    {{ decoded | b64encode }}

To create a UUID from a string (new in version 1.9)::

    {{ hostname | to_uuid }}

To cast values as certain types, such as when you input a string as "True" from a vars_prompt and the system
doesn't know it is a boolean value::

   - debug: msg=test
     when: some_string_value | bool

To match strings against a regex, use the "match" or "search" filter::

    vars:
      url: "http://example.com/users/foo/resources/bar"

    tasks:
        - shell: "msg='matched pattern 1'"
          when: url | match("http://example.com/users/.*/resources/.*")

        - debug: "msg='matched pattern 2'"
          when: url | search("/users/.*/resources/.*")

'match' will require a complete match in the string, while 'search' will require a match inside of the string.

To replace text in a string with regex, use the "regex_replace" filter::

    # convert "ansible" to "able"    
    {{ 'ansible' | regex_replace('^a.*i(.*)$', 'a\\1') }}         

    # convert "foobar" to "bar"
    {{ 'foobar' | regex_replace('^f.*o(.*)$', '\\1') }}

.. note:: If "regex_replace" filter is used with variables inside YAML arguments (as opposed to simpler 'key=value' arguments),
   then you need to escape backreferences (e.g. ``\\1``) with 4 backslashes (``\\\\``) instead of 2 (``\\``).

A few useful filters are typically added with each new Ansible release.  The development documentation shows
how to extend Ansible filters by writing your own as plugins, though in general, we encourage new ones
to be added to core so everyone can make use of them.

.. _builtin filters: http://jinja.pocoo.org/docs/templates/#builtin-filters

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_conditionals`
       Conditional statements in playbooks
   :doc:`playbooks_variables`
       All about variables
   :doc:`playbooks_loops`
       Looping in playbooks
   :doc:`playbooks_roles`
       Playbook organization by roles
   :doc:`playbooks_best_practices`
       Best practices in playbooks
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


