"""Illustrative valuation reading contracts; no model, provider or ranking.

The intervals are display examples with qualifications, never universal quality
scores or an industry-average substitute. Raw supplied numbers stay untouched.
"""
from dataclasses import FrozenInstanceError
import math
import unittest


class ValuationReferenceContracts(unittest.TestCase):
    def test_positive_reference_boundaries_keep_the_stated_inclusive_ranges(self):
        from quantgen_desktop.metric_help import valuation_reference
        examples = {
            'per': ((9.99, 0), (10, 1), (20, 1), (20.01, 2), (1000, 2)),
            'pbr': ((.99, 0), (1, 1), (3, 1), (3.01, 2), (1000, 2)),
        }
        for language in ('ko', 'en'):
            for metric, cases in examples.items():
                for value, band in cases:
                    with self.subTest(language=language, metric=metric, value=value):
                        reading = valuation_reference(metric, value, language)
                        self.assertEqual(reading.band_index, band)
                        self.assertIsNotNone(reading.position)
                        self.assertTrue(math.isfinite(reading.position))
                        self.assertGreaterEqual(reading.position, 0)
                        self.assertLessEqual(reading.position, 1)
                        self.assertEqual(len(reading.labels), 3)
                        self.assertTrue(all(reading.labels))
                        self.assertTrue(reading.reading)

    def test_missing_nonpositive_nonfinite_and_boolean_values_get_no_pointer(self):
        from quantgen_desktop.metric_help import valuation_reference
        for metric in ('per', 'pbr'):
            for language in ('ko', 'en'):
                for value in (None, 0, -1, math.nan, math.inf, -math.inf, True, False):
                    with self.subTest(metric=metric, language=language, value=value):
                        reading = valuation_reference(metric, value, language)
                        self.assertIsNone(reading.position)
                        self.assertIsNone(reading.band_index)
                        self.assertTrue(reading.reading)
                        self.assertTrue(reading.hover)

    def test_reference_copy_keeps_industry_context_and_is_immutable(self):
        from quantgen_desktop.metric_help import valuation_reference
        for metric in ('per', 'pbr'):
            for language in ('ko', 'en'):
                reading = valuation_reference(metric, 1, language)
                copy = reading.reading + ' ' + reading.hover
                if language == 'ko':
                    self.assertIn('업종', copy)
                    self.assertTrue('예시' in copy or '참고' in copy)
                else:
                    self.assertIn('industr', copy.lower())
                    self.assertTrue('example' in copy.lower() or 'reference' in copy.lower())
                with self.assertRaises(FrozenInstanceError):
                    reading.position = .5


if __name__ == '__main__':
    unittest.main()
