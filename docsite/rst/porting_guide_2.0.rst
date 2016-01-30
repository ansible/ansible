Porting Guide
=============


Playbook
--------

* backslash escapes When specifying parameters in jinja2 expressions in YAML
  dicts, backslashes sometimes needed to be escaped twice. This has been fixed
  in 2.0.x so that escaping once works. The following example shows how
  playbooks must be modified::

    # Syntax in 1.9.x
    - debug:
        msg: "{{ 'test1_junk 1\\\\3' | regex_replace('(.*)_junk (.*)', '\\\\1 \\\\2') }}"
    # Syntax in 2.0.x
    - debug:
        msg: "{{ 'test1_junk 1\\3' | regex_replace('(.*)_junk (.*)', '\\1 \\2') }}"

    # Output:
    "msg": "test1 1\\3"

To make an escaped string that will work on all versions you have two options::

- debug: msg="{{ 'test1_junk 1\\3' | regex_replace('(.*)_junk (.*)', '\\1 \\2') }}"

uses key=value escaping which has not changed.  The other option is to check for the ansible version::

"{{ (ansible_version|version_compare('ge', '2.0'))|ternary( 'test1_junk 1\\3' | regex_replace('(.*)_junk (.*)', '\\1 \\2') , 'test1_junk 1\\\\3' | regex_replace('(.*)_junk (.*)', '\\\\1 \\\\2') ) }}"

* trailing newline When a string with a trailing newline was specified in the
  playbook via yaml dict format, the trailing newline was stripped. When
  specified in key=value format, the trailing newlines were kept. In v2, both
  methods of specifying the string will keep the trailing newlines. If you
  relied on the trailing newline being stripped, you can change your playbook
  using the following as an example::

    # Syntax in 1.9.x
    vars:
      message: >
        Testing
        some things
    tasks:
    - debug:
        msg: "{{ message }}"

    # Syntax in 2.0.x
    vars:
      old_message: >
        Testing
        some things
      message: "{{ old_messsage[:-1] }}"
    - debug:
        msg: "{{ message }}"
    # Output
    "msg": "Testing some things"

* When specifying complex args as a variable, the variable must use the full jinja2
  variable syntax (```{{var_name}}```) - bare variable names there are no longer accepted.
  In fact, even specifying args with variables has been deprecated, and will not be
  allowed in future versions::

    ---
    - hosts: localhost
      connection: local
      gather_facts: false
      vars:
        my_dirs:
          - { path: /tmp/3a, state: directory, mode: 0755 }
          - { path: /tmp/3b, state: directory, mode: 0700 }
      tasks:
        - file:
          args: "{{item}}" # <- args here uses the full variable syntax
          with_items: my_dirs

* porting task includes
* More dynamic. Corner-case formats that were not supposed to work now do not, as expected.
* variables defined in the yaml dict format https://github.com/ansible/ansible/issues/13324
* templating (variables in playbooks and template lookups) has improved with regard to keeping the original instead of turning everything into a string.
  If you need the old behavior, quote the value to pass it around as a string.
* Empty variables and variables set to null in yaml are no longer converted to empty strings. They will retain the value of `None`.
  You can override the `null_representation` setting to an empty string in your config file by setting the `ANSIBLE_NULL_REPRESENTATION` environment variable.
* Extras callbacks must be whitelisted in ansible.cfg. Copying is no longer necessary but whitelisting in ansible.cfg must be completed.
* dnf module has been rewritten. Some minor changes in behavior may be observed.
* win_updates has been rewritten and works as expected now.

Deprecated
----------

While all items listed here will show a deprecation warning message, they still work as they did in 1.9.x. Please note that they will be removed in 2.2 (Ansible always waits two major releases to remove a deprecated feature).

* Bare variables in `with_` loops should instead use the “{{var}}” syntax, which helps eliminate ambiguity.
* The ansible-galaxy text format requirements file. Users should use the YAML format for requirements instead.
* Undefined variables within a `with_` loop’s list currently do not interrupt the loop, but they do issue a warning; in the future, they will issue an error.
* Using dictionary variables to set all task parameters is unsafe and will be removed in a future version. For example::

    - hosts: localhost
      gather_facts: no
      vars:
        debug_params:
          msg: "hello there"
      tasks:
        # These are both deprecated:
        - debug: "{{debug_params}}"
        - debug:
          args: "{{debug_params}}"

        # Use this instead:
        - debug:
            msg: "{{debug_params['msg']}}"

* Host patterns should use a comma (,) or colon (:) instead of a semicolon (;) to separate hosts/groups in the pattern.
* Ranges specified in host patterns should use the [x:y] syntax, instead of [x-y].
* Playbooks using privilege escalation should always use “become*” options rather than the old su*/sudo* options.
* The “short form” for vars_prompt is no longer supported.
  For example::

    vars_prompt:
        variable_name: "Prompt string"

* Specifying variables at the top level of a task include statement is no longer supported. For example::

    - include: foo.yml
        a: 1

Should now be::

    - include: foo.yml
      args:
        a: 1

* Setting any_errors_fatal on a task is no longer supported. This should be set at the play level only.
* Bare variables in the `environment` dictionary (for plays/tasks/etc.) are no longer supported. Variables specified there should use the full variable syntax: ‘{{foo}}’.
* Tags should no longer be specified with other parameters in a task include. Instead, they should be specified as an option on the task.
  For example::

    - include: foo.yml tags=a,b,c

  Should be::

    - include: foo.yml
      tags: [a, b, c]

* The first_available_file option on tasks has been deprecated. Users should use the with_first_found option or lookup (‘first_found’, …) plugin.


Porting plugins
===============

In ansible-1.9.x, you would generally copy an existing plugin to create a new one. Simply implementing the methods and attributes that the caller of the plugin expected made it a plugin of that type. In ansible-2.0, most plugins are implemented by subclassing a base class for each plugin type. This way the custom plugin does not need to contain methods which are not customized.


Lookup plugins
--------------
* lookup plugins ; import version


Connection plugins
------------------

* connection plugins

Action plugins
--------------

* action plugins

Callback plugins
----------------

Although Ansible 2.0 provides a new callback API the old one continues to work
for most callback plugins.  However, if your callback plugin makes use of
:attr:`self.playbook`, :attr:`self.play`, or :attr:`self.task` then you will
have to store the values for these yourself as ansible no longer automatically
populates the callback with them.  Here's a short snippet that shows you how::

    from ansible.plugins.callback import CallbackBase

    class CallbackModule(CallbackBase):
        def __init__(self):
            self.playbook = None
            self.play = None
            self.task = None

        def v2_playbook_on_start(self, playbook):
            self.playbook = playbook

        def v2_playbook_on_play_start(self, play):
            self.play = play

        def v2_playbook_on_task_start(self, task, is_conditional):
            self.task = task

        def v2_on_any(self, *args, **kwargs):
            self._display.display('%s: %s: %s' % (self.playbook.name,
            self.play.name, self.task))


Connection plugins
------------------

* connection plugins


Porting custom scripts
======================

Custom scripts that used the ``ansible.runner.Runner`` API in 1.x have to be ported in 2.x.  Please refer to:
https://github.com/ansible/ansible/blob/devel/docsite/rst/developing_api.rst
