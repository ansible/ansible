#!/usr/bin/env python

import time
import Queue
import traceback
from multiprocessing import Process, Manager, Pipe, RLock

from ansible.playbook.play import Play
from ansible.playbook.task import Task
from ansible.utils.debug import debug

NUM_WORKERS = 50
NUM_HOSTS   = 2500
NUM_TASKS   = 1

class Foo:
   def __init__(self, i, j):
      self._foo = "FOO_%05d_%05d" % (i, j)

   def __repr__(self):
      return self._foo

   def __getstate__(self):
      debug("pickling %s" % self._foo)
      return dict(foo=self._foo)

   def __setstate__(self, data):
      debug("unpickling...")
      self._foo = data.get('foo', "BAD PICKLE!")
      debug("unpickled %s" % self._foo)

def results(pipe, workers):
   cur_worker = 0
   def _read_worker_result(cur_worker):
      result = None
      starting_point = cur_worker
      while True:
         (worker_prc, main_pipe, res_pipe) = workers[cur_worker]
         cur_worker += 1
         if cur_worker >= len(workers):
            cur_worker = 0

         if res_pipe[1].poll(0.01):
            debug("worker %d has data to read" % cur_worker)
            result = res_pipe[1].recv()
            debug("got a result from worker %d: %s" % (cur_worker, result))
            break

         if cur_worker == starting_point:
            break

      return (result, cur_worker)

   while True:
      result = None
      try:
         (result, cur_worker) = _read_worker_result(cur_worker)
         if result is None:
            time.sleep(0.01)
            continue
         pipe.send(result)
      except (IOError, EOFError, KeyboardInterrupt) as e:
         debug("got a breaking error: %s" % e)
         break
      except Exception as e:
         debug("EXCEPTION DURING RESULTS PROCESSING: %s" % e)
         traceback.print_exc()
         break

def worker(main_pipe, res_pipe):
   while True:
      foo = None
      try:
         if main_pipe.poll(0.01):
            foo = main_pipe.recv()
            time.sleep(0.07)
            res_pipe.send(foo)
         else:
            time.sleep(0.01)
      except (IOError, EOFError, KeyboardInterrupt), e:
         debug("got a breaking error: %s" % e)
         break
      except Exception, e:
         debug("EXCEPTION DURING WORKER PROCESSING: %s" % e)
         traceback.print_exc()
         break

workers = []
for i in range(NUM_WORKERS):
   (main_p1, main_p2) = Pipe()
   (res_p1, res_p2)   = Pipe()
   worker_p = Process(target=worker, args=(main_p2, res_p1))
   worker_p.start()
   workers.append((worker_p, (main_p1, main_p2), (res_p1, res_p2)))

in_p, out_p = Pipe()
res_p = Process(target=results, args=(in_p, workers))
res_p.start()

def send_data(obj):
   global cur_worker
   global workers
   global pending_results

   (w_proc, main_pipe, res_pipe) = workers[cur_worker]
   cur_worker += 1
   if cur_worker >= len(workers):
      cur_worker = 0

   pending_results += 1
   main_pipe[0].send(obj)
 
def _process_pending_results():
   global out_p
   global pending_results
   
   try:
      #p_lock.acquire()
      while out_p.poll(0.01):
         result = out_p.recv()
         debug("got final result: %s" % (result,))
         pending_results -= 1
   finally:
      #p_lock.release()
      pass

def _wait_on_pending_results():
   global pending_results
   while pending_results > 0:
      debug("waiting for pending results (%d left)" % pending_results)
      _process_pending_results()
      time.sleep(0.01)


debug("starting")
cur_worker      = 0
pending_results = 0

sample_play = Play()
for i in range(NUM_TASKS):
   for j in range(NUM_HOSTS):
      debug("queuing %d, %d" % (i, j))
      send_data(Task().load(dict(name="task %d %d" % (i,j), ping=""), sample_play))
      debug("done queuing %d, %d" % (i, j))
      _process_pending_results()
   debug("waiting for the results to drain...")
   _wait_on_pending_results()

in_p.close()
out_p.close()
res_p.terminate()

for (w_p, main_pipe, res_pipe) in workers:
   res_pipe[1].close()
   res_pipe[0].close()
   main_pipe[1].close()
   main_pipe[0].close()
   w_p.terminate()

debug("done")
