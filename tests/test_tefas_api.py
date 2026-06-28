"""Supplementary TEFAS /api/funds client: envelope handling + distribution mapping.

Driven via httpx.MockTransport (no network — tefas.gov.tr is WAF/egress blocked).
Response bodies mirror shapes captured from the live site (June 2026).
"""
import asyncio

import httpx

from providers.tefas_api_provider import TefasApiProvider, map_distribution_rows


def _provider(post_status, post_json=None, post_text=None, content_type="application/json"):
    def handler(request):
        if request.method == "GET":  # page priming
            return httpx.Response(200, text="<html>ok</html>")
        if post_json is not None:
            return httpx.Response(post_status, json=post_json)
        return httpx.Response(post_status, text=post_text or "", headers={"content-type": content_type})
    return TefasApiProvider(transport=httpx.MockTransport(handler))


def test_fund_types_normalized():
    p = _provider(200, {"errorCode": None, "errorMessage": None, "resultList": [
        {"sfonTuru": 100, "sfonTurAciklama": "Borçlanma Araçları Şemsiye Fonu"},
        {"sfonTuru": 104, "sfonTurAciklama": "Hisse Senedi Şemsiye Fonu"},
    ]})
    env = asyncio.run(p.fund_types())
    assert env["ok"] is True
    assert {"code": 100, "name": "Borçlanma Araçları Şemsiye Fonu"} in env["types"]


def test_fund_categories_normalized():
    p = _provider(200, {"errorMessage": None, "resultList": [{"tanim": "Hisse Senedi"}, {"tanim": "Katılım"}]})
    env = asyncio.run(p.fund_categories())
    assert env["categories"] == ["Hisse Senedi", "Katılım"]


def test_error_message_envelope_matches_live_empty_case():
    # Exactly what the live single-day fonGnlBlgSiraliGetir returned in the HAR.
    p = _provider(200, {"errorCode": None, "errorMessage": "Index 0 out of bounds for length 0", "resultList": None})
    env = asyncio.run(p.fund_list(sfon_tur_kod="100"))
    assert env["ok"] is False
    assert env["error"] == "tefas_api_error"


def test_throttled_429():
    p = _provider(429, post_text='{"faultStatusCode":"429"}')
    env = asyncio.run(p.fund_list())
    assert env["ok"] is False and env["error"] == "tefas_api_throttled"


def test_bot_protection_non_json_marked_unavailable():
    p = _provider(200, post_text="<html>challenge</html>", content_type="text/html")
    env = asyncio.run(p.portfolio_distribution(fund_code="TPC"))
    assert env["ok"] is False and env["error"] == "tefas_api_unavailable"


def test_fund_list_passes_through_raw_rows():
    p = _provider(200, {"errorMessage": None, "resultList": [{"FONKODU": "TPC", "GETIRI1A": 3.2}], "toplamSayi": 1})
    env = asyncio.run(p.fund_list(sfon_tur_kod="104"))
    assert env["ok"] is True
    assert env["result"][0]["FONKODU"] == "TPC"
    assert env["total"] == 1


def test_map_distribution_rows_heuristic_and_raw_preserved():
    rows = [
        {"kiymetTipAciklama": "Hisse Senedi", "dagilimOran": 65.4, "note": "ignored"},
        {"kiymetTipAciklama": "Devlet Tahvili", "dagilimOran": 34.6},
    ]
    mapped = map_distribution_rows(rows)
    assert mapped[0]["asset_type"] == "Hisse Senedi"
    assert mapped[0]["weight"] == 65.4
    assert mapped[0]["raw"] == rows[0]
    assert mapped[1]["asset_type"] == "Devlet Tahvili"
