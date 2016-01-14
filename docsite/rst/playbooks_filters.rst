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

    {{ some_variable | to_json }}
    {{ some_variable | to_yaml }}

For human readable output, you can use::

    {{ some_variable | to_nice_json }}
    {{ some_variable | to_nice_yaml }}

Alternatively, you may be reading in some already formatted data::

    {{ some_variable | from_json }}
    {{ some_variable | from_yaml }}

for example::

    tasks:
      - shell: cat /some/path/to/file.json
        register: result

      - set_fact: myvar="{{ result.stdout | from_json }}"

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

      - debug: msg="it succeeded in Ansible >= 2.1"
        when: result|succeeded

      - debug: msg="it succeeded"
        when: result|success

      - debug: msg="it was skipped"
        when: result|skipped

.. note:: From 2.1 You can also use success, failure, change, skip so the grammer matches, for those that want to be strict about it.

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

.. note:: If you are "chaining" additional filters after the `default(omit)` filter, you should instead do something like this:
      `"{{ foo | default(None) | some_filter or omit }}"`. In this example, the default `None` (python null) value will cause the
      later filters to fail, which will trigger the `or omit` portion of the logic. Using omit in this manner is very specific to
      the later filters you're chaining though, so be prepared for some trial and error if you do this.

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

Other hashes (platform dependent)::

    {{ 'test2'|hash('blowfish') }}

To get a sha512 password hash (random salt)::

    {{ 'passwordsaresecret'|password_hash('sha512') }}

To get a sha256 password hash with a specific salt::

    {{ 'secretpassword'|password_hash('sha256', 'mysecretsalt') }}


Hash types available depend on the master system running ansible,
'hash' depends on hashlib password_hash depends on crypt.

.. _combine_filter:

Combining hashes/dictionaries
-----------------------------

.. versionadded:: 2.0

The `combine` filter allows hashes to be merged. For example, the
following would override keys in one hash::

    {{ {'a':1, 'b':2}|combine({'b':3}) }}

The resulting hash would be::

    {'a':1, 'b':3}

The filter also accepts an optional `recursive=True` parameter to not
only override keys in the first hash, but also recurse into nested
hashes and merge their keys too::

    {{ {'a':{'foo':1, 'bar':2}, 'b':2}|combine({'a':{'bar':3, 'baz':4}}, recursive=True) }}

This would result in::

    {'a':{'foo':1, 'bar':3, 'baz':4}, 'b':2}

The filter can also take multiple arguments to merge::

    {{ a|combine(b, c, d) }}

In this case, keys in `d` would override those in `c`, which would
override those in `b`, and so on.

This behaviour does not depend on the value of the `hash_behaviour`
setting in `ansible.cfg`.

.. _extract_filter:

Extracting values from containers
---------------------------------

.. versionadded:: 2.1

The `extract` filter is used to map from a list of indices to a list of
values from a container (hash or array)::

    {{ [0,2]|map('extract', ['x','y','z'])|list }}
    {{ ['x','y']|map('extract', {'x': 42, 'y': 31})|list }}

The results of the above expressions would be::

    ['x', 'z']
    [42, 31]

The filter can take another argument::

    {{ groups['x']|map('extract', hostvars, 'ec2_ip_address')|list }}

This takes the list of hosts in group 'x', looks them up in `hostvars`,
and then looks up the `ec2_ip_address` of the result. The final result
is a list of IP addresses for the hosts in group 'x'.

The third argument to the filter can also be a list, for a recursive
lookup inside the container::

    {{ ['a']|map('extract', b, ['x','y'])|list }}

This would return a list containing the value of `b['a']['x']['y']`.

.. _comment_filter:

Comment Filter
--------------

.. versionadded:: 2.0

The `comment` filter allows to decorate the text with a chosen comment
style. For example the following::

    {{ "Plain style (default)" | comment }}

will produce this output::

    #
    # Plain style (default)
    #

Similar way can be applied style for C (``//...``), C block
(``/*...*/``), Erlang (``%...``) and XML (``<!--...-->``)::

    {{ "C style" | comment('c') }}
    {{ "C block style" | comment('cblock') }}
    {{ "Erlang style" | comment('erlang') }}
    {{ "XML style" | comment('xml') }}

It is also possible to fully customize the comment style::

    {{ "Custom style" | comment('plain', prefix='#######\n#', postfix='#\n#######\n   ###\n    #') }}

That will create the following output::

    #######
    #
    # Custom style
    #
    #######
       ###
        #

The filter can also be applied to any Ansible variable. For example to
make the output of the ``ansible_managed`` variable more readable, we can
change the definition in the ``ansible.cfg`` file to this::

    [defaults]

    ansible_managed = This file is managed by Ansible.%n
      template: {file}
      date: %Y-%m-%d %H:%M:%S
      user: {uid}
      host: {host}

and then use the variable with the `comment` filter::

    {{ ansible_managed | comment }}

which will produce this output::

    #
    # This file is managed by Ansible.
    #
    # template: /home/ansible/env/dev/ansible_managed/roles/role1/templates/test.j2
    # date: 2015-09-10 11:02:58
    # user: ansible
    # host: myhost
    #

.. _other_useful_filters:

Other Useful Filters
--------------------

To add quotes for shell usage::

    - shell: echo {{ string_value | quote }} 

To use one value on true and another on false (new in version 1.9)::

   {{ (name == "John") | ternary('Mr','Ms') }}

To concatenate a list into a string::

   {{ list | join(" ") }}

To get the last name of a file path, like 'foo.txt' out of '/etc/asdf/foo.txt'::

    {{ path | basename }}

To get the last name of a windows style file path (new in version 2.0)::

    {{ path | win_basename }}

To separate the windows drive letter from the rest of a file path (new in version 2.0)::

    {{ path | win_splitdrive }}

To get only the windows drive letter::

    {{ path | win_splitdrive | first }}

To get the rest of the path without the drive letter::

    {{ path | win_splitdrive | last }}

To get the directory from a path::

    {{ path | dirname }}

To get the directory from a windows path (new version 2.0)::

    {{ path | win_dirname }}

To expand a path containing a tilde (`~`) character (new in version 1.5)::

    {{ path | expanduser }}

To get the real path of a link (new in version 1.8)::

   {{ path | realpath }}

To get the relative path of a link, from a start point (new in version 1.7)::

    {{ path | relpath('/etc') }}

To get the root and extension of a path or filename (new in version 2.0)::

    # with path == 'nginx.conf' the return would be ('nginx', '.conf')
    {{ path | splitext }}

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

.. versionadded:: 1.6

To replace text in a string with regex, use the "regex_replace" filter::

    # convert "ansible" to "able"
    {{ 'ansible' | regex_replace('^a.*i(.*)$', 'a\\1') }}

    # convert "foobar" to "bar"
    {{ 'foobar' | regex_replace('^f.*o(.*)$', '\\1') }}

    # convert "localhost:80" to "localhost, 80" using named groups
    {{ 'localhost:80' | regex_replace('^(?P<host>.+):(?P<port>\\d+)$', '\\g<host>, \\g<port>') }}

.. note:: Prior to ansible 2.0, if "regex_replace" filter was used with variables inside YAML arguments (as opposed to simpler 'key=value' arguments),
   then you needed to escape backreferences (e.g. ``\\1``) with 4 backslashes (``\\\\``) instead of 2 (``\\``).

.. versionadded:: 2.0

To escape special characters within a regex, use the "regex_escape" filter::

    # convert '^f.*o(.*)$' to '\^f\.\*o\(\.\*\)\$'
    {{ '^f.*o(.*)$' | regex_escape() }}

To make use of one attribute from each item in a list of complex variables, use the "map" filter (see the `Jinja2 map() docs`_ for more)::

    # get a comma-separated list of the mount points (e.g. "/,/mnt/stuff") on a host
    {{ ansible_mounts|map(attribute='mount')|join(',') }}

A few useful filters are typically added with each new Ansible release.  The development documentation shows
how to extend Ansible filters by writing your own as plugins, though in general, we encourage new ones
to be added to core so everyone can make use of them.

.. _Jinja2 map() docs: http://jinja.pocoo.org/docs/dev/templates/#map

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


