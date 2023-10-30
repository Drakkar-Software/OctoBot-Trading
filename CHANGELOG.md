# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.39] - 2023-10-30
### Fixed
- [Config] Realtime timeframe issues

## [2.4.38] - 2023-10-29
### Fixed
- [Config] handle malformed pairs in get_all_currencies

## [2.4.37] - 2023-10-27
### Added
- [API] get_candles_as_list

## [2.4.36] - 2023-10-24
### Added
- [Stats] skip history on simulated trading

## [2.4.35] - 2023-10-18
### Added
- [TradingModes] add are_initialization_orders_pending

## [2.4.34] - 2023-10-15
### Added
- [Orders] add ALLOW_SIMULATED_ORDERS_INSTANT_FILL env var
- [Backtesting] handle accurate price timeframe when available

## [2.4.33] - 2023-10-11
### Updated
- [TradingModes] Missing funds log

## [2.4.32] - 2023-10-11
### Added
- [TradingModes] Portfolio optimization basis

## [2.4.31] - 2023-10-04
### Added
- [Signals] Sorting
### Updated
- [Orders] Chained orders creation issues log
### Fixed
- [Orders] Rare filled order crash

## [2.4.30] - 2023-09-26
### Updated
- [Storage] increase storage update interval

## [2.4.29] - 2023-09-25
### Updated
- [Storage] push open orders

## [2.4.28] - 2023-09-24
### Updated
- [Trades] push USD-like volume

## [2.4.27] - 2023-09-12
### Fixed
- [Orders] get_split_orders_count_and_increment: take exchange precision into account

## [2.4.26] - 2023-09-07
### Fixed
- [PNL] Division error
- [Exchanges] Stop issues

## [2.4.25] - 2023-09-05
### Updated
- [Signals] set UPDATE_WITH_TRIGGERING_ORDER_FEES

## [2.4.24] - 2023-09-03
### Updated
- [Backtesting] use local time channel name

## [2.4.23] - 2023-09-01
### Fixed
- [ExchangeData] format

## [2.4.22] - 2023-09-01
### Added
- [Credentials] warning when sandboxed exchange in credential check
### Updated
- [Tickers] ensure seconds in timestamp

## [2.4.21] - 2023-08-30
### Added
- [Trades] exchange side trade id handling
- [Trades] trades aggregate by order id
### Updated
- [Orders] raise AuthenticationError on missing trading permissions

## [2.4.20] - 2023-08-25
### Updated
- [Dataclasses] use FlexibleDataclass

## [2.4.19] - 2023-08-23
### Updated
- [Exchanges] support info and parsed forced markets

## [2.4.18] - 2023-08-17
### Updated
- [CCXT] to version 4.0.65
### Fixed
- [Storage] handle corrupted db files auto fix

## [2.4.17] - 2023-08-16
### Added
- [Orders] %s and %t amounts
### Fixed
- [Backtesting] fees on small amounts

## [2.4.16] - 2023-08-14
### Fixed
- [Exchanges] unwanted market status load

## [2.4.15] - 2023-08-14
### Updated
- [Backtesting] handle forced market statuses
### Fixed
- [Exchanges] randomness in symbols processing

## [2.4.14] - 2023-08-07
### Updated
- [PortfolioStorage] update profitability

## [2.4.13] - 2023-08-05
### Updated
- [Orders][TradingMode] Improve flexibility
- logs clarity

## [2.4.12] - 2023-07-28
### Updated
- [Orders] include minimal info in storage

## [2.4.11] - 2023-07-26
### Fixed
- [Portfolio] simulated portfolio history load

## [2.4.10] - 2023-07-24
### Updated
- [ExchangeData] default value and typing

## [2.4.9] - 2023-07-23
### Updated
- [Tests] testing tools
- [TradingModes] logs on minimum trading volumes
### Fixed
- [Websockets] Reconnection issues

## [2.4.8] - 2023-07-08
### Fixed
- [Positions] Contracts live update

## [2.4.7] - 2023-07-07
### Added
- [Positions] Log error on hedged positions

## [2.4.6] - 2023-07-05
### Fixed
- [API] is_trader_existing_and_enabled

## [2.4.5] - 2023-07-03
### Added
- Full stop loss support for supporting exchanges
- Binance futures support
- MEXC support
### Updated
- Improved futures trading related error messages
- Position and orders update request policy: now retry once before giving up and falling back to the next update cycle
- Improved orders logs
### Fixed
- Positions sync issues when order are instantly filled
- Positions duplicate issues
- Futures trading non-future symbols related errors
- Decimal division by zero error when building signals

## [2.4.4] - 2023-06-08
### Fixed
- Orders sync issues
- Order sizing issues when using % param

## [2.4.3] - 2023-05-12
### Updated
- Use orders shared if for pnl
### Fixed
- Chained orders in trading signals

## [2.4.2] - 2023-05-10
### Added
- Display timeframe
- Quote denominated amount in trading modes settings
### Updated
- Orders API
### Fixed
- Order storage typing issues
- Chained orders trading signals issues

## [2.4.1] - 2023-05-05
### Fixed
- Real order chained orders pnl

## [2.4.0] - 2023-05-02
### Updated
- Supported python versions
### Removed
- Cython

## [2.3.39] - 2023-04-26
### Updated
- [Websockets] improve exchange reconnect 

## [2.3.38] - 2023-04-25
### Updated
- [Websockets] exchange reconnect 

## [2.3.37] - 2023-04-21
### Updated
- [CCXT] bump to version 3.0.74 
- [Exchanges] handle authentication requiring exchanges (coinbase)
### Fixed
- [Orders] Orders creation related issues
- [Websockets] Candles warning spam

## [2.3.36] - 2023-04-17
### Updated
- [Websockets] Handle partially managed timeframes
- [TradingModes] Order creation errors explanations 
### Fixed
- [Websockets] Error spam
- [PortfolioHistory] Invalid saved value

## [2.3.35] - 2023-03-30
### Added
- [Orders] historical orders update
### Updated
- [OrdersChannel] add update_type

## [2.3.34] - 2023-03-27
### Updated
- [Exchanges] Inherit AbstractTentacle
### Fixed
- [PNL] Invalid orders error

## [2.3.33] - 2023-03-24
### Fixed
- [Orders] Reading typing

## [2.3.32] - 2023-03-23
### Fixed
- [Orders] default_exchange_update_order_status type error

## [2.3.31] - 2023-03-23
### Fixed
- [Profitability] missing price warning

## [2.3.30] - 2023-03-22
### Added
- [PNL] accurate fees
- [API] price convertor
### Fixed
- [ExchangeRequests] handle time sync issue in each request

## [2.3.29] - 2023-03-20
### Fixed
- [OrderStorage] fix saved orders typing

## [2.3.28] - 2023-03-19
### Fixed
- [PortfolioValue] trading pairs origin price computation

## [2.3.27] - 2023-03-16
### Added
- [Portfolio] indirect currency valuation
### Fixed
- [Portfolio] price initialisation

## [2.3.26] - 2023-03-15
### Added
- [Orders] storage system to keep track of groups, chained orders, entries and tags
- [Exchanges] support for crypto.com
### Updated
- [Exchanges] fees checking to ensure closed order fees availability
### Fixed
- [PNL] PNL when entry is a sell order

## [2.3.25] - 2023-03-09
### Added
- [Exchanges] get_leverage_tiers 
### Updated
[Market Status] Allow missing price limits
### Fixed
- [Funding] Skip funding fetch on spot pairs

## [2.3.24] - 2023-03-03
### Added
- [PNL] TradesPNL system
- [Futures] Margin mode API
- [Positions] Active positions can now be awaited
- [Orders] Accurate cancel order error management
### Updated
- [Orders] Better order synchronization from exchange 
- [Community] Optimize auth storage 
- [CCXT] to ccxt==2.8.4 
### Fixed
- [Orders] Cancel order error 
- [Websocket] Rare on-disconnect crash 
- [Futures] Funding issues

## [2.3.23] - 2023-02-17
### Fixed
- [Cython] Header

## [2.3.22] - 2023-02-16
### Fixed
- [Exchange] Infinite loop error

## [2.3.21] - 2023-02-14
### Fixed
- [Portfolio] Non trading exchanges portfolio errors

## [2.3.20] - 2023-02-13
### Fixed
- [CCXT] Don't clear throttler queue on close

## [2.3.19] - 2023-02-12
### Updated
- [Memory] Improve memory management

## [2.3.18] - 2023-02-11
### Fixed
- [Orders] Restore portfolio refresh of exchange missing funds error

## [2.3.17] - 2023-02-11
### Added
- [History] Now save and load portfolio and trades history
### Updated
- [OrdersManager] Handle since and until params
- [Errors] Improve error management

## [2.3.16] - 2023-02-05
### Added
- [API] get_exchange_backtesting_time_window
### Updated
- [Order groups] Handled pending cancel orders
- [Trading modes] Wait for open orders init before trading

## [2.3.15] - 2023-01-30
### Updated
- [FuturesTrading] Make contract error more understandable

## [2.3.14] - 2023-01-30
### Updated
- [Exchanges] Remove kline warning, replace it by debug log

## [2.3.13] - 2023-01-27
### Updated
- [Exchanges] Improve futures support
- [Websockets] Reconnect error management

## [2.3.12] - 2023-01-25
### Fixed
- [Websockets] Recreate a full ccxt client on reconnection

## [2.3.11] - 2023-01-23
### Fixed
- [Websockets] Reconnection on long lasting connections

## [2.3.10] - 2023-01-18
### Fixed
- [Ticker] Simulated ticker

## [2.3.9] - 2023-01-18
### Added
- [Storage] Add authenticated data call on portfolio and trades update

## [2.3.8] - 2023-01-15
### Fixed
- [CandlesManager] Typing issue

## [2.3.7] - 2023-01-11
### Updated
- [Orders] Properly handle pending creation orders for exchanges that work this way (ex: bybit)
### Fixed
- [Orders] Initial open order fetch timeout error### Fixed
- [Adapters] Ticker, OHLCV and order issues

## [2.3.6] - 2023-01-09
### Added
- [Config] Log trading mode and exchange config on load
### Updated
- [Exchanges] Migrate from cryptofeed to ccxt_pro for websocket exchanges

## [2.3.5] - 2023-01-06
### Updated
- [Exchanges] Refactor exchanges to simplify into rest exchange, connectors and adapters

## [2.3.4] - 2023-01-02
### Updated
- [CCXT] bump to 2.4.60

## [2.3.3] - 2023-01-01
### Updated
- [API] add exchange data getter

## [2.3.2] - 2022-12-28
### Updated
- [CandlesManager] do not use cython memory view
### Fixed
- [PreloadedCandlesManager] typing issues

## [2.3.1] - 2022-12-24
### Added
- [TradingMode] cache and plot clear methods

## [2.3.0] - 2022-12-23
### Added
- [Trader] backtesting optimizations
### Updated
- [Requirements] Bump

## [2.2.37] - 2022-12-13
### Fixed
- [Trader] cancel order TypeError

## [2.2.36] - 2022-12-10
### Updated
- [PortfolioHistory] store at the end of the backtest only

## [2.2.35] - 2022-12-08
### Added
- [Orders] custom price in quantity computation

## [2.2.34] - 2022-12-08
### Added
- [Orders] handling of pending cancel state
### Updated
- [CCXT] to 2.2.84

## [2.2.33] - 2022-12-06
### Fixed
- Position entry price on first update
- Cleared order exchange synchronization

### Updated
- CI spot tests to binanceus and future tests to bybit
- Renamed `get_symbol_positions` to `get_position`

## [2.2.32] - 2022-11-28
### Updated
- exchanges API

## [2.2.31] - 2022-11-22
### Added
- Trading mode order quantity user input

## [2.2.30] - 2022-11-19
### Updated
- trading modes API

## [2.2.29] - 2022-11-11
### Fixed
- Stop loss related crash

## [2.2.28] - 2022-11-01
### Fixed
- Order decimal rounding

## [2.2.27] - 2022-10-31
### Fixed
- Send signal on order group callbacks

## [2.2.26] - 2022-10-31
### Updated
- Cryptofeed version

## [2.2.25] - 2022-10-23
### Added
- Environment variables for ccxt common options

## [2.2.24] - 2022-10-28
### Added
- get minimal order amount
### Fixed
- portfolio attribute error

## [2.2.23] - 2022-10-23
### Fixed
- trading mode user inputs

## [2.2.22] - 2022-10-20
### Added
- close position api
- trading signal emission on close position and cancel order api call
### Updated
- cryptofeed version
### Fixed
- crash when computing historical portfolio

## [2.2.21] - 2022-10-16
### Fixed
- Fees computation on future

## [2.2.20] - 2022-10-15
### Fixed
- Fees computation on spot

## [2.2.19] - 2022-10-15
### Fixed
- Signals use identifier instead of strategy

## [2.2.18] - 2022-10-12
### Added
- Exchange manager debug info

## [2.2.17] - 2022-10-12
### Added
- User inputs support
- Run storages
- Futures trading symbols handling
### Updated
- CCXT

## [2.2.16] - 2022-09-13
No change, pypi issue version

## [2.2.15] - 2022-09-12
### Fixed
- [Orders] creation time

## [2.2.14] - 2022-09-11
### Fixed
- [Futures trading] minimal order size on futures

## [2.2.13] - 2022-09-09
### Fixed
- [Futures trading] multiple issues and error messages

## [2.2.12] - 2022-09-02
### Fixed
- [Signals] fix push issues

## [2.2.11] - 2022-08-31
### Fixed
- [Exchanges] kwargs usage and attributes visibility

## [2.2.10] - 2022-08-23
### Fixed
- [Supports] Fix use support call

## [2.2.9] - 2022-08-22
### Updated
- [Trading signals] Use signals from octobot-commons

## [2.2.8] - 2022-08-08
### Updated
- [Trading signals] Signals format
### Fixed
- [Websockets] Multiple issues
- [TradingModes] Decimal related issues

## [2.2.7] - 2022-07-02
### Updated
- [Supports] Associate supports to futures trading instead of websockets
- [Futures] Automatically select contract types in simulator mode
- [Symbols] Update for symbol object

## [2.2.6] - 2022-06-12
### Fixes
- [Exchanges] Backtesting KeyError on OHLCV simulator

## [2.2.5] - 2022-06-06
### Updated
- [Exchanges] Supported exchanges

## [2.2.4] - 2022-06-04
### Fixes
- [Cython] Fix header files

## [2.2.3] - 2022-05-24
### Fixes
- [Cython] Fix header files

## [2.2.2] - 2022-05-21
### Fixes
- [Exchanges] Fix crash on compiled exchanges init

## [2.2.1] - 2022-05-16
### Updated
- [Orders] Order total
### Fixes
- [Contracts] Fix inverse contracts issues

## [2.2.0] - 2022-05-07
### Added
- [Trading mode] Scripted trading mode system
- [Orders] Chained orders
- [Portfolio] Historical portfolio values
- [Signals] Trading signals

## [2.1.2] - 2022-02-05
### Fixed
- [PricesManager] Fix mark price float issue

## [2.1.1] - 2022-01-22
### Added
- [Asset] Add restore state when raising PortfolioNegativeError
- [Position] Add get_margin_from_size and get_size_from_margin

### Fixed
- [ExchangePersonalData] Deduct funding fee from the position margin when no sufficient available balance

## [2.1.0] - 2022-01-18
### Added
- [Exchange] hollaex support
- [MarkPrice] Decimal conversion
- [FutureCCXTExchange] is_linear_pair and is_inverse_pair
- [FutureExchange] contract initialization
- [FutureContract] maintenance_margin_rate
- [FutureExchange] position mode parsing
- [FutureExchange] is_inverse, is_linear and is_futures
- [PositionsManager] both position side in position id
- [FutureContract] `__str__`
- [PositionsManager] get_symbol_positions with None symbol
- [API] positions
- [CCXTExchanges] get_default_type
- [Position] initial_margin and fee_to_close in _update
- [Trader] close position, set_margin_type, set_leverage and set_position_mode
- [MarginContract] check_leverage_update
- [Transaction] class
- [TransactionsManager] class
- [TransactionsManager] factory
- [TransactionsManager] transfer, blockchain, fee and realised_pnl

### Fixed
- [Positions] missing mark_price fetching
- [Positions] Prevent negative margin
- [LinearPosition] liquidation price calculation
- [Position] liquidation PNL total impact
- [FuturePortfolio] order available decreasing size release

### Removed
- [FutureExchange] "open" position references
- [Portfolio] inheritance
- [Portfolio] unused async

## [2.0.0] - 2022-01-15
### Added
- [CryptofeedWebsocketConnector] future index feed
- [CryptofeedWebsocketConnector] sandbox support
- [FutureExchangeSimulator] default leverage and margin_type values
- [Future][Exchange] get_contract_type
- [Contracts] MarginContract
- [Portfolio] Asset class
- [Portfolio] spot, margin and future assets
- [Portfolio] create_currency_asset
- [MarginAsset] implementation
- [FutureAsset] implementation
- [FundingManager] predicted_funding_rate
- [FundingChannel] predicted_funding_rate
- [Position] LiquidationState creation when liquidation detected
- [Position] size attribute from quantity
- [Positions] InversePosition and LinearPosition (from cross and isolated)
- [Position] Notional value update
- [LiquidatePositionState] terminate implementation
- [MarginContract] set_current_leverage
- [FutureContract] PositionMode
- [FutureExchange] PositionMode
- [FuturePortfolio] update_portfolio_from_liquidated_position
- [Position] close method
- [Order] get_position_side
- [Positions] multiple position per symbol support
- [FutureContract] is_one_way_position_mode
- [ExchangePersonalData] reduce only and close position when filling order
- [PositionsManager] get_order_position
- [Position] get_quantity_to_close and get_update_quantity_from_order
- [Position] close when size after update is ZERO
- [Position] InvalidOperation catching
- [Asset] _ensure_not_negative
- [Position] on_pnl_update
- [ExchangePersonalData] handle_portfolio_update_from_funding

### Updated
- FutureContract Moved to exchange_data
- Moved Asset methods to SpotAsset
- [MarginContract] Made margin_type and current_leverage writable
- [Portfolio] Migrated to assets
- [Portfolio] Migrated to get_currency_portfolio

### Fixed
- [ExchangeSymbolData] FundingManager when future

### Removed
- [Order] get_currency_and_market

## [1.14.2] - 2021-11-23
### Fixed
- Orders: fees related typing issues

## [1.14.1] - 2021-11-18
### Added
- AbstractSupervisor and AbstractPortfolioSupervisor classes
- [Websocket] Order callback implementation
- [Websocket] Pair independent channels

### Updated
- [Websocket] Update cryptofeed integration to 2.1.0

### Fixed
- [OrderAdapter] Digit precision

## [1.14.0] - 2021-09-20
### Added
- ExchangeWrapper class
- [Websocket] Do not start when nothing to watch

### Updated
- [Websocket] Update cryptofeed integration to 2.0.0

### Removed
- CLI

## [1.13.23] - 2021-09-19
### Fixed
- [Trades] Handle trades from canceled orders
- [Orders] Handle orders with None price data

## [1.13.22] - 2021-09-16
### Fixed
- [Orders] Improve order parsing when no order type is available

## [1.13.21] - 2021-09-14
### Fixed
- [Websockets] Watched symbols subscribe issues

## [1.13.20] - 2021-09-13
### Fixed
- [Websockets] Subscribe issue

## [1.13.19] - 2021-09-12
### Fixed
- [Orders] Parsing issue
- [Trader] set_risk api

## [1.13.18] - 2021-09-10
### Updated
- [TradesManager] Increase max trade history from 500 to 100000

## [1.13.17] - 2021-09-9
### Fixed
- [Websockets] feed subscription

## [1.13.16] - 2021-09-08
### Fixed
- Typing issues

## [1.13.15] - 2021-09-08
### Fixed
- [Websockets] watched pairs

## [1.13.14] - 2021-09-08
### Added
- [Websockets] watched pairs
### Updated
- [Orders] use decimal.Decimal instead of floats
- [Portfolio] use decimal.Decimal instead of floats

## [1.13.13] - 2021-08-30
### Added
- [Exchange Manager] exchange subaccount
- [CCXTExchange] exchange subaccount list

### Updated
- [CCXTExchange] order precision and limits when required

### Removed
- [Order Manager] Order limit

## [1.13.12] - 2021-08-25
### Added
- [CCXTExchange] options and headers setters

## [1.13.11] - 2021-08-11
### Fixed
- Exchanges: added available_required_time_frames

## [1.13.10] - 2021-08-11
### Fixed
- Clear method in websocket exchanges

## [1.13.9] - 2021-08-09
### Added
- Clear method in websocket exchanges

## [1.13.8] - 2021-08-08
### Updated
- Supported exchanges

## [1.13.7] - 2021-08-08
### Added
- Mark price from ticker feed

### Updated
- Cryptofeed logs to devnull

### Fixed
- fetchOrder not supported

## [1.13.6] - 2021-08-07
### Fixed
- Error log url

## [1.13.5] - 2021-08-05
### Added
- Cryptofeed Websocket authenticated feeds basis

### Fixed
- [Portfolio] race condition
- [Position] multiple fixes

## [1.13.4] - 2021-07-21
### Updated
- [Exchanges] handle supporters authentication

### Fixed
- [Exchanges] optimize websockets initialization and pairs addition

## [1.13.3] - 2021-07-13
### Updated
- [Exchanges] add is_valid_account on api

## [1.13.2] - 2021-07-12
### Updated
- Requirements

## [1.13.1] - 2021-07-09
### Added
- [Exchanges] add exchange details on api

### Updated
- [Websockets] Optimize websockets usage

## [1.13.0] - 2021-06-26
### Added
- [Exchanges] trading-backend integration

### Updated
- [Future] Position management
- [Future] Migrate PositionUpdater to AsyncJob
- [Future] Position Channel

## [1.12.19] - 2021-06-04
### Updated
- [Exchanges][WS] properly log error messages

## [1.12.18] - 2021-06-03
### Fixed
- [Exchanges][WS] handle unsupported candles and timeframes

## [1.12.17] - 2021-06-01
### Fixed
- [Exchanges][WS] candles init
- [Channels] timeframe typing in consumers filtering

## [1.12.16] - 2021-05-31
### Fixed
- [Exchanges][WS] async callback async declaration
- [Exchanges][WS] stop and close

## [1.12.15] - 2021-05-30
### Fixed
- [Exchanges][WS] Fix CryptofeedWebsocketConnector cython declaration

## [1.12.14] - 2021-05-30
### Fixed
- [Exchanges][API] Consider websockets in overloaded computations

## [1.12.13] - 2021-05-30
### Fixed
- [Exchanges][CryptoFeedWebsocket] timestamps in kline and candles and prevent double channel registration

## [1.12.12] - 2021-05-26
### Fixed
- [Exchanges][CryptoFeedWebsocket] Feeds stop and close
- [Updater][OHLCV] Initialization with websockets

## [1.12.11] - 2021-05-24
### Fixed
- [Exchanges][CryptoFeedWebsocket] Feeds handling and websockets logging

## [1.12.10] - 2021-05-09
### Added
- [Portfolio] Raise PortfolioNegativeValueError when the update will cause a negative value.

## [1.12.9] - 2021-05-05
### Added
- since in candle history fetching (thanks to @valouvaliavlo)

### Updated
- bump requirements

## [1.12.8] - 2021-04-27
### Updated
- requirements

## [1.12.7] - 2021-04-24
### Added
- get_traded_pairs_by_currency to trading util (from flask_util)

## [1.12.6] - 2021-04-10
### Added
- TradingMode producers and consumer automated creation with class attributes

## [1.12.5] - 2021-04-09 
### Added
- AbstractModeProducer cryptocurrencies, symbols and timeframes wildcard subscription to MatrixChannel through boolean methods

## [1.12.4] - 2021-04-07 
### Fixed
- string formatting in float order adapter

## [1.12.3] - 2021-04-06 
### Added
- decimal.Decimal handling

## [1.12.2] - 2021-04-01 
### Fixed
- Wildcard configuration issues

## [1.12.1] - 2021-03-30 
### Fixed
- Integrate hitbtc order fix https://github.com/ccxt/ccxt/pull/8744
 
## [1.12.0] - 2021-03-25
### Added 
- Cryptofeed websocket connector
 
## [1.11.39] - 2021-03-22 
### Updated 
- tentacles url

## [1.11.38] - 2021-03-06 
### Updated 
- Force chardet version

## [1.11.37] - 2021-03-03 
### Added 
- Python 3.9 support

## [1.11.36] - 2021-02-25
### Updated
- Requirements

## [1.11.35] - 2021-02-24
### Added
- New supported order status (PENDING_CANCEL, EXPIRED, REJECTED)

## [1.11.34] - 2021-02-23
### Updated
- Improved exchange unsupported order types handling

## [1.11.33] - 2021-02-19
### Fixed
- Portfolio balance parsing None values

## [1.11.32] - 2021-02-15
### Fixed
- Order synchronization and cancellation related issues

## [1.11.31] - 2021-02-10
### Fixed
- Order cancellation issues

## [1.11.30] - 2021-02-09
### Updated
- Profitability computation issues

## [1.11.29] - 2021-02-08
### Updated
- Requirements

## [1.11.28] - 2021-02-03
### Updated
- Requirements
  
## [1.11.27] - 2021-01-30
### Fixed
- [CCXT] Use a CCXT version without binance candles fetching issues.
  
## [1.11.26] - 2021-01-30
### Fixed
- [Orders] Improve internal orders management reliability regarding internal exchange order API server-side 
  sync issues.

## [1.11.25] - 2021-01-26
### Fixed
- [CCXT_Exchange] Fix unnecessary 'recvWindows' param

## [1.11.24] - 2021-01-25
### Added
- [Orders] Orders update event logs

## [1.11.23] - 2021-01-16
### Fixed
- [CCXTExchange] NoneType when client.timeframes exists but is None

## [1.11.22] - 2021-01-04
### Fixed
- Prevent multiple channel creations on traded pair duplication

## [1.11.21] - 2020-12-28
### Updated
- Requirements

## [1.11.20] - 2020-12-23
### Added
- Profiles handling

## [1.11.19] - 2020-12-09
### Updated
- Use OctoBot commons configuration keys

## [1.11.18] - 2020-12-06
### Fixed
- Order creation typing issue
- Updater data issues

## [1.11.17] - 2020-11-30
### Added
- Exchange load management
- Exchanges and websockets testing tools
### Fixed
- Websockets stop

## [1.11.16] - 2020-11-25
### Fixed
- CCXT order creations

## [1.11.15] - 2020-11-23
### Updated
- Websocket implementation

## [1.11.14] - 2020-11-15
### Added
- Disabled currencies handling
### Updated
- Exchange architecture to include exchange connectors and remove double inheritance

## [1.11.13] - 2020-11-14
### Fixed
- ExchangeSimulator's implementations exchange manager reference leaking

## [1.11.12] - 2020-11-14
### Fixed
- Object type declaration

## [1.11.11] - 2020-11-07
### Updated
- Requirements

## [1.11.10] - 2020-11-02
### Fixed
- Order creation

## [1.11.9] - 2020-10-29
### Updated
- Numpy requirement

## [1.11.8] - 2020-10-27
### Fixed
- PortfolioValueHolder declaration

## [1.11.7] - 2020-10-27
### Fixed
- Mode factory declaration

## [1.11.6] - 2020-10-26
### Updated
- CCXT requirement

## [1.11.5] - 2020-10-23
### Fixed
- [ModeFactory] Typing

## [1.11.4] - 2020-10-23
### Updated
- Python 3.8 support

## [1.11.3] - 2020-10-22
### Fixed
- [ExchangeData] Cython circular import
- [PersonalData] Cython circular import
- [Lint] Style issues

## [1.11.2] - 2020-10-12
### Fixed
- [ExchangeChannels] Cython circular import

## [1.11.1] - 2020-09-17
### Added
- ExchangeFactory from ExchangeManager refactor
- ExchangeChannels from ExchangeManager refactor
- ExchangeWebsocketFactory from ExchangeManager refactor

### Updated
- [ExchangeManager] Refactor

### Fixed
- [Producers] Potential circular import

## [1.11.0] - 2020-09-15
### Added
- [Portfolio] Balance delta update
- [PortfolioValueHolder] From PortfolioProfitability refactor

### Updated
- [PortfolioProfitability] Refactor

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
