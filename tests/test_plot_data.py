"""Regression tests for utils.plot_data."""
import sys
import types

import pandas as pd
from unittest.mock import MagicMock


def _install_fake_app(monkeypatch, tmp_path):
    """Shadow tethysapp.tethysdash.app so get_plot_data resolves a workspace.

    The real App.get_app_workspace() only works inside a Tethys app/request
    context, so we inject a lightweight stand-in pointing at a temp dir.
    """
    class _Workspace:
        path = str(tmp_path)

    class App:
        @classmethod
        def get_app_workspace(cls):
            return _Workspace()

    tethysapp = types.ModuleType("tethysapp")
    tethysapp.__path__ = []
    tethysdash = types.ModuleType("tethysapp.tethysdash")
    tethysdash.__path__ = []
    app_mod = types.ModuleType("tethysapp.tethysdash.app")
    app_mod.App = App

    monkeypatch.setitem(sys.modules, "tethysapp", tethysapp)
    monkeypatch.setitem(sys.modules, "tethysapp.tethysdash", tethysdash)
    monkeypatch.setitem(sys.modules, "tethysapp.tethysdash.app", app_mod)


def test_return_periods_requests_gumbel_distribution(monkeypatch, tmp_path):
    """return-periods must request the 'gumbel' distribution.

    geoglows 2.x defaults distribution='logpearson3', which is absent from the
    current return-period dataset and raises KeyError, breaking every plot.
    """
    _install_fake_app(monkeypatch, tmp_path)

    from tethysdash_plugin_geoglows.utils import plot_data

    canned = pd.DataFrame({12345: [1.0, 2.0]})
    return_periods_spy = MagicMock(return_value=canned)
    monkeypatch.setattr(plot_data.geoglows.data, "return_periods", return_periods_spy)

    result = plot_data.get_plot_data(12345, "return-periods")

    return_periods_spy.assert_called_once_with(12345, distribution="gumbel")
    assert result is canned
