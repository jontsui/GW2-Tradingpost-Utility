from threading import Thread
from queue import Queue

class WorkerThread(Thread):
        
        def __init__(self, pool):
            Thread.__init__(self, daemon = True)
            self.pool_queue = pool.queue
            self.pool_results = pool.results
        
        def run(self): # Will be called by Thread.start
            while True:
                '''task is a tuple - task[0], task[1], task[2] are the 
                callable, args, kwargs respectively'''
                task = self.pool_queue.get()
                if task is None:
                    break
                # Unpack the positional and keyword arguments
                self.pool_results.append(task[0](*task[1], **task[2]))   
                self.pool_queue.task_done()

class ThreadPool:
    
    def __init__(self, num_threads):
        ''' Reference to these attributes will be passed to each thread'''
        self.threads_list = []
        self.queue = Queue()
        self.results = [] # To hold data that threads process
    
        for i in range(num_threads):
            self.threads_list.append(WorkerThread(self))
    
    def add_task(self, worker_func, *args, **kwargs):
        '''Adds a tuple to the queue containing the worker function and arguments to be 
        called by each thread'''
        self.queue.put((worker_func, args, kwargs)) # (func, [], {}), Note inner parenthesis
    
    def start(self):
        for t in self.threads_list:
            t.start()
    
    def join(self):
        '''Block until count of unfinished tasks in queue drops to zero'''
        self.queue.join()
    
    def stop_threads(self):
        '''Populate queue with None to signal threads to stop'''
        for i in self.threads_list:
            self.queue.put(None)

if __name__ == '__main__':
    
    def unit_test1():
        import time

        def worker(x):
            time.sleep(0.01)
            return x**2

        p = ThreadPool(1)

        for i in range(1, 101):
            p.add_task(worker, i)
        
        p.start()
        p.join()
        print(p.results)
        p.stop_threads()

    def unit_test2():
        x = 'Hello'

        def worker():
            print(x + 'World')
        
        t = Thread(target = worker)
        t.start()
    

    
    



