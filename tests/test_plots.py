"""Fast, network-free unit tests for Plots.read() bias-correction wiring.

These stub the plugin's only tethysapp dependency (VisualizationError) so the
module imports without a configured Tethys portal, then spy on the geoglows
boundaries to assert which correction path each mode takes.
"""
import importlib
import json
import sys
import types

import pandas as pd
import pytest
from unittest.mock import MagicMock

RIVER = 760400565
OBS_JSON = json.dumps(
    {"Datetime": ["2015-01-01", "2015-01-02", "2015-01-03"],
     "Streamflow (m3/s)": [10.0, 11.0, 12.5]}
)


def _fake_fig():
    """A stand-in plotly figure: read() only calls .to_json() on it."""
    fig = MagicMock()
    fig.to_json.return_value = '{"data": [{"x": [1]}], "layout": {}}'
    return fig


@pytest.fixture
def plots(monkeypatch):
    """Import the plots module with tethysapp.tethysdash.exceptions stubbed."""
    exc_mod = types.ModuleType("tethysapp.tethysdash.exceptions")

    class VisualizationError(Exception):
        pass

    exc_mod.VisualizationError = VisualizationError
    pkg = types.ModuleType("tethysapp")
    pkg.__path__ = []
    sub = types.ModuleType("tethysapp.tethysdash")
    sub.__path__ = []
    monkeypatch.setitem(sys.modules, "tethysapp", pkg)
    monkeypatch.setitem(sys.modules, "tethysapp.tethysdash", sub)
    monkeypatch.setitem(sys.modules, "tethysapp.tethysdash.exceptions", exc_mod)
    monkeypatch.delitem(sys.modules, "tethysdash_plugin_geoglows.plots", raising=False)
    return importlib.import_module("tethysdash_plugin_geoglows.plots")


def _stub_data_layer(monkeypatch, plots):
    """Canned data frames + return-period computation (no network)."""
    monkeypatch.setattr(
        plots, "get_plot_data",
        lambda river_id, kind="forecast": pd.DataFrame({river_id: [1.0, 2.0, 3.0]}),
    )
    monkeypatch.setattr(
        plots, "compute_return_periods",
        MagicMock(return_value=pd.DataFrame({"rp": [1.0]})),
    )


def _corrected_frame(*_args, **_kwargs):
    return pd.DataFrame({RIVER: [1.0, 2.0]})


def test_none_forecast_calls_plain_forecast(monkeypatch, plots):
    _stub_data_layer(monkeypatch, plots)
    forecast_spy = MagicMock(return_value=_fake_fig())
    dt_spy, cf_spy = MagicMock(), MagicMock()
    monkeypatch.setattr(plots.geoglows.plots, "forecast", forecast_spy)
    monkeypatch.setattr(plots.geoglows.bias, "discharge_transform", dt_spy)
    monkeypatch.setattr(plots.geoglows.bias, "correct_forecast", cf_spy)

    result = plots.Plots(RIVER, "forecast", bias_correction="None").read()

    assert isinstance(result, dict) and "data" in result
    forecast_spy.assert_called_once()
    dt_spy.assert_not_called()
    cf_spy.assert_not_called()


def test_global_forecast_uses_discharge_transform(monkeypatch, plots):
    _stub_data_layer(monkeypatch, plots)
    dt_spy = MagicMock(side_effect=_corrected_frame)
    pfbc_spy = MagicMock(return_value=_fake_fig())
    forecast_spy, cf_spy = MagicMock(return_value=_fake_fig()), MagicMock()
    monkeypatch.setattr(plots.geoglows.bias, "discharge_transform", dt_spy)
    monkeypatch.setattr(plots.geoglows.bias, "correct_forecast", cf_spy)
    monkeypatch.setattr(plots.geoglows.plots, "forecast", forecast_spy)
    monkeypatch.setattr(plots, "plot_forecast_bias_correct", pfbc_spy)

    result = plots.Plots(
        RIVER, "forecast", bias_correction="Global", observed_historical_data="none"
    ).read()

    assert isinstance(result, dict)
    assert dt_spy.call_count >= 1
    pfbc_spy.assert_called_once()
    forecast_spy.assert_not_called()
    cf_spy.assert_not_called()


def test_local_forecast_uses_correct_forecast_with_observed(monkeypatch, plots):
    _stub_data_layer(monkeypatch, plots)
    ch_spy = MagicMock(side_effect=_corrected_frame)
    cf_spy = MagicMock(side_effect=_corrected_frame)
    dt_spy = MagicMock()
    pfbc_spy = MagicMock(return_value=_fake_fig())
    monkeypatch.setattr(plots.geoglows.bias, "correct_historical", ch_spy)
    monkeypatch.setattr(plots.geoglows.bias, "correct_forecast", cf_spy)
    monkeypatch.setattr(plots.geoglows.bias, "discharge_transform", dt_spy)
    monkeypatch.setattr(plots, "plot_forecast_bias_correct", pfbc_spy)

    result = plots.Plots(
        RIVER, "forecast", bias_correction="Local", observed_historical_data=OBS_JSON
    ).read()

    assert isinstance(result, dict)
    ch_spy.assert_called_once()
    cf_spy.assert_called_once()
    assert cf_spy.call_args.kwargs.get("observed_data") is not None
    dt_spy.assert_not_called()


def test_none_bias_performance_raises(monkeypatch, plots):
    _stub_data_layer(monkeypatch, plots)
    with pytest.raises(plots.VisualizationError):
        plots.Plots(RIVER, "bias-performance", bias_correction="None").read()


def test_global_bias_performance_raises(monkeypatch, plots):
    _stub_data_layer(monkeypatch, plots)
    monkeypatch.setattr(
        plots.geoglows.bias, "discharge_transform", MagicMock(side_effect=_corrected_frame)
    )
    with pytest.raises(plots.VisualizationError):
        plots.Plots(
            RIVER, "bias-performance", bias_correction="Global",
            observed_historical_data="none",
        ).read()


def test_local_invalid_json_raises(monkeypatch, plots):
    _stub_data_layer(monkeypatch, plots)
    with pytest.raises(plots.VisualizationError):
        plots.Plots(
            RIVER, "forecast", bias_correction="Local",
            observed_historical_data="not-valid-json",
        ).read()


def test_local_double_encoded_observed_is_unwrapped(monkeypatch, plots):
    """A double-encoded JSON string (JSON string of a JSON string) still works."""
    _stub_data_layer(monkeypatch, plots)
    monkeypatch.setattr(
        plots.geoglows.bias, "correct_historical", MagicMock(side_effect=_corrected_frame)
    )
    cf_spy = MagicMock(side_effect=_corrected_frame)
    monkeypatch.setattr(plots.geoglows.bias, "correct_forecast", cf_spy)
    monkeypatch.setattr(plots, "plot_forecast_bias_correct", MagicMock(return_value=_fake_fig()))

    result = plots.Plots(
        RIVER, "forecast", bias_correction="Local",
        observed_historical_data=json.dumps(OBS_JSON),  # OBS_JSON is already JSON text
    ).read()

    assert isinstance(result, dict)
    cf_spy.assert_called_once()


def test_local_scalar_observed_raises_friendly(monkeypatch, plots):
    _stub_data_layer(monkeypatch, plots)
    with pytest.raises(plots.VisualizationError):
        plots.Plots(
            RIVER, "forecast", bias_correction="Local", observed_historical_data="42"
        ).read()


def test_local_missing_columns_raises_friendly(monkeypatch, plots):
    _stub_data_layer(monkeypatch, plots)
    payload = json.dumps({"Datetime": ["2015-01-01"]})  # missing 'Streamflow (m3/s)'
    with pytest.raises(plots.VisualizationError):
        plots.Plots(
            RIVER, "forecast", bias_correction="Local", observed_historical_data=payload
        ).read()
