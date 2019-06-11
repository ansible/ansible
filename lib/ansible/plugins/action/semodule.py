from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text
import ansible.module_utils.semodule as semodule
from ansible.utils.hashing import checksum
import traceback

class ActionModule(ActionBase):

    def _check_policy_version(self, new_version, cur_version):
        version_list = [ int(x) for x in new_version.split('.') ]
        cur_version_list = [ int(x) for x in cur_version.split('.') ]
        if version_list < cur_version_list:
            return True, 'older'
        elif version_list > cur_version_list:
            return True, 'newer'
        else:
            return False, 'same'

    def _module_exist_(self, name, semodule_info):
        if name in semodule_info:
            return True
        return False

    def _get_semodule_info(self):
        result = self._low_level_execute_command('semodule -l')
        if result['rc'] != 0:
            AnsibleError('semodule command failed')
        return to_text(result['stdout'])

    def _remove_module(self, name):
        result = self._low_level_execute_command('semodule -r {module}'.format(module=name))
        if result['rc'] != 0:
            AnsibleError('failed to remove policy')

    def _copy_te_file(self, file, dest, task_vars):
        local_checksum = checksum(file)
        remote_path = self._transfer_file(file, dest)
        self._fixup_perms2((self._connection._shell.tmpdir, remote_path))
        remote_checksum = self._execute_remote_stat(dest, all_vars=task_vars, follow=False)
        if local_checksum != remote_checksum['checksum']:
            AnsibleError('.te file copy failed, checksum does not match')

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)
        self._make_tmp_path()
        new_module = self._task.copy()
        new_module_args = self._task.args.copy()
        state = self._task.args.get('state', 'present')
        file_name = self._task.args.get('src', None)
        tmp_src = self._connection._shell.join_path(self._connection._shell.tmpdir, 'source')
        try:
            te_file = self._find_needle('files', file_name)
        except AnsibleError as error:
            result['failed'] = True
            result['msg'] = to_text(error)
            result['exception'] = traceback.format_exc()
            return result
        policy_def = semodule.parse_module_info(semodule.read_te_file(te_file))
        semodule_info = self._get_semodule_info()
        cur_pol = None
        if self._module_exist_(policy_def['name'], semodule_info):
            cur_pol = semodule.parse_pol_info(policy_def['name'], semodule_info)
        if state == 'latest':
            if cur_pol:
                ver_check = self._check_policy_version(policy_def['version'], cur_pol['version'])
                if ver_check[1] == 'newer':
                    self._copy_te_file(te_file, tmp_src, task_vars)
                    new_module_args.update(dict(src=tmp_src))
                    module_return = self._execute_module(module_name='semodule', module_args=new_module_args, task_vars=task_vars)
                    result.update(module_return)
                else:
                    result['version'] = cur_pol['version']
                    result['name'] = cur_pol['name']
        elif state == 'present':
            if not cur_pol:
                self._copy_te_file(te_file, tmp_src, task_vars)
                new_module_args.update(dict(src=tmp_src))
                module_return = self._execute_module(module_name='semodule', module_args=new_module_args, task_vars=task_vars)
                result.update(module_return)
        elif state == 'absent':
            if cur_pol:
                self._remove_module(policy_def['name'])
                result['changed'] = True
                result['name'] = cur_pol['name']
                result['version'] = cur_pol['version']
            else:
                result['changed'] = False
                result['name'] = None
                result['version'] = None
        # clean up temp path
        self._remove_tmp_path(self._connection._shell.tmpdir)
        return result