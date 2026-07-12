"""Tests that empty vendor results never become fabricated data.

Covers two systematic fixes:
  - load_ohlcv must not cache an empty download (cache poisoning), and must
    raise NoMarketDataError instead of returning an empty frame.
  - route_to_vendor must convert NoMarketDataError into a single explicit
    "NO_DATA_AVAILABLE" sentinel after all vendors are exhausted.
"""

import os
import unittest
from unittest import mock

import pandas as pd
import pytest

from tradingagents.dataflows import interface, stockstats_utils
from tradingagents.dataflows.config import set_config
from tradingagents.dataflows.symbol_utils import NoMarketDataError


@pytest.mark.unit
class TestLoadOhlcvNoPoison(unittest.TestCase):
    def setUp(self):
        self._tmp = os.path.join(os.path.dirname(__file__), "_tmp_cache")
        os.makedirs(self._tmp, exist_ok=True)
        set_config({"data_cache_dir": self._tmp})

    def tearDown(self):
        for f in os.listdir(self._tmp):
            os.remove(os.path.join(self._tmp, f))
        os.rmdir(self._tmp)

    def test_empty_download_raises_and_does_not_cache(self):
        empty = pd.DataFrame()
        with mock.patch.object(stockstats_utils.yf, "download", return_value=empty), \
                self.assertRaises(NoMarketDataError):
            stockstats_utils.load_ohlcv("FAKE", "2026-01-01")
        # Nothing should have been written to the cache.
        self.assertEqual(os.listdir(self._tmp), [])

        # A second call must re-attempt the fetch (no poisoned cache served).
        with mock.patch.object(stockstats_utils.yf, "download", return_value=empty) as dl2:
            with self.assertRaises(NoMarketDataError):
                stockstats_utils.load_ohlcv("FAKE", "2026-01-01")
            self.assertTrue(dl2.called)


@pytest.mark.unit
class TestRouteToVendorSentinel(unittest.TestCase):
    def test_alpha_vantage_error_string_falls_back_to_configured_yfinance(self):
        def alpha_returns_error(*args, **kwargs):
            return "Error retrieving rsi data: Alpha Vantage rate limit exceeded"

        def yfinance_returns_success(*args, **kwargs):
            return "## RSI values\n\n2026-01-10: 48.2"

        patched = {
            "alpha_vantage": alpha_returns_error,
            "yfinance": yfinance_returns_success,
        }
        with mock.patch.object(
            interface, "get_vendor", return_value="alpha_vantage,yfinance"
        ), mock.patch.dict(
            interface.VENDOR_METHODS, {"get_indicators": patched}, clear=False
        ):
            result = interface.route_to_vendor(
                "get_indicators", "RKLB", "rsi", "2026-01-10", 30
            )

        self.assertIn("RSI values", result)
        self.assertNotIn("Error retrieving", result)

    def test_alpha_vantage_information_payload_falls_back_to_configured_yfinance(self):
        def alpha_returns_information(*args, **kwargs):
            return '{"Information": "This is a premium endpoint."}'

        def yfinance_returns_success(*args, **kwargs):
            return "# Stock data for RKLB"

        patched = {
            "alpha_vantage": alpha_returns_information,
            "yfinance": yfinance_returns_success,
        }
        with mock.patch.object(
            interface, "get_vendor", return_value="alpha_vantage,yfinance"
        ), mock.patch.dict(
            interface.VENDOR_METHODS, {"get_stock_data": patched}, clear=False
        ):
            result = interface.route_to_vendor(
                "get_stock_data", "RKLB", "2026-01-01", "2026-01-10"
            )

        self.assertEqual(result, "# Stock data for RKLB")

    def test_no_data_from_all_vendors_returns_sentinel(self):
        def raises_no_data(symbol, *a, **k):
            raise NoMarketDataError(symbol, "GC=F", "no rows")

        patched = {"yfinance": raises_no_data, "alpha_vantage": raises_no_data}
        with mock.patch.dict(
            interface.VENDOR_METHODS, {"get_stock_data": patched}, clear=False
        ):
            result = interface.route_to_vendor(
                "get_stock_data", "XAUUSD+", "2026-01-01", "2026-01-10"
            )
        self.assertIn("NO_DATA_AVAILABLE", result)
        self.assertIn("XAUUSD+", result)
        self.assertIn("GC=F", result)
        self.assertIn("Do not estimate", result)

    def test_unconfigured_fallback_does_not_mask_no_data(self):
        # When the primary vendor reports no data and the fallback is simply
        # unavailable (e.g. missing API key -> raises), the no-data sentinel
        # must win rather than the fallback's incidental error crashing out.
        def raises_no_data(symbol, *a, **k):
            raise NoMarketDataError(symbol, symbol, "no rows")

        def raises_unavailable(symbol, *a, **k):
            raise ValueError("ALPHA_VANTAGE_API_KEY environment variable is not set.")

        patched = {"yfinance": raises_no_data, "alpha_vantage": raises_unavailable}
        with mock.patch.dict(
            interface.VENDOR_METHODS, {"get_stock_data": patched}, clear=False
        ):
            result = interface.route_to_vendor(
                "get_stock_data", "FAKE", "2026-01-01", "2026-01-10"
            )
        self.assertIn("NO_DATA_AVAILABLE", result)


if __name__ == "__main__":
    unittest.main()
