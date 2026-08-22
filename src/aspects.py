"""Bilingual seed lexicon for service-aspect tagging (Appendix D).

Tagging is a plain substring match on the normalised text plus the raw text
(lower-cased) so English matches survive Arabic normalisation and vice versa.
The lexicon is the first pass of the two-pass aspect procedure; the second
pass (BERTopic) is run independently and merged afterwards.
"""

from __future__ import annotations

import pandas as pd

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


def _norm_ar(s: str) -> str:
    """Light Arabic normalisation so Arabic seeds match the normalised column."""
    return (s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
             .replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي"))


_LEXICON = {a: [k.lower() for k in kws] + [_norm_ar(k) for k in kws if any("؀" <= ch <= "ۿ" for ch in k)]
            for a, kws in ASPECTS.items()}


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
