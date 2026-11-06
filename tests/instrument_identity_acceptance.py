"""Synthetic acceptance for a detached resolver, not provider/routing evidence.

The 17 request cases come from the 00d32eb design proposal. That proposal's
required_evidence strings describe evidence still needed; they are NOT metadata.
Every record below, including venue and cost-row assertions, is deliberately
injected SYNTHETIC data. No live registry, frozen cost code or old ledger is used.
"""
from dataclasses import FrozenInstanceError, replace
import socket
import unittest
from unittest.mock import patch

from core.research.instrument_identity import (
    AssetClass, CostRow, IdentityRegistry, InstrumentMetadata, Reason,
    ResolutionStatus, resolve_instrument, resolve_many,
)


PROVIDER = 'synthetic-provider'
VERSION = 'synthetic-pr-b-17-v1'


def evidence(symbol, asset, base, quote, venue=None, row=None, continuous=False):
    return InstrumentMetadata(PROVIDER, symbol, asset, base, quote, venue, row, continuous)


# Explicit test assumptions, NOT inferred from the alias spelling and NOT
# provider-verified statements. Unknown crypto/FX venues remain None.
SYNTHETIC_ALIASES = (
    evidence('BTCUSD', AssetClass.CRYPTO, 'BTC', 'USD', row=CostRow.CRYPTO),
    evidence('BTC-USD', AssetClass.CRYPTO, 'BTC', 'USD', row=CostRow.CRYPTO),
    evidence('BTCUSDT', AssetClass.CRYPTO, 'BTC', 'USDT', row=CostRow.CRYPTO),
    evidence('KRW-BTC', AssetClass.CRYPTO, 'BTC', 'KRW', row=CostRow.CRYPTO),
    evidence('EURUSD', AssetClass.FX, 'EUR', 'USD', row=CostRow.FX),
    evidence('EURUSD=X', AssetClass.FX, 'EUR', 'USD', row=CostRow.FX),
    evidence('FX@EURUSD', AssetClass.FX, 'EUR', 'USD', row=CostRow.FX),
    evidence('NAS:AAPL', AssetClass.EQUITY, 'AAPL', 'USD', 'XNAS', CostRow.US),
    evidence('AAPL', AssetClass.EQUITY, 'AAPL', 'USD', 'XNAS', CostRow.US),
    evidence('SPY', AssetClass.ETF, 'SPY', 'USD', 'ARCX', CostRow.US),
    evidence('005930', AssetClass.EQUITY, '005930', 'KRW', 'XKRX', CostRow.KRX_STOCK),
    evidence('069500', AssetClass.ETF, '069500', 'KRW', 'XKRX', CostRow.KRX_ETF),
    evidence('252670.KS', AssetClass.ETF, '252670', 'KRW', 'XKRX', CostRow.KRX_ETF),
    evidence('ES=F', AssetClass.FUTURES, 'ES', 'USD', 'XCME', CostRow.FUTURES, True),
    evidence('VOD.L', AssetClass.EQUITY, 'VOD', 'GBP', 'XLON'),
)
REGISTRY = IdentityRegistry(VERSION, SYNTHETIC_ALIASES)
EMPTY = IdentityRegistry('synthetic-empty-v1')

# Independent expected contract table in the historical proposal's exact order.
# Asset class distinguishes an ETF from the existing cost-row name "us".
CASES = (
    ('BTCUSD', 'RESOLVED', 'crypto', 'BTC', 'USD', None, 'crypto'),
    ('BTC-USD', 'RESOLVED', 'crypto', 'BTC', 'USD', None, 'crypto'),
    ('BTCUSDT', 'RESOLVED', 'crypto', 'BTC', 'USDT', None, 'crypto'),
    ('KRW-BTC', 'RESOLVED', 'crypto', 'BTC', 'KRW', None, 'crypto'),
    ('EURUSD', 'RESOLVED', 'fx', 'EUR', 'USD', None, 'fx'),
    ('EURUSD=X', 'RESOLVED', 'fx', 'EUR', 'USD', None, 'fx'),
    ('FX@EURUSD', 'RESOLVED', 'fx', 'EUR', 'USD', None, 'fx'),
    ('NAS:AAPL', 'RESOLVED', 'equity', 'AAPL', 'USD', 'XNAS', 'us'),
    ('AAPL', 'RESOLVED', 'equity', 'AAPL', 'USD', 'XNAS', 'us'),
    ('SPY', 'RESOLVED', 'etf', 'SPY', 'USD', 'ARCX', 'us'),
    ('005930', 'RESOLVED', 'equity', '005930', 'KRW', 'XKRX', 'krx_stock'),
    ('069500', 'RESOLVED', 'etf', '069500', 'KRW', 'XKRX', 'krx_etf'),
    ('252670.KS', 'RESOLVED', 'etf', '252670', 'KRW', 'XKRX', 'krx_etf'),
    ('ES=F', 'RESOLVED', 'futures', 'ES', 'USD', 'XCME', 'futures'),
    ('UNKNOWN', 'UNKNOWN', None, None, None, None, None),
    ('VOD.L', 'UNSUPPORTED_COST', 'equity', 'VOD', 'GBP', 'XLON', None),
    ('', 'UNKNOWN', None, None, None, None, None),
)


class InstrumentIdentityTests(unittest.TestCase):
    def assert_refusal(self, result, status, reason):
        self.assertIs(result.resolution_status, status)
        self.assertIs(result.reason, reason)
        self.assertIsNone(result.cost_row)
        self.assertIsNone(result.asset_class)
        self.assertIsNone(result.base)
        self.assertIsNone(result.quote_currency)
        self.assertIsNone(result.venue)
        self.assertIsNone(result.orderable)

    def test_historical_17_requests_with_explicit_synthetic_registry(self):
        self.assertEqual(len(CASES), 17)
        for symbol, status, asset, base, quote, venue, row in CASES:
            with self.subTest(symbol=symbol):
                result = resolve_instrument(PROVIDER, symbol, registry=REGISTRY)
                self.assertEqual((result.resolution_status, result.asset_class,
                                  result.base, result.quote_currency, result.venue, result.cost_row),
                                 (status, asset, base, quote, venue, row))
                self.assertEqual(result.provider, PROVIDER)
                self.assertEqual(result.provider_symbol, symbol)
                self.assertEqual(result.registry_version, VERSION)
                if status == 'RESOLVED':
                    self.assertIs(result.reason, Reason.EXPLICIT_ALIAS)

    def test_no_registry_means_no_suffix_or_bare_name_guess(self):
        for symbol in (row[0] for row in CASES if row[0]):
            with self.subTest(symbol=symbol):
                self.assert_refusal(resolve_instrument(PROVIDER, symbol, registry=EMPTY),
                                    ResolutionStatus.UNKNOWN, Reason.NO_EVIDENCE)

    def test_proposal_requirement_text_is_not_provider_metadata(self):
        requirement = {'required_evidence': 'known alias registry or provider instrument metadata; no implicit venue',
                       'provider': PROVIDER, 'provider_symbol': 'BTCUSD'}
        self.assert_refusal(resolve_instrument(PROVIDER, 'BTCUSD', registry=EMPTY, metadata=requirement),
                            ResolutionStatus.UNKNOWN, Reason.INVALID_METADATA)

    def test_ascii_case_boundary_whitespace_lookup_preserves_original_strings(self):
        provider, symbol = '  SYNTHETIC-Provider\t', '\t bTc-UsD \n'
        result = resolve_instrument(provider, symbol, registry=REGISTRY)
        self.assertIs(result.resolution_status, ResolutionStatus.RESOLVED)
        self.assertEqual((result.provider, result.provider_symbol), (provider, symbol))
        self.assertEqual((result.base, result.quote_currency, result.venue), ('BTC', 'USD', None))
        # Unicode case folding must not turn a distinct symbol into an alias.
        self.assert_refusal(resolve_instrument(PROVIDER, '252670.KS', registry=REGISTRY),
                            ResolutionStatus.UNKNOWN, Reason.NO_EVIDENCE)

    def test_provider_scoping_and_explicit_metadata_bind_both_request_fields(self):
        original = SYNTHETIC_ALIASES[0]
        another = replace(original, provider='other-provider', quote_currency='USDT')
        scoped = IdentityRegistry('synthetic-provider-scoping', (original, another))
        first = resolve_instrument(PROVIDER, 'BTCUSD', registry=scoped)
        second = resolve_instrument('other-provider', 'BTCUSD', registry=scoped)
        self.assertEqual((first.quote_currency, second.quote_currency), ('USD', 'USDT'))
        self.assert_refusal(resolve_instrument('absent-provider', 'BTCUSD', registry=scoped),
                            ResolutionStatus.UNKNOWN, Reason.NO_EVIDENCE)
        for mismatch in (another, replace(original, provider_symbol='BTC-USD')):
            with self.subTest(mismatch=mismatch):
                self.assert_refusal(resolve_instrument(PROVIDER, 'BTCUSD', registry=REGISTRY, metadata=mismatch),
                                    ResolutionStatus.UNKNOWN, Reason.METADATA_BINDING_MISMATCH)

    def test_metadata_only_and_agreement_require_explicit_identity_and_row(self):
        record = replace(SYNTHETIC_ALIASES[0], provider='SYNTHETIC-PROVIDER', provider_symbol=' btcusd ')
        only = resolve_instrument(PROVIDER, 'BTCUSD', registry=EMPTY, metadata=record)
        both = resolve_instrument(PROVIDER, 'BTCUSD', registry=REGISTRY, metadata=record)
        self.assertIs(only.reason, Reason.EXPLICIT_METADATA)
        self.assertIs(both.reason, Reason.EXPLICIT_AGREEMENT)
        self.assertEqual(only.cost_row, 'crypto')
        self.assertEqual(both.cost_row, 'crypto')
        no_row = replace(record, cost_row=None)
        refused = resolve_instrument(PROVIDER, 'BTCUSD', registry=EMPTY, metadata=no_row)
        self.assertIs(refused.resolution_status, ResolutionStatus.UNSUPPORTED_COST)
        self.assertEqual((refused.base, refused.quote_currency, refused.venue), ('BTC', 'USD', None))
        self.assertIsNone(refused.cost_row)

    def test_matching_duplicate_aliases_refuse_even_identical_metadata(self):
        original = SYNTHETIC_ALIASES[0]
        for duplicate in (original, replace(original, provider_symbol=' btcusd '),
                          replace(original, quote_currency='USDT')):
            with self.subTest(duplicate=duplicate):
                registry = IdentityRegistry('synthetic-ambiguous', (original, duplicate))
                self.assert_refusal(resolve_instrument(PROVIDER, 'BTCUSD', registry=registry, metadata=original),
                                    ResolutionStatus.AMBIGUOUS, Reason.MULTIPLE_ALIASES)

    def test_conflicting_identity_row_or_null_evidence_never_merges(self):
        original = SYNTHETIC_ALIASES[0]
        conflicts = (replace(original, quote_currency='USDT'),
                     replace(original, venue='XNAS'),
                     replace(original, base='ETH'),
                     replace(original, asset_class=AssetClass.EQUITY),
                     replace(original, cost_row=CostRow.US),
                     replace(original, cost_row=None))
        for metadata in conflicts:
            with self.subTest(metadata=metadata):
                self.assert_refusal(resolve_instrument(PROVIDER, 'BTCUSD', registry=REGISTRY, metadata=metadata),
                                    ResolutionStatus.AMBIGUOUS, Reason.CONFLICTING_EVIDENCE)
        # Also refuse the opposite direction, concrete registry venue vs null.
        known_venue = replace(original, venue='SYNTHETIC-VENUE')
        self.assert_refusal(resolve_instrument(PROVIDER, 'BTCUSD',
                            registry=IdentityRegistry('synthetic-venue', (known_venue,)), metadata=original),
                            ResolutionStatus.AMBIGUOUS, Reason.CONFLICTING_EVIDENCE)
        future = SYNTHETIC_ALIASES[13]
        self.assert_refusal(resolve_instrument(PROVIDER, 'ES=F', registry=REGISTRY,
                                              metadata=replace(future, continuous=False)),
                            ResolutionStatus.AMBIGUOUS, Reason.CONFLICTING_EVIDENCE)

    def test_crypto_quote_series_remain_distinct_and_venue_unknown(self):
        results = resolve_many(PROVIDER, ['BTCUSD', 'BTC-USD', 'BTCUSDT', 'KRW-BTC'], registry=REGISTRY)
        self.assertEqual([r.quote_currency for r in results], ['USD', 'USD', 'USDT', 'KRW'])
        self.assertEqual([r.base for r in results], ['BTC'] * 4)
        self.assertEqual([r.venue for r in results], [None] * 4)
        self.assertEqual([r.orderable for r in results], [None] * 4)
        self.assertEqual(len(set((r.base, r.quote_currency, r.venue) for r in results)), 3)

    def test_london_missing_venue_and_wrong_quote_cannot_inherit_us_cost(self):
        london = SYNTHETIC_ALIASES[-1]
        apple = SYNTHETIC_ALIASES[8]
        records = (london, replace(london, cost_row=CostRow.US),
                   replace(london, quote_currency='USD', cost_row=CostRow.US),
                   replace(apple, venue=None), replace(apple, venue='UNRECOGNIZED'),
                   replace(apple, quote_currency='GBP'))
        for record in records:
            with self.subTest(record=record):
                result = resolve_instrument(PROVIDER, record.provider_symbol, registry=EMPTY, metadata=record)
                self.assertIs(result.resolution_status, ResolutionStatus.UNSUPPORTED_COST)
                self.assertIs(result.reason, Reason.UNSUPPORTED_COST_ROW)
                self.assertIsNone(result.cost_row)
                self.assertEqual((result.base, result.quote_currency, result.venue),
                                 (record.base, record.quote_currency, record.venue))
                self.assertIsNone(result.orderable)

    def test_existing_cost_row_names_require_consistent_explicit_asset_and_market(self):
        records = (replace(SYNTHETIC_ALIASES[0], cost_row=CostRow.US),
                   replace(SYNTHETIC_ALIASES[8], cost_row=CostRow.CRYPTO),
                   replace(SYNTHETIC_ALIASES[10], cost_row=CostRow.KRX_ETF),
                   replace(SYNTHETIC_ALIASES[11], cost_row=CostRow.KRX_STOCK),
                   replace(SYNTHETIC_ALIASES[12], quote_currency='USD'),
                   replace(SYNTHETIC_ALIASES[12], venue=None),
                   replace(SYNTHETIC_ALIASES[13], venue=None),
                   replace(SYNTHETIC_ALIASES[13], quote_currency='KRW'),
                   replace(SYNTHETIC_ALIASES[4], quote_currency='EUR'))
        for record in records:
            with self.subTest(record=record):
                result = resolve_instrument(PROVIDER, record.provider_symbol, registry=EMPTY, metadata=record)
                self.assertIs(result.resolution_status, ResolutionStatus.UNSUPPORTED_COST)
                self.assertIsNone(result.cost_row)

    def test_etf_and_continuous_series_have_no_invented_tradable_identity(self):
        etf = resolve_instrument(PROVIDER, '252670.KS', registry=REGISTRY)
        future = resolve_instrument(PROVIDER, 'ES=F', registry=REGISTRY)
        self.assertIs(etf.asset_class, AssetClass.ETF)
        self.assertIs(etf.cost_row, CostRow.KRX_ETF)
        self.assertIsNone(etf.orderable)
        self.assertEqual((future.provider_symbol, future.base, future.venue), ('ES=F', 'ES', 'XCME'))
        self.assertTrue(future.continuous)
        self.assertIs(future.orderable, False)
        self.assertIs(future.cost_row, CostRow.FUTURES)
        # False continuous means no continuous-series evidence, not permission
        # to turn a series alias into an executable contract.
        unspecified = resolve_instrument(PROVIDER, 'ES=F', registry=EMPTY,
                                         metadata=replace(SYNTHETIC_ALIASES[13], continuous=False))
        self.assertIsNone(unspecified.orderable)

    def test_fx_same_currency_is_refused_even_when_metadata_case_differs(self):
        for base, quote in (('USD', 'USD'), ('usd', 'USD'), ('USD', 'usd')):
            with self.subTest(base=base, quote=quote):
                record = evidence('synthetic-fx', AssetClass.FX, base, quote, row=CostRow.FX)
                result = resolve_instrument(PROVIDER, 'synthetic-fx', registry=EMPTY, metadata=record)
                self.assertIs(result.resolution_status, ResolutionStatus.UNSUPPORTED_COST)
                self.assertIsNone(result.cost_row)
                self.assertEqual((result.base, result.quote_currency), (base, quote))

    def test_malformed_requests_return_typed_refusal_and_preserve_string_input(self):
        for value in (None, 23, [], {}, '', ' \t\n', 'BTC USD', 'BTC\x00USD', 'BTC\x7fUSD'):
            with self.subTest(value=value):
                symbol_result = resolve_instrument(PROVIDER, value, registry=REGISTRY)
                provider_result = resolve_instrument(value, 'BTCUSD', registry=REGISTRY)
                self.assert_refusal(symbol_result, ResolutionStatus.UNKNOWN, Reason.INVALID_REQUEST)
                self.assert_refusal(provider_result, ResolutionStatus.UNKNOWN, Reason.INVALID_REQUEST)
                self.assertEqual(symbol_result.provider_symbol, value if isinstance(value, str) else None)
                self.assertEqual(provider_result.provider, value if isinstance(value, str) else None)

    def test_malformed_registry_refuses_globally_without_attribute_errors(self):
        for registry in (None, {}, 'registry', object(), IdentityRegistry(''),
                         IdentityRegistry(None), IdentityRegistry('synthetic', []),
                         IdentityRegistry('synthetic', (None,)),
                         IdentityRegistry('synthetic', (SYNTHETIC_ALIASES[0], {'unrelated': 'malformed'}))):
            with self.subTest(registry=registry):
                self.assert_refusal(resolve_instrument(PROVIDER, 'BTCUSD', registry=registry),
                                    ResolutionStatus.UNKNOWN, Reason.INVALID_REGISTRY)

    def test_invalid_metadata_and_untyped_enum_strings_are_refused(self):
        original = SYNTHETIC_ALIASES[0]
        invalid = ({}, object(), replace(original, provider=None),
                   replace(original, provider_symbol='BTC USD'),
                   replace(original, asset_class='crypto'),
                   replace(original, base=None), replace(original, quote_currency=''),
                   replace(original, quote_currency=' USD '), replace(original, venue=''),
                   replace(original, cost_row='crypto'), replace(original, cost_row='new-row'),
                   replace(original, continuous=1), replace(original, continuous=True))
        for metadata in invalid:
            with self.subTest(metadata=metadata):
                self.assert_refusal(resolve_instrument(PROVIDER, 'BTCUSD', registry=EMPTY, metadata=metadata),
                                    ResolutionStatus.UNKNOWN, Reason.INVALID_METADATA)
                self.assert_refusal(resolve_instrument(PROVIDER, 'BTCUSD',
                                    registry=IdentityRegistry('synthetic-malformed', (metadata,))),
                                    ResolutionStatus.UNKNOWN, Reason.INVALID_REGISTRY)

    def test_mixed_universe_retains_each_refusal_duplicate_and_request_position(self):
        inputs = ['BTCUSD', 'VOD.L', 'UNKNOWN', '252670.KS', 'ES=F', None, 'BTCUSD']
        saved = inputs.copy()
        results = resolve_many(PROVIDER, inputs, registry=REGISTRY)
        self.assertIsInstance(results, tuple)
        self.assertEqual(inputs, saved)
        self.assertEqual([r.provider_symbol for r in results], saved)
        self.assertEqual([r.resolution_status for r in results],
                         ['RESOLVED', 'UNSUPPORTED_COST', 'UNKNOWN', 'RESOLVED', 'RESOLVED', 'UNKNOWN', 'RESOLVED'])
        self.assertEqual([r.cost_row for r in results], ['crypto', None, None, 'krx_etf', 'futures', None, 'crypto'])
        self.assertEqual(results[0], results[-1])
        self.assertEqual(resolve_many(PROVIDER, [], registry=REGISTRY), ())
        for invalid in ('BTCUSD', None, {'BTCUSD'}, iter(['BTCUSD'])):
            with self.subTest(invalid=invalid):
                with self.assertRaises(TypeError):
                    resolve_many(PROVIDER, invalid, registry=REGISTRY)

    def test_results_and_injected_evidence_are_immutable_and_repeatable(self):
        original = SYNTHETIC_ALIASES[0]
        result = resolve_instrument(PROVIDER, 'BTCUSD', registry=REGISTRY)
        for instance, field, replacement in ((result, 'quote_currency', 'KRW'),
                                              (original, 'base', 'ETH'),
                                              (REGISTRY, 'version', 'changed')):
            with self.subTest(instance=instance):
                with self.assertRaises(FrozenInstanceError):
                    setattr(instance, field, replacement)
        self.assertEqual(resolve_instrument(PROVIDER, 'BTCUSD', registry=REGISTRY), result)
        self.assertEqual(original.base, 'BTC')
        self.assertEqual(REGISTRY.version, VERSION)

    def test_resolution_needs_no_file_or_provider_connection(self):
        symbols = [row[0] for row in CASES]
        expected = resolve_many(PROVIDER, symbols, registry=REGISTRY)
        with patch('builtins.open', side_effect=AssertionError('No file access during resolution')), \
                patch.object(socket.socket, 'connect', side_effect=AssertionError('No provider connections')):
            self.assertEqual(resolve_many(PROVIDER, symbols, registry=REGISTRY), expected)


if __name__ == '__main__':
    unittest.main()
