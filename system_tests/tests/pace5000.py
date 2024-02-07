import unittest
from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister, ProcServLauncher
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim


DEVICE_PREFIX = "PACE5000_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("PACE5000"),
        "macros": {},
        "emulator": "Pace5000",
        "ioc_launcher_class": ProcServLauncher,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


DEVICE_VARIABLES = {
    "PRESSURE":    "pressure",
    "EFFORT":      "effort",
    "LIMIT:UPPER": "limit_upper",
    "LIMIT:LOWER": "limit_lower",
    "ERROR":       "error",
    "UNITS":       "units",
    "SLEW:MODE:SP": "slew_mode",
    "SOURCE_PRESSURE": "source_pressure"
}


class Pace5000Tests(unittest.TestCase):
    """
    Tests for the Pace5000 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Pace5000", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0)
        self._reset_device()

    def _reset_device(self):
        if IOCRegister.uses_rec_sim:
            self.ca.set_pv_value(f"SIM:PRESSURE", 0.0)
            self.ca.set_pv_value(f"SIM:PRESSURE:SP", 0.0)
            self.ca.set_pv_value(f"SIM:SLEW", 0.0)
            self.ca.set_pv_value(f"SIM:SLEW:MODE", 0)
            self.ca.set_pv_value(f"SIM:UNITS", "BAR")
            self.ca.set_pv_value(f"SIM:STATE", 0)
            self.ca.set_pv_value(f"SIM:EFFORT", 0.0)
            self.ca.set_pv_value(f"SIM:LIMIT:UPPER", 0.0)
            self.ca.set_pv_value(f"SIM:LIMIT:LOWER", 0.0)
            self.ca.set_pv_value(f"SIM:ERROR", "0, No error")
        else:
            self._lewis.backdoor_run_function_on_device("reset")

    def _set(self, pv, value):
        if IOCRegister.uses_rec_sim:
            self.ca.set_pv_value(f"SIM:{pv}", value)
        else:
            self._lewis.backdoor_set_on_device(DEVICE_VARIABLES[pv], value)

    @parameterized.expand(parameterized_list([
        ("PRESSURE",    0.5),
        ("EFFORT",      12.5),
        ("LIMIT:UPPER", 0.7),
        ("LIMIT:LOWER", 0.3),
        ("ERROR",       "202, \"No query allowed\""),
        ("SOURCE_PRESSURE", 1.233)
    ]))
    def test_WHEN_read_only_pv_set_THEN_pv_read_correctly(self, _, pv, value):
        self._set(pv, value)
        self.ca.assert_that_pv_is(pv, value)


    @skip_if_recsim("requires emulator logic")
    def test_WHEN_pressure_above_vent_threshold_THEN_cannot_vent(self):
        threshold = 5
        pressure = 12.0
        self._set("PRESSURE", pressure)
        self.ca.assert_that_pv_is("PRESSURE", pressure)
        self.ca.set_pv_value("VENT_THRESHOLD", threshold)
        self.ca.set_pv_value("VENT:SP", 1)
        self.ca.assert_that_pv_is_not("VENT:SP:OUT", 1)
        self.ca.assert_that_pv_is("VENT_STATUS.RVAL", 0)
        self.ca.assert_that_pv_is("PRESSURE", pressure)

    @skip_if_recsim("requires emulator logic")
    def test_WHEN_pressure_below_vent_threshold_THEN_can_vent(self):
        threshold = 5
        pressure = 3.0
        self._set("PRESSURE", pressure)
        self.ca.assert_that_pv_is("PRESSURE", pressure)
        self.ca.set_pv_value("VENT_THRESHOLD", threshold)
        self.ca.set_pv_value("VENT:SP", 1)
        self.ca.assert_that_pv_is("VENT_STATUS.RVAL", 2)
        self.ca.assert_that_pv_is("PRESSURE", 0)
    
    @parameterized.expand(parameterized_list([
        ("PRESSURE:SP:RBV", "PRESSURE:SP",  0.5),
        ("SLEW",            "SLEW:SP",      0.3),
        ("SLEW:MODE",       "SLEW:MODE:SP", "LIN"),
        ("STATE",           "STATE:SP",     "Control")
    ]))
    def test_WHEN_pv_set_THEN_pv_read_correctly(self, _, pv, sp, value):
        self.ca.set_pv_value(sp, value)
        self.ca.assert_that_pv_is(pv, value)

    @parameterized.expand(parameterized_list([
        ("PRESSURE:SP:RBV", "PRESSURE:SP_NO_ACTION",  0.5),
        ("SLEW",            "SLEW:SP_NO_ACTION",      0.3),
        ("SLEW:MODE",       "SLEW:MODE:SP_NO_ACTION", "LIN"),
        ("STATE",           "STATE:SP_NO_ACTION",     "Control")
    ]))
    def test_GIVEN_no_action_setpoint_set_WHEN_action_triggered_THEN_pv_set_correctly(self, _, pv, sp_no_action, value):
        self.ca.set_pv_value(sp_no_action, value)
        self.ca.set_pv_value("SET", 1)
        self.ca.assert_that_pv_is(pv, value)

    def test_WHEN_stop_issued_THEN_pressure_setpoint_set_correctly(self):
        pressure = 12.0
        self._set("PRESSURE", pressure)

        self.ca.assert_that_pv_is("PRESSURE", pressure)
        self.ca.assert_that_pv_is_not("PRESSURE:SP", pressure)
        self.ca.assert_that_pv_is_not("PRESSURE:SP:RBV", pressure)

        self.ca.set_pv_value("STOP", 1)
        self.ca.assert_that_pv_is("PRESSURE:SP", pressure)
        self.ca.assert_that_pv_is("PRESSURE:SP:RBV", pressure)

    @skip_if_recsim("Requires emulator for disconnect logic.")
    def test_WHEN_device_disconnects_THEN_pvs_go_into_alarm(self):
        self.ca.assert_that_pv_alarm_is("PRESSURE", self.ca.Alarms.NONE)

        with self._lewis.backdoor_simulate_disconnected_device():
            self.ca.assert_that_pv_alarm_is("PRESSURE", self.ca.Alarms.INVALID, timeout=30)

        self.ca.assert_that_pv_alarm_is("PRESSURE", self.ca.Alarms.NONE, timeout=30)

    @skip_if_recsim("Requires emulator for disconnect logic.")
    def test_WHEN_device_disconnects_and_units_changed_THEN_previous_units_reinforced(self):
        self.ca.assert_that_pv_is("UNITS", "Bar")
        with self._lewis.backdoor_simulate_disconnected_device():
            self._set("UNITS", "PSI")
        self.ca.set_pv_value("DEFAULTS_SETTER.PROC", 1)
        self.ca.assert_that_pv_is("UNITS", "Bar", timeout=30)

    @skip_if_recsim("Requires emulator.")
    def test_WHEN_ioc_started_THEN_slew_mode_set_to_linear(self):
        # Restart the IOC
        with self._ioc.start_with_macros({}, pv_to_wait_for="UNITS"):
            expected = "LIN"
            self.ca.assert_that_pv_is("SLEW:MODE", expected)

