*********************
module_utils/basic.py
*********************

.. contents:: Topics

.. _dev_guide_module_utils_basic:

Basic.py
========


AnsibleModule & argument_spec
------------------------------


# FIXME Flesh out example showing all options

# FIXME Add a module & integration test that defends all of this (I think modules can go relative to the roles directory)

.. code-block:: python

    def main():
        module = AnsibleModule(
            argument_spec=dict(
                state=dict(default='present', choices=['present', 'absent']),
                username=dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
                password=dict(no_log=True),
                token=dict(no_log=True),
                src=dict(type='path'),
                priority=dict(type='int'),
                src_options=dict(removed_in_version='2.4'),
            ),
            mutually_exclusive=(['password', 'token'],),
            required_together=(['username', 'password'],),
            required_one_of=[['password', 'token']],
            required_if=[('state', 'present', ['src', 'priority'])],
            supports_check_mode=True
        )

The ``AnsibleModule`` class takes the following:

All arguments are optional unless otherwise specified.

:argument_spec:
  A dictionary of options in the following form:

  :name: `required`
    The (primary) name of the option. A ``dict`` defines the following parameters:

    :required:
      Is this option `always` required?
      Only needed if True, as the default is False.
      If the option is only required sometimes see the conditional options such as ``mutually_exclusive``, ``required_together``, etc.
    :default:
      If not specified by the user what is the default value for this option.
    :fallback:
      If a value isn't specified in the playbook gives the ability to read from another source.
      Currently supports ``env_fallback``. In this case the environment variable of where Ansible is run is used.
      You will need to add ``from ansible.module_utils.basic import env_fallback``
    :type:
      Optionally validate the format of the data.
      If you wish to add extra validation rules, see ``module_utils/basic.py``.
      The following types are built into Ansible.

        :str:
          A string, this is the default, so can be skipped.
        :list:
          A list.
          Allows passing a YAML list in via the Playbook.
        :dict:
          A dictionary.
        :bool:
          This option should accept the common terms for truth, such as "yes", "on", 1, True, etc.
          If you find yourself trying to create an option that access bool & other values then that's an indication that the design needs revisiting.
          Do not specify ``choices`` when using bool.
        :int:
          An integer.
        :float:
          A floating point.
        :path:
          Ensure option is a path where the playbook is executed.
        :raw:
          FIXME details of when this would be useful.
        :jsonarg:
          FIXME details of when this would be useful.
        :json:
        :bytes: # example (human_to_bytes)
          # FIXME test and check return type
        :bits: # example (human_to_bytes)
          # FIXME test and check return type
    :choices:
      A list of possible allowed values for this option.
      Must not be set when using ``type='bool'``.
    :aliases:
      A list of aliases that this option name can be referred to in playbooks.
    :no_log:
      Boolean to state if this option may contain sensitive data, such as passwords, or authentication tokens.
    :removed_in_version:
      In which version of Ansible this option will be removed.
      A deprecation message will be printed if this option is used.
      Should have a corresponding line in ``DOCUMENTATION`` block


* suboptions - separate example

* Link to how to document your module
* Shared arguments (cloud, network)
* add_file_common_args


* supports_check_mode
* Naming of common options (verify_ssl)



