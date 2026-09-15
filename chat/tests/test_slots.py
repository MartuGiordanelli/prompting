"""Tests de chat/slots.py. Sin red."""

import unittest

from chat.slots import SLOTS, SlotError, get_slot, validate_effort


class SlotsTableTests(unittest.TestCase):
    def test_hay_exactamente_cuatro_slots(self):
        self.assertEqual(len(SLOTS), 4)
        self.assertEqual([s.number for s in SLOTS], [1, 2, 3, 4])

    def test_get_slot_devuelve_el_correcto(self):
        self.assertEqual(get_slot(1).model, "openai/gpt-5.6-luna")
        self.assertEqual(get_slot(2).model, "anthropic/claude-haiku-4.5")
        self.assertEqual(get_slot(3).model, "google/gemini-3.7-flash")
        self.assertEqual(get_slot(4).model, "deepseek/deepseek-v4-flash-0731")

    def test_get_slot_invalido_falla_claro(self):
        with self.assertRaises(SlotError):
            get_slot(0)
        with self.assertRaises(SlotError):
            get_slot(5)

    def test_slot_2_no_tiene_efforts_pero_si_cache_control(self):
        slot2 = get_slot(2)
        self.assertEqual(slot2.supported_efforts, ())
        self.assertIsNone(slot2.default_effort)
        self.assertTrue(slot2.cache_control)
        self.assertEqual(slot2.fixed_provider, "anthropic")

    def test_slot_4_proveedor_tbd(self):
        self.assertIsNone(get_slot(4).fixed_provider)


class ValidateEffortTests(unittest.TestCase):
    def test_acepta_effort_valido_por_slot(self):
        validate_effort(1, "high")
        validate_effort(3, "low")
        validate_effort(4, "max")

    def test_rechaza_effort_invalido_por_slot(self):
        with self.assertRaises(SlotError):
            validate_effort(1, "ultra")
        with self.assertRaises(SlotError):
            validate_effort(3, "xhigh")  # valido en el slot 1, no en el 3
        with self.assertRaises(SlotError):
            validate_effort(4, "medium")  # el slot 4 no tiene "medium"

    def test_slot_2_rechaza_cualquier_effort(self):
        with self.assertRaises(SlotError):
            validate_effort(2, "high")
        with self.assertRaises(SlotError):
            validate_effort(2, "none")

    def test_slot_invalido_en_validate_effort_falla_claro(self):
        with self.assertRaises(SlotError):
            validate_effort(9, "high")


if __name__ == "__main__":
    unittest.main()
