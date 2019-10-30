from world.world import Equipment
from typing import Tuple

class JobFactory:

    def __init__(self):
        pass

    def create_job(self, jobtype:str):
        if jobtype == "base":
            return BaseJob()
        else:
            return None


class BaseTask:

    def __init__(self,name):
        self.name = name

    def need_toolchange(self):
        pass

    def _get_equipment(self):
        pass

    def run(self):
        pass

    def get_name(self):
        pass

    def get_priority(self):
        pass

    def prereq_met(self):
        pass


class BaseJob:

    def __init__(self):
        self.tasks = list()
        pass

    def need_toolchange(self):
        pass

    def get_current_task_name(self):
        pass

    def get_current_priority(self):
        pass

    def _get_next_task(self):
        pass

    def run_next_task(self):
        pass

    def cancel(self):
        pass

    def is_ready(self) -> bool:
        pass

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

    def get_prechecked_item(self, item_name: str):
        if item_name not in self.items.keys():
            return None
        else:
            for item in self.items[item_name]:
                if item.is_free():
                    return item
        return None

    def checkout_prechecked_item(self, item_name, reserve_if_not_free=False,capacity=1)-> Equipment:
        if item_name not in self.items.keys():
            return None
        else:
            #prefer "availability" before "capacity"
            #if desired capacity is not found, look for one step lower capacity
            for cap in range(capacity, 1, -1):
                for item in self.items[item_name]:
                    if item.is_free() and item.capacity() == cap:
                        item.free = False
                        return item

            if reserve_if_not_free:
                for cap in range(capacity, 0, -1):
                    for item in self.items[item_name]:
                        if not item.is_reserved():
                            item.has_reservation = True
                            return item

        return None

    def get_item_w_slots(self, item_name: str, prefered_capacity: int)-> Tuple[int,Equipment]:
        pass


class JobCoordinator:

    def __init__(self, job_factory, res_handler:ResourceHandler):
        self.running_jobs = list()
        self.orders = 0
        self.finished_jobs = list()
        self.waiting_jobs = list()
        self.factory = job_factory
        self.res_handler = res_handler

    def process_orders(self):
        #Find resources to fill the order
        #the reshandler will first return free items, then reserved items of desired slot size
        if self.orders > 1:
            pref_cap = 2
        else:
            pref_cap = 1

        slots,  iron = self.res_handler.get_item_w_slots("iron", pref_cap)

        if slots != 0:
            self.factory


    def add_order(self):
        self.orders+=1

    def remove_order(self):
        if self.orders>0:
            self.orders-=1

    def command_jobs(self):
        pass

    def _create_job_from_orders(self):
        pass

    def _get_highest_priority_job(self):
        pass

    def cancel_job(self, job:BaseJob):
        self.running_jobs.remove(job)

    #For test only
    def add_run_jobs(self, joblist):
        self.running_jobs = joblist
