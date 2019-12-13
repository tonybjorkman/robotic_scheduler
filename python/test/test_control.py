import unittest
from unittest.mock import Mock
import random
from control.control import *
from world.world import Equipment, WaffleIron

#       python -m unittest test.test_control

# Shared methods


class BaseTaskTest(unittest.TestCase):

    def test_test1(self):
        self.assertTrue(True)


class MockBaseJob(BaseJob):

    def __init__(self, ready, req_tool_change, prio):
        super().__init__(None, None)
        self.ready = ready
        self.req_tool_change = req_tool_change
        self.prio = prio

    def is_ready(self):
        return self.ready

    def need_toolchange(self):
        return self.req_tool_change

    def get_current_priority(self):
        return self.prio


class LoadedResourceHandler(ResourceHandler):

    def __init__(self):
        super().__init__()
        self.populate()

    def get_bowl(self,free,res,name):
        bowl = Equipment(None)
        bowl.free = free
        bowl.has_reservation = res
        bowl.name = name
        return bowl

    def get_iron(self,free,res,name,slots):
        iron = WaffleIron(None,slots)
        iron.free = free
        iron.has_reservation = res
        iron.name = name
        return iron

    def populate(self):
        bowl1 = self.get_bowl(False, False, "2.Not free, unreserved")
        bowl2 = self.get_bowl(True, False, "1.free, unreserved")
        bowl3 = self.get_bowl(False, True, "Not free, reserved")
        bowl4 = self.get_bowl(False, True, "Not free, reserved")

        self.add_item("bowl", bowl1)
        self.add_item("bowl", bowl2)
        self.add_item("bowl", bowl3)
        self.add_item("bowl", bowl4)

        iron1 = self.get_iron(False, False, "big Not free, unreserved",2)
        iron2 = self.get_iron(True, False, "big free, unreserved",2)
        iron3 = self.get_iron(True, False, "small free, unreserved",1)
        iron4 = self.get_iron(False, True, "Not free, reserved",2)

        self.add_item("iron", iron1)
        self.add_item("iron", iron2)
        self.add_item("iron", iron3)
        self.add_item("iron", iron4)


class ResourceHandlerTest(unittest.TestCase):

    def test_capacity_availability(self):
        rh = LoadedResourceHandler()
        i1 = rh.checkout_prechecked_item("iron", 2)
        i2 = rh.checkout_prechecked_item("iron", 2)

        self.assertEqual(i1.name,"big free, unreserved")
        self.assertEqual(i2.name, "small free, unreserved")

    def test_add_get(self):
        rh = LoadedResourceHandler()
        freebowl = rh.get_free_equipment_by_string("bowl")
        freebowl.free = False
        nobowl = rh.get_free_equipment_by_string("bowl")

        self.assertEqual(freebowl.name, "1.free, unreserved")
        self.assertEqual(nobowl, None)

    def test_checkout(self):
        rh = LoadedResourceHandler()

        b1 = rh.checkout_prechecked_item("bowl")
        b2 = rh.checkout_prechecked_item("bowl")
        b3 = rh.checkout_prechecked_item("bowl")
        b4 = rh.checkout_prechecked_item("bowl")

        self.assertEqual(b1.name, "1.free, unreserved")
        self.assertEqual(b2, None)
        self.assertEqual(b3, None)
        self.assertEqual(b4, None)


class JobCoordinatorTest(unittest.TestCase):

    def test_order_to_jobs(self):
        res_mock = Mock()
        iron_mock = Mock()
        iron_mock.get_capacity.return_value = 2
        iron_mock_small = Mock()
        iron_mock_small.get_capacity.return_value = 1

        res_mock.checkout_prechecked_item.return_value = iron_mock

        jc = JobCoordinator(JobFactory(), res_mock)
        jc.add_order()
        jc.add_order()
        jc.add_order()
        jc.add_order()

        job1 = jc._create_job_from_orders()
        res_mock.checkout_prechecked_item.return_value = iron_mock_small
        job2 = jc._create_job_from_orders()
        self.assertEqual(jc.orders, 1)
        jc.remove_orders(1)
        job3 = jc._create_job_from_orders()

        self.assertEqual(job1.name, "big")
        self.assertEqual(job2.name, "base")
        self.assertEqual(job3, None)
        # here there is no order left to remove!
        self.assertFalse(jc.remove_orders())

    def test_job_prioritization(self):
        ''' Tests priority between jobs in terms of prio-value, if ready, if need to change tool '''
        #also tests job removal
        jc = JobCoordinator(JobFactory(), ResourceHandler())
        #mock jobs with diff prio
        # if not is_ready, skip
        #same tool + is_ready
        joblist=list()
        rdy_hi_priojob = MockBaseJob(True, False, 8)
        joblist.append(rdy_hi_priojob)
        rdy_lo_priojob = MockBaseJob(True, False, 1)
        joblist.append(rdy_lo_priojob)
        rdy_hi_prio_tool2_job1 = MockBaseJob(True, True, 3)
        joblist.append(rdy_hi_prio_tool2_job1)
        rdy_hi_prio_tool2_job2 = MockBaseJob(True, True, 2)
        joblist.append(rdy_hi_prio_tool2_job2)
        rdy_med_prio_tool3_job = MockBaseJob(True, True, 1.5)
        joblist.append(rdy_med_prio_tool3_job)
        not_ready_hi_priojob = MockBaseJob(False, False, 1)
        joblist.append(not_ready_hi_priojob)
        jbl_cpy = joblist.copy()
        random.shuffle(jbl_cpy) # shuffles in place
        jc.add_run_jobs(jbl_cpy)

        for num, job in enumerate(joblist):
            prioJob = jc.get_highest_priority_job(4)
            print("check job nr"+str(num))
            #last job, nr5, will never be returned since it is not
            #allowed to run (since its not ready!).
            if num < 5:
                self.assertEqual(prioJob, job)
                jc.cancel_job(prioJob)
            else:
                self.assertEqual(prioJob, None)

