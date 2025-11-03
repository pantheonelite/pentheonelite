"""
Crypto-themed agents inspired by legendary investors and crypto personalities.

This module contains crypto-specific agents that embody the philosophies
of various legendary investors and crypto personalities, adapted for the
cryptocurrency market.
"""

from .crypto_analyst import CryptoAnalystAgent
from .crypto_sentiment import CryptoSentimentAgent
from .crypto_technical import CryptoTechnicalAgent
from .cz_binance import CZBinanceAgent
from .defi_agent import DeFiAgent
from .elon_musk import ElonMuskAgent
from .michael_saylor import MichaelSaylorAgent
from .satoshi_nakamoto import SatoshiNakamotoAgent
from .vitalik_buterin import VitalikButerinAgent

__all__ = [
    "CZBinanceAgent",
    "CryptoAnalystAgent",
    "CryptoSentimentAgent",
    "CryptoTechnicalAgent",
    "DeFiAgent",
    "ElonMuskAgent",
    "MichaelSaylorAgent",
    "SatoshiNakamotoAgent",
    "VitalikButerinAgent",
]
