# -*- coding: utf-8 -*-
import time, threading
import Queue
from pylibs.utils import UtilsException
from logging import info, debug, warning, error

class MultiThreadsTasksManagerException(UtilsException):
    pass

class MultiThreadsTasksManager(object):
    
    class Task(object):
        
        def __init__(self, data):
            self.data = data
            self.error = None
            self.result = None
        
        def perform(self):
            raise NotImplementedError("Need implement is subclass")
    
            
    class WorkerThread(threading.Thread):
        def __init__(self, queue, threadID):
            threading.Thread.__init__(self)
            self.name = 'WorkerThread %s' % threadID
            self.queue = queue
            self.id = threadID
            self._stop = threading.Event()

        def run(self):
            debug('%s started' % self.name)
            while True:
                if self._stop.is_set():
                    break
                try:
                    task = self.queue.get_nowait()
                    debug('%s found task %s' % (self.name, task))
                    try:
                        task.result = task.perform()
                    except Exception as e:
                        task.error = e
                        error('%s error: %s' % (self.name, e))
                        
                    self.queue.task_done()
                    
                except Queue.Empty:
                    time.sleep(1)
                except Exception as e:
                    error('%s error: %s' % (self.name, e))
            debug('%s finished' % self.name)

        def stop(self):
            self._stop.set()
            
    def __init__(self, num_threads):
        self.queue = Queue.Queue()
        self.num_threads = num_threads
        self.threads = []


    def start(self):
        debug('Spider started.')
        for i in range(self.num_threads):
            thread = MultiThreadsTasksManager.WorkerThread(self.queue, i)
            thread.start()
            self.threads.append(thread)

    def execute(self, tasks_data, ignore_errors = False):
        
        tasks = map(lambda x: self.__class__.Task(x), tasks_data)
            
        for task in tasks:
            self.queue.put(task)
        self.queue.join()
            
        cnt_errors = 0
        cnt_total = 0
        
        errors = []
        for task in tasks:
            cnt_total += 1
            if task.error is not None:
                cnt_errors += 1
                if not ignore_errors:
                    errors.append('%s in task %s' % (task.error, task))
    
        if len(errors) > 0:
            raise MultiThreadsTasksManagerException("Not all tasks completed. Error in %s tasks from %s. Last error: %s." % (cnt_errors, cnt_total, errors[-1]))

        info("Count of tasks: %s. Errors: %s." % (cnt_total, cnt_errors))
        return tasks

    def stop(self):
        for thread in self.threads:
            thread.stop()

        while True:
            allStopped = True
            for thread in self.threads:
                if thread.isAlive():
                    allStopped = False
                    break
            if allStopped:
                break
            else:
                debug('Wait stopping of threads')
                time.sleep(1)
        debug('All threads stopped!')
