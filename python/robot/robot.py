import serial
import re
import threading
from enum import Enum


# Example position format
'''+500.00,+0.00,+46.30,+0.00,+179.99,R,A,O'''

MelfaResponseType = Enum('MelfaResponseType', 'POSITION NONE')


class Position:
    def __init__(self, x=0, y=0, z=0, A=0, B=0, arg1="R", arg2="A", grip="O"):
        self.x = x
        self.y = y
        self.z = z
        self.A = A
        self.B = B
        self.arg1 = arg1
        self.arg2 = arg2
        self.grip = grip

    @classmethod
    def from_string(cls, position_string):
        pos_dict = Position.pos_string_to_dict(position_string)
        return cls(**pos_dict)

    @staticmethod
    def pos_string_to_dict(string: str) -> dict:
        """ extract values in pos string like "+500.00,+0.00,+46.30,+0.00,+179.99,R,A,O" """
        RV_E3J_pos_pattern = "^([\+|-]\d+.\d+),([\+|-]\d+.\d+),([\+|-]\d+.\d+),([\+|-]\d+.\d+),([\+|-]\d+.\d+)," \
                            "([R|L]),([A|B]),([O|C])$"
        pattern = re.compile(RV_E3J_pos_pattern)
        groups = pattern.match(string)

        keys = ["x","y","z","A","B","arg1","arg2","grip"]
        if groups.lastindex==len(keys):
            pos_values = list(groups.groups())
            pos_values[:5] = [float(x) for x in pos_values[:5]]
            print("successfully parsed position string")
            pos_dict = dict(zip(keys,pos_values))
            print("dict:"+str(pos_dict))
            return pos_dict
        else:
            raise SyntaxError("Illegal position format:"+str(string))

    def is_empty(self):
        keys = ["x", "y", "z", "A", "B"]
        positions=[self.__dict__.get(x) for x in keys]
        all_zero = all(x==0 for x in positions)
        return all_zero

    def __str__(self):
        posString = f'{self.x},{self.y},{self.z},{self.A},{self.B},{self.arg1},{self.arg2},{self.grip}'
        return posString


class RobotMovement:
    """ Responsible for all movement changes and position of the robot"""
    def __init__(self,controller: 'MySerial'):
        self.controller = controller
        self.gripper_open_port = 1
        self.gripper_close_port = 0

    def validate_limits(self, lower_limit, upper_limit, *x):

        for c in x:
            if c > upper_limit or c < lower_limit:
                raise ValueError("requested coordinate out of bounds:"+str(c))

    def validate_joint(self,*x):
        self.validate_limits(-180,180,*x)

    def get_position(self) -> Position:
        """ WHERE - Get current position """

        wh_msg = MelfaMessage("WH", MelfaResponseType.POSITION)
        print("built Melfamessage")
        curr_pos_str = self.controller.send_melfa_msg(wh_msg)
        pos_obj = Position.from_string(curr_pos_str)
        return pos_obj

    def read_position_inx(self, pos_inx) -> Position:
        wh_msg = MelfaMessage(f'PR {pos_inx}', MelfaResponseType.POSITION)
        curr_pos_str = self.controller.send_melfa_msg(wh_msg)
        print(f'read position inx{pos_inx}={curr_pos_str}')
        return Position.from_string(curr_pos_str)

    def write_pos_to_controller(self,position,pos_inx):
        wh_msg = MelfaMessage(f'PD {pos_inx},{str(position)}', MelfaResponseType.NONE)
        self.controller.send_melfa_msg(wh_msg)

    def move_to_position_with_offset(self, base_pos_inx, offset_pos):
        """ MOVE APPROACH - the controller only accepts using presaved positions
            could also use """
        if self.read_position_inx(99).is_empty():
            self.write_pos_to_controller(offset_pos)
            ma_msg = MelfaMessage(f'MA {base_pos_inx},{str(offset_pos)}', MelfaResponseType.NONE)
            self.controller.send_melfa_msg(ma_msg)




    def move_straight(self, x=0, y=0, z=0):
        """ DRAW STRAIGHT - Move from current position with linear interpolation"""

        self.validate_limits(-1000, 1000, x, y, z)
        print("coordinates validated")
        mov_msg = MelfaMessage(f'DS {x},{y},{z}', MelfaResponseType.NONE)
        print("built Melfamessage")
        self.controller.send_melfa_msg(mov_msg)
        print("sent melfa message")


    def move_tool_straight(self,distance):

        self.validate_limits(-100, 100, distance)
        print("distance validated")
        mov_msg = MelfaMessage(f'DS {distance}', MelfaResponseType.NONE)
        print("built Melfamessage")
        self.controller.send_melfa_msg(mov_msg)
        print("sent melfa message")


    def close_gripper(self):
        close_duration = 1
        self._gripper_call(self.gripper_close_port,close_duration)


    def open_gripper(self):
        open_duration = 1
        self._gripper_call(self.gripper_open_port,open_duration)

    def _gripper_call(self, bit_number, duration):
        grip_msg = MelfaMessage(f'OB +{bit_number}', MelfaResponseType.NONE)
        self.controller.send_melfa_msg(grip_msg)
        try:
            threading.Timer(duration,self.de_power_gripper).start()
        except Exception: #if anything goes wrong with turn off delay, turn off directly.
            self.de_power_gripper()

    def de_power_gripper(self):
        deactivate_close_msg = MelfaMessage(f'OB -{self.gripper_close_port}', MelfaResponseType.NONE)
        deactivate_open_msg = MelfaMessage(f'OB -{self.gripper_open_port}', MelfaResponseType.NONE)
        self.controller.send_melfa_msg(deactivate_close_msg)
        self.controller.send_melfa_msg(deactivate_open_msg)


class Robot:

    def __init__(self, robot_movement: RobotMovement):
        self.robot_movement = robot_movement



class MelfaMessage:

    def __init__(self, content: str, expected_response: MelfaResponseType):
        self.responseType = expected_response
        self.content = content

    def validate_response(self,response: str) -> None:
        """Throws a NameError exception if validation fails"""

        if self.responseType == MelfaResponseType.POSITION:
            args = str(response).split(",")
            print("after parse:"+str(args))
            if len(args)!=8:
                raise NameError("Validation error, Expected Position response")

    def expects_response(self) -> bool:
        return self.responseType != MelfaResponseType.NONE


class MySerial:
    def __init__(self, comport: str, w_timeout=None):
        self.ser=None
        self.open_serial(comport,w_timeout)
        self.last_msg = None

    def open_serial(self,comport, w_timeout):
        print("Serial opened")
        self.ser = serial.Serial(comport, baudrate=9600, timeout=2, stopbits=serial.STOPBITS_TWO,
                                 parity=serial.PARITY_EVEN, rtscts=True, write_timeout=w_timeout)

    def _set_last_msg(self,msg: MelfaMessage):
        self.last_msg = msg

    def send_melfa_msg(self, msg: MelfaMessage) -> str:
        serial_response = ""
        print(f'tries to send {msg.content}')
        self.ser.write(bytes((msg.content + '\r\n'), encoding="ascii"))
        print("sent serial text: "+msg.content)
        self.last_msg = msg
        if msg.expects_response():
            timeout, serial_response = self.get_response()
            if timeout:
                raise TimeoutError(f'cmd {msg.content} timed out')
            msg.validate_response(serial_response)

        return serial_response

    def get_last_msg_content(self):
        print("MySerial last_msg:"+self.last_msg.content)
        return self.last_msg.content

    def get_response(self) -> (bool,str):
        response = str(self.ser.readline(), "utf-8")
        print("received serial response: " + response)

        timeout = len(response) == 0
        response = response.rstrip()

        return timeout, response

    def close(self):
        self.ser.close()

if __name__== "__main__":
    rm = RobotMovement(MySerial('COM1'))
