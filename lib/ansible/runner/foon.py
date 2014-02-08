# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.




import multiprocessing.pool as mpool
import multiprocessing
import sys
import os

POOL = None
OLD_SIZE = 0

class MyPool(mpool.Pool):

    '''
    What is Foon?
    A Foon is another name for a Spork, which is a Fork plus a Spoon
    this class is a wrapper around multiprocessing in Python
    which deals with parallelism via Forks. 
    there is no Spoon.

    Two things we do differently over stock multiprocessing:
       * intercept exceptions
       * duplicate stdin per host to enable the process to ask questions about host key checking

    That's it.  This class is specific to Ansible's runner forking and is not meant to be generic.
    '''       


    def __init__(self, *args, **kwargs):
        super(MyPool, self).__init__(*args, **kwargs)

    # overriding map_async to catch exceptions and be extensible

    def map_async(self, func, iterable, chunksize=None, callback=None):
        '''
        Asynchronous equivalent of `map()` builtin
        '''

        mapstar = mpool.mapstar

        if not hasattr(iterable, '__len__'):
            iterable = list(iterable)

        if chunksize is None:
            chunksize, extra = divmod(len(iterable), len(self._pool) * 4)
            if extra:
                chunksize += 1

        task_batches = MyPool._get_tasks(func, iterable, chunksize)

        new_batches = []
        stdins = []
        for x in task_batches:
            # make sure each batch has a different stdin
            new_stdin = os.fdopen(os.dup(sys.stdin.fileno()))
            (function, data_list) = x
            new_data_list = []
            for host_name in data_list:
               new_data_list.append((host_name, new_stdin))
            stdins.append(new_stdin)
            new_batches.append((function, new_data_list))

        result = mpool.MapResult(self._cache, chunksize, len(iterable), callback)

        #for i, x in enumerate(task_batches):
        #   print "%s => %s" % (i,x)

        self._taskqueue.put(
        (
             (
                (result._job, i, mapstar, (x,), {}) for i, x in enumerate(new_batches) # task_batches)
             ), None)
        )

        for x in stdins:
           x.close()

        return result


       

class Foon(object):

   def __init__(self, size):
       self.pool = self._make_pool(size)

   def _make_pool(self, processes=None, initializer=None, initargs=()):
       '''
       Returns a process pool object
       '''
       return MyPool(processes, initializer, initargs)

   def map(self, function, data_list):
       try:
           return self.pool.map(function, data_list)
       except KeyboardInterrupt:
           print "KEYBOARD INTERRUPT!"
           sys.exit(1)






