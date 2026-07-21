"""Review collection from public app stores.

Collects user reviews for the apps defined in ``config.APP_LIST`` from Google
Play and the Apple App Store. Raw output is written to ``data/raw/`` and is
never edited by hand.
"""

from __future__ import annotations

import pandas as pd


def scrape_google_play(gplay_id: str, lang: str = "en", country: str = "ae") -> pd.DataFrame:
    """Collect reviews for a single app from Google Play.

    Args:
        gplay_id: Google Play package identifier (e.g. ``"ae.uaepass.mobile"``).
        lang: Language filter passed to the store API.
        country: Country/store filter passed to the store API.

    Returns:
        A DataFrame of raw reviews with store metadata.
    """
    raise NotImplementedError


def scrape_app_store(appstore_id: str, country: str = "ae") -> pd.DataFrame:
    """Collect reviews for a single app from the Apple App Store.

    Args:
        appstore_id: Apple App Store numeric identifier.
        country: Country/store filter passed to the store API.

    Returns:
        A DataFrame of raw reviews with store metadata.
    """
    raise NotImplementedError


def collect_all(app_list: list[dict]) -> pd.DataFrame:
    """Collect reviews for every app across both platforms.

    Args:
        app_list: List of app records, each with ``app_name``, ``gplay_id``,
            and ``appstore_id`` (see ``config.APP_LIST``).

    Returns:
        A combined DataFrame of raw reviews for all apps and platforms.
    """
    raise NotImplementedError
