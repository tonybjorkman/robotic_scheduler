import unittest
from robot.robot import *
from queue import Queue
from threading import Thread
import time

""" python -m unittest test.test_robot """


# def serial_auto_responder_testing(auto_response):
#     """ This should run in its own thread to act as robotcontroller-responder for PC serial commands"""
#     controller_port = MySerial("COM7")
#     # Wait for first message, get_response is blocking so it will wait here
#     controller_port.get_response()
#     controller_port.send_melfa_msg(auto_response)
#     controller_port.close()



class MockMySerialUp(MySerial):
    """ Can be used for either giving the serial-response used by what you want to test
    or return the MelfaMessage's content-string for assertion"""
    def __init__(self, test_output: str):
        self.test_output=test_output
        self.sent_msgs = list()
        super().__init__("")

    def open_serial(self,comport, w_timeout):
        pass # This is a mock so skip

    def send_melfa_msg(self, msg: MelfaMessage):
        self._set_last_msg(msg)
        self.sent_msgs.append(msg)
        print("in mock, last msg content:"+self.get_last_msg_content())
        return self.test_output

    def get_sent_msgs(self):
        return self.sent_msgs

    def close(self):
        pass


standard_pos = "+500.00,+0.00,-46.30,+0.01,-179.99,R,A,C"
standard_pos_simple = "500.0,0.0,-46.3,0.01,-179.99,R,A,C"


def assert_standard_pos(test: unittest.TestCase, myPos: Position):
    test.assertEqual(myPos.x, 500)
    test.assertEqual(myPos.y, 0)
    test.assertEqual(myPos.z, -46.3)
    test.assertEqual(myPos.A, 0.01)
    test.assertEqual(myPos.B, -179.99)
    test.assertEqual(myPos.arg1, "R")
    test.assertEqual(myPos.arg2, "A")
    test.assertEqual(myPos.grip, "C")

class MelfaMessageTest(unittest.TestCase):

    def test_validation_noresponse1(self):
        msg = MelfaMessage("TEST", MelfaResponseType.NONE)
        msg.validate_response("N")

    def test_validation_response(self):
        msg = MelfaMessage("TEST", MelfaResponseType.POSITION)
        self.assertTrue(msg.expects_response())

    def test_validation_bad_position(self):
        """Missing a comma in the position"""
        msg = MelfaMessage("TEST", MelfaResponseType.POSITION)
        self.assertRaises(NameError, msg.validate_response, "+500.00,+0.00,+46.30,+0.00+179.99,R,A,O")

    def test_validation_ok_position(self):
        """position string complete"""
        msg = MelfaMessage("TEST", MelfaResponseType.POSITION)
        msg.validate_response("+500.00,+0.00,+46.30,+0.00,+179.99,R,A,O")

class MySerialTest(unittest.TestCase):
    """ COM6 and COM7 are virtual COM-ports which are connected to each other on the development-machine"""

    def test_open_close(self):
        ser = MySerial("COM6")
        ser.close()

    def send_receive_enqueue(self, port: MySerial, msg: MelfaMessage, queue: Queue):
        response = port.send_melfa_msg(msg)
        queue.put(response)

    def test_receive_melfa_msg(self):
        pos_str = "+500.00,+0.00,+46.30,+0.00,+179.99,R,A,O"
        pc_WH_Msg = MelfaMessage("WH", MelfaResponseType.POSITION)
        pos_response_msg = MelfaMessage(pos_str, MelfaResponseType.NONE)

        pc_port = MySerial("COM6")
        controller_port = MySerial("COM7")

        # The send cmd needs to be in another thread so we can send the response while its waiting
        q = Queue()
        pc_send_thread = Thread(target=self.send_receive_enqueue, args=(pc_port, pc_WH_Msg, q,))
        pc_send_thread.start()
        time.sleep(1)

        # Have the controller received the sent cmd from the PC?
        _, resp = controller_port.get_response()
        self.assertEqual(resp, "WH")
        controller_port.send_melfa_msg(pos_response_msg)

        response_to_sentcmd = q.get()

        # Check that the PC received the position from the simulated controller
        self.assertEqual(response_to_sentcmd, pos_str)

        pc_send_thread.join()
        pc_port.close()
        controller_port.close()

    def test_receive_melfa_msg_timeout(self):
        pc_WH_Msg = MelfaMessage("WH", MelfaResponseType.POSITION)

        pc_port = MySerial("COM6")
        controller_port = MySerial("COM7") # we need this so pc_port wont timeout


        # it will wait 2s for a Position response that will never arrive
        self.assertRaises(TimeoutError, pc_port.send_melfa_msg, pc_WH_Msg)

        pc_port.close()
        controller_port.close()

class RobotMovementTest(unittest.TestCase):

    def test_co_validation(self):
        rm = RobotMovement(None)
        rm.validate_limits(-1000, 1000, 999, -999, 0)
        self.assertRaises(ValueError, rm.validate_limits, -999, 999, 1001)
        self.assertRaises(TypeError, rm.validate_limits, -999, 999, "a")

    def test_move_straight(self):
        mys = MockMySerialUp("")
        rm = RobotMovement(mys)
        rm.move_straight(y=5,x=-10)
        movecmd_str = mys.get_last_msg_content()
        self.assertEqual(movecmd_str,"DS -10,5,0")


    def test_get_position(self):
        mys = MockMySerialUp(standard_pos)
        rm = RobotMovement(mys)
        pos_obj = rm.get_position()
        assert_standard_pos(self, pos_obj)

    def test_close_gripper(self):
        """ Make sure it first activates, and then after a while, sends deactivation of output """
        mys = MockMySerialUp(standard_pos)
        rm = RobotMovement(mys)
        rm.close_gripper()
        num_msgs_sent = len(mys.get_sent_msgs())
        self.assertEqual(num_msgs_sent, 1)
        time.sleep(4) # wait for the timer to send de_activation_msgs
        num_msgs_sent = len(mys.get_sent_msgs())
        self.assertEqual(num_msgs_sent, 3)
        self.assertEqual(mys.get_last_msg_content(), "OB -1")

    def test_read_position_inx(self):
        mys = MockMySerialUp(standard_pos)
        rm = RobotMovement(mys)
        std_pos_obj = rm.read_position_inx(99)
        self.assertEqual(str(std_pos_obj), standard_pos_simple)


class PositionTest(unittest.TestCase):

    def test_pos_string_to_dict(self):
        pos = "+500.00,+0.00,+46.30,+0.00,-179.99,R,A,O"
        dict = Position.pos_string_to_dict(pos)
        self.assertEqual(dict.__len__(), 8)
        self.assertEqual(dict.get("B"), -179.99)

    def test_constructor(self):
        myPos = Position(y=5)
        self.assertTrue(myPos.y,5)

    def test_classmethod(self):
        myPos = Position.from_string(standard_pos)
        assert_standard_pos(self, myPos)

    def test_is_empty(self):
        pos = "+500.00,+0.00,+46.30,+0.00,-179.99,R,A,O"
        pos_obj = Position.from_string(pos)
        self.assertFalse(pos_obj.is_empty())
        pos_obj = Position(z=0)
        self.assertTrue(pos_obj.is_empty())

    def test_to_string(self):
        pos = "+500.00,+0.00,+46.30,+0.00,-179.99,R,A,O"
        pos_obj = Position.from_string(pos)
        self.assertEqual(str(pos_obj),"500.0,0.0,46.3,0.0,-179.99,R,A,O")


if __name__ == '__main__':
    unittest.main()
