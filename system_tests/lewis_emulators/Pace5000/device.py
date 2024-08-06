from collections import OrderedDict

from lewis.devices import StateMachineDevice

from .states import DefaultState


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

        # Set slew mode and psi to non-ideal values as we need to test that we set them correctly 
        # on startup 
        self.slew_mode = "MAX"
        self.units = "PSI"
        self.state = 0
        self.effort = 0.0
        self.limit_upper = 0.0
        self.limit_lower = 0.0
        self.error = "0, No error"
        self.vent_status = 0
        self.source_pressure = 0

    def vent(self, start):
        if start == 1:
            self.vent_status = 1
            self.pressure = 0
            self.vent_status = 2
        else: 
            self.vent_status = 1
