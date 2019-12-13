from control.control import *
from world.world import *
from collections import deque
from threading import Timer
import logging
import sys

logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s:%(message)s', filename='debug.log', filemode="w", level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
''' TASK TYPES '''


class RobotTask(BaseTask):

    def __init__(self,name, res_handler: ResourceHandler,prio=2):
        super().__init__(name,prio)
        self.res_handler = res_handler
        self.robot = self.res_handler.get_free_equipment_by_string("robot")
        self.tool_stand = self.res_handler.get_free_equipment_by_string("tool")
        self.tool_req = Tool.GRIPPER #the "base" tool when nothing else is equipped

    def need_toolchange(self):
        tool_ok = self.tool_stand.get_equipped_tool() != self.tool_req
        return tool_ok


class PourBatter(RobotTask):

    def __init__(self, name, iron, res_handler: ResourceHandler,slot=1):
        super().__init__(name, res_handler)
        self.iron = iron
        self.res_handler = res_handler
        self.bowl = self.res_handler.get_free_equipment_by_string("bowl")
        self.tool_req = Tool.SCOOP

    def run(self):
        self.tool_stand.get_tool(self.tool_req)
        self.bowl.retrieve()
        self.iron.pour()

    def __str__(self):
        return super().__str__()+" : "+self.bowl.get_name()


class ServeWaffle(RobotTask):

    def __init__(self, name, iron, res_handler: ResourceHandler,slot=1):
        super().__init__(name,res_handler,3) #High priority to serve the waffle
        self.iron = iron
        self.res_handler = res_handler
        self.tray = self.res_handler.get_free_equipment_by_string("tray")

    def run(self):
        self.tool_stand.get_tool(Tool.FORK)
        self.iron.grab_waffle()

    def __str__(self):
        return super().__str__()+" : "+self.tray.get_name()


class OperateIron(RobotTask):

    def __init__(self, name, iron, res_handler: ResourceHandler, command, prio=2):
        super().__init__(name,res_handler,prio)
        self.command = command
        self.res_handler = res_handler
        self.iron = iron

    def run(self):
        self.tool_stand.get_tool(Tool.GRIPPER)
        if self.command == "open":
            self.iron.open_lid()
        elif self.command == "close":
            self.iron.close_lid()
        elif self.command == "turn on":
            self.iron.start()

    def __str__(self):
        return super().__str__()+" : "+self.command


class WaitingTask(BaseTask):

    def __init__(self,name,time):
        super().__init__(name,4) # its very high priority to start waiting timer for time to be accurate
        self.finished = False
        self.time = time

    def run(self):
        t = Timer(self.time, self.set_finished)
        t.start()

    def set_finished(self):
        self.finished = True

    def is_finished(self):
        return self.finished



''' JOB TYPES '''


class SingleWaffleJob(BaseJob):

    def __init__(self, res_handler, iron):
        super().__init__(res_handler,iron)

        self.task_queue.appendleft(OperateIron("start iron", self.iron, self.res_handler, "turn on"))
        self.task_queue.appendleft(OperateIron("open for fill", self.iron, self.res_handler, "open"))
        self.task_queue.appendleft(PourBatter("pouring batter", self.iron, self.res_handler))
        self.task_queue.appendleft(OperateIron("close for frying", self.iron, self.res_handler, "close"))
        self.task_queue.appendleft(WaitingTask("waiting while frying", 5)) # Cook for 5 sek
        self.task_queue.appendleft(OperateIron("open for retrieving", self.iron, self.res_handler, "open", 3))
        self.task_queue.appendleft(ServeWaffle("serving waffle", self.iron, self.res_handler))
        self.task_queue.appendleft(OperateIron("turn off iron", self.iron, self.res_handler, "turn off"))
        self.task_queue.appendleft(OperateIron("close finish", self.iron, self.res_handler, "close"))


class DualWaffleJob(BaseJob):

    def __init__(self, res_handler, iron):
        super().__init__(res_handler, iron)
        self.task_queue.appendleft(OperateIron("start iron", self.iron, self.res_handler, "turn on"))
        self.task_queue.appendleft(OperateIron("open for fill", self.iron, self.res_handler, "open"))
        self.task_queue.appendleft(PourBatter("pouring batter slot1", self.iron, self.res_handler,1))
        self.task_queue.appendleft(PourBatter("pouring batter slot2", self.iron, self.res_handler,2))
        self.task_queue.appendleft(OperateIron("close for frying", self.iron, self.res_handler, "close"))
        self.task_queue.appendleft(WaitingTask("waiting while frying", 5)) # Cook for 5 sek
        self.task_queue.appendleft(OperateIron("open for retrieving", self.iron, self.res_handler, "open", 3))
        self.task_queue.appendleft(ServeWaffle("serving waffle slot 1", self.iron, self.res_handler, 1))
        self.task_queue.appendleft(ServeWaffle("serving waffle slot 2", self.iron, self.res_handler, 2))
        self.task_queue.appendleft(OperateIron("turn off iron", self.iron, self.res_handler, "turn off"))
        self.task_queue.appendleft(OperateIron("close finish", self.iron, self.res_handler, "close"))



'''   - - - - - - - - - - -  '''


class WaffleResourceHandler(ResourceHandler):

    def __init__(self):
        super().__init__()
        pass


class WaffleCoordinator(JobCoordinator):

    def __init__(self, job_factory, res_handler):
        super().__init__(job_factory, res_handler)


class WaffleJobFactory(JobFactory):

    def __init__(self):
        super().__init__()
        pass

    def create_job(self, jobtype:str, iron:Equipment, res_handler):
        if jobtype == "base":
            job = SingleWaffleJob(res_handler, iron)
        elif jobtype == "big":
            job = DualWaffleJob(res_handler, iron)
        else:
            job = None

        if job is not None:
            logging.info("Created job "+str(job))
        else:
            logging.error("Invalid jobtype")
        return job


class RoboticWaffles:

    def __init__(self):
        self.job_factory = WaffleJobFactory()
        self.res_handler = WaffleResourceHandler()
        self.res_handler.add_item("iron", WaffleIron(None, "Small cute iron", 1))
        self.res_handler.add_item("iron", WaffleIron(None, "Big nasty iron", 2))
        self.res_handler.add_item("bowl", Bowl(None, "red bowling bowl"))
        self.res_handler.add_item("tray", Tray(None, "plastic tray"))
        self.res_handler.add_item("tool", ToolStand(None, "tool stand"))

        self.coordinator = WaffleCoordinator(self.job_factory, self.res_handler)
        print("init program")

    def main(self):
        self.run()

    def run(self):
        print("o: order a waffle")
        print("p: process orders")
        print("e: execute orders")

        cmd = "o"
        while cmd != "":
            cmd = input("Select cmd:")
            if cmd == "o":
                logging.info("Add order selected")
                self.coordinator.add_order()
            elif cmd == "p":
                logging.info("Process orders selected")
                self.coordinator.process_orders()
            elif cmd == "e":
                logging.info("Executing next job task")
                self.coordinator.execute_next_job_task()

        self.close()

    def close(self):
        print("closing down waffle software")


if __name__== "__main__":
    r=RoboticWaffles()
    r.main()
