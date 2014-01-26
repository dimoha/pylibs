# -*- coding: utf-8 -*-
import time, threading
import Queue
from pylibs.utils import UtilsException

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
            print 'started'
            while True:
                if self._stop.is_set():
                    break
                try:
                    task = self.queue.get_nowait()
                    print 'Finded task %s' % task
                    try:
                        task.result = task.perform()
                    except Exception as e:
                        task.error = e
                        print '===> %s' % str(e)
                        
                    self.queue.task_done()
                    
                except Queue.Empty:
                    time.sleep(1)
                except Exception as e:
                    print 'Exception: %s' % e
            print 'finished'

        def stop(self):
            self._stop.set()
            
    def __init__(self, num_threads):
        self.queue = Queue.Queue()
        self.num_threads = num_threads
        self.threads = []


    def start(self):
        print 'Spider started.'
        for i in range(self.num_threads):
            thread = MultiThreadsTasksManager.WorkerThread(self.queue, i)
            thread.start()
            self.threads.append(thread)

    def execute(self, tasks_data):
        
        tasks = map(lambda x: self.__class__.Task(x), tasks_data)
            
        for task in tasks:
            self.queue.put(task)
        self.queue.join()
            
        for task in tasks:
            if task.error is not None:
                raise MultiThreadsTasksManagerException('Not all tasks completed. Exception: %s in task %s.' % (task.error, task))
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
                print 'wait stopping of threads'
                time.sleep(1)
        print 'all threads stopped!'
