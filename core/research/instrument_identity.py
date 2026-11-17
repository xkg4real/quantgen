"""Detached explicit-evidence identity resolution; no routing or cost arithmetic.

The caller supplies the complete registry and optional provider-bound metadata.
Aliases are provider-scoped, with ASCII case and boundary whitespace ignored for
lookup only. Original request strings remain in the immutable result. Neither
symbol suffixes nor alphabetic names supply evidence. Registry versions are
caller labels, not a claim that vendor records were independently verified.

Conservative choices: malformed registries refuse globally; duplicate matching
aliases are ambiguous even when identical; null and concrete evidence disagree.
The caller-supplied CostRow enum and small MIC/quote allowlist are bounded
detached implementation choices, not verified vendor policy or production cost
approval. Equity/ETF/futures rows need the listed quote and venue; crypto/FX rows
use explicit class/row evidence without asserting venue support. An FX self-pair
refuses even across ASCII case variants. Other identified instruments refuse
cost selection. Metadata uses actual enums, not unvalidated strings, and its
identity fields are compared exactly for conflicts. No cost values,
frozen modules, default registry, filesystem, environment or provider clients are
used. Even RESOLVED does not authorize a trade or a production cost change.
"""
from dataclasses import dataclass
from enum import Enum


class AssetClass(str, Enum):
    EQUITY = 'equity'
    ETF = 'etf'
    CRYPTO = 'crypto'
    FX = 'fx'
    FUTURES = 'futures'


class CostRow(str, Enum):
    US = 'us'
    KRX_STOCK = 'krx_stock'
    KRX_ETF = 'krx_etf'
    CRYPTO = 'crypto'
    FX = 'fx'
    FUTURES = 'futures'


class ResolutionStatus(str, Enum):
    RESOLVED = 'RESOLVED'
    UNKNOWN = 'UNKNOWN'
    AMBIGUOUS = 'AMBIGUOUS'
    UNSUPPORTED_COST = 'UNSUPPORTED_COST'


class Reason(str, Enum):
    EXPLICIT_ALIAS = 'EXPLICIT_ALIAS'
    EXPLICIT_METADATA = 'EXPLICIT_METADATA'
    EXPLICIT_AGREEMENT = 'EXPLICIT_AGREEMENT'
    INVALID_REQUEST = 'INVALID_REQUEST'
    INVALID_REGISTRY = 'INVALID_REGISTRY'
    INVALID_METADATA = 'INVALID_METADATA'
    METADATA_BINDING_MISMATCH = 'METADATA_BINDING_MISMATCH'
    NO_EVIDENCE = 'NO_EVIDENCE'
    MULTIPLE_ALIASES = 'MULTIPLE_ALIASES'
    CONFLICTING_EVIDENCE = 'CONFLICTING_EVIDENCE'
    UNSUPPORTED_COST_ROW = 'UNSUPPORTED_COST_ROW'


@dataclass(frozen=True)
class InstrumentMetadata:
    provider: str
    provider_symbol: str
    asset_class: AssetClass
    base: str
    quote_currency: str
    venue: str | None = None
    cost_row: CostRow | None = None
    continuous: bool = False


@dataclass(frozen=True)
class IdentityRegistry:
    version: str
    aliases: tuple[InstrumentMetadata, ...] = ()


@dataclass(frozen=True)
class InstrumentIdentity:
    provider: str | None
    provider_symbol: str | None
    registry_version: str | None
    resolution_status: ResolutionStatus
    reason: Reason
    asset_class: AssetClass | None = None
    base: str | None = None
    quote_currency: str | None = None
    venue: str | None = None
    cost_row: CostRow | None = None
    continuous: bool | None = None
    # Continuous series are explicitly non-orderable; all other identities have
    # no execution/orderability evidence in this detached resolver.
    orderable: bool | None = None


_ASCII_LOWER = str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')


def _key(value):
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in stripped):
        return None
    return stripped.translate(_ASCII_LOWER)


def _token(value):
    return isinstance(value, str) and value == value.strip() and _key(value) is not None


def _valid_metadata(record):
    if not isinstance(record, InstrumentMetadata):
        return False
    if not _key(record.provider) or not _key(record.provider_symbol):
        return False
    if not isinstance(record.asset_class, AssetClass) or not _token(record.base) or not _token(record.quote_currency):
        return False
    if record.venue is not None and not _token(record.venue):
        return False
    if record.cost_row is not None and not isinstance(record.cost_row, CostRow):
        return False
    if type(record.continuous) is not bool:
        return False
    return not record.continuous or record.asset_class is AssetClass.FUTURES


def _evidence(record):
    return (record.asset_class, record.base, record.quote_currency, record.venue,
            record.cost_row, record.continuous)


def _supported_cost(record):
    asset, quote, venue, row = record.asset_class, record.quote_currency, record.venue, record.cost_row
    if row is CostRow.US:
        return asset in (AssetClass.EQUITY, AssetClass.ETF) and quote == 'USD' and venue in {'XNAS', 'XNYS', 'ARCX'}
    if row in (CostRow.KRX_STOCK, CostRow.KRX_ETF):
        expected = AssetClass.EQUITY if row is CostRow.KRX_STOCK else AssetClass.ETF
        return asset is expected and quote == 'KRW' and venue == 'XKRX'
    if row is CostRow.CRYPTO:
        return asset is AssetClass.CRYPTO
    if row is CostRow.FX:
        return asset is AssetClass.FX and _key(record.base) != _key(quote)
    if row is CostRow.FUTURES:
        return asset is AssetClass.FUTURES and quote == 'USD' and venue in {'XCME', 'XCBT'}
    return False


def resolve_instrument(provider, provider_symbol, *, registry, metadata=None):
    """Resolve one request from explicit evidence, returning typed refusals.

    A non-string malformed request is represented by None rather than copied
    into the immutable result. Valid string input is preserved exactly, even
    on refusal. Metadata must bind to this provider AND requested alias. The
    venue allowlist intentionally supports only this bounded contract; unknown
    venues cannot inherit US costs. No security ID or execution ID is invented.
    """
    raw_provider = provider if isinstance(provider, str) else None
    raw_symbol = provider_symbol if isinstance(provider_symbol, str) else None
    version = registry.version if isinstance(registry, IdentityRegistry) and _token(registry.version) else None

    def result(status, reason, record=None):
        known = {} if record is None else dict(
            asset_class=record.asset_class, base=record.base, quote_currency=record.quote_currency,
            venue=record.venue, cost_row=record.cost_row if status is ResolutionStatus.RESOLVED else None,
            continuous=record.continuous, orderable=False if record.continuous else None)
        return InstrumentIdentity(raw_provider, raw_symbol, version, status, reason, **known)

    key = (_key(provider), _key(provider_symbol))
    if None in key:
        return result(ResolutionStatus.UNKNOWN, Reason.INVALID_REQUEST)
    if (version is None or type(registry.aliases) is not tuple
            or not all(_valid_metadata(record) for record in registry.aliases)):
        return result(ResolutionStatus.UNKNOWN, Reason.INVALID_REGISTRY)
    if metadata is not None:
        if not _valid_metadata(metadata):
            return result(ResolutionStatus.UNKNOWN, Reason.INVALID_METADATA)
        if (_key(metadata.provider), _key(metadata.provider_symbol)) != key:
            return result(ResolutionStatus.UNKNOWN, Reason.METADATA_BINDING_MISMATCH)
    matches = [record for record in registry.aliases
               if (_key(record.provider), _key(record.provider_symbol)) == key]
    if len(matches) > 1:
        return result(ResolutionStatus.AMBIGUOUS, Reason.MULTIPLE_ALIASES)
    if matches and metadata is not None and _evidence(matches[0]) != _evidence(metadata):
        return result(ResolutionStatus.AMBIGUOUS, Reason.CONFLICTING_EVIDENCE)
    record = metadata if metadata is not None else matches[0] if matches else None
    if record is None:
        return result(ResolutionStatus.UNKNOWN, Reason.NO_EVIDENCE)
    if not _supported_cost(record):
        return result(ResolutionStatus.UNSUPPORTED_COST, Reason.UNSUPPORTED_COST_ROW, record)
    reason = Reason.EXPLICIT_AGREEMENT if matches and metadata is not None else (
        Reason.EXPLICIT_METADATA if metadata is not None else Reason.EXPLICIT_ALIAS)
    return result(ResolutionStatus.RESOLVED, reason, record)


def resolve_many(provider, symbols, *, registry):
    """Preserve mixed-universe order and every refusal; never aggregate costs."""
    if not isinstance(symbols, (list, tuple)):
        raise TypeError('symbols must be a list or tuple of request symbols')
    return tuple(resolve_instrument(provider, symbol, registry=registry) for symbol in symbols)
