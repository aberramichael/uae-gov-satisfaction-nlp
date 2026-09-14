"""Bilingual seed lexicon for service-aspect tagging (Appendix D).

Tagging is a plain substring match on the normalised text plus the raw text
(lower-cased) so English matches survive Arabic normalisation and vice versa.
The lexicon is the first pass of the two-pass aspect procedure; the second
pass (BERTopic) is run independently and merged afterwards.
"""

from __future__ import annotations

import pandas as pd

from .arabic import fold_arabic, has_arabic

ASPECTS = {
    "login": ["login", "log in", "sign in", "otp", "password", "uae pass",
              "authentication", "تسجيل الدخول", "كلمة المرور", "رمز"],
    "payment": ["payment", "pay", "fee", "card", "refund", "charge", "invoice",
                "دفع", "رسوم", "بطاقة", "استرداد", "فاتورة"],
    "usability": ["easy", "confusing", "interface", "ui", "ux", "navigate",
                  "design", "simple", "سهل", "واجهة", "معقد", "تصميم"],
    "performance": ["slow", "crash", "freeze", "lag", "loading", "bug", "error",
                    "بطيء", "يتوقف", "تعليق", "خطأ", "بطء"],
    "update": ["update", "version", "upgrade", "new version",
               "تحديث", "الاصدار", "النسخة"],
    "support": ["support", "customer service", "help", "contact", "response",
                "دعم", "خدمة العملاء", "مساعدة", "تواصل"],
    "verification": ["verify", "verification", "emirates id", "document", "upload",
                     "تحقق", "الهوية", "مستند", "رفع"],
    "notifications": ["notification", "alert", "reminder", "sms",
                      "اشعار", "إشعار", "تنبيه", "رسالة"],
    "language": ["arabic", "english", "translation", "language",
                 "عربي", "العربية", "انجليزي", "ترجمة", "لغة"],
    "registration": ["register", "registration", "sign up", "account creation",
                     "تسجيل", "حساب جديد", "انشاء حساب"],
}

ASPECT_DISPLAY = {
    "login": "Login / authentication", "payment": "Payment", "usability": "Usability",
    "performance": "Performance / stability", "update": "Updates", "support": "Customer support",
    "verification": "Verification", "notifications": "Notifications",
    "language": "Language", "registration": "Registration",
}




#: Lexicon version. Frozen at the value the thesis published; see
#: ``docs/aspect_lexicon.md`` for the known limitations of this pass.
LEXICON_VERSION = "1.0"

# Each Arabic seed is stored in both its raw and its folded form, so a seed
# matches whether it is compared against ``review_text`` or ``clean_text``.
_LEXICON = {
    a: [k.lower() for k in kws] + [fold_arabic(k) for k in kws if has_arabic(k)]
    for a, kws in ASPECTS.items()
}


def tag_aspects(clean: str, raw: str) -> list[str]:
    blob = f"{clean or ''} {(raw or '').lower()}"
    return [a for a, kws in _LEXICON.items() if any(k in blob for k in kws)]


def add_aspect_columns(df: pd.DataFrame) -> pd.DataFrame:
    tags = [tag_aspects(c, r) for c, r in zip(df["clean_text"], df["review_text"])]
    df = df.copy()
    df["aspect_tags"] = ["|".join(t) for t in tags]
    for a in ASPECTS:
        df[f"aspect_{a}"] = [a in t for t in tags]
    df["n_aspects"] = [len(t) for t in tags]
    return df


def tag_aspects_detailed(clean: str, raw: str) -> list[dict]:
    """Like :func:`tag_aspects`, but reports which seed term fired and where.

    The dashboard needs this: showing an analyst *why* a review was tagged is
    what makes the aspect statistics inspectable rather than an oracle, and it
    is what lets someone spot a false positive at a glance. The lexicon is a
    substring matcher with no word-boundary check, so false positives are a
    known and documented property of version 1.0.

    Returns one entry per matched aspect::

        [{"aspect": "login", "matched": ["otp", "تسجيل الدخول"], "field": "clean"}]

    ``field`` reports where the first match landed: ``"clean"`` if the term was
    found in the normalised text, ``"raw"`` if only in the lower-cased original.
    """
    clean_blob = (clean or "").lower()
    raw_blob = (raw or "").lower()

    out: list[dict] = []
    for aspect, keywords in _LEXICON.items():
        matched = [k for k in keywords if k in clean_blob or k in raw_blob]
        if not matched:
            continue
        field = "clean" if any(k in clean_blob for k in matched) else "raw"
        # Preserve lexicon order but drop the duplicate folded/unfolded forms
        # that resolve to the same surface string.
        seen: set[str] = set()
        unique = [k for k in matched if not (k in seen or seen.add(k))]
        out.append({"aspect": aspect, "matched": unique, "field": field})
    return out
