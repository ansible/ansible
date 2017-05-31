import os
import os.path
import tempfile
from ansible import utils
from ansible.runner.return_data import ReturnData
from ansible.utils import template

class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def _assemble_from_fragments(self, src_path):
        ''' assemble a file from a directory of fragments '''
        tmpfd, temp_path = tempfile.mkstemp()
        tmp = os.fdopen(tmpfd,'w')
        for f in sorted(os.listdir(src_path)):
            fragment = "%s/%s" % (src_path, f)
            if os.path.isfile(fragment):
                tmp.write(file(fragment).read())
        tmp.close()
        return temp_path

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):

        # load up options
        options  = {}
        if complex_args:
            options.update(complex_args)
        options.update(utils.parse_kv(module_args))

        changed = False
        source = options.get('src', None)
        dest = options.get('dest', None)

        if source is None or dest is None:
            result = dict(failed=True, msg="src and dest are required")
            return ReturnData(conn=conn, comm_ok=False, result=result)

        source = template.template(self.runner.basedir, source, inject)
        source = utils.path_dwim(self.runner.basedir, source)

        if not os.path.exists(source):
            result = dict(failed=True, msg="Source (%s) does not exist" % source)
            return ReturnData(conn=conn, comm_ok=False, result=result)

        if not os.path.isdir(source):
            result = dict(failed=True, msg="Source (%s) does not directory" % source)
            return ReturnData(conn=conn, comm_ok=False, result=result)

        destmd5 = False
        if os.path.exists(dest):
            destmd5 = utils.md5(dest)

        # Does all work assembling the file
        path = self._assemble_from_fragments(source)
        pathmd5 = utils.md5(path)

        if pathmd5 != destmd5:
            os.rename(path, dest)
            changed = True

        return ReturnData(conn=conn, comm_ok=True, result=dict(changed=changed))
