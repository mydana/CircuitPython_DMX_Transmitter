# SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
#
# SPDX-License-Identifier: Unlicense
# pylint: disable=invalid-name
# pylint: enable=invalid-name
import random
import unittest

from dmx_transmitter.dmx_payload import DMXPayload


class PayloadMixin:
    """Test the dmx_payload properties"""

    def runTest(self):  # pylint: disable=invalid-name
        properties = {}
        #
        # This length is calculated
        self.assertEqual(len(self.payload), self.slots, "incorrect array length")
        #
        # This length is a property
        self.assertEqual(self.payload.slots, self.slots, "incorrect slot length")
        #
        # This is defined by DMX. It is 0 unless subclassed
        self.assertEqual(self.payload.start_code, 0, "incorrect start code")
        #
        # Set up some data
        self.data = [random.randint(0, 255) for _ in range(len(self.payload))]
        #
        # Assign that data:
        self.payload[:] = self.data
        #
        # Assign other properties
        for my_property in (
            "mark_before_break",
            "space_for_break",
            "mark_after_break",
            "mark_after_start_code",
            "mark_between_slots",
        ):
            properties[my_property] = random.randint(7, 255)
            setattr(self.payload, my_property, properties[my_property])
        #
        # Verify the data
        self.assertEqual(list(self.payload), self.data, "DMX data mismatch")
        #
        # Check the properties
        for my_property in properties:  # pylint: disable=consider-using-dict-items
            self.assertEqual(
                getattr(self.payload, my_property),
                properties[my_property],
                f"Property {my_property} did not match",
            )
        #
        # Check the interval
        interval = (
            sum(properties.values())
            - properties["mark_between_slots"]
            + (4 + 32) * 2  # Start and data bits
            + (4 + 32 + self.payload.mark_between_slots) * (self.slots - 1)
        )
        self.assertEqual(interval, self.payload.interval, "Interval")
        #
        # See if clear works
        self.payload.clear()
        self.assertEqual(
            list(self.payload), [0] * len(self.payload), "Clear method failed"
        )


class GeneralTestCase(PayloadMixin, unittest.TestCase):
    """Test the standard"""

    def setUp(self):
        self.slots = random.randint(2, 512)
        self.payload = DMXPayload(slots=self.slots)


class MinimumSlotsTestCase(PayloadMixin, unittest.TestCase):
    """Minimum slots allowed"""

    def setUp(self):
        self.slots = 1
        self.payload = DMXPayload(slots=self.slots)


class MaximumSlotsTestCase(PayloadMixin, unittest.TestCase):
    """Maximum slots allowed"""

    def setUp(self):
        self.slots = 512
        self.payload = DMXPayload(slots=self.slots)


class ResourceLimitsTestCase(unittest.TestCase):
    """Verify the resource limits"""

    def runTest(self):  # pylint: disable=invalid-name
        with self.assertRaises(ValueError):
            DMXPayload(slots=0)
        with self.assertRaises(ValueError):
            DMXPayload(slots=513)
        DMXPayload()
