"""Assert wrappers map their public args onto the real skill-script kwargs.

Regression for #opend-calendar: get_economic_calendar / get_earnings_calendar /
get_institution_list / get_plate_list passed kwargs the skill function does not
accept (date=, max_count=, name=, count= on scripts whose params are
begin_date/markets_str/count / market_str/begin_date / market_str/name_part /
limit), producing `unexpected keyword argument` TypeErrors from the runner.

These tests monkeypatch skill_runner._run_skill_json to capture the call, and
assert the emitted kwargs are exactly the script's parameter names.
"""
from __future__ import annotations

import datetime as dt

from futu_opend_mcp.tools import financials, institutions, macro, plates


def _patch(monkeypatch, mod, capture):
    monkeypatch.setattr(mod.connection, "get_context", lambda: None)

    def fake_run(fn, *a, **k):
        capture["fn"] = fn.__name__
        capture["args"] = a
        capture["kwargs"] = k
        return {"data": []}

    monkeypatch.setattr(mod.skill_runner, "_run_skill_json", fake_run)


# --- get_economic_calendar -------------------------------------------------

def test_economic_calendar_maps_to_script_kwargs(monkeypatch):
    cap = {}
    _patch(monkeypatch, macro, cap)
    macro.get_economic_calendar(market="US", date="2026-09-01",
                                end_date="2026-12-31", max_count=60)
    assert cap["kwargs"] == {"begin_date": "2026-09-01", "end_date": "2026-12-31",
                             "markets_str": "US", "count": 60}
    assert cap["args"] == ()


def test_economic_calendar_date_defaults_to_today(monkeypatch):
    cap = {}
    _patch(monkeypatch, macro, cap)
    macro.get_economic_calendar(market="US")
    # begin_date is required by the skill script; default to today when omitted.
    assert cap["kwargs"]["begin_date"] == dt.date.today().isoformat()
    assert cap["kwargs"]["end_date"] is None
    assert cap["kwargs"]["markets_str"] == "US"
    # no bad-param kwargs leak through
    assert "date" not in cap["kwargs"] and "max_count" not in cap["kwargs"]


# --- get_earnings_calendar -------------------------------------------------

def test_earnings_calendar_maps_to_script_kwargs(monkeypatch):
    cap = {}
    _patch(monkeypatch, financials, cap)
    financials.get_earnings_calendar("US", date="2026-09-15")
    assert cap["kwargs"] == {"market_str": "US", "begin_date": "2026-09-15"}
    assert cap["args"] == ()
    assert "date" not in cap["kwargs"] and "max_count" not in cap["kwargs"]


# --- get_institution_list --------------------------------------------------

def test_institution_list_maps_to_script_kwargs(monkeypatch):
    cap = {}
    _patch(monkeypatch, institutions, cap)
    institutions.get_institution_list("US", name="Bridgewater", count=10)
    assert cap["kwargs"] == {"market_str": "US", "name_part": "Bridgewater",
                             "count": 10}
    assert cap["args"] == ()
    assert "name" not in cap["kwargs"]


# --- get_plate_list --------------------------------------------------------

def test_plate_list_maps_count_to_limit(monkeypatch):
    cap = {}
    _patch(monkeypatch, plates, cap)
    plates.get_plate_list("HK", plate_type="CONCEPT", keyword="chip", count=25)
    # market stays positional; the script's row cap is `limit`, not `count`.
    assert cap["args"] == ("HK",)
    assert cap["kwargs"] == {"plate_type": "CONCEPT", "keyword": "chip",
                             "limit": 25}
    assert "count" not in cap["kwargs"]
