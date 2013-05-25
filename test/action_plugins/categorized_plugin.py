from ansible.runner import return_data


class ActionModule (object):
    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject,
            complex_args=None, **kwargs):
        # This plug-in should be ignored in deference to
        # category/categorized_plugin.py, so it should never actually
        # run.
        return return_data.ReturnData(
            conn=conn, comm_ok=True,
            result={"msg": "this plug-in should never be run"})
