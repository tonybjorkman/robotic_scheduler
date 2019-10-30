from control.control import *
from world.world import *

''' TASK TYPES '''


class PourBatter(BaseTask):

    def __init__(self, name, iron):
        super().__init__(name)
        self.iron = iron

    def run(self):
        pass


class ServeWaffle(BaseTask):

    def __init__(self, name, iron):
        super().__init__(name)
        self.iron = iron

    def run(self):
        pass


class OperateIron(BaseTask):

    def __init__(self, name):
        super().__init__(name)


''' JOB TYPES '''


class SingleWaffleJob(BaseJob):

    def __init__(self):
        super().__init__()
        pass

    def run_next_task(self):
        pass


class DualWaffleJob(BaseJob):

    def __init__(self):
        super().__init__()
        pass

    def run_next_task(self):
        pass


'''   - - - - - - - - - - -  '''


class WaffleResourceHandler(ResourceHandler):

    def __init__(self):
        super().__init__()
        pass

class WaffleCoordinator(JobCoordinator):

    def __init__(self,job_factory, res_handler):
        super().__init__(job_factory, res_handler)

    def _create_job_from_orders(self):
        if self.orders > 1:
            iron_for_job = self.res_handler.checkout_prechecked_item("iron",True,2)
        while iron_for_job is not None:
            if iron_for_job.is_free:
                self.running_jobs.append()

class RoboticWaffles:

    def __init__(self):
        pass