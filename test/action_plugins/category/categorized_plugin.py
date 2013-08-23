from ansible.runner import return_data


class ActionModule (object):
    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject,
            complex_args=None, **kwargs):
        return return_data.ReturnData(conn=conn, comm_ok=True,
                                      result={"msg": "categorized"})
