import unittest
from time import sleep

from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import (
    get_running_lewis_and_ioc,
    skip_if_recsim,
)

# Device prefix
DEVICE_A_PREFIX = "CCD100_01"
DEVICE_E_PREFIX = "CCD100_02"

EMULATOR_DEVICE = "CCD100"

IOCS = [
    {
        "name": DEVICE_A_PREFIX,
        "directory": get_default_ioc_dir("CCD100"),
        "emulator": EMULATOR_DEVICE,
        "emulator_id": DEVICE_A_PREFIX,
    },
    {
        "name": DEVICE_E_PREFIX,
        "directory": get_default_ioc_dir("CCD100", iocnum=2),
        "emulator": EMULATOR_DEVICE,
        "emulator_id": DEVICE_E_PREFIX,
        "macros": {"ADDRESS": "e"},
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


def set_up_connections(device):
    _lewis, _ioc = get_running_lewis_and_ioc(device, device)

    _lewis.backdoor_set_on_device("connected", True)
    _lewis.backdoor_set_on_device("is_giving_errors", False)

    return _lewis, _ioc, ChannelAccess(device_prefix=device)


class CCD100Tests(unittest.TestCase):
    """
    General tests for the CCD100.
    """

    def setUp(self):
        self._lewis, self._ioc, self.ca = set_up_connections(DEVICE_A_PREFIX)

    @parameterized.expand([("0", 0), ("1.23", 1.23), ("10", 10)])
    def test_GIVEN_setpoint_set_WHEN_readback_THEN_readback_is_same_as_setpoint(self, _, point):
        self.ca.set_pv_value("READING:SP", point)
        self.ca.assert_that_pv_is("READING:SP:RBV", point)

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_device_not_connected_WHEN_get_status_THEN_alarm(self):
        self.ca.assert_that_pv_alarm_is("READING", ChannelAccess.Alarms.NONE)
        with self._lewis.backdoor_simulate_disconnected_device():
            # Read timeout is 5s
            sleep(6)
            self.ca.assert_that_pv_alarm_is("READING", ChannelAccess.Alarms.INVALID)
        # Assert alarms clear on reconnection
        self.ca.assert_that_pv_alarm_is("READING", ChannelAccess.Alarms.NONE)


class CCD100SecondDeviceTests(CCD100Tests):
    """
    Tests for the second CCD100 device.
    """

    def setUp(self):
        self._lewis, self._ioc, self.ca = set_up_connections(DEVICE_E_PREFIX)
        self._lewis.backdoor_set_on_device("address", "e")
