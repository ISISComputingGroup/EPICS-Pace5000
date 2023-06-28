import unittest
from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim


DEVICE_PREFIX = "PACE5000_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("PACE5000"),
        "macros": {},
        "emulator": "Pace5000",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


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
            self.ca.set_pv_value(f"SIM:SLEW", 0.0)
            self.ca.set_pv_value(f"SIM:SLEW:MODE", 0)
            self.ca.set_pv_value(f"SIM:UNITS", "BAR")
            self.ca.set_pv_value(f"SIM:STATE", 0)
            self.ca.set_pv_value(f"SIM:EFFORT", 0)
            self.ca.set_pv_value(f"SIM:LIMIT:UPPER", 0.0)
            self.ca.set_pv_value(f"SIM:LIMIT:LOWER", 0.0)
            self.ca.set_pv_value(f"SIM:ERROR", "0, \"No error\"")
        else:
            self._lewis.backdoor_run_function_on_device("reset")

    def _set(self, pv, device_variable, value):
        if IOCRegister.uses_rec_sim:
            self.ca.set_pv_value(f"SIM:{pv}", value)
        else:
            self._lewis.backdoor_set_on_device(device_variable, value)

    @parameterized.expand(parameterized_list([
        ("PRESSURE",    "pressure",     0.5),
        ("EFFORT",      "effort",       12.5),
        ("LIMIT:UPPER", "limit_upper",  0.7),
        ("LIMIT:LOWER", "limit_lower",  0.3),
        ("ERROR",       "error",        "202, \"No query allowed\"")
    ]))
    def test_WHEN_read_only_pv_set_THEN_pv_read_correctly(self, _, pv, device_variable, value):
        self._set(pv, device_variable, value)
        self.ca.assert_that_pv_is(pv, value)
    
    @parameterized.expand(parameterized_list([
        ("PRESSURE:SP:RBV", "PRESSURE:SP",  0.5),
        ("SLEW",            "SLEW:SP",      0.3),
        ("SLEW:MODE",       "SLEW:MODE:SP", "LIN"),
        ("UNITS",           "UNITS:SP",     "ATM"),
        ("STATE",           "STATE:SP",     "Control")
    ]))
    def test_WHEN_pv_set_THEN_pv_read_correctly(self, _, pv, sp, value):
        self.ca.set_pv_value(sp, value)
        self.ca.assert_that_pv_is(pv, value)

    def test_WHEN_stop_issued_THEN_pressure_setpoint_set_correctly(self):
        pressure = 12.0
        self._set("PRESSURE", "pressure", pressure)

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
