# Nautilus_Trader - Data

**Pages:** 12

---

## Cache

**URL:** https://nautilustrader.io/docs/latest/api_reference/cache

**Contents:**
- Cache
  - class Cache​
    - account(self, AccountId account_id) → Account​
    - account_for_venue(self, Venue venue) → Account​
    - account_id(self, Venue venue) → AccountId​
    - accounts(self) → list​
    - actor_ids(self) → set​
    - add(self, str key, bytes value) → void​
    - add_account(self, Account account) → void​
    - add_bar(self, Bar bar) → void​

The cache subpackage provides common caching infrastructure.

A running Nautilus system generally uses a single centralized cache which can be accessed by many components.

Cache(CacheDatabaseFacade database: CacheDatabaseFacade | None = None, config: CacheConfig | None = None) -> None

Provides a common object cache for market and execution related data.

Return the account matching the given ID (if found).

Return the account matching the given client ID (if found).

If unique_venue is set, it will be used instead of the provided venue.

Return the account ID for the given venue (if found).

Return all accounts in the cache.

Return all actor IDs.

Add the given general object value to the cache.

The cache is agnostic to what the object actually is (and how it may be serialized), offering maximum flexibility.

Add the given account to the cache.

Add the given bar to the cache.

Add the given bars to the cache.

Add the given currency to the cache.

Add the given funding rate update to the cache.

Add greeks to the cache.

Add the given index price update to the cache.

Add the given instrument to the cache.

Add the given mark price update to the cache.

Add the given order to the cache indexed with the given position ID.

Add the given order book to the cache.

Add the given order list to the cache.

Add the given own order book to the cache.

Add the given position to the cache.

Index the given position ID with the other given IDs.

Add the given quote tick to the cache.

Add the given quotes to the cache.

Add the given synthetic instrument to the cache.

Add the given trade tick to the cache.

Add the given trades to the cache.

Index the given client order ID with the given venue order ID.

Add a yield curve to the cache.

Audit all own order books against open and inflight order indexes.

Ensures closed orders are removed from own order books. This includes both orders tracked in _index_orders_open (ACCEPTED, TRIGGERED, PENDING_*, PARTIALLY_FILLED) and _index_orders_inflight (INITIALIZED, SUBMITTED) to prevent false positives during venue latency windows.

Logs all failures as errors.

Return the bar for the given bar type at the given index (if found).

Last bar if no index specified.

The caches bar capacity.

The count of bars for the given bar type.

Return all bar types with the given query filters.

If a filter parameter is None, then no filtering occurs for that parameter.

Return bars for the given bar type.

The count of order book updates for the given instrument ID.

Will return zero if there is no book for the instrument ID.

Build the cache index from objects currently held in memory.

Clear the current accounts cache and load accounts from the cache database.

Clears and loads the currencies, instruments, synthetics, accounts, orders, and positions. from the cache database.

Clear the current currencies cache and load currencies from the cache database.

Clear the current general cache and load the general objects from the cache database.

Clear the current instruments cache and load instruments from the cache database.

Clear the current order lists cache and load order lists using cached orders.

Clear the current orders cache and load orders from the cache database.

Clear the current positions cache and load positions from the cache database.

Clear the current synthetic instruments cache and load synthetic instruments from the cache database.

Check integrity of data within the cache.

All data should be loaded from the database prior to this call. If an error is found then a log error message will also be produced.

Check for any residual open state and log warnings if any are found.

‘Open state’ is considered to be open orders and open positions.

Clear the exchange rate based on mark price.

Clear the exchange rates based on mark price.

Return the specific execution client ID matching the given client order ID (if found).

Return the client order ID matching the given venue order ID (if found).

Return all client order IDs with the given query filters.

Return all closed client order IDs with the given query filters.

Return all emulated client order IDs with the given query filters.

Return all in-flight client order IDs with the given query filters.

Return all open client order IDs with the given query filters.

Delete the given actor from the cache.

Delete the given strategy from the cache.

Dispose of the cache which will close any underlying database adapter.

Return all execution algorithm IDs.

Return the total filled quantity for the given execution spawn ID (if found).

If no execution spawn ID matches then returns None.

Return the total leaves quantity for the given execution spawn ID (if found).

If no execution spawn ID matches then returns None.

Return the total quantity for the given execution spawn ID (if found).

If no execution spawn ID matches then returns None.

Flush the caches database which permanently removes all persisted data.

Force removal of an order from own order books and clean up all indexes.

This method is used when order.apply() fails and we need to ensure terminal orders are properly cleaned up from own books and all relevant indexes. Replicates the index cleanup that update_order performs for closed orders.

Return the funding rate for the given instrument ID (if found).

Return the general object for the given key.

The cache is agnostic to what the object actually is (and how it may be serialized), offering maximum flexibility.

Return the exchange rate based on mark price.

Will return None if an exchange rate has not been set.

Return the calculated exchange rate.

If the exchange rate cannot be calculated then returns None.

Return the latest cached greeks for the given instrument ID.

If the cache has a database backing.

Return a value indicating whether the cache has bars for the given bar type.

Return a value indicating whether the cache has index prices for the given instrument ID.

Return a value indicating whether the cache has mark prices for the given instrument ID.

Return a value indicating whether the cache has an order book snapshot for the given instrument ID.

Return a value indicating whether the cache has quotes for the given instrument ID.

Return a value indicating whether the cache has trades for the given instrument ID.

Add a heartbeat at the given timestamp.

Return the index price for the given instrument ID at the given index (if found).

Last index price if no index specified.

The count of index prices for the given instrument ID.

Return index prices for the given instrument ID.

Return the instrument corresponding to the given instrument ID.

Return all instrument IDs held by the cache.

Return all instruments held by the cache.

Return a value indicating whether an order with the given ID is closed.

Return a value indicating whether an order with the given ID is emulated.

Return a value indicating whether an order with the given ID is in-flight.

Return a value indicating whether an order with the given ID is open.

Return a value indicating whether an order with the given ID is pending cancel locally.

Return a value indicating whether a position with the given ID exists and is closed.

Return a value indicating whether a position with the given ID exists and is open.

Load the account associated with the given account_id (if found).

Load the state dictionary into the given actor.

Load the instrument associated with the given instrument ID (if found).

Load the order associated with the given ID (if found).

Load the position associated with the given ID (if found).

Load the state dictionary into the given strategy.

Load the synthetic instrument associated with the given instrument_id (if found).

Return the mark price for the given instrument ID at the given index (if found).

Last mark price if no index specified.

The count of mark prices for the given instrument ID.

Return mark prices for the given instrument ID.

Return the order matching the given client order ID (if found).

Return the order book for the given instrument ID (if found).

Return a value indicating whether an order with the given ID exists.

Return the order list matching the given order list ID (if found).

Return a value indicating whether an order list with the given ID exists.

Return all order list IDs.

Return all order lists matching the given query filters.

No particular order of list elements is guaranteed.

Return all orders matching the given query filters.

No particular order of list elements is guaranteed.

Return all closed orders with the given query filters.

No particular order of list elements is guaranteed.

Return the count of closed orders with the given query filters.

Return all emulated orders with the given query filters.

No particular order of list elements is guaranteed.

Return the count of emulated orders with the given query filters.

Return all execution algorithm orders for the given query filters.

Return all orders for the given execution spawn ID (if found).

Will also include the primary (original) order.

Return all orders for the given position ID.

Return all in-flight orders with the given query filters.

No particular order of list elements is guaranteed.

Return the count of in-flight orders with the given query filters.

Return all open orders with the given query filters.

No particular order of list elements is guaranteed.

Return the count of open orders with the given query filters.

Return the total count of orders with the given query filters.

Return own ask orders for the given instrument ID (if found).

Return own bid orders for the given instrument ID (if found).

Return the own order book for the given instrument ID (if found).

If account state events are written to the backing database.

Return the position associated with the given ID (if found).

Return all closed position IDs with the given query filters.

Return a value indicating whether a position with the given ID exists.

Return the position associated with the given client order ID (if found).

Return the position ID associated with the given client order ID (if found).

Return all position IDs with the given query filters.

Return all open position IDs with the given query filters.

Return the raw pickled snapshot bytes for the given position ID.

Return all position IDs for position snapshots with the given instrument filter.

Return all position snapshots with the given optional identifier filter.

Return all positions with the given query filters.

No particular order of list elements is guaranteed.

Return all closed positions with the given query filters.

No particular order of list elements is guaranteed.

Return the count of closed positions with the given query filters.

Return all open positions with the given query filters.

No particular order of list elements is guaranteed.

Return the count of open positions with the given query filters.

Return the total count of positions with the given query filters.

Return the price for the given instrument ID and price type.

Return a map of latest prices per instrument ID for the given price type.

Purge all account state events which are outside the lookback window.

Purge all closed orders from the cache.

Purge all closed positions from the cache.

Purge the order for the given client order ID from the cache (if found).

For safety, an order is prevented from being purged if it’s open.

Purge the position for the given position ID from the cache (if found).

For safety, a position is prevented from being purged if it’s open.

Return the quote tick for the given instrument ID at the given index (if found).

Last quote tick if no index specified.

The count of quotes for the given instrument ID.

Return the quotes for the given instrument ID.

All stateful fields are reset to their initial value.

Set the exchange rate based on mark price.

Will also set the inverse xrate automatically.

Set a specific venue that the cache will use for subsequent account_for_venue calls.

Primarily for Interactive Brokers, a multi-venue brokerage where account updates are not tied to a single venue.

Snapshot the state dictionary for the given order.

This method will persist to the backing cache database.

Snapshot the given position in its current state.

The position ID will be appended with a UUID v4 string.

Snapshot the state dictionary for the given position.

This method will persist to the backing cache database.

Return the strategy ID associated with the given ID (if found).

Return the strategy ID associated with the given ID (if found).

Return all strategy IDs.

Return the synthetic instrument corresponding to the given instrument ID.

Return all synthetic instrument IDs held by the cache.

Return all synthetic instruments held by the cache.

The caches tick capacity.

Return the trade tick for the given instrument ID at the given index (if found).

Last trade tick if no index specified.

The count of trades for the given instrument ID.

Return trades for the given instrument ID.

Update the given account in the cache.

Update the given actor state in the cache.

Update the given order in the cache.

Update the given order as pending cancel locally.

Update the own order book for the given order.

Orders without prices (MARKET, etc.) are skipped as they cannot be represented in own books.

Update the given position in the cache.

Update the given strategy state in the cache.

Return the order ID matching the given client order ID (if found).

Return the latest cached yield curve for the given curve name.

Bases: CacheDatabaseFacade

CacheDatabaseAdapter(TraderId trader_id, UUID4 instance_id, Serializer serializer, config: CacheConfig | None = None) -> None

Provides a generic cache database adapter.

Redis can only accurately store int64 types to 17 digits of precision. Therefore nanosecond timestamp int64’s with 19 digits will lose 2 digits of precision when persisted. One way to solve this is to ensure the serializer converts timestamp int64’s to strings on the way into Redis, and converts timestamp strings back to int64’s on the way out. One way to achieve this is to set the timestamps_as_str flag to true for the MsgSpecSerializer, as per the default implementations for both TradingNode and BacktestEngine.

Add the given general object value to the database.

Add the given account to the database.

Add the given currency to the database.

Add the given instrument to the database.

Add the given order to the database.

Add the given position to the database.

Add the given synthetic instrument to the database.

Close the backing database adapter.

Delete the given account event from the database.

Delete the given actor from the database.

Delete the given order from the database.

Delete the given position from the database.

Delete the given strategy from the database.

Flush the database which clears all data.

Add a heartbeat at the given timestamp.

Add an index entry for the given client_order_id to position_id.

Add an index entry for the given venue_order_id to client_order_id.

Return all keys in the database matching the given pattern.

Using the default ‘*’ pattern string can have serious performance implications and can take a long time to execute if many keys exist in the database. This operation can lead to high memory and CPU usage, and should be used with caution, especially in production environments.

Load all general objects from the database using bulk loading for efficiency.

Load the account associated with the given account ID (if found).

Load all accounts from the database.

Load the state for the given actor.

Load all cache data from the database.

Load all currencies from the database using bulk loading for efficiency.

Load the currency associated with the given currency code (if found).

Load the order to execution client index from the database.

Load the order to position index from the database.

Load the instrument associated with the given instrument ID (if found).

Load all instruments from the database using bulk loading for efficiency.

Load the order associated with the given client order ID (if found).

Load all orders from the database.

Load the position associated with the given ID (if found).

Load all positions from the database.

Load the state for the given strategy.

Load the synthetic instrument associated with the given synthetic instrument ID (if found).

Load all synthetic instruments from the database using bulk loading for efficiency.

Snapshot the state of the given order.

Snapshot the state of the given position.

Update the given account in the database.

Update the given actor state in the database.

Update the given order in the database.

Update the given position in the database.

Update the given strategy state in the database.

Cache(CacheDatabaseFacade database: CacheDatabaseFacade | None = None, config: CacheConfig | None = None) -> None

Provides a common object cache for market and execution related data.

Return the account matching the given ID (if found).

Return the account matching the given client ID (if found).

If unique_venue is set, it will be used instead of the provided venue.

Return the account ID for the given venue (if found).

Return all accounts in the cache.

Return all actor IDs.

Add the given general object value to the cache.

The cache is agnostic to what the object actually is (and how it may be serialized), offering maximum flexibility.

Add the given account to the cache.

Add the given bar to the cache.

Add the given bars to the cache.

Add the given currency to the cache.

Add the given funding rate update to the cache.

Add greeks to the cache.

Add the given index price update to the cache.

Add the given instrument to the cache.

Add the given mark price update to the cache.

Add the given order to the cache indexed with the given position ID.

Add the given order book to the cache.

Add the given order list to the cache.

Add the given own order book to the cache.

Add the given position to the cache.

Index the given position ID with the other given IDs.

Add the given quote tick to the cache.

Add the given quotes to the cache.

Add the given synthetic instrument to the cache.

Add the given trade tick to the cache.

Add the given trades to the cache.

Index the given client order ID with the given venue order ID.

Add a yield curve to the cache.

Audit all own order books against open and inflight order indexes.

Ensures closed orders are removed from own order books. This includes both orders tracked in _index_orders_open (ACCEPTED, TRIGGERED, PENDING_*, PARTIALLY_FILLED) and _index_orders_inflight (INITIALIZED, SUBMITTED) to prevent false positives during venue latency windows.

Logs all failures as errors.

Return the bar for the given bar type at the given index (if found).

Last bar if no index specified.

The caches bar capacity.

The count of bars for the given bar type.

Return all bar types with the given query filters.

If a filter parameter is None, then no filtering occurs for that parameter.

Return bars for the given bar type.

The count of order book updates for the given instrument ID.

Will return zero if there is no book for the instrument ID.

Build the cache index from objects currently held in memory.

Clear the current accounts cache and load accounts from the cache database.

Clears and loads the currencies, instruments, synthetics, accounts, orders, and positions. from the cache database.

Clear the current currencies cache and load currencies from the cache database.

Clear the current general cache and load the general objects from the cache database.

Clear the current instruments cache and load instruments from the cache database.

Clear the current order lists cache and load order lists using cached orders.

Clear the current orders cache and load orders from the cache database.

Clear the current positions cache and load positions from the cache database.

Clear the current synthetic instruments cache and load synthetic instruments from the cache database.

Check integrity of data within the cache.

All data should be loaded from the database prior to this call. If an error is found then a log error message will also be produced.

Check for any residual open state and log warnings if any are found.

‘Open state’ is considered to be open orders and open positions.

Clear the exchange rate based on mark price.

Clear the exchange rates based on mark price.

Return the specific execution client ID matching the given client order ID (if found).

Return the client order ID matching the given venue order ID (if found).

Return all client order IDs with the given query filters.

Return all closed client order IDs with the given query filters.

Return all emulated client order IDs with the given query filters.

Return all in-flight client order IDs with the given query filters.

Return all open client order IDs with the given query filters.

Delete the given actor from the cache.

Delete the given strategy from the cache.

Dispose of the cache which will close any underlying database adapter.

Return all execution algorithm IDs.

Return the total filled quantity for the given execution spawn ID (if found).

If no execution spawn ID matches then returns None.

Return the total leaves quantity for the given execution spawn ID (if found).

If no execution spawn ID matches then returns None.

Return the total quantity for the given execution spawn ID (if found).

If no execution spawn ID matches then returns None.

Flush the caches database which permanently removes all persisted data.

Force removal of an order from own order books and clean up all indexes.

This method is used when order.apply() fails and we need to ensure terminal orders are properly cleaned up from own books and all relevant indexes. Replicates the index cleanup that update_order performs for closed orders.

Return the funding rate for the given instrument ID (if found).

Return the general object for the given key.

The cache is agnostic to what the object actually is (and how it may be serialized), offering maximum flexibility.

Return the exchange rate based on mark price.

Will return None if an exchange rate has not been set.

Return the calculated exchange rate.

If the exchange rate cannot be calculated then returns None.

Return the latest cached greeks for the given instrument ID.

If the cache has a database backing.

Return a value indicating whether the cache has bars for the given bar type.

Return a value indicating whether the cache has index prices for the given instrument ID.

Return a value indicating whether the cache has mark prices for the given instrument ID.

Return a value indicating whether the cache has an order book snapshot for the given instrument ID.

Return a value indicating whether the cache has quotes for the given instrument ID.

Return a value indicating whether the cache has trades for the given instrument ID.

Add a heartbeat at the given timestamp.

Return the index price for the given instrument ID at the given index (if found).

Last index price if no index specified.

The count of index prices for the given instrument ID.

Return index prices for the given instrument ID.

Return the instrument corresponding to the given instrument ID.

Return all instrument IDs held by the cache.

Return all instruments held by the cache.

Return a value indicating whether an order with the given ID is closed.

Return a value indicating whether an order with the given ID is emulated.

Return a value indicating whether an order with the given ID is in-flight.

Return a value indicating whether an order with the given ID is open.

Return a value indicating whether an order with the given ID is pending cancel locally.

Return a value indicating whether a position with the given ID exists and is closed.

Return a value indicating whether a position with the given ID exists and is open.

Load the account associated with the given account_id (if found).

Load the state dictionary into the given actor.

Load the instrument associated with the given instrument ID (if found).

Load the order associated with the given ID (if found).

Load the position associated with the given ID (if found).

Load the state dictionary into the given strategy.

Load the synthetic instrument associated with the given instrument_id (if found).

Return the mark price for the given instrument ID at the given index (if found).

Last mark price if no index specified.

The count of mark prices for the given instrument ID.

Return mark prices for the given instrument ID.

Return the order matching the given client order ID (if found).

Return the order book for the given instrument ID (if found).

Return a value indicating whether an order with the given ID exists.

Return the order list matching the given order list ID (if found).

Return a value indicating whether an order list with the given ID exists.

Return all order list IDs.

Return all order lists matching the given query filters.

No particular order of list elements is guaranteed.

Return all orders matching the given query filters.

No particular order of list elements is guaranteed.

Return all closed orders with the given query filters.

No particular order of list elements is guaranteed.

Return the count of closed orders with the given query filters.

Return all emulated orders with the given query filters.

No particular order of list elements is guaranteed.

Return the count of emulated orders with the given query filters.

Return all execution algorithm orders for the given query filters.

Return all orders for the given execution spawn ID (if found).

Will also include the primary (original) order.

Return all orders for the given position ID.

Return all in-flight orders with the given query filters.

No particular order of list elements is guaranteed.

Return the count of in-flight orders with the given query filters.

Return all open orders with the given query filters.

No particular order of list elements is guaranteed.

Return the count of open orders with the given query filters.

Return the total count of orders with the given query filters.

Return own ask orders for the given instrument ID (if found).

Return own bid orders for the given instrument ID (if found).

Return the own order book for the given instrument ID (if found).

If account state events are written to the backing database.

Return the position associated with the given ID (if found).

Return all closed position IDs with the given query filters.

Return a value indicating whether a position with the given ID exists.

Return the position associated with the given client order ID (if found).

Return the position ID associated with the given client order ID (if found).

Return all position IDs with the given query filters.

Return all open position IDs with the given query filters.

Return the raw pickled snapshot bytes for the given position ID.

Return all position IDs for position snapshots with the given instrument filter.

Return all position snapshots with the given optional identifier filter.

Return all positions with the given query filters.

No particular order of list elements is guaranteed.

Return all closed positions with the given query filters.

No particular order of list elements is guaranteed.

Return the count of closed positions with the given query filters.

Return all open positions with the given query filters.

No particular order of list elements is guaranteed.

Return the count of open positions with the given query filters.

Return the total count of positions with the given query filters.

Return the price for the given instrument ID and price type.

Return a map of latest prices per instrument ID for the given price type.

Purge all account state events which are outside the lookback window.

Purge all closed orders from the cache.

Purge all closed positions from the cache.

Purge the order for the given client order ID from the cache (if found).

For safety, an order is prevented from being purged if it’s open.

Purge the position for the given position ID from the cache (if found).

For safety, a position is prevented from being purged if it’s open.

Return the quote tick for the given instrument ID at the given index (if found).

Last quote tick if no index specified.

The count of quotes for the given instrument ID.

Return the quotes for the given instrument ID.

All stateful fields are reset to their initial value.

Set the exchange rate based on mark price.

Will also set the inverse xrate automatically.

Set a specific venue that the cache will use for subsequent account_for_venue calls.

Primarily for Interactive Brokers, a multi-venue brokerage where account updates are not tied to a single venue.

Snapshot the state dictionary for the given order.

This method will persist to the backing cache database.

Snapshot the given position in its current state.

The position ID will be appended with a UUID v4 string.

Snapshot the state dictionary for the given position.

This method will persist to the backing cache database.

Return the strategy ID associated with the given ID (if found).

Return the strategy ID associated with the given ID (if found).

Return all strategy IDs.

Return the synthetic instrument corresponding to the given instrument ID.

Return all synthetic instrument IDs held by the cache.

Return all synthetic instruments held by the cache.

The caches tick capacity.

Return the trade tick for the given instrument ID at the given index (if found).

Last trade tick if no index specified.

The count of trades for the given instrument ID.

Return trades for the given instrument ID.

Update the given account in the cache.

Update the given actor state in the cache.

Update the given order in the cache.

Update the given order as pending cancel locally.

Update the own order book for the given order.

Orders without prices (MARKET, etc.) are skipped as they cannot be represented in own books.

Update the given position in the cache.

Update the given strategy state in the cache.

Return the order ID matching the given client order ID (if found).

Return the latest cached yield curve for the given curve name.

Bases: CacheDatabaseFacade

CacheDatabaseAdapter(TraderId trader_id, UUID4 instance_id, Serializer serializer, config: CacheConfig | None = None) -> None

Provides a generic cache database adapter.

Redis can only accurately store int64 types to 17 digits of precision. Therefore nanosecond timestamp int64’s with 19 digits will lose 2 digits of precision when persisted. One way to solve this is to ensure the serializer converts timestamp int64’s to strings on the way into Redis, and converts timestamp strings back to int64’s on the way out. One way to achieve this is to set the timestamps_as_str flag to true for the MsgSpecSerializer, as per the default implementations for both TradingNode and BacktestEngine.

Add the given general object value to the database.

Add the given account to the database.

Add the given currency to the database.

Add the given instrument to the database.

Add the given order to the database.

Add the given position to the database.

Add the given synthetic instrument to the database.

Close the backing database adapter.

Delete the given account event from the database.

Delete the given actor from the database.

Delete the given order from the database.

Delete the given position from the database.

Delete the given strategy from the database.

Flush the database which clears all data.

Add a heartbeat at the given timestamp.

Add an index entry for the given client_order_id to position_id.

Add an index entry for the given venue_order_id to client_order_id.

Return all keys in the database matching the given pattern.

Using the default ‘*’ pattern string can have serious performance implications and can take a long time to execute if many keys exist in the database. This operation can lead to high memory and CPU usage, and should be used with caution, especially in production environments.

Load all general objects from the database using bulk loading for efficiency.

Load the account associated with the given account ID (if found).

Load all accounts from the database.

Load the state for the given actor.

Load all cache data from the database.

Load all currencies from the database using bulk loading for efficiency.

Load the currency associated with the given currency code (if found).

Load the order to execution client index from the database.

Load the order to position index from the database.

Load the instrument associated with the given instrument ID (if found).

Load all instruments from the database using bulk loading for efficiency.

Load the order associated with the given client order ID (if found).

Load all orders from the database.

Load the position associated with the given ID (if found).

Load all positions from the database.

Load the state for the given strategy.

Load the synthetic instrument associated with the given synthetic instrument ID (if found).

Load all synthetic instruments from the database using bulk loading for efficiency.

Snapshot the state of the given order.

Snapshot the state of the given position.

Update the given account in the database.

Update the given actor state in the database.

Update the given order in the database.

Update the given position in the database.

Update the given strategy state in the database.

Provides a read-only facade for the common Cache.

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

Abstract method (implement in subclass).

---

## Data

**URL:** https://nautilustrader.io/docs/latest/api_reference/model/data

**Contents:**
- Data
  - class Bar​
    - bar_type​
    - close​
    - static from_dict(dict values) → Bar​
    - static from_pyo3(pyo3_bar) → Bar​
    - static from_pyo3_list(list pyo3_bars) → list[Bar]​
    - static from_raw(BarType bar_type, PriceRaw open, PriceRaw high, PriceRaw low, PriceRaw close, uint8_t price_prec, QuantityRaw volume, uint8_t size_prec, uint64_t ts_event, uint64_t ts_init) → Bar​
    - static from_raw_arrays_to_list(BarType bar_type, uint8_t price_prec, uint8_t size_prec, double[:] opens, double[:] highs, double[:] lows, double[:] closes, double[:] volumes, uint64_t[:] ts_events, uint64_t[:] ts_inits) → list[Bar]​
    - classmethod fully_qualified_name(cls) → str​

Bar(BarType bar_type, Price open, Price high, Price low, Price close, Quantity volume, uint64_t ts_event, uint64_t ts_init, bool is_revision=False) -> None

Represents an aggregated bar.

Return the bar type of bar.

Return the close price of the bar.

Return a bar parsed from the given values.

Return a legacy Cython bar converted from the given pyo3 Rust object.

Return legacy Cython bars converted from the given pyo3 Rust objects.

Return the fully qualified name for the Data class.

Return the high price of the bar.

If this bar is a revision for a previous bar with the same ts_event.

Determine if the current class is a signal type, optionally checking for a specific signal name.

If the OHLC are all equal to a single price.

Return the low price of the bar.

Return the open price of the bar.

Return a dictionary representation of this object.

Return a pyo3 object from this legacy Cython instance.

Return pyo3 Rust bars converted from the given legacy Cython objects.

UNIX timestamp (nanoseconds) when the data event occurred.

UNIX timestamp (nanoseconds) when the object was initialized.

Return the volume of the bar.

Returns self, the complex conjugate of any int.

Number of bits necessary to represent self in binary.

Number of ones in the binary representation of the absolute value of self.

Also known as the population count.

Return an array of bytes representing an integer.

length : Length of bytes object to use. An OverflowError is raised if the integer is not representable with the given number of bytes. Default is length 1.

byteorder : The byte order used to represent the integer. If byteorder is ‘big’, the most significant byte is at the beginning of the byte array. If byteorder is ‘little’, the most significant byte is at the end of the byte array. To request the native byte order of the host system, use sys.byteorder as the byte order value. Default is to use ‘big’.

signed : Determines whether two’s complement is used to represent the integer. If signed is False and a negative integer is given, an OverflowError is raised.

Return the integer represented by the given array of bytes.

bytes : Holds the array of bytes to convert. The argument must either support the buffer protocol or be an iterable object producing bytes. Bytes and bytearray are examples of built-in objects that support the buffer protocol.

byteorder : The byte order used to represent the integer. If byteorder is ‘big’, the most significant byte is at the beginning of the byte array. If byteorder is ‘little’, the most significant byte is at the end of the byte array. To request the native byte order of the host system, use sys.byteorder as the byte order value. Default is to use ‘big’.

signed : Indicates whether two’s complement is used to represent the integer.

Return a pair of integers, whose ratio is equal to the original int.

The ratio is in lowest terms and has a positive denominator.

Returns True. Exists for duck type compatibility with float.is_integer.

the real part of a complex number

the imaginary part of a complex number

the numerator of a rational number in lowest terms

the denominator of a rational number in lowest terms

Returns self, the complex conjugate of any int.

Number of bits necessary to represent self in binary.

Number of ones in the binary representation of the absolute value of self.

Also known as the population count.

Return an array of bytes representing an integer.

length : Length of bytes object to use. An OverflowError is raised if the integer is not representable with the given number of bytes. Default is length 1.

byteorder : The byte order used to represent the integer. If byteorder is ‘big’, the most significant byte is at the beginning of the byte array. If byteorder is ‘little’, the most significant byte is at the end of the byte array. To request the native byte order of the host system, use sys.byteorder as the byte order value. Default is to use ‘big’.

signed : Determines whether two’s complement is used to represent the integer. If signed is False and a negative integer is given, an OverflowError is raised.

Return the integer represented by the given array of bytes.

bytes : Holds the array of bytes to convert. The argument must either support the buffer protocol or be an iterable object producing bytes. Bytes and bytearray are examples of built-in objects that support the buffer protocol.

byteorder : The byte order used to represent the integer. If byteorder is ‘big’, the most significant byte is at the beginning of the byte array. If byteorder is ‘little’, the most significant byte is at the end of the byte array. To request the native byte order of the host system, use sys.byteorder as the byte order value. Default is to use ‘big’.

signed : Indicates whether two’s complement is used to represent the integer.

Return a pair of integers, whose ratio is equal to the original int.

The ratio is in lowest terms and has a positive denominator.

Returns True. Exists for duck type compatibility with float.is_integer.

the real part of a complex number

the imaginary part of a complex number

the numerator of a rational number in lowest terms

the denominator of a rational number in lowest terms

BarSpecification(int step, BarAggregation aggregation, PriceType price_type) -> None

Represents a bar aggregation specification that defines how market data should be aggregated into bars (candlesticks).

A bar specification consists of three main components:

Bar specifications are used to define different types of bars:

Time-based bars: Aggregate data over fixed time intervals

Tick-based bars: Aggregate data after a certain number of ticks

Volume-based bars: Aggregate data after a certain volume threshold

Value-based bars: Aggregate data after a certain dollar value threshold

Information-based bars: Advanced aggregation based on information flow

The specification determines:

Return the aggregation for the specification.

Check if the given aggregation is an information-based aggregation type.

Information-based aggregation creates bars based on market microstructure patterns and sequential runs of similar market events. These bars capture information flow and market efficiency patterns by detecting sequences of directionally similar price movements or trading activity.

Information-based aggregation types include:

Runs are sequences of consecutive events with the same directional property (e.g., consecutive upticks or downticks). This aggregation method is useful for analyzing market microstructure, information flow, and detecting patterns in high-frequency trading activity.

This differs from time-based aggregation (fixed intervals) and threshold-based aggregation (activity levels), focusing instead on sequential patterns and information content of market events.

Check if the given aggregation is a threshold-based aggregation type.

Threshold-based aggregation creates bars when accumulated market activity reaches predefined thresholds, providing activity-driven sampling rather than time-driven sampling. These bars capture market dynamics based on actual trading patterns and volumes.

Threshold-based aggregation types include:

This differs from time-based aggregation which creates bars at fixed time intervals, and information-based aggregation which creates bars based on market microstructure patterns and runs.

Check if the given aggregation is a time-based aggregation type.

Time-based aggregation creates bars at fixed time intervals, where each bar represents market data for a specific time period. These bars are emitted when the time interval expires, regardless of trading activity level.

Time-based aggregation types include:

This is distinct from threshold-based aggregation (TICK, VOLUME, VALUE) which creates bars when activity thresholds are reached, and information-based aggregation (RUNS) which creates bars based on market microstructure patterns.

Return a bar specification parsed from the given string.

Parameters: value (str) – The bar specification string to parse.

Return type: BarSpecification

Raises: ValueError – If value is not a valid string.

Return a bar specification parsed from the given timedelta and price_type.

Return type: BarSpecification

Raises: ValueError – If duration is not rounded step of aggregation.

Return the interval length in nanoseconds for time-based bar specifications.

Converts the bar specification’s time interval to nanoseconds based on its aggregation type and step size. This method is used for time calculations and (TODO: bar alignment).

Return a value indicating whether the aggregation method is information-driven.

Information-based aggregation creates bars based on market microstructure patterns and sequential runs of similar market events. This aggregation method captures information flow, market efficiency patterns, and the sequential nature of trading activity by detecting directional runs.

Information-based aggregation types supported:

A “run” is a sequence of consecutive market events with the same directional or categorical property. For example, a tick run might be 5 consecutive upticks followed by 3 consecutive downticks.

Information-based bars are ideal for:

This differs from time-based aggregation (fixed time intervals) and threshold-based aggregation (activity levels), focusing instead on the sequential information content and patterns within market events.

Get timedelta for time-based bars:

Return a value indicating whether the aggregation method is threshold-based.

Threshold-based aggregation types trigger bar creation when cumulative activity reaches predefined levels, making them ideal for volume and value-driven analysis rather than time-based intervals.

Threshold-Based Aggregation Types

Activity threshold types supported:

Imbalance threshold types supported:

Threshold-based bars are ideal for:

This differs from time-based aggregation (fixed time intervals) and information-based aggregation (information content patterns), focusing instead on measurable activity and participation thresholds.

check_threshold_aggregated : Static method for threshold aggregation checking

is_time_aggregated : Check for time-based aggregation

is_information_aggregated : Check for information-based aggregation

Return a value indicating whether the aggregation method is time-driven.

Time-based aggregation creates bars at fixed time intervals based on calendar or clock time, providing consistent temporal sampling of market data. Each bar covers a specific time period regardless of trading activity level.

Time-based aggregation types supported:

Time-based bars are ideal for:

This differs from threshold aggregation (volume/tick-based) which creates bars when activity levels are reached, and information aggregation which creates bars based on market microstructure patterns.

is_threshold_aggregated : Check for threshold-based aggregation

is_information_aggregated : Check for information-based aggregation

Return the price type for the specification.

Return the step size for the specification.

Return the timedelta for the specification.

BarType(InstrumentId instrument_id, BarSpecification bar_spec, AggregationSource aggregation_source=AggregationSource.EXTERNAL) -> None

Represents a bar type including the instrument ID, bar specification and aggregation source.

Return the aggregation source for the bar type.

Return a bar type parsed from the given string.

Return the instrument ID for the bar type.

Return a value indicating whether the bar type corresponds to BarType::Composite in Rust.

Return a value indicating whether the bar aggregation source is EXTERNAL.

Return a value indicating whether the bar aggregation source is INTERNAL.

Return a value indicating whether the bar type corresponds to BarType::Standard in Rust.

Return the specification for the bar type.

BookOrder(OrderSide side, Price price, Quantity size, uint64_t order_id) -> None

Represents an order in a book.

Return the total exposure for this order (price * size).

Return an order from the given dict values.

Return an book order from the given raw values.

Return the book orders side.

Return the book orders price.

Return the book orders side.

Return the signed size of the order (negative for SELL).

Return the book orders size.

Return a dictionary representation of this object.

CustomData(DataType data_type, Data data) -> None

Provides a wrapper for custom data which includes data type information.

Return the fully qualified name for the Data class.

Determine if the current class is a signal type, optionally checking for a specific signal name.

UNIX timestamp (nanoseconds) when the data event occurred.

UNIX timestamp (nanoseconds) when the object was initialized.

DataType(type type, dict metadata=None) -> None

Represents a data type including metadata.

This class may be used as a key in hash maps throughout the system, thus the key and value contents of metadata must themselves be hashable.

The data types metadata.

The data types topic string.

The Data type of the data.

FundingRateUpdate(InstrumentId instrument_id, rate, uint64_t ts_event, uint64_t ts_init, next_funding_ns=None) -> None

Represents a funding rate update for a perpetual swap instrument.

Return a funding rate update from the given dict values.

Return a legacy Cython funding rate update converted from the given pyo3 Rust object.

Return legacy Cython funding rate updates converted from the given pyo3 Rust objects.

Return the fully qualified name for the Data class.

The instrument ID for the funding rate.

Determine if the current class is a signal type, optionally checking for a specific signal name.

UNIX timestamp (nanoseconds) of the next funding payment (if available, otherwise zero).

The current funding rate.

Return a dictionary representation of this object.

UNIX timestamp (nanoseconds) when the data event occurred.

UNIX timestamp (nanoseconds) when the object was initialized.

IndexPriceUpdate(InstrumentId instrument_id, Price value, uint64_t ts_event, uint64_t ts_init) -> None

Represents an index price update.

Return an index price from the given dict values.

Return a legacy Cython index price converted from the given pyo3 Rust object.

Return legacy Cython index prices converted from the given pyo3 Rust objects.

Return the fully qualified name for the Data class.

Return the instrument ID.

Determine if the current class is a signal type, optionally checking for a specific signal name.

Return a dictionary representation of this object.

Return a pyo3 object from this legacy Cython instance.

Return pyo3 Rust index prices converted from the given legacy Cython objects.

UNIX timestamp (nanoseconds) when the data event occurred.

UNIX timestamp (nanoseconds) when the object was initialized.

InstrumentClose(InstrumentId instrument_id, Price close_price, InstrumentCloseType close_type, uint64_t ts_event, uint64_t ts_init) -> None

Represents an instrument close at a venue.

The instrument close price.

The instrument close type.

Return an instrument close price event from the given dict values.

Return a legacy Cython instrument close converted from the given pyo3 Rust object.

Return legacy Cython instrument closes converted from the given pyo3 Rust objects.

Return the fully qualified name for the Data class.

The event instrument ID.

Determine if the current class is a signal type, optionally checking for a specific signal name.

Return a dictionary representation of this object.

Return a pyo3 object from this legacy Cython instance.

Return pyo3 Rust index prices converted from the given legacy Cython objects.

UNIX timestamp (nanoseconds) when the data event occurred.

UNIX timestamp (nanoseconds) when the instance was created.

InstrumentStatus(InstrumentId instrument_id, MarketStatusAction action, uint64_t ts_event, uint64_t ts_init, str reason=None, str trading_event=None, is_trading: bool | None = None, is_quoting: bool | None = None, is_short_sell_restricted: bool | None = None) -> None

Represents an event that indicates a change in an instrument market status.

The instrument market status action.

Return an instrument status update from the given dict values.

Return a legacy Cython quote tick converted from the given pyo3 Rust object.

Return legacy Cython instrument status converted from the given pyo3 Rust objects.

Return the fully qualified name for the Data class.

Return the state of quoting in the instrument (if known).

Return the state of short sell restrictions for the instrument (if known and applicable).

Determine if the current class is a signal type, optionally checking for a specific signal name.

Return the state of trading in the instrument (if known).

Additional details about the cause of the status change.

Return a dictionary representation of this object.

Return a pyo3 object from this legacy Cython instance.

Further information about the status change (if provided).

UNIX timestamp (nanoseconds) when the data event occurred.

UNIX timestamp (nanoseconds) when the instance was created.

MarkPriceUpdate(InstrumentId instrument_id, Price value, uint64_t ts_event, uint64_t ts_init) -> None

Represents a mark price update.

Return a mark price from the given dict values.

Return a legacy Cython mark price converted from the given pyo3 Rust object.

Return legacy Cython trades converted from the given pyo3 Rust objects.

Return the fully qualified name for the Data class.

Return the instrument ID.

Determine if the current class is a signal type, optionally checking for a specific signal name.

Return a dictionary representation of this object.

Return a pyo3 object from this legacy Cython instance.

Return pyo3 Rust mark prices converted from the given legacy Cython objects.

UNIX timestamp (nanoseconds) when the data event occurred.

UNIX timestamp (nanoseconds) when the object was initialized.

OrderBookDelta(InstrumentId instrument_id, BookAction action, BookOrder order: BookOrder | None, uint8_t flags, uint64_t sequence, uint64_t ts_event, uint64_t ts_init) -> None

Represents a single update/difference on an OrderBook.

Return the deltas book action {ADD, UPDATE, DELETE, CLEAR}

Return an order book delta which acts as an initial CLEAR.

Return the flags for the delta.

Return an order book delta from the given dict values.

Return a legacy Cython order book delta converted from the given pyo3 Rust object.

Return legacy Cython order book deltas converted from the given pyo3 Rust objects.

Return an order book delta from the given raw values.

Return the fully qualified name for the Data class.

Return the deltas book instrument ID.

If the deltas book action is an ADD.

If the deltas book action is a CLEAR.

If the deltas book action is a DELETE.

Determine if the current class is a signal type, optionally checking for a specific signal name.

If the deltas book action is an UPDATE.

Return the deltas book order for the action.

Return the sequence number for the delta.

Return a dictionary representation of this object.

Return pyo3 Rust order book deltas converted from the given legacy Cython objects.

UNIX timestamp (nanoseconds) when the data event occurred.

UNIX timestamp (nanoseconds) when the object was initialized.

OrderBookDeltas(InstrumentId instrument_id, list deltas) -> None

Represents a batch of OrderBookDelta updates for an OrderBook.

Groups the given list of OrderBookDelta records into batches, creating OrderBookDeltas objects when an F_LAST flag is encountered.

The method iterates through the data list and appends each OrderBookDelta to the current batch. When an F_LAST flag is found, it indicates the end of a batch. The batch is then appended to the list of completed batches and a new batch is started.

UserWarning : If there are remaining deltas in the final batch after the last F_LAST flag.

Return the contained deltas.

Return the flags for the last delta.

Return order book deltas from the given dict values.

Return the fully qualified name for the Data class.

Return the deltas book instrument ID.

Determine if the current class is a signal type, optionally checking for a specific signal name.

If the deltas is a snapshot.

Return the sequence number for the last delta.

Return a dictionary representation of this object.

Return a pyo3 object from this legacy Cython instance.

UNIX timestamp (nanoseconds) when the data event occurred.

UNIX timestamp (nanoseconds) when the object was initialized.

OrderBookDepth10(InstrumentId instrument_id, list bids, list asks, list bid_counts, list ask_counts, uint8_t flags, uint64_t sequence, uint64_t ts_event, uint64_t ts_init) -> None

Represents a self-contained order book update with a fixed depth of 10 levels per side.

Return the count of ask orders level for the update.

Return the ask orders for the update.

Return the count of bid orders per level for the update.

Return the bid orders for the update.

Return the flags for the depth update.

Return order book depth from the given dict values.

Return a legacy Cython order book depth converted from the given pyo3 Rust object.

Return legacy Cython order book depths converted from the given pyo3 Rust objects.

Return the fully qualified name for the Data class.

Return the depth updates book instrument ID.

Determine if the current class is a signal type, optionally checking for a specific signal name.

Return the sequence number for the depth update.

Return a dictionary representation of this object.

Return a QuoteTick created from the top of book levels.

Returns None when the top-of-book bid or ask is missing or invalid (NULL order or zero size).

UNIX timestamp (nanoseconds) when the data event occurred.

UNIX timestamp (nanoseconds) when the object was initialized.

QuoteTick(InstrumentId instrument_id, Price bid_price, Price ask_price, Quantity bid_size, Quantity ask_size, uint64_t ts_event, uint64_t ts_init) -> None

Represents a single quote tick in a market.

Contains information about the best top-of-book bid and ask.

Return the top-of-book ask price.

Return the top-of-book ask size.

Return the top-of-book bid price.

Return the top-of-book bid size.

Extract the price for the given price type.

Extract the size for the given price type.

Return a quote tick parsed from the given values.

Return a legacy Cython quote tick converted from the given pyo3 Rust object.

Return legacy Cython quotes converted from the given pyo3 Rust objects.

Return a quote tick from the given raw values.

Return the fully qualified name for the Data class.

Return the tick instrument ID.

Determine if the current class is a signal type, optionally checking for a specific signal name.

Return a dictionary representation of this object.

Return a pyo3 object from this legacy Cython instance.

Return pyo3 Rust quotes converted from the given legacy Cython objects.

UNIX timestamp (nanoseconds) when the data event occurred.

UNIX timestamp (nanoseconds) when the object was initialized.

TradeTick(InstrumentId instrument_id, Price price, Quantity size, AggressorSide aggressor_side, TradeId trade_id, uint64_t ts_event, uint64_t ts_init) -> None

Represents a single trade tick in a market.

Contains information about a single unique trade which matched buyer and seller counterparties.

Return the ticks aggressor side.

Return a trade tick from the given dict values.

Return a legacy Cython trade tick converted from the given pyo3 Rust object.

Return legacy Cython trades converted from the given pyo3 Rust objects.

Return a trade tick from the given raw values.

Return the fully qualified name for the Data class.

Return the ticks instrument ID.

Determine if the current class is a signal type, optionally checking for a specific signal name.

Return the ticks price.

Return the ticks size.

Return a dictionary representation of this object.

Return a pyo3 object from this legacy Cython instance.

Return pyo3 Rust trades converted from the given legacy Cython objects.

Return the ticks trade match ID.

UNIX timestamp (nanoseconds) when the data event occurred.

UNIX timestamp (nanoseconds) when the object was initialized.

**Examples:**

Example 1 (pycon):
```pycon
>>> bin(37)'0b100101'>>> (37).bit_length()6
```

Example 2 (pycon):
```pycon
>>> bin(13)'0b1101'>>> (13).bit_count()3
```

Example 3 (pycon):
```pycon
>>> (10).as_integer_ratio()(10, 1)>>> (-10).as_integer_ratio()(-10, 1)>>> (0).as_integer_ratio()(0, 1)
```

Example 4 (pycon):
```pycon
>>> bin(37)'0b100101'>>> (37).bit_length()6
```

---

## Data

**URL:** https://nautilustrader.io/docs/latest/api_reference/data

**Contents:**
- Data
- Aggregation​
  - class BarAggregator​
    - bar_type​
    - handle_bar(self, Bar bar) → void​
    - handle_quote_tick(self, QuoteTick tick) → void​
    - handle_trade_tick(self, TradeTick tick) → void​
    - is_running​
    - start_batch_update(self, handler: Callable[[Bar], None], uint64_t time_ns) → None​
    - stop_batch_update(self) → None​

The data subpackage groups components relating to the data stack and data tooling for the platform.

The layered architecture of the data stack somewhat mirrors the execution stack with a central engine, cache layer beneath, database layer beneath, with alternative implementations able to be written on top.

Due to the high-performance, the core components are reusable between both backtest and live implementations - helping to ensure consistent logic for trading operations.

BarAggregator(Instrument instrument, BarType bar_type, handler: Callable[[Bar], None]) -> None

Provides a means of aggregating specified bars and sending to a registered handler.

The aggregators bar type.

Update the aggregator with the given bar.

Update the aggregator with the given tick.

Update the aggregator with the given tick.

BarBuilder(Instrument instrument, BarType bar_type) -> None

Provides a generic bar builder for aggregation.

Return the aggregated bar with the given closing timestamp, and reset.

Return the aggregated bar and reset.

The builders current update count.

If the builder is initialized.

The price precision for the builders instrument.

Reset the bar builder.

All stateful fields are reset to their initial value.

The size precision for the builders instrument.

UNIX timestamp (nanoseconds) when the builder last updated.

Update the bar builder.

Update the bar builder.

RenkoBarAggregator(Instrument instrument, BarType bar_type, handler: Callable[[Bar], None]) -> None

Provides a means of building Renko bars from ticks.

Renko bars are created when the price moves by a fixed amount (brick size) regardless of time or volume. Each bar represents a price movement equal to the step size in the bar specification.

The aggregators bar type.

Update the aggregator with the given bar.

Update the aggregator with the given tick.

Update the aggregator with the given tick.

TickBarAggregator(Instrument instrument, BarType bar_type, handler: Callable[[Bar], None]) -> None

Provides a means of building tick bars from ticks.

When received tick count reaches the step threshold of the bar specification, then a bar is created and sent to the handler.

The aggregators bar type.

Update the aggregator with the given bar.

Update the aggregator with the given tick.

Update the aggregator with the given tick.

TimeBarAggregator(Instrument instrument, BarType bar_type, handler: Callable[[Bar], None], Clock clock, str interval_type=’left-open’, bool timestamp_on_close=True, bool skip_first_non_full_bar=False, bool build_with_no_updates=True, time_bars_origin_offset: pd.Timedelta | pd.DateOffset = None, int bar_build_delay=0) -> None

Provides a means of building time bars from ticks with an internal timer.

When the time reaches the next time interval of the bar specification, then a bar is created and sent to the handler.

The aggregators bar type.

Return the start time for the aggregators next bar.

Update the aggregator with the given bar.

Update the aggregator with the given tick.

Update the aggregator with the given tick.

The aggregators time interval.

The aggregators time interval.

The aggregators next closing time.

Stop the bar aggregator.

ValueBarAggregator(Instrument instrument, BarType bar_type, handler: Callable[[Bar], None]) -> None

Provides a means of building value bars from ticks.

When received value reaches the step threshold of the bar specification, then a bar is created and sent to the handler.

The aggregators bar type.

Return the current cumulative value of the aggregator.

Update the aggregator with the given bar.

Update the aggregator with the given tick.

Update the aggregator with the given tick.

VolumeBarAggregator(Instrument instrument, BarType bar_type, handler: Callable[[Bar], None]) -> None

Provides a means of building volume bars from ticks.

When received volume reaches the step threshold of the bar specification, then a bar is created and sent to the handler.

The aggregators bar type.

Update the aggregator with the given bar.

Update the aggregator with the given tick.

Update the aggregator with the given tick.

DataClient(ClientId client_id, MessageBus msgbus, Cache cache, Clock clock, Venue venue: Venue | None = None, config: NautilusConfig | None = None)

The base class for all data clients.

This class should not be used directly, but through a concrete subclass.

Degrade the component.

While executing on_degrade() any exception will be logged and reraised, then the component will remain in a DEGRADING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Dispose of the component.

While executing on_dispose() any exception will be logged and reraised, then the component will remain in a DISPOSING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Calling this method multiple times has the same effect as calling it once (it is idempotent). Once called, it cannot be reversed, and no other methods should be called on this instance.

While executing on_fault() any exception will be logged and reraised, then the component will remain in a FAULTING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Return the fully qualified name for the components class.

If the client is connected.

Return whether the current component state is DEGRADED.

Return whether the current component state is DISPOSED.

Return whether the current component state is FAULTED.

Return whether the component has been initialized (component.state >= INITIALIZED).

Return whether the current component state is RUNNING.

Return whether the current component state is STOPPED.

Request data for the given data type.

All stateful fields are reset to their initial value.

While executing on_reset() any exception will be logged and reraised, then the component will remain in a RESETTING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Resume the component.

While executing on_resume() any exception will be logged and reraised, then the component will remain in a RESUMING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Initiate a system-wide shutdown by generating and publishing a ShutdownSystem command.

The command is handled by the system’s NautilusKernel, which will invoke either stop (synchronously) or stop_async (asynchronously) depending on the execution context and the presence of an active event loop.

While executing on_start() any exception will be logged and reraised, then the component will remain in a STARTING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Return the components current state.

While executing on_stop() any exception will be logged and reraised, then the component will remain in a STOPPING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Subscribe to data for the given data type.

Return the custom data types subscribed to.

The trader ID associated with the component.

Unsubscribe from data for the given data type.

The clients venue ID (if applicable).

MarketDataClient(ClientId client_id, MessageBus msgbus, Cache cache, Clock clock, Venue venue: Venue | None = None, config: NautilusConfig | None = None)

The base class for all market data clients.

This class should not be used directly, but through a concrete subclass.

Degrade the component.

While executing on_degrade() any exception will be logged and reraised, then the component will remain in a DEGRADING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Dispose of the component.

While executing on_dispose() any exception will be logged and reraised, then the component will remain in a DISPOSING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Calling this method multiple times has the same effect as calling it once (it is idempotent). Once called, it cannot be reversed, and no other methods should be called on this instance.

While executing on_fault() any exception will be logged and reraised, then the component will remain in a FAULTING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Return the fully qualified name for the components class.

If the client is connected.

Return whether the current component state is DEGRADED.

Return whether the current component state is DISPOSED.

Return whether the current component state is FAULTED.

Return whether the component has been initialized (component.state >= INITIALIZED).

Return whether the current component state is RUNNING.

Return whether the current component state is STOPPED.

Request data for the given data type.

Request historical Bar data. To load historical data from a catalog, you can pass a list[DataCatalogConfig] to the TradingNodeConfig or the BacktestEngineConfig.

Request Instrument data for the given instrument ID.

Request all Instrument data for the given venue.

Request order book snapshot data.

Request historical QuoteTick data.

Request historical TradeTick data.

All stateful fields are reset to their initial value.

While executing on_reset() any exception will be logged and reraised, then the component will remain in a RESETTING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Resume the component.

While executing on_resume() any exception will be logged and reraised, then the component will remain in a RESUMING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Initiate a system-wide shutdown by generating and publishing a ShutdownSystem command.

The command is handled by the system’s NautilusKernel, which will invoke either stop (synchronously) or stop_async (asynchronously) depending on the execution context and the presence of an active event loop.

While executing on_start() any exception will be logged and reraised, then the component will remain in a STARTING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Return the components current state.

While executing on_stop() any exception will be logged and reraised, then the component will remain in a STOPPING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Subscribe to data for the given data type.

Subscribe to Bar data for the given bar type.

Subscribe to FundingRateUpdate data for the given instrument ID.

Subscribe to IndexPriceUpdate data for the given instrument ID.

Subscribe to the Instrument with the given instrument ID.

Subscribe to InstrumentClose updates for the given instrument ID.

Subscribe to InstrumentStatus data for the given instrument ID.

Subscribe to all Instrument data.

Subscribe to MarkPriceUpdate data for the given instrument ID.

Subscribe to OrderBookDeltas data for the given instrument ID.

Subscribe to OrderBookDepth10 data for the given instrument ID.

Subscribe to OrderBook snapshots data for the given instrument ID.

Subscribe to QuoteTick data for the given instrument ID.

Subscribe to TradeTick data for the given instrument ID.

Return the bar types subscribed to.

Return the custom data types subscribed to.

Return the funding rate update instruments subscribed to.

Return the index price update instruments subscribed to.

Return the instrument closes subscribed to.

Return the status update instruments subscribed to.

Return the instruments subscribed to.

Return the mark price update instruments subscribed to.

Return the order book delta instruments subscribed to.

Return the order book snapshot instruments subscribed to.

Return the quote tick instruments subscribed to.

Return the trade tick instruments subscribed to.

The trader ID associated with the component.

Unsubscribe from data for the given data type.

Unsubscribe from Bar data for the given bar type.

Unsubscribe from FundingRateUpdate data for the given instrument ID.

Unsubscribe from IndexPriceUpdate data for the given instrument ID.

Unsubscribe from Instrument data for the given instrument ID.

Unsubscribe from InstrumentClose data for the given instrument ID.

Unsubscribe from InstrumentStatus data for the given instrument ID.

Unsubscribe from all Instrument data.

Unsubscribe from MarkPriceUpdate data for the given instrument ID.

Unsubscribe from OrderBookDeltas data for the given instrument ID.

Unsubscribe from OrderBookDepth10 data for the given instrument ID.

Unsubscribe from OrderBook snapshots data for the given instrument ID.

Unsubscribe from QuoteTick data for the given instrument ID.

Unsubscribe from TradeTick data for the given instrument ID.

The clients venue ID (if applicable).

The DataEngine is the central component of the entire data stack.

The data engines primary responsibility is to orchestrate interactions between the DataClient instances, and the rest of the platform. This includes sending requests to, and receiving responses from, data endpoints via its registered data clients.

The engine employs a simple fan-in fan-out messaging pattern to execute DataCommand type messages, and process DataResponse messages or market data objects.

Alternative implementations can be written on top of the generic engine - which just need to override the execute, process, send and receive methods.

DataEngine(MessageBus msgbus, Cache cache, Clock clock, config: DataEngineConfig | None = None) -> None

Provides a high-performance data engine for managing many DataClient instances, for the asynchronous ingest of data.

Check all of the engines clients are connected.

Check all of the engines clients are disconnected.

The total count of data commands received by the engine.

Connect the engine by calling connect on all registered clients.

The total count of data stream objects received by the engine.

If debug mode is active (will provide extra debug logging).

Return the default data client registered with the engine.

Degrade the component.

While executing on_degrade() any exception will be logged and reraised, then the component will remain in a DEGRADING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Deregister the given data client from the data engine.

Disconnect the engine by calling disconnect on all registered clients.

Dispose of the component.

While executing on_dispose() any exception will be logged and reraised, then the component will remain in a DISPOSING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Execute the given data command.

Calling this method multiple times has the same effect as calling it once (it is idempotent). Once called, it cannot be reversed, and no other methods should be called on this instance.

While executing on_fault() any exception will be logged and reraised, then the component will remain in a FAULTING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Return the fully qualified name for the components class.

Returns the configured external client order IDs.

Return whether the current component state is DEGRADED.

Return whether the current component state is DISPOSED.

Return whether the current component state is FAULTED.

Return whether the component has been initialized (component.state >= INITIALIZED).

Return whether the current component state is RUNNING.

Return whether the current component state is STOPPED.

Process the given data.

Register the given data catalog with the engine.

Register the given data client with the data engine.

Register the given client as the default routing client (when a specific venue routing cannot be found).

Any existing default routing client will be overwritten.

Register the given client to route messages to the given venue.

Any existing client in the routing map for the given venue will be overwritten.

Return the execution clients registered with the engine.

Handle the given request.

The total count of data requests received by the engine.

All stateful fields are reset to their initial value.

While executing on_reset() any exception will be logged and reraised, then the component will remain in a RESETTING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Handle the given response.

The total count of data responses received by the engine.

Resume the component.

While executing on_resume() any exception will be logged and reraised, then the component will remain in a RESUMING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

dict[Venue, DataClient]

Return the default data client registered with the engine.

Initiate a system-wide shutdown by generating and publishing a ShutdownSystem command.

The command is handled by the system’s NautilusKernel, which will invoke either stop (synchronously) or stop_async (asynchronously) depending on the execution context and the presence of an active event loop.

While executing on_start() any exception will be logged and reraised, then the component will remain in a STARTING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Return the components current state.

While executing on_stop() any exception will be logged and reraised, then the component will remain in a STOPPING state.

If the component is not in a valid state from which to execute this method, then the component state will not change, and an error will be logged.

Stop the registered clients.

Return the bar types subscribed to.

Return the custom data types subscribed to.

Return the funding rate update instruments subscribed to.

Return the index price update instruments subscribed to.

Return the close price instruments subscribed to.

Return the status update instruments subscribed to.

Return the instruments subscribed to.

Return the mark price update instruments subscribed to.

Return the order book delta instruments subscribed to.

Return the order book snapshot instruments subscribed to.

Return the quote tick instruments subscribed to.

Return the synthetic instrument quotes subscribed to.

Return the synthetic instrument trades subscribed to.

Return the trade tick instruments subscribed to.

The trader ID associated with the component.

DataCommand(DataType data_type, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

The base class for all data commands.

This class should not be used directly, but through a concrete subclass.

The data client ID for the command.

The command data type.

The command message ID.

Additional specific parameters for the command.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

DataResponse(ClientId client_id: ClientId | None, Venue venue: Venue | None, DataType data_type, data, UUID4 correlation_id, UUID4 response_id, uint64_t ts_init, datetime start, datetime end, dict params: dict | None = None) -> None

Represents a response with data.

The data client ID for the response.

The response correlation ID.

The response data type.

The end datetime (UTC) of response time range.

The response message ID.

Additional specific parameters for the response.

The start datetime (UTC) of response time range (inclusive).

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the response.

RequestBars(BarType bar_type, datetime start: datetime | None, datetime end: datetime | None, int limit, ClientId client_id: ClientId | None, Venue venue: Venue | None, callback: Callable[[Any], None], UUID4 request_id, uint64_t ts_init, dict params: dict | None) -> None

Represents a request for bars.

The bar type for the request.

The callback for the response.

The data client ID for the request.

The request data type.

The end datetime (UTC) of request time range.

The request message ID.

The instrument ID for the request.

The limit on the amount of data to return for the request.

Additional specific parameters for the command.

The start datetime (UTC) of request time range (inclusive).

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the request.

RequestData(DataType data_type, InstrumentId instrument_id: InstrumentId | None, datetime start: datetime | None, datetime end: datetime | None, int limit, ClientId client_id: ClientId | None, Venue venue: Venue | None, callback: Callable[[Any], None], UUID4 request_id, uint64_t ts_init, dict params: dict | None) -> None

Represents a request for data.

The callback for the response.

The data client ID for the request.

The request data type.

The end datetime (UTC) of request time range.

The request message ID.

The instrument ID for the request.

The limit on the amount of data to return for the request.

Additional specific parameters for the command.

The start datetime (UTC) of request time range (inclusive).

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the request.

RequestInstrument(InstrumentId instrument_id, datetime start: datetime | None, datetime end: datetime | None, ClientId client_id: ClientId | None, Venue venue: Venue | None, callback: Callable[[Any], None], UUID4 request_id, uint64_t ts_init, dict params: dict | None) -> None

Represents a request for an instrument.

The callback for the response.

The data client ID for the request.

The request data type.

The end datetime (UTC) of request time range.

The request message ID.

The instrument ID for the request.

The limit on the amount of data to return for the request.

Additional specific parameters for the command.

The start datetime (UTC) of request time range (inclusive).

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the request.

RequestInstruments(datetime start: datetime | None, datetime end: datetime | None, ClientId client_id: ClientId | None, Venue venue: Venue | None, callback: Callable[[Any], None], UUID4 request_id, uint64_t ts_init, dict params: dict | None) -> None

Represents a request for instruments.

The callback for the response.

The data client ID for the request.

The request data type.

The end datetime (UTC) of request time range.

The request message ID.

The instrument ID for the request.

The limit on the amount of data to return for the request.

Additional specific parameters for the command.

The start datetime (UTC) of request time range (inclusive).

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the request.

RequestOrderBookDepth(InstrumentId instrument_id, datetime start: datetime | None, datetime end: datetime | None, int limit, int depth, ClientId client_id: ClientId | None, Venue venue: Venue | None, callback: Callable[[Any], None], UUID4 request_id, uint64_t ts_init, dict params: dict | None) -> None

Represents a request for historical OrderBookDepth10 data.

The callback for the response.

The data client ID for the request.

The request data type.

The maximum depth for the order book depths.

The end datetime (UTC) of request time range.

The request message ID.

The instrument ID for the request.

The limit on the amount of data to return for the request.

Additional specific parameters for the command.

The start datetime (UTC) of request time range (inclusive).

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the request.

RequestOrderBookSnapshot(InstrumentId instrument_id, int limit, ClientId client_id: ClientId | None, Venue venue: Venue | None, callback: Callable[[Any], None], UUID4 request_id, uint64_t ts_init, dict params: dict | None) -> None

Represents a request for an order book snapshot.

The callback for the response.

The data client ID for the request.

The request data type.

The end datetime (UTC) of request time range.

The request message ID.

The instrument ID for the request.

The limit on the amount of data to return for the request.

Additional specific parameters for the command.

The start datetime (UTC) of request time range (inclusive).

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the request.

RequestQuoteTicks(InstrumentId instrument_id, datetime start: datetime | None, datetime end: datetime | None, int limit, ClientId client_id: ClientId | None, Venue venue: Venue | None, callback: Callable[[Any], None], UUID4 request_id, uint64_t ts_init, dict params: dict | None) -> None

Represents a request for quote ticks.

The callback for the response.

The data client ID for the request.

The request data type.

The end datetime (UTC) of request time range.

The request message ID.

The instrument ID for the request.

The limit on the amount of data to return for the request.

Additional specific parameters for the command.

The start datetime (UTC) of request time range (inclusive).

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the request.

RequestTradeTicks(InstrumentId instrument_id, datetime start: datetime | None, datetime end: datetime | None, int limit, ClientId client_id: ClientId | None, Venue venue: Venue | None, callback: Callable[[Any], None], UUID4 request_id, uint64_t ts_init, dict params: dict | None) -> None

Represents a request for trade ticks.

The callback for the response.

The data client ID for the request.

The request data type.

The end datetime (UTC) of request time range.

The request message ID.

The instrument ID for the request.

The limit on the amount of data to return for the request.

Additional specific parameters for the command.

The start datetime (UTC) of request time range (inclusive).

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the request.

SubscribeBars(BarType bar_type, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to subscribe to bars for an instrument.

The bar type for the subscription.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

Convert this subscribe message to a request message.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

SubscribeData(DataType data_type, InstrumentId instrument_id: InstrumentId | None, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to subscribe to data.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

Convert this subscribe message to a request message.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

SubscribeFundingRates(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to subscribe to funding rates.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

Convert this subscribe message to a request message.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

SubscribeIndexPrices(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to subscribe to index prices.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

Convert this subscribe message to a request message.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

SubscribeInstrument(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to subscribe to an instrument.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

Convert this subscribe message to a request message.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

SubscribeInstrumentClose(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to subscribe to the close of an instrument.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

Convert this subscribe message to a request message.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

SubscribeInstrumentStatus(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to subscribe to the status of an instrument.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

Convert this subscribe message to a request message.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

SubscribeInstruments(ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to subscribe to all instruments of a venue.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

Convert this subscribe message to a request message.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

SubscribeMarkPrices(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to subscribe to mark prices.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

Convert this subscribe message to a request message.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

SubscribeOrderBook(InstrumentId instrument_id, type book_data_type, BookType book_type, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, int depth=0, bool managed=True, int interval_ms=0, dict params: dict | None = None) -> None

Represents a command to subscribe to order book deltas for an instrument.

The data client ID for the command.

The command data type.

The maximum depth for the subscription.

The command message ID.

The instrument ID for the subscription.

The order book snapshot interval in milliseconds (must be positive for snapshots).

If an order book should be managed by the data engine based on the subscribed feed.

Additional specific parameters for the command.

Convert this subscribe message to a request message.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

SubscribeQuoteTicks(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to subscribe to quote ticks.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

Convert this subscribe message to a request message.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

SubscribeTradeTicks(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to subscribe to trade ticks.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

Convert this subscribe message to a request message.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

Bases: UnsubscribeData

UnsubscribeBars(BarType bar_type, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to unsubscribe from bars for an instrument.

The bar type for the subscription.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

UnsubscribeData(DataType data_type, InstrumentId instrument_id: InstrumentId | None, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to unsubscribe to data.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

Bases: UnsubscribeData

UnsubscribeFundingRates(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to unsubscribe from funding rates for an instrument.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

Bases: UnsubscribeData

UnsubscribeIndexPrices(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to unsubscribe from index prices for an instrument.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

Bases: UnsubscribeData

UnsubscribeInstrument(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to unsubscribe to an instrument.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

Bases: UnsubscribeData

UnsubscribeInstrumentClose(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to unsubscribe from instrument close for an instrument.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

Bases: UnsubscribeData

UnsubscribeInstrumentStatus(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to unsubscribe from instrument status.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

Bases: UnsubscribeData

UnsubscribeInstruments(ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to unsubscribe to all instruments.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

Bases: UnsubscribeData

UnsubscribeMarkPrices(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to unsubscribe from mark prices for an instrument.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

Bases: UnsubscribeData

UnsubscribeOrderBook(InstrumentId instrument_id, type book_data_type, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to unsubscribe from order book updates for an instrument.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

Bases: UnsubscribeData

UnsubscribeQuoteTicks(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to unsubscribe from quote ticks for an instrument.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

Bases: UnsubscribeData

UnsubscribeTradeTicks(InstrumentId instrument_id, ClientId client_id: ClientId | None, Venue venue: Venue | None, UUID4 command_id, uint64_t ts_init, dict params: dict | None = None) -> None

Represents a command to unsubscribe from trade ticks for an instrument.

The data client ID for the command.

The command data type.

The command message ID.

The instrument ID for the subscription.

Additional specific parameters for the command.

UNIX timestamp (nanoseconds) when the object was initialized.

The venue for the command.

---

