from enum import Enum
import logging

logger = logging.getLogger(__name__)

Tool = Enum('Tool', 'GRIPPER SCOOP FORK')


class Equipment:

    def __init__(self, origin, name="Unnamed Equipment", capacity=1):
        self.origin = origin
        self.name = name
        self.has_reservation = False
        self.free = True
        self.capacity = capacity
        self.reserve_capacity_used = 0 # Refactor. used to add more orders to reserved item

    def is_free(self):
        return self.free

    def is_reserved(self):
        return self.has_reservation

    def get_capacity(self):
        return self.capacity

    def get_capacity_used(self):
        return self.reserve_capacity_used

    def get_reserve_capacity_left(self):
        return self.capacity - self.reserve_capacity_used

    def get_name(self):
        return self.name

    def req_tool(self, operation):
        return None


class Tray(Equipment):

    def __init__(self, origin, name):
        super().__init__(origin, name)
        pass

    def release_waffle(self):
        pass

    def req_tool(self,op):
        if op == "serve":
            return Tool.FORK
        else:
            return None


class ToolStand(Equipment):

    def __init__(self, origin, name):
        super().__init__(origin, name)
        self.current_tool = Tool.GRIPPER

    def get_equipped_tool(self):
        return self.current_tool

    def get_tool(self, tool: Tool):
        if self.current_tool == tool:
            logger.info("Toolchange not required")
            return
        else:
            logger.info("Not implemented: Switching tools from "+str(self.current_tool)+" to "+ str(tool))
            self.current_tool = tool


class WaffleIron(Equipment):

    def __init__(self, origin,name, slots):
        super().__init__(origin,name,slots)
        pass

    def open_lid(self):
        logger.info("opening lid")

    def close_lid(self):
        logger.info("closing lid")

    def grab_waffle(self):
        logger.info("waffle grabbed")

    def pour(self):
        logger.info("pour")

    def read_indicator(self):
        pass

    def start(self):
        pass

    def req_tool(self, op):
        if op == "open" or "close":
            return Tool.GRIPPER
        elif op == "grab":
            return Tool.FORK
        elif op == "pour":
            return Tool.SCOOP
        else:
            return None


class Bowl(Equipment):

    def __init__(self, origin,name):
        super().__init__(origin,name)
        pass

    def retrieve(self):
        print("retrieve")

    def req_tool(self, op):
        if op == "retrieve":
            return Tool.SCOOP
        else:
            return None

    # just for fun!
    def stir(self):
        pass