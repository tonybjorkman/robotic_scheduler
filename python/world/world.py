from enum import Enum


class Equipment:

    def __init__(self, origin):
        self.origin = origin
        self.name = "Unnamed Equipment"
        self.has_reservation = False
        self.free = True
        self.capacity = 1

    def is_free(self):
        return self.free

    def is_reserved(self):
        return self.has_reservation

    def capacity(self):
        return self.capacity


class Tray(Equipment):

    def __init__(self, origin):
        super().__init__(origin)
        pass

    def release_waffle(self):
        pass


Tool = Enum('Tool', 'GRIPPER SCOOP FORK')


class ToolStand(Equipment):

    def __init__(self, origin):
        super().__init__(origin)
        pass

    def get_tool(self, tool: Tool):
        pass


class WaffleIron(Equipment):

    def __init__(self, origin,slots):
        super().__init__(origin)
        self.slots=slots
        pass

    def open_lid(self):
        pass

    def close_lid(self):
        pass

    def grab_waffle(self):
        pass

    def pour(self):
        pass

    def read_indicator(self):
        pass


class Bowl(Equipment):

    def __init__(self, origin):
        super().__init__(origin)
        pass

    def retrieve(self):
        pass

    # just for fun!
    def stir(self):
        pass