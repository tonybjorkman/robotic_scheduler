from world.world import Equipment
from typing import Tuple, List
from collections import deque
import logging

logger = logging.getLogger(__name__)


class JobFactory:

    def __init__(self):
        pass

    def create_job(self, jobtype:str, iron:Equipment, res_handler):
        if jobtype == "base":
            return BaseJob(jobtype, res_handler)
        elif jobtype == "big":
            return BaseJob(jobtype, res_handler)
        else:
            return None


class BaseTask:

    def __init__(self, name, robot, prio=2):
        self.robot = robot
        self.name = name
        self.prio = prio

    def need_toolchange(self):
        return False

    def _get_equipment(self):
        pass

    def run(self):
        pass

    def get_name(self):
        return self.name

    def get_priority(self):
        return self.prio

    def prereq_met(self):
        pass

    def is_finished(self):
        return True

    def __str__(self):
        return self.get_name()


class BaseJob:

    def __init__(self, res_handler, iron, name=None):
        self.current_task = None
        self.task_queue = deque()
        self.name=name
        self.res_handler = res_handler
        self.iron = iron
        pass

    def need_toolchange(self):
        task = self._get_next_task()
        return task.need_toolchange()

    def get_current_task_name(self):
        pass

    def get_current_priority(self):
        task = self._get_next_task()
        prio = task.get_priority()
        return prio

    def _get_next_task(self):
        if len(self.task_queue) == 0:
            return 0
        task = self.task_queue.pop()
        self.task_queue.append(task)
        return task

    def run_next_task(self):
        task = self.task_queue.pop()
        self.current_task = task
        logging.info("Running Task:"+str(task) + " in job:"+str(self))
        task.run()

    def cancel(self):
        pass

    def is_ready(self) -> bool:
        ready = self.current_task is None or self.current_task.is_finished()
        return ready

    def is_finished(self):
        finished = len(self.task_queue)==0
        return finished

    def tasks_left(self) -> int:
        pass


class ResourceHandler:

    def __init__(self):
        self.items=dict()

    def add_item(self, item_name, item):
        if item_name in self.items.keys():
            self.items[item_name].append(item)
        else:
            self.items[item_name] = list()
            self.items[item_name].append(item)

    def get_free_equipment_by_string(self, item_name: str):
        if item_name not in self.items.keys():
            return None
        else:
            for item in self.items[item_name]:
                if item.is_free():
                    return item
        return None

    def checkout_prechecked_item(self, item_name, capacity=1)-> Equipment:
        ''' Get an item that is free and with the most suitable capacity '''
        if item_name not in self.items.keys():
            return None
        else:
            #prefer "availability" before "capacity"

            # equipment may be in three states:
            # 1. Free
            # 2. Occupied but not reserved
            # 3. Occupied and with a capacity reserved

            #if desired capacity is not found, look for one step lower capacity
            free_items = list(filter(lambda x: x.is_free(),self.items[item_name]))
            closest_capacity_sort = sorted(free_items,key=lambda x: abs(x.get_capacity()-capacity))

            for item in closest_capacity_sort:
                item.free = False
                return item

        return None

    # For single responsibility, let the resourcehandler decide whats free or not
    def check_in(self,item):
        item.free = True

    def get_item_w_slots(self, item_name: str, prefered_capacity: int)-> Tuple[int,Equipment]:
        pass



# Creates Jobs that are based on a specific Equipment with a specific slot capacity for
# processing orders in parallel. Such as an big Equipment doing multiple orders or
# a small doing a single order.
class JobCoordinator:

    def __init__(self, job_factory, res_handler:ResourceHandler):
        self.running_jobs: List[BaseJob]=[]
        self.orders = 0
        self.finished_jobs = list()
        self.waiting_jobs = list()
        self.factory = job_factory
        self.res_handler = res_handler

    # Should based on the order-list generate jobs and add to either reserved or
    # running list
    def get_equip_for_orders(self, job_equipment:str):
        #Find resources to fill the order
        #the reshandler will first return free items, then reserved items of desired slot size
        if self.orders > 1:
            pref_cap = 2
        elif self.orders == 1:
            pref_cap = 1
        else:
            return None

        iron = self.res_handler.checkout_prechecked_item(job_equipment, capacity=pref_cap)

        return iron

    def process_orders(self):
        job = self._create_job_from_orders()
        if job is not None:
            self.running_jobs.append(job)

    def add_order(self):
        self.orders += 1

    def remove_orders(self, number=1)->bool:
        if self.orders >= number:
            self.orders -= number
            return True
        else:
            return False

    def execute_next_job_task(self):
        job = self.get_highest_priority_job(3)
        if job is not None:
            job.run_next_task()
            if job.is_finished():
                self.finish_job(job)
        else:
            logger.info("No tasks to execute. Idling")

    def finish_job(self,job:BaseJob):
        # release the iron so it can be used to fulfill other orders
        self.res_handler.check_in(job.iron)

        self.running_jobs.remove(job)
        self.finished_jobs.append(job)
        logger.info("Job:" + str(job) + " is completed")

    def _create_job_from_orders(self):

        iron = self.get_equip_for_orders("iron")

        if iron is None:
            return None
        logger.info("Iron " + iron.get_name() + " is checked out by job "+str(self))

        if self.orders >= iron.get_capacity() == 2:
            new_job = self.factory.create_job("big", iron, self.res_handler)
            self.remove_orders(2)
        else:
            new_job = self.factory.create_job("base", iron, self.res_handler)
            self.remove_orders(1)

        return new_job

    def get_highest_priority_job(self,high_prio_treshold=3):
        # Prio for a job is based on its next tasks prio, 1 is low, 2 is default, 3 high,
        ready_jobs = list(filter(lambda x: x.is_ready(), self.running_jobs))
        jobs_prio_sort = sorted(ready_jobs,key=lambda x:(x.get_current_priority()),reverse=True)

        if len(jobs_prio_sort) == 0:
            return None

        #first look for high prio, that is more important than tool change
        if jobs_prio_sort[0].get_current_priority() >= high_prio_treshold:
            return jobs_prio_sort[0]

        jobs_tool_sort = sorted(ready_jobs, key=lambda x: (not x.need_toolchange(), x.get_current_priority())
                                , reverse=True)
        print(str(jobs_tool_sort))
        return jobs_tool_sort[0]

    def cancel_job(self, job: BaseJob):
        self.running_jobs.remove(job)

    #For test only
    def add_run_jobs(self, joblist):
        self.running_jobs = joblist
