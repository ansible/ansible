# Copyright (c) 2012 Michael DeHaan <michael.dehaan@gmail.com>
#
# Permission is hereby granted, free of charge, to any person 
# obtaining a copy of this software and associated documentation 
# files (the "Software"), to deal in the Software without restriction, 
# including without limitation the rights to use, copy, modify, merge, 
# publish, distribute, sublicense, and/or sell copies of the Software, 
# and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be 
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR 
# ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import ansible.runner
import ansible.constants as C
import json
import yaml

# TODO: make a constants file rather than
# duplicating these

class PlayBook(object):
    ''' 
    runs an ansible playbook, given as a datastructure
    or YAML filename
    '''

    def __init__(self, 
        playbook     =None,
        host_list    =C.DEFAULT_HOST_LIST,
        module_path  =C.DEFAULT_MODULE_PATH,
        forks        =C.DEFAULT_FORKS,
        timeout      =C.DEFAULT_TIMEOUT,
        remote_user  =C.DEFAULT_REMOTE_USER,
        remote_pass  =C.DEFAULT_REMOTE_PASS,
        verbose=False):

        # runner is reused between calls

        self.runner = ansible.runner.Runner(
            host_list=host_list,
            module_path=module_path,
            forks=forks,
            timeout=timeout,
            remote_user=remote_user,
            remote_pass=remote_pass,
            verbose=verbose
        )

        if type(playbook) == str:
            playbook = yaml.load(file(playbook).read())

    def run(self):
        pass

#    r = Runner(
#       host_list = DEFAULT_HOST_LIST,
#       module_name='ping',
#       module_args='',
#       pattern='*',
#       forks=3
#    )   
#    print r.run()

 

