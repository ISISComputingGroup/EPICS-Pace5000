from lewis.adapters.stream import StreamInterface
from lewis.core.logging import has_log
from lewis.utils.command_builder import CmdBuilder
from lewis.utils.replies import conditional_reply


@has_log
class Pace5000StreamInterface(StreamInterface):
    in_terminator = "\r"
    out_terminator = "\r"

    def __init__(self):
        super(Pace5000StreamInterface, self).__init__()
        # Commands that we expect via serial during normal operation
        self.commands = {
            CmdBuilder(self.get_pressure).escape(":SENS:PRES?").eos().build(),
            CmdBuilder(self.get_source_pressure).escape(":SOUR:PRES:COMP?").eos().build(),
            CmdBuilder(self.get_pressure_sp).escape(":SOUR:PRES:LEV:IMM:AMPL?").eos().build(),
            CmdBuilder(self.set_pressure_sp)
            .escape(":SOUR:PRES:LEV:IMM:AMPL")
            .spaces(at_least_one=True)
            .float()
            .eos()
            .build(),
            CmdBuilder(self.get_slew).escape(":SOUR:PRES:SLEW?").eos().build(),
            CmdBuilder(self.set_slew)
            .escape(":SOUR:PRES:SLEW")
            .spaces(at_least_one=True)
            .float()
            .eos()
            .build(),
            CmdBuilder(self.get_vent).escape(":SOUR:PRES:LEV:IMM:AMPL:VENT?").eos().build(),
            CmdBuilder(self.set_vent)
            .escape(":SOUR:PRES:LEV:IMM:AMPL:VENT")
            .spaces(at_least_one=True)
            .int()
            .eos()
            .build(),
            CmdBuilder(self.get_slew_mode).escape(":SOUR:PRES:SLEW:MODE?").eos().build(),
            CmdBuilder(self.set_slew_mode)
            .escape(":SOUR:PRES:SLEW:MODE")
            .spaces(at_least_one=True)
            .string()
            .eos()
            .build(),
            CmdBuilder(self.get_units).escape(":UNIT:PRES?").eos().build(),
            CmdBuilder(self.set_units)
            .escape(":UNIT:PRES")
            .spaces(at_least_one=True)
            .string()
            .eos()
            .build(),
            CmdBuilder(self.get_state).escape(":OUTP:STAT?").eos().build(),
            CmdBuilder(self.set_state)
            .escape(":OUTP:STAT")
            .spaces(at_least_one=True)
            .int()
            .eos()
            .build(),
            CmdBuilder(self.get_effort).escape(":SOUR:PRES:EFF?").eos().build(),
            CmdBuilder(self.get_limits).escape(":INST:SENS:FULL?").eos().build(),
            CmdBuilder(self.get_error).escape(":SYST:ERR?").eos().build(),
        }

    def handle_error(self, request, error):
        """
        If command is not recognised print and error

        Args:
            request: requested string
            error: problem

        """
        self.log.error("An error occurred at request " + repr(request) + ": " + repr(error))

    @conditional_reply("connected")
    def get_pressure(self):
        return f":SENS:PRES {self.device.pressure}"

    @conditional_reply("connected")
    def get_source_pressure(self):
        return f":SOUR:PRES:COMP {self.device.source_pressure}"

    @conditional_reply("connected")
    def get_pressure_sp(self):
        return f":SOUR:PRES:LEV:IMM:AMPL {self.device.pressure_sp}"

    @conditional_reply("connected")
    def set_pressure_sp(self, value):
        self.device.pressure_sp = value

    @conditional_reply("connected")
    def get_slew(self):
        return f":SOUR:PRES:SLEW {self.device.slew}"

    @conditional_reply("connected")
    def set_slew(self, value):
        self.device.slew = value

    @conditional_reply("connected")
    def get_vent(self):
        return f":SOUR:PRES:LEV:IMM:AMPL:VENT {self.device.vent_status}"

    @conditional_reply("connected")
    def set_vent(self, value):
        self.device.vent(value)

    @conditional_reply("connected")
    def get_slew_mode(self):
        return f":SOUR:PRES:SLEW:MODE {self.device.slew_mode}"

    @conditional_reply("connected")
    def set_slew_mode(self, value):
        self.device.slew_mode = value

    @conditional_reply("connected")
    def get_units(self):
        return f":UNIT:PRES {self.device.units}"

    @conditional_reply("connected")
    def set_units(self, value):
        self.device.units = value

    @conditional_reply("connected")
    def get_state(self):
        return f":OUTP:STAT {self.device.state}"

    @conditional_reply("connected")
    def set_state(self, value):
        self.device.state = value

    @conditional_reply("connected")
    def get_effort(self):
        return f":SOUR:PRES:EFF {self.device.effort}"

    @conditional_reply("connected")
    def get_limits(self):
        return f":INST:SENS:FULL {self.device.limit_upper}, {self.device.limit_lower}"

    @conditional_reply("connected")
    def get_error(self):
        return f":SYST:ERR {self.device.error}"
