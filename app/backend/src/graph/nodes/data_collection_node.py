"""Data collection node for crypto trading workflow."""

from datetime import datetime

import structlog
from app.backend.client.aster.rest import AsterClient
from app.backend.src.graph.enhanced_state import CryptoAgentState, PriceData

from .base_node import BaseNode

logger = structlog.get_logger(__name__)


class DataCollectionNode(BaseNode):
    """Node for collecting market data from various sources."""

    def __init__(self):
        super().__init__(
            name="data_collection",
            description="Collects price, volume, and news data for crypto symbols",
        )

    def get_required_data(self) -> list[str]:
        """
        Get list of required input data fields.

        Returns
        -------
        list[str]
            Required data fields
        """
        return ["symbols", "start_date", "end_date", "timeframe"]

    def get_output_data(self) -> list[str]:
        """
        Get list of output data fields.

        Returns
        -------
        list[str]
            Output data fields
        """
        return ["price_data", "volume_data", "news_data"]

    def execute(self, state: CryptoAgentState) -> CryptoAgentState:
        """
        Execute data collection for all symbols within date range.

        Collects:
        - Historical price data from Aster API (with date range and interval)
        - Historical volume data from Aster API (with date range and interval)
        - News data from RSS feeds and web search

        Parameters
        ----------
        state : CryptoAgentState
            Current workflow state containing:
            - symbols: List of crypto symbols
            - start_date: Start date for data collection
            - end_date: End date for data collection
            - timeframe: Time interval (e.g., '1h', '4h', '1d')

        Returns
        -------
        CryptoAgentState
            Updated state with collected data
        """
        try:
            symbols = state.get("symbols", [])
            start_date = state.get("start_date")
            end_date = state.get("end_date")
            timeframe = state.get("timeframe", "1h")

            logger.info(
                "Collecting data for %s symbols from %s to %s with %s interval",
                len(symbols),
                start_date,
                end_date,
                timeframe,
            )

            logger.info("Collecting historical price data...")
            state = self._collect_price_data(state)

            logger.info("Collecting volume data...")
            state = self._collect_volume_data(state)

            logger.info("Collecting news data...")
            state = self._collect_news_data(state)

            logger.info("Data collection completed successfully")

            return state

        except Exception:
            logger.exception("Error in data collection")
            return state

    def _collect_price_data(self, state: CryptoAgentState) -> CryptoAgentState:
        """Collect historical price data for all symbols within date range."""
        symbols = state["symbols"]
        start_date = state.get("start_date")
        end_date = state.get("end_date")
        timeframe = state.get("timeframe", "1h")
        price_data = {}

        for symbol in symbols:
            aster_symbol = self.to_aster_symbol(symbol)

            with AsterClient() as aster_client:
                logger.debug(
                    "Fetching historical klines for %s from %s to %s with %s interval",
                    symbol,
                    start_date,
                    end_date,
                    timeframe,
                )

                start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
                end_date_str = end_date.strftime("%Y-%m-%d") if end_date else None

                try:
                    klines = aster_client.get_klines_by_date_range(
                        aster_symbol, timeframe, start_date_str, end_date_str
                    )
                    logger.debug("API returned %d klines for %s", len(klines) if klines else 0, symbol)
                except Exception as e:
                    logger.error("Failed to fetch klines for %s: %s", symbol, e)
                    klines = []

                if klines:
                    latest_kline = klines[-1]
                    ticker_data = aster_client.get_ticker(aster_symbol)

                    logger.info(
                        "Historical data for %s: %d klines from %s to %s",
                        symbol,
                        len(klines),
                        klines[0].timestamp,
                        klines[-1].timestamp,
                    )

                    price_data[symbol] = PriceData(
                        symbol=symbol,
                        price=float(latest_kline.close),
                        volume=float(latest_kline.volume),
                        change_24h=float(ticker_data.change_24h),
                        change_percent_24h=float(ticker_data.change_percent_24h),
                        high_24h=float(ticker_data.high_24h),
                        low_24h=float(ticker_data.low_24h),
                        timestamp=datetime.now(),
                        historical_klines=klines,
                        start_date=start_date,
                        end_date=end_date,
                        timeframe=timeframe,
                    )
                else:
                    logger.warning(
                        "No historical data found for %s (aster_symbol: %s, date_range: %s to %s, timeframe: %s)",
                        symbol,
                        aster_symbol,
                        start_date_str,
                        end_date_str,
                        timeframe,
                    )
                    ticker_data = aster_client.get_ticker(aster_symbol)
                    price_data[symbol] = PriceData(
                        symbol=symbol,
                        price=float(ticker_data.price),
                        volume=float(ticker_data.volume),
                        change_24h=float(ticker_data.change_24h),
                        change_percent_24h=float(ticker_data.change_percent_24h),
                        high_24h=float(ticker_data.high_24h),
                        low_24h=float(ticker_data.low_24h),
                        timestamp=datetime.now(),
                    )

        state["price_data"] = price_data
        return state

    def _collect_volume_data(self, state: CryptoAgentState) -> CryptoAgentState:
        """Collect historical volume data for all symbols within date range."""
        symbols = state["symbols"]
        start_date = state.get("start_date")
        end_date = state.get("end_date")
        timeframe = state.get("timeframe", "1h")
        volume_data = {}

        for symbol in symbols:
            aster_symbol = self.to_aster_symbol(symbol)

            with AsterClient() as aster_client:
                # Get historical klines for volume analysis
                logger.debug("Fetching historical volume data for %s with %s interval", symbol, timeframe)

                # Calculate the number of periods needed
                if start_date and end_date:
                    time_diff = end_date - start_date
                    if timeframe == "1h":
                        periods = int(time_diff.total_seconds() / 3600) + 1
                    elif timeframe == "4h":
                        periods = int(time_diff.total_seconds() / (4 * 3600)) + 1
                    elif timeframe == "1d":
                        periods = int(time_diff.total_seconds() / (24 * 3600)) + 1
                    else:
                        periods = 100  # Default fallback
                else:
                    periods = 100  # Default fallback

                # Limit to reasonable number of periods
                periods = min(periods, 1000)

                # Convert datetime objects to string format for API
                start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
                end_date_str = end_date.strftime("%Y-%m-%d") if end_date else None

                try:
                    klines = aster_client.get_klines_by_date_range(
                        aster_symbol, timeframe, start_date_str, end_date_str
                    )
                    logger.debug("API returned %d klines for %s", len(klines) if klines else 0, symbol)
                except Exception as e:
                    logger.error("Failed to fetch klines for %s: %s", symbol, e)
                    klines = []

                if klines:
                    volumes = [float(kline.volume) for kline in klines]
                    volume_data[symbol] = {
                        "current_volume": volumes[-1] if volumes else 0.0,
                        "avg_volume": sum(volumes) / len(volumes) if volumes else 0.0,
                        "max_volume": max(volumes) if volumes else 0.0,
                        "min_volume": min(volumes) if volumes else 0.0,
                        "volume_trend": "increasing"
                        if len(volumes) > 1 and volumes[-1] > volumes[-2]
                        else "decreasing",
                        "volume_volatility": self._calculate_volume_volatility(volumes),
                        "historical_volumes": volumes,
                        "start_date": start_date,
                        "end_date": end_date,
                        "timeframe": timeframe,
                        "timestamp": datetime.now(),
                    }

                    logger.info(
                        "Volume data for %s: %d periods, avg: %.2f, trend: %s",
                        symbol,
                        len(volumes),
                        volume_data[symbol]["avg_volume"],
                        volume_data[symbol]["volume_trend"],
                    )
                else:
                    logger.warning(
                        "No volume data found for %s (aster_symbol: %s, timeframe: %s)",
                        symbol,
                        aster_symbol,
                        timeframe,
                    )
                    volume_data[symbol] = {
                        "current_volume": 0.0,
                        "avg_volume": 0.0,
                        "max_volume": 0.0,
                        "min_volume": 0.0,
                        "volume_trend": "unknown",
                        "volume_volatility": 0.0,
                        "historical_volumes": [],
                        "start_date": start_date,
                        "end_date": end_date,
                        "timeframe": timeframe,
                        "timestamp": datetime.now(),
                    }

        state["volume_data"] = volume_data
        return state

    def _collect_news_data(self, state: CryptoAgentState) -> CryptoAgentState:
        """
        Collect news data for all symbols from multiple sources.

        Uses:
        - ToolManager for centralized news collection
        """
        symbols = state["symbols"]
        news_data = {}

        for symbol in symbols:
            try:
                logger.debug("Collecting news for %s", symbol)

                # Use ToolManager for centralized news collection
                news_data[symbol] = self.tool_manager.get_news_data(symbol, max_results=10)
                news_data[symbol]["timestamp"] = datetime.now()

            except Exception as e:
                logger.warning("Error collecting news for %s: %s", symbol, e)
                news_data[symbol] = {
                    "news_count": 0,
                    "headlines": [],
                    "timestamp": datetime.now(),
                    "error": str(e),
                }

        state["news_data"] = news_data
        return state

    def _collect_social_data(self, state: CryptoAgentState) -> CryptoAgentState:
        """
        Collect social media data for all symbols.

        Uses:
        - TwitterTools for Twitter sentiment and mentions
        """
        symbols = state["symbols"]
        social_data = {}

        for symbol in symbols:
            try:
                # Clean symbol for searching
                clean_symbol = symbol.replace("/USDT", "").replace("USDT", "").replace("/", "").strip()

                # Try to get Twitter sentiment data
                try:
                    twitter_sentiment = self.twitter_tools.analyze_crypto_sentiment(clean_symbol, max_results=50)
                    sentiment_score = twitter_sentiment.get("sentiment_score", 0.0)
                    sentiment_label = twitter_sentiment.get("sentiment_label", "neutral")
                    total_tweets = twitter_sentiment.get("total_tweets", 0)

                    social_data[symbol] = {
                        "sentiment_score": sentiment_score,
                        "mention_count": total_tweets,
                        "social_trend": sentiment_label,
                        "engagement_score": twitter_sentiment.get("engagement_score", 0.0),
                        "top_tweets": twitter_sentiment.get("top_tweets", [])[:5],  # Top 5 tweets
                        "timestamp": datetime.now(),
                        "source": "Twitter",
                    }
                except Exception:
                    # Twitter not configured or failed - use neutral data
                    social_data[symbol] = {
                        "sentiment_score": 0.0,
                        "mention_count": 0,
                        "social_trend": "neutral",
                        "engagement_score": 0.0,
                        "top_tweets": [],
                        "timestamp": datetime.now(),
                        "source": "None (Twitter not available)",
                    }

            except Exception as e:
                logger.warning("Error collecting social data for %s: %s", symbol, e)
                social_data[symbol] = {
                    "sentiment_score": 0.0,
                    "mention_count": 0,
                    "social_trend": "neutral",
                    "engagement_score": 0.0,
                    "top_tweets": [],
                    "timestamp": datetime.now(),
                    "error": str(e),
                }

        state["social_data"] = social_data
        return state

    def _calculate_volume_volatility(self, volumes: list[float]) -> float:
        """
        Calculate volume volatility (coefficient of variation).

        Parameters
        ----------
        volumes : list[float]
            List of volume values

        Returns
        -------
        float
            Volume volatility (0.0 = no volatility, higher = more volatile)
        """
        if not volumes or len(volumes) < 2:
            return 0.0

        mean_volume = sum(volumes) / len(volumes)
        if mean_volume == 0:
            return 0.0

        variance = sum((v - mean_volume) ** 2 for v in volumes) / len(volumes)
        std_dev = variance**0.5

        # Coefficient of variation (standard deviation / mean)
        return std_dev / mean_volume
