import unittest

from scripts.snapshot_kalshi_liquidity import summarize_book


class KalshiLiquidityTests(unittest.TestCase):
    def test_complement_and_sizes_use_best_prices_not_source_order(self):
        result = summarize_book({'orderbook_fp': {
            'yes_dollars': [['0.30', '10'], ['0.40', '2.5']],
            'no_dollars': [['0.50', '8'], ['0.20', '12']]}})
        self.assertEqual(result['depth_yes_bid'], .4)
        self.assertEqual(result['depth_yes_ask'], .5)
        self.assertEqual(result['best_yes_ask_quantity'], 8)
        self.assertEqual(result['best_yes_bid_quantity'], 2.5)
        self.assertTrue(result['depth_two_sided'])

    def test_empty_or_crossed_books_are_not_two_sided(self):
        empty = summarize_book({'orderbook_fp': {'yes_dollars': [], 'no_dollars': None}})
        self.assertIsNone(empty['depth_yes_ask'])
        self.assertFalse(empty['depth_two_sided'])
        crossed = summarize_book({'orderbook_fp': {
            'yes_dollars': [['0.70', '1']], 'no_dollars': [['0.40', '1']]}})
        self.assertFalse(crossed['depth_two_sided'])

    def test_invalid_or_duplicate_levels_fail(self):
        for levels in [[['0.4', '-2']], [['NaN', '2']], [['1.2', '2']],
                       [['0.4', '2'], ['0.4', '3']]]:
            with self.assertRaises(ValueError):
                summarize_book({'orderbook_fp': {'yes_dollars': levels, 'no_dollars': []}})


if __name__ == '__main__':
    unittest.main()
