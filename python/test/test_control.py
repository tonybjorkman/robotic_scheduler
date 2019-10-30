import unittest
import random
from control.control import *
from world.world import Equipment, WaffleIron


class BaseTaskTest(unittest.TestCase):

    def test_test1(self):
        self.assertTrue(True)


class MockBaseJob(BaseJob):

    def __init__(self, ready, req_tool_change, prio):
        super().__init__()
        self.ready = ready
        self.req_tool_change=req_tool_change
        self.prio=prio

    def is_ready(self):
        return self.ready

    def need_tool_change(self):
        return self.req_tool_change

    def get_current_priority(self):
        return self.prio


class MockJobFactory(JobFactory):

    def __init__(self):
        super().__init__()
        pass

    def create_job(self, quantity):
        if quantity > 1:
            return 2, BaseJob()
        elif quantity == 1:
            return 1, MockBaseJob(True,True,666)
        else:
            return None


class ResourceHandlerTest(unittest.TestCase):

    def get_bowl(self,free,res,name):
        bowl = Equipment(None)
        bowl.free=free
        bowl.has_reservation=res
        bowl.name=name
        return bowl

    def get_iron(self,free,res,name,slots):
        iron = WaffleIron(None)
        iron.free=free
        iron.has_reservation=res
        iron.name=name
        iron.slots = slots
        return iron

    def get_populated_rh(self):
        rh = ResourceHandler()
        bowl1 = self.get_bowl(False, False, "2.Not free, unreserved")
        bowl2 = self.get_bowl(True, False, "1.free, unreserved")
        bowl3 = self.get_bowl(False, True, "Not free, reserved")
        bowl4 = self.get_bowl(False, True, "Not free, reserved")

        rh.add_item("bowl", bowl1)
        rh.add_item("bowl", bowl2)
        rh.add_item("bowl", bowl3)
        rh.add_item("bowl", bowl4)

        iron1 = self.get_iron(False, False, "big Not free, unreserved",2)
        iron2 = self.get_iron(True, False, "big free, unreserved",2)
        iron3 = self.get_iron(True, False, "small free, unreserved",1)
        iron4 = self.get_iron(False, True, "Not free, reserved",2)

        rh.add_item("iron", iron1)
        rh.add_item("iron", iron2)
        rh.add_item("iron", iron3)
        rh.add_item("iron", iron4)

        return rh

    def test_capacity_availability(self):
        rh = self.get_populated_rh()
        i1 = rh.checkout_prechecked_item("iron", True, 2)
        i2 = rh.checkout_prechecked_item("iron", True, 2)
        i3 = rh.checkout_prechecked_item("iron", True, 2)

        self.assertEqual(i1.name,"big free, unreserved")
        self.assertEqual(i2.name, "small free, unreserved")

    def test_add_get(self):
        rh = self.get_populated_rh()
        freebowl = rh.get_prechecked_item("bowl")
        freebowl.free = False
        nobowl = rh.get_prechecked_item("bowl")

        self.assertEqual(freebowl.name, "1.free, unreserved")
        self.assertEqual(nobowl, None)

    def test_checkout_reserve(self):
        rh = self.get_populated_rh()

        b1 = rh.checkout_prechecked_item("bowl", True)
        b2 = rh.checkout_prechecked_item("bowl", True)
        b3 = rh.checkout_prechecked_item("bowl", True)
        b4 = rh.checkout_prechecked_item("bowl", True)

        self.assertEqual(b1.name, "1.free, unreserved")
        self.assertEqual(b2.name, "2.Not free, unreserved")
        self.assertEqual(b3.name, "1.free, unreserved")
        self.assertEqual(b4, None)


class JobCoordinatorTest(unittest.TestCase):

    def test_order_to_jobs(self):
        jc = JobCoordinator(JobFactory(), ResourceHandler())
        jc.add_order()
        jc.add_order()
        jc.remove_order()
        job1 = jc._create_job_from_orders()
        job2 = jc._create_job_from_orders()
        self.assertTrue(isinstance(job1, BaseJob))
        self.assertEqual(job2, None)
        # here there is no order left to remove!
        self.assertRaises(jc.remove_order())

    def test_job_prioritization(self):
        #also tests job removal
        jc = JobCoordinator()
        #mock jobs with diff prio
        # if not is_ready, skip
        #same tool + is_ready
        joblist=list()
        rdy_hi_priojob = MockBaseJob(True, False, 1)
        joblist.append(rdy_hi_priojob)
        rdy_lo_priojob = MockBaseJob(True, False, 8)
        joblist.append(rdy_lo_priojob)
        rdy_hi_prio_tool2_job1 = MockBaseJob(True, True, 1)
        joblist.append(rdy_hi_prio_tool2_job1)
        rdy_hi_prio_tool2_job2 = MockBaseJob(True, True, 1)
        joblist.append(rdy_hi_prio_tool2_job2)
        rdy_med_prio_tool3_job = MockBaseJob(True, True, 4)
        joblist.append(rdy_med_prio_tool3_job)
        not_ready_hi_priojob = MockBaseJob(False, False, 1)
        joblist.append(not_ready_hi_priojob)
        jc.add_run_jobs(random.shuffle(joblist.copy()))

        for num, job in enumerate(joblist):
            prioJob = jc._get_highest_priority_job()
            print("check job nr"+str(num))
            #last job, nr5, will never be returned since it is not
            #allowed to run (since its not ready!).
            if num < 5:
                self.assertEqual(prioJob, job)
            else:
                self.assertEqual(prioJob, None)
            jc.cancel_job(prioJob)
