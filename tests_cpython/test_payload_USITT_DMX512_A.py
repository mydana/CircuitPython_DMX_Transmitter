# SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
#
# SPDX-License-Identifier: Unlicense
# pylint: disable=invalid-name
# pylint: enable=invalid-name
import random
import unittest

from dmx_transmitter.payload_USITT_DMX512_A import Payload_USITT_DMX512_A


class PayloadMixin:
    """Test the payload_USITT_DMX512_A properties"""

    def runTest(self):  # pylint: disable=invalid-name
        properties = {}
        #
        # This length is calculated
        self.assertEqual(len(self), self.slots, "incorrect array length")
        #
        # This length is a property
        self.assertEqual(self.slots, self.slots, "incorrect slot length")
        #
        # This is defined by DMX. It is 0 unless subclassed
        self.assertEqual(self.start_code, 0, "incorrect start code")
        #
        # Set up some data
        self.data = [random.randint(0, 255) for _ in range(len(self))]
        #
        # Assign that data:
        self[:] = self.data
        #
        # Pre-check the mark_before_break
        properties["mark_before_break"] = random.randint(7, 255)
        setattr(self, "mark_before_break", properties["mark_before_break"])
        self.assertEqual(
            getattr(self, "mark_before_break"),
            properties["mark_before_break"],
            "Property mark_before_break did not match",
        )
        #
        # Assign other properties
        for my_property in (
            "space_for_break",
            "mark_after_break",
            "mark_after_start_code",
            "mark_between_slots",
            "mark_after_frame",
            # Re-check mark_before_break after setting mark_after_frame
            "mark_before_break",
        ):
            properties[my_property] = random.randint(7, 255)
            setattr(self, my_property, properties[my_property])
        #
        # Verify the data
        self.assertEqual(list(self), self.data, "DMX data mismatch")
        #
        # Check the properties
        for my_property in properties:  # pylint: disable=consider-using-dict-items
            self.assertEqual(
                getattr(self, my_property),
                properties[my_property],
                f"Property {my_property} did not match",
            )
        #
        # Check the interval
        interval = (
            sum(properties.values())
            - properties["mark_between_slots"]
            + (4 + 32) * 2  # Start and data bits
            + (4 + 32 + self.mark_between_slots) * self.slots
        )
        self.assertEqual(interval, self.interval, "Interval")
        #
        # See if clear works
        self.clear()
        self.assertEqual(list(self), [0] * len(self), "Clear method failed")


class GeneralTestCase(PayloadMixin, unittest.TestCase):
    """Test the standard"""

    def setUp(self):
        self.slots = random.randint(2, 512)


class MinimumSlotsTestCase(PayloadMixin, unittest.TestCase):
    """Minimum slots allowed"""

    def setUp(self):
        self.slots = 1


class MaximumSlotsTestCase(PayloadMixin, unittest.TestCase):
    """Maximum slots allowed"""

    def setUp(self):
        self.slots = 512


class ResourceLimitsTestCase(unittest.TestCase):
    """Verify the resource limits"""

    def runTest(self):  # pylint: disable=invalid-name
        with self.assertRaises(ValueError):
            Payload_USITT_DMX512_A(slots=0)
        with self.assertRaises(ValueError):
            Payload_USITT_DMX512_A(slots=513)
        Payload_USITT_DMX512_A()
