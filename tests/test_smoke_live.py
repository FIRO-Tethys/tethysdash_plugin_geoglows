"""Live smoke test: exercises real geoglows data + bias APIs end to end.

Network-bound and slow, so marked ``integration`` and excluded from the default
run (see pyproject ``addopts``). Run explicitly with::

    pytest -m integration

This is the test that catches upstream GEOGLOWS API/data drift (e.g. the
return_periods 'logpearson3' break) that unit tests with mocks cannot see.
"""
import json
import math
import os
from datetime import datetime, timedelta

import pytest

pytestmark = pytest.mark.integration

RIVER = 760400565


@pytest.fixture(scope="module")
def plots_cls(tmp_path_factory):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tethys_portal.settings")
    import django

    django.setup()

    # App.get_app_workspace() only resolves inside a Tethys app/request context.
    import tethysapp.tethysdash.app as appmod

    cache_dir = tmp_path_factory.mktemp("geoglows_ws")

    class _Workspace:
        path = str(cache_dir)

    appmod.App.get_app_workspace = classmethod(lambda cls: _Workspace())

    from tethysdash_plugin_geoglows.plots import Plots

    return Plots


def _synthetic_observed_json():
    start = datetime(2015, 1, 1)
    n = 365 * 3
    dates, vals = [], []
    for i in range(n):
        d = start + timedelta(days=i)
        seasonal = 25 + 18 * math.sin(2 * math.pi * d.timetuple().tm_yday / 365.0)
        dates.append(d.strftime("%Y-%m-%d"))
        vals.append(round(max(0.5, seasonal), 2))
    return json.dumps({"Datetime": dates, "Streamflow (m3/s)": vals})


@pytest.mark.parametrize(
    "bias,plot",
    [
        ("None", "forecast"),
        ("None", "retro-simulation"),
        ("Global", "forecast"),
        ("Global", "retro-simulation"),
        ("Local", "forecast"),
        ("Local", "bias-performance"),
    ],
)
def test_plot_renders_live(plots_cls, bias, plot):
    observed = _synthetic_observed_json() if bias == "Local" else "none"

    result = plots_cls(
        river_id=RIVER, plot_name=plot, bias_correction=bias,
        observed_historical_data=observed,
    ).read()

    assert isinstance(result, dict)
    assert result.get("data"), f"{bias}/{plot} produced no traces"
