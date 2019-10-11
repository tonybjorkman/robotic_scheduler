import serial
import re
from enum import Enum



'''I would never...

                                           $"   *.
               d$$$$$$$P"                  $    J
                   ^$.                     4r  "
                   d"b                    .db
                  P   $                  e" $
         ..ec.. ."     *.              zP   $.zec..
     .^        3*b.     *.           .P" .@"4F      "4
   ."         d"  ^b.    *c        .$"  d"   $         %
  /          P      $.    "c      d"   @     3r         3
 4        .eE........$r===e$$$$eeP    J       *..        b
 $       $$$$$       $   4$$$$$$$     F       d$$$.      4
 $       $$$$$       $   4$$$$$$$     L       *$$$"      4
 4         "      ""3P ===$$$$$$"     3                  P
  *                 $       """        b                J
   ".             .P                    %.             @
     %.         z*"                      ^%.        .r"
        "*==*""                             ^"*==*""  '''




'''+500.00,+0.00,+46.30,+0.00,+179.99,R,A,O'''

MelfaResponseType = Enum('MelfaResponseType', 'POSITION NONE')




class Position:
    def __init__(self, x: float, y: float, z: float, A: float, B: float, arg1="R", arg2="A", grip="O"):
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





class RobotMovement:
    """ Responsible for all movement changes and position of the robot"""
    def __init__(self,controller: 'MySerial'):
        self.controller = controller

    def validate_limits(self, lower_limit, upper_limit, *x):
        ok = True
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

    def move_straight(self, x=0, y=0, z=0):
        """ DRAW STRAIGHT - Move from current position with linear interpolation"""

        self.validate_limits(-1000, 1000, x, y, z)
        print("coordinates validated")
        mov_msg = MelfaMessage(f'DS {x},{y},{z}', MelfaResponseType.NONE)
        print("built Melfamessage")
        self.controller.send_melfa_msg(mov_msg)
        print("sent melfa message")


    def move_tool_straight(self,distance):
        try:
            self.validate_limits(-100, 100, distance)
            print("distance validated")
            mov_msg = MelfaMessage(f'DS {distance}', MelfaResponseType.NONE)
            print("built Melfamessage")
            self.controller.send_melfa_msg(mov_msg)
            print("sent melfa message")
        except Exception:
            print("Exception occurred at moveStraight")


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
