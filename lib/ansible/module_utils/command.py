# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

def get_command_args():
  return dict(
      _raw_params=dict(),
      _uses_shell=dict(type='bool', default=False),
      argv=dict(type='list', elements='str'),
      chdir=dict(type='path'),
      executable=dict(),
      creates=dict(type='path'),
      removes=dict(type='path'),
      # The default for this really comes from the action plugin
      warn=dict(type='bool', default=False, removed_in_version='2.14', removed_from_collection='ansible.builtin'),
      stdin=dict(required=False),
      stdin_add_newline=dict(type='bool', default=True),
      strip_empty_ends=dict(type='bool', default=True),
      cmd=dict(),
  )