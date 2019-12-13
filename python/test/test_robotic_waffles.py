import unittest
from unittest.mock import Mock
import time
from robotic_waffles import *


class WaitingTaskTest(unittest.TestCase):

    def test_run(self):
        t = WaitingTask("testwait", 2)
        t.run()
        self.assertFalse(t.is_finished())
        time.sleep(3) # wait for the timer to send de_activation_msgs
        self.assertTrue(t.is_finished())


class SingleWaffleJobTest(unittest.TestCase):

    def test_full(self):
        res_handler = Mock()
        res_handler.get_free_equipment_by_string.return_value = "mock_item"

        swj = SingleWaffleJob(res_handler, None)
        first_task = swj.task_queue.pop()
        last_task = swj.task_queue.popleft()
        self.assertEqual(first_task.get_name(), "start iron")
        self.assertEqual(last_task.get_name(), "close finish")
        self.assertTrue(swj.is_ready())

    def test_first_task(self):
        res_handler = Mock()
        res_handler.get_free_equipment_by_string.return_value = "mock_item"

        mock_iron = Mock()

        swj = SingleWaffleJob(res_handler, mock_iron)
        swj.run_next_task()
        mock_iron.start.assert_called()



