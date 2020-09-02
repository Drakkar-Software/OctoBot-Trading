# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.10.1] - 2020-09-02
### Fixed
- [Exchange] Error logger typing issue
- [OrderState] Multiple open order updates

### Updated
- [OrderState] Raise exceptions in finalize

## [1.10.0] - 2020-09-01
### Added
- [Orders] Integrate async job
- [Order] is_to_be_maintained

### Updated
- [OrderState] Disable cancel and close synchronization with exchange
- [ClosedOrdersUpdater] Disable temporary

### Fixed
- [Orders] double order state refresh
- [Orders] portfolio refresh
- [Orders] double order creation channel push
- [Orders] double order state refresh
- [Trader] cancelled order status
- [OrderState] force filling
- [OpenOrders] no call to check missing
- [FillOrderState] ignored filled order
- [CancelOrderState] missing notification when not using trader
- [OpenOrderState] missing creation Orders Channel notification

## [1.9.4] - 2020-08-23
### Fixed
- [Orders] Fix average price handling

## [1.9.3] - 2020-08-23
### Fixed
- [Portfolio] Portfolio refresh issues

## [1.9.2] - 2020-08-22
### Fixed
- [OrderState] Tests double fill

## [1.9.1] - 2020-08-15
### Fixed
- [OrderState] Tests async loop error

## [1.9.0] - 2020-08-15
### Added
- OrderState implementation : manage order synchronization for OPEN, FILL, CANCEL and CLOSE status

## [1.8.10] - 2020-07-24
### Fixed
- OHLCV Updater exchange spamming

## [1.8.9] - 2020-07-24
### Updated
- [API] Move cancel_ccxt_throttle_task in exchange API

## [1.8.8] - 2020-07-19
### Updated
- [Real Trading] Multiple fixes to enable real trading

## [1.8.7] - 2020-06-30
### Updated
- [WebsocketExchange] Adaptations for Binance websocket
### Fixed
- [MarkPrice] Fix mark price initialization when recent trades arrive at first

## [1.8.6] - 2020-06-29
### Fixed
- [SymbolDataAPI] Fix missing mark price source argument in force_set_mark_price

## [1.8.5] - 2020-06-28
### Updated
- [PricesManager] Mark price is now only based on recent trades (except if not available : ticker)

## [1.8.4] - 2020-06-28
### Added
- [Exchanges] Handle exchange tentacles activation

## [1.8.3] - 2020-06-27
### Added
- [Order] Synchronizing after creation on exchange
- [Order] Handling filled and cancelled events from exchange

### Fixed
- [OHLCVUpdater] Initialization exchange spam

## [1.8.2] - 2020-06-19
### Updated
- Requirements

## [1.8.1] - 2020-06-15
### Updated
- Order super calls

## [1.8.0] - 2020-06-13
### Added
- New Order types support : Trailing stop, Trailing stop limit, Take profit, Take profit limit
### Updated
- Order fill and post fill refactor
### Fixed
- Tests silent exceptions

## [1.7.2] - 2020-06-01
### Added
- PriceEventManager
### Updated
- Optimize MarketStatusFixer

## [1.7.1] - 2020-05-27
### Updated
- Cython version

## [1.7.0] - 2020-05-25
### Updated
- Order close by cancel and fill processes

## [1.6.24] - 2020-05-22
### Removed
- Book data class, moved in order_book_manager

## [1.6.23] - 2020-05-22
### Updated
- Migrate order tests
- Refactor book data class

### Removed
- Pandas requirement

## [1.6.22] - 2020-05-21
### Updated
- Remove advanced manager from commons

## [1.6.21] - 2020-05-20
### Updated
- [API] Candles API

## [1.6.20] - 2020-05-19
### Fixed
- [Channels] Trading channels issues
- [DataManagers] Trading data issues

## [1.6.19] - 2020-05-19
### Updated
- [API] Order and trading registration API

## [1.6.18] - 2020-05-17
### Fixed
- [ExchangeMarketStatusFixer] Header

## [1.6.17] - 2020-05-17
### Fixed
- [RestExchange] C typing and add debug logs

## [1.6.16] - 2020-05-16
### Fixed
- [ExchangePersonalData] Kwarg argument

## [1.6.15] - 2020-05-16
### Fixed
- [RestExchange] Candle since timestamp

## [1.6.14] - 2020-05-16
### Updated
- Requirements

## [1.6.13] - 2020-05-16
### Updated
- [Exchanges] Tested exchanges list

### Fixed
- [RealTrading] Fix real trading orders workflow issues

## [1.6.12] - 2020-05-16
### Updated
- [ExchangeSimulator] Time manager call

## [1.6.11] - 2020-05-16
### Updated
- [ExchangeSimulator] Move time_frames and symbols to set

## [1.6.10] - 2020-05-16
### Updated
- [Channels] Exchange channels optimization

## [1.6.9] - 2020-05-11
### Fixed
- [Backtesting] Multiple data files handling

## [1.6.8] - 2020-05-10
### Fixed
- [Cython] Headers

## [1.6.7] - 2020-05-10
### Update
- [Backtesting] Multiple optimizations

### Fixed
- [Backtesting] Profitability and recent trades management

## [1.6.6] - 2020-05-09
### Added
- [Consumers] OctoBot channel

## [1.6.5] - 2020-05-08
### Updated
- [Requirements] update requirements

## [1.6.4] - 2020-05-08
### Added
- [API] is_mark_price_initialized

### Updated
- [ExchangeSimulator] Always display at least one candle data

## [1.6.3] - 2020-05-06
### Fixed
- [Simulators] Time consumer cython declaration

## [1.6.2] - 2020-05-05
### Fixed
- [OHLCVUpdater] Retry candle history loading
- [AbstractModeConsumer] Error handling

## [1.6.1] - 2020-05-02
### Added
- [Channel] Synchronization support

### Fixed
- [RestExchange] ccxt sandbox mode support

## [1.6.0] - 2020-04-30
### Updated
- Use centralized backtesting in exchange simulator

## [1.5.7] - 2020-04-30
### Updated
- Use object in trading modes final_eval

## [1.5.6] - 2020-04-30
### Updated
- Use str states in trading modes channels

## [1.5.5] - 2020-04-30
### Updated
- OctoBot-Commons update

## [1.5.4] - 2020-04-30
### Fixed
- [OrderAdapter] fix math.nan handling

## [1.5.3] - 2020-04-28
### Added
- [Exchanges] exchange current time API and in construction candles

### Updated
- [Trading modes] trading modes migration
- [Memory management] improve post-backtesting memory clear

## [1.5.2] - 2020-04-25
### Updated
- [CandleManager] Commons shift usage
- [ExchangeFactory] Tests

## [1.5.1] - 2020-04-17
### Added
- [ModeChannel] data param to consumers callback
- [ModeChannel] consumer filtering by state

### Fixed
- [AbstractModeProducer] Matrix channel subscription

## [1.5.0] - 2020-04-13
### Added
- [ExchangeChannel] Cryptocurrency param to channels callbacks

## [1.4.27] - 2020-04-10
### Added
- [ExchangeChannel] TimeFrameExchangeChannel class

### Fixed
- [Channel] time frame filter

### Updated
- symbols_by_crypto_currencies instead of currencies in exchanges

## [1.4.26] - 2020-04-08
### Fixed
- CandleManager cython headers
- AbstractModeConsumer cython headers

## [1.4.25] - 2020-04-08
### Removed
- AbstractTradingMode cythonization

## [1.4.24] - 2020-04-08
### Fixed
- Cython headers

## [1.4.23] - 2020-04-07
### Fixed
- Wildcard imports

## [1.4.22] - 2020-04-06
### Added
- [Channels] 
  - Book Ticker
  - Mini Ticker
  - Liquidations
- [Websocket] keep alive

## [1.4.21] - 2020-04-05
### Updated
- Integrate OctoBot-tentacles-manager 2.0.0

## [1.4.20] - 2020-04-04
### Added
- [Exchanges] account management (CASH, MARGIN, FUTURE)

### Updated
- [Future trading] Position parsing improvements
- [Exchanges] Improve keys error handling
- Bump ccxt version with DrakkarSoftware fixes

### Removed
- OctoBot-Websocket requirement

## [1.4.19] - 2020-02-24
### Added
- Stop ExchangeManager when an error occurs at build stage

### Updated
- Optimize candles management
- Use compact logger.exception format
- Improve Kline error management
 
### Fixed
- CandleManager max candles handling

## [1.4.18] - 2020-02-14
### Added
- TradeFactory

### Updated
- ExchangeManager stop handling
- exchange, mode, portfolio, profitability, symbol_data, trades APIs

### Fixed
- Profitability bugs

## [1.4.17] - 2020-01-19
### Changed
- ExchangeFactory to ExchangeBuilder

### Fixed
- Order missing add_linked_order method

## [1.4.16] - 2020-01-18
### Added
- get_exchange_id_from_matrix_id and get_exchange_ids in APIs
- Handle matrix_id in ExchangeConfiguration

### Updated
- ExchangeFactory can now use matrix_id
- Use exchange_id in exchange channels

## [1.4.15] - 2020-01-18
### Added
- Candle missing data filter

### Fixed
- Candles first index data was missing

## [1.4.14] - 2020-01-12
### Added
- Cryptocurrency management in evaluators
- APIs for exchanges, trading modes, orders, portfolio, profitability, symbol data, trader, trades
- get_total_paid_fees in trades manager
- cancel_order_with_id in trader

### Updated
- handle_order_update now always notifies orders channel

### Fixed
- get_name from trading modes

## [1.4.13] - 2020-01-05
### Added
- Exchange ID in ExchangeChannels notifications

## [1.4.12] - 2020-01-05
### Added
- ExchangeManager generated ID attribute
- Order factory methods

### Changed
- Trader adapted from OctoBot legacy
- Order attributes from OctoBot legacy

### Updated
**Requirements**
- Commons version to 1.2.2
- Channels version to 1.3.19
- colorlog version to 4.1.0

## [1.4.11] - 2019-12-21
### Added
- Exchange create tentacle path parameter

### Updated
**Requirements**
- Commons version to 1.2.0
- Channels version to 1.3.17ccxt
- Backtesting version to 1.3.2
- Websockets version to 1.1.7
- ccxt version to 1.21.6
- scipy version to 1.4.1

## [1.4.10] - 2019-12-14
### Fixed
- ExchangeMarketStatusFixer cython compatilibity

## [1.4.9] - 2019-12-17
### Added
- Makefile

### Fixed
- ExchangeSymbolData symbol_candles and symbol_klines visibility to public
- CandleManager incompatible static method

## [1.4.8] - 2019-12-14
### Fixed
- Removed CCXT find_market method

## [1.4.7] - 2019-12-14
### Updated
**Requirements**
- Commons version to 1.1.51
- Channels version to 1.3.6
- Backtesting version to 1.3.1
- Websockets version to 1.1.6
- ccxt version to 1.20.80
- ccxt version to 1.20.80
- scipy version to 1.3.3

## [1.4.6] - 2019-11-19
### Fixed
- Updaters connection loss support

## [1.4.5] - 2019-11-07
## Fixed
- OHLCV simulator timestamp management

## [1.4.4] - 2019-10-30
## Added
- OSX support

## [1.4.3] - 2019-09-14
## Added
- Price Channel
- Price Manager
- Mark price updater (price reference for a symbol)

## [1.4.2] - 2019-09-13
## Changed
- Moved __init__ constants declaration to constants

## [1.4.1] - 2019-09-10
## Added
- PyPi manylinux deployment

## [1.4.0] - 2019-09-10
### Added
- Simulator for backtesting support
- Pause and resume management for updaters
- Exchange config

### Changed
- Setup install

### Fixed
- Trader config and risk
- Ticker updater
- Websocket management
- Cython compilation & runtime
- Orders management

## [1.3.1-alpha] - 2019-09-02
### Added
- Exchange global access through Exchanges singleton

### Fixed
- Trader enabled method call in __init__

## [1.3.0-alpha] - 2019-09-01
### Added
- Trading mode implementation

## [1.2.0-alpha] - 2019-08-01
### Added
- New channels : Position, BalanceProfitability
- CLI improvements

### Changed
- Order channel : added is_closed boolean param

### Fixes
- Trader : 
    - Order creation
    - Portfolio

## [1.1.0-alpha] - 2019-06-10
### Added
- Data class that stores personal data
- Data management classes that manage personal and symbol data stored
- Exchange Channels from OctoBot-Channel
- Basis of CLI interface
- Demo file
- Backtesting classes from OctoBot

### Removed
- Exchange dispatcher

## [1.0.1-alpha] - 2019-05-27
### Added
- Updaters & Simulators (Producers)
- Orders management
