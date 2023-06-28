from collections import OrderedDict
from .states import DefaultState
from lewis.devices import StateMachineDevice


class SimulatedPace5000(StateMachineDevice):

    def _initialize_data(self):
        self.reset()

    def _get_state_handlers(self):
        return { "default": DefaultState() }

    def _get_initial_state(self):
        return "default"

    def _get_transition_handlers(self):
        return OrderedDict([])

    def reset(self):
        self.connected = True

        self.pressure = 0.0
        self.pressure_sp = 0.0
        self.slew = 0.0
        self.slew_mode = "MAX"
        self.units = "BAR"
        self.state = 0
        self.effort = 0.0
        self.limit_upper = 0.0
        self.limit_lower = 0.0
        self.error = "0, \"No error\""
