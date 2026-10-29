"""PR-B observed behavior, NOT acceptance of the proposed fix or current bug."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import dotenv
with patch.object(dotenv,'load_dotenv',return_value=False):
    from core.quant.validate import cost_class,cost_floor_bp,COST_BP_PER_SIDE

CASES=json.loads((Path(__file__).parent/'fixtures/instrument_identity/pr_b_proposal.json').read_text())['cases']
class InstrumentCharacterization(unittest.TestCase):
    def test_record_current_behavior_for_all_aliases(self):
        for row in CASES:
            with self.subTest(symbol=row['symbol']):
                self.assertEqual(cost_class(row['symbol']),row['current_class'])
    def test_mixed_cost_floor_is_conservative_and_unknown_refuses(self):
        self.assertEqual(cost_floor_bp(['BTC-USD','SPY'])[0],50)
        self.assertIsNone(cost_floor_bp(['BTC-USD','VOD.L'])[0])
    def test_fixture_exposes_known_gaps_without_lowering_cost_table(self):
        gaps={r['symbol'] for r in CASES if r['current_class']!=r['proposed_class']}
        self.assertEqual(gaps,{'BTCUSD','EURUSD','UNKNOWN'})
        self.assertEqual(COST_BP_PER_SIDE,{'krx_etf':3.,'krx_stock':35.,'us':50.,'crypto':10.,'futures':5.,'fx':10.})
if __name__=='__main__':unittest.main()
