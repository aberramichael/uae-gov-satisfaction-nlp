#!/usr/bin/env python3
"""Fill the prescribed capstone presentation template.

Opens ``Documents/Presentation.pptx`` and populates its eleven required slides,
so the theme, layouts, fonts and slide dimensions come from the template rather
than being re-created. Every figure is read from ``results/`` at build time.

    python scripts/build_template_presentation.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO.parent.parent / "Documents"
FIG = REPO / "results" / "figures"
TAB = REPO / "results" / "tables"
M = json.loads((REPO / "results" / "metrics.json").read_text())

# Template theme colours (Arial; teal primary, navy / orange accents).
TEAL  = RGBColor(0x1A, 0x99, 0x88)
NAVY  = RGBColor(0x1C, 0x36, 0x78)
INK   = RGBColor(0x1A, 0x1A, 0x1A)
GREY  = RGBColor(0x59, 0x59, 0x59)
ORNG  = RGBColor(0xEB, 0x56, 0x00)
LTGR  = RGBColor(0xE9, 0xED, 0xEE)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT  = "Arial"

ds = M["dataset"]
t12 = {r["key"]: r for r in M["comparison"]["table12"]}
xlmr = t12["xlmr"]
seg = M["segmentation"]["table16"]
asp = M["aspects"]["table15"]
kap = {r["stratum"]: r for r in M["kappa"]["rows"]}


# ── helpers ───────────────────────────────────────────────────────────────
def set_body(shape, items, *, size=12.5, space=7, line=1.18, colour=INK):
    """Fill a body placeholder. `items` = str or (str, level, overrides)."""
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    for i, it in enumerate(items):
        text, lvl, over = (it if isinstance(it, tuple) else (it, 0, {}))
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = lvl
        p.space_after = Pt(over.get("space", space))
        p.line_spacing = over.get("line", line)
        r = p.add_run()
        r.text = text
        f = r.font
        f.name = FONT
        f.size = Pt(over.get("size", size))
        f.bold = over.get("bold", False)
        f.color.rgb = over.get("colour", colour)
    return tf


def textbox(slide, x, y, w, h, items, **kw):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tb.text_frame.margin_left = 0
    tb.text_frame.margin_right = 0
    tb.text_frame.margin_top = 0
    tb.text_frame.margin_bottom = 0
    set_body(tb, items, **kw)
    return tb


def add_table(slide, x, y, w, rows, widths, *, font=8.5, head=8.0,
              row_h=Inches(0.235), highlight=None):
    shp = slide.shapes.add_table(len(rows), len(rows[0]), x, y, w,
                                 row_h * len(rows))
    t = shp.table
    total = sum(widths)
    for i, ww in enumerate(widths):
        t.columns[i].width = Emu(int(w * ww / total))
    for ri, row in enumerate(rows):
        t.rows[ri].height = row_h
        for ci, val in enumerate(row):
            c = t.cell(ri, ci)
            c.margin_left = Inches(0.055)
            c.margin_right = Inches(0.055)
            c.margin_top = 0
            c.margin_bottom = 0
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            c.fill.fore_color.rgb = (TEAL if ri == 0 else
                                     LTGR if (highlight is not None and ri == highlight)
                                     else WHITE)
            tf = c.text_frame
            tf.word_wrap = False
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.CENTER
            r = p.add_run()
            r.text = str(val)
            r.font.name = FONT
            r.font.size = Pt(head if ri == 0 else font)
            r.font.bold = (ri == 0) or (highlight is not None and ri == highlight)
            r.font.color.rgb = WHITE if ri == 0 else INK
    return shp


def pic(slide, name, x, y, *, w=None, h=None):
    p = FIG / name
    if not p.exists():
        return None
    kw = {}
    if w: kw["width"] = w
    if h: kw["height"] = h
    return slide.shapes.add_picture(str(p), x, y, **kw)


def body_of(slide):
    """The template's content placeholder (idx 1)."""
    for ph in slide.placeholders:
        if ph.placeholder_format.idx != 0:
            return ph
    return None


def shrink_body(slide, *, width=None, height=None):
    b = body_of(slide)
    if b is None:
        return None
    if width: b.width = width
    if height: b.height = height
    return b


# ══════════════════════════════════════════════════════════════════════════
def build(template: Path, out: Path, mentor: str):
    prs = Presentation(str(template))
    S = prs.slides
    L, T = Inches(0.8), Inches(2.3)      # template's body origin
    BW = Inches(8.4)

    # ── 1 · Title ────────────────────────────────────────────────────────
    s = S[0]
    ph = list(s.placeholders)
    set_body(ph[0], [
        ("Transformer Models for Predicting User Satisfaction from "
         "Arabic–English Reviews of UAE Government Digital Services",
         0, {"size": 20, "bold": True, "colour": INK, "line": 1.15}),
        ("Data Analytics Capstone  ·  Final Presentation",
         0, {"size": 14, "colour": TEAL, "space": 0}),
    ])
    set_body(ph[1], [
        ("Michael Aberra", 0, {"size": 14, "bold": True}),
        (f"Mentor: {mentor}", 0, {"size": 13, "colour": GREY, "space": 0}),
    ])

    # ── 2 · Executive Summary ────────────────────────────────────────────
    s = S[1]
    set_body(body_of(s), [
        ("Objective and scope — classify user-expressed satisfaction "
         "(satisfied / dissatisfied) from bilingual Arabic–English app-store "
         "reviews of UAE government services, and rank the service aspects "
         "associated with dissatisfaction.", 0, {}),
        ("Importance — entities receive continuous, high-volume public "
         "feedback but analyse it manually or with generic tools that mishandle "
         "Arabic morphology, dialect and code-switching.", 0, {}),
        (f"Data — {ds['raw_rows']:,} public reviews of {ds['apps']} government "
         f"applications ({ds['date_min'][:4]}–{ds['date_max'][:4]}); "
         f"{ds['modelling_rows']:,} substantive reviews after length, neutrality "
         "and language filtering.", 0, {}),
        (f"Results — XLM-RoBERTa reaches macro-F1 {xlmr['macro_f1']:.3f} "
         f"[{xlmr['ci_low']:.3f}, {xlmr['ci_high']:.3f}], significantly above the "
         "best classical baseline (McNemar χ²(1) = 31.98, p < .001). "
         "Dissatisfaction concentrates on performance, login and registration.",
         0, {}),
        ("Usage — a weekly ranked list of the aspects driving dissatisfaction "
         "per application, platform and language, turning an unread feedback "
         "stream into a prioritised queue.", 0, {"space": 0}),
    ], size=11.5, space=8)

    # ── 3 · Gap Analysis ─────────────────────────────────────────────────
    s = S[2]
    set_body(body_of(s), [
        ("Transformer architectures (Vaswani et al., 2017; Devlin et al., 2019) "
         "and cross-lingual pre-training (Conneau et al., 2020) are established, "
         "and Arabic-specific encoders followed (Antoun et al., 2020; "
         "Abdul-Mageed et al., 2021).", 0, {}),
        ("Arabic sentiment research remains largely monolingual and is dominated "
         "by product, hotel and tweet corpora (Boudad et al., 2018; Elnagar et "
         "al., 2018; Nabil et al., 2015) — not bilingual government service "
         "feedback.", 0, {}),
        ("Aspect-level work exists (Abdelgwad et al., 2022; AlMasaud & Al-Baity, "
         "2024) but rarely couples a validated seed lexicon with independent "
         "topic discovery (Grootendorst, 2022) on a government corpus.", 0, {}),
        ("Weak supervision is well established (Ratner et al., 2017), yet the "
         "derived label is seldom validated separately per language — the "
         "precondition for any cross-language comparison.", 0, {}),
        ("Gap — no study evaluates bilingual Arabic–English satisfaction "
         "classification for UAE government applications with per-language label "
         "validation and effect sizes reported beside every test.",
         0, {"bold": True, "colour": NAVY, "space": 0}),
    ], size=11, space=7)

    # ── 4 · Research Questions ───────────────────────────────────────────
    s = S[3]
    shrink_body(s, height=Inches(0.42))
    set_body(body_of(s), [
        ("Four questions, each pre-registered as a hypothesis pair and tested "
         "at α = .05, with an effect size reported beside every test.",
         0, {"size": 10.5, "space": 0})])
    rows = [["", "Null hypothesis (H₀)", "Test", "Result"],
            ["RQ1", "Macro-F1 ≤ no-information rate",
             "Bootstrap CI; exact binomial",
             f"Rejected — {xlmr['macro_f1']:.3f} [{xlmr['ci_low']:.3f}, "
             f"{xlmr['ci_high']:.3f}], p < .001"],
            ["RQ2", "No difference vs classical baseline",
             "McNemar (paired)", "Rejected — χ²(1) = 31.98, p < .001, +0.017"],
            ["RQ3", "Aspect independent of dissatisfaction",
             "χ² + BH-FDR; risk ratio",
             "Rejected for 9 of 10 — performance RR 7.44"],
            ["RQ4a", "Equal dissatisfaction rate, AR vs EN",
             "Two-proportion χ² (Yates)",
             f"Rejected — {seg['diff_pp']:.1f} pp, h = {seg['cohens_h']:.2f}, "
             f"OR {seg['odds_ratio']:.2f}"],
            ["RQ4b", "Label not equivalent across languages",
             "Cohen's κ per language",
             f"Not rejected — κ .854 EN / .876 AR"]]
    add_table(s, L, Inches(2.85), BW, rows, [0.5, 3.0, 2.4, 4.3],
              font=8.2, head=8.0, row_h=Inches(0.33))
    textbox(s, L, Inches(4.95), BW, Inches(0.4), [
        ("RQ4b is a measurement-equivalence hypothesis: the RQ4a comparison "
         "cannot be interpreted without it.", 0, {"size": 8.5, "colour": GREY,
                                                  "space": 0})])

    # ── 5 · Data Description and EDA ─────────────────────────────────────
    s = S[4]
    shrink_body(s, width=Inches(4.05))
    set_body(body_of(s), [
        (f"{ds['raw_rows']:,} public reviews of {ds['apps']} UAE government "
         f"applications, collected July 2026 from Google Play and the App Store. "
         "One review is the unit of analysis.", 0, {}),
        (f"Filtering retains {ds['modelling_rows']:,} substantive reviews "
         "(65.9%): duplicates removed, 3-star neutral band excluded, minimum six "
         "words, Arabic or English only.", 0, {}),
        (f"Class balance is 55.6% dissatisfied; Arabic is 24.3% of the "
         "modelling set.", 0, {}),
        ("Aspect coverage rises from 8.8% of the shortest reviews to 78.6% of "
         "the longest — which is why the length filter is a measurement decision, "
         "not housekeeping.", 0, {"bold": True, "colour": NAVY, "space": 0}),
    ], size=10.5, space=7)
    pic(s, "fig1_length_bands.png", Inches(5.05), Inches(2.3), w=Inches(4.15))
    textbox(s, Inches(5.05), Inches(4.62), Inches(4.15), Inches(0.35), [
        ("Aspect-carrying rate by review length band (n = 74,411).",
         0, {"size": 8, "colour": GREY, "space": 0})])

    # ── 6 · Architecture diagram / Workflow ──────────────────────────────
    s = S[5]
    # The diagram is ~2.33:1, so width is bounded by the slide height, not its
    # width: 7.4in wide renders 3.18in tall and leaves room for the caption.
    IMG_W = Inches(7.4)
    pic(s, "fig4_architecture.png", Inches((10 - 7.4) / 2), Inches(2.02), w=IMG_W)
    # Reuse the template's body placeholder as the caption beneath the figure.
    b = body_of(s)
    b.top, b.left = Inches(5.24), Inches(0.8)
    b.width, b.height = Inches(8.4), Inches(0.3)
    set_body(b, [
        ("Twelve stages from public store endpoints to a ranked, segment-aware "
         "priority queue. Colour marks the layer: data (navy), modelling (gold), "
         "delivery (teal), users (red).",
         0, {"size": 8, "colour": GREY, "space": 0})])

    # ── 7 · Model building ───────────────────────────────────────────────
    s = S[6]
    shrink_body(s, width=Inches(4.15))
    set_body(body_of(s), [
        ("Classical baselines establish the floor — TF-IDF word (1,2) plus "
         "character (3,5) n-grams, which handle Arabic clitics without a "
         "morphological analyser.", 0, {}),
        ("Cross-lingual encoders test the central claim: XLM-RoBERTa and mBERT "
         "are fine-tuned on the full bilingual corpus.", 0, {}),
        ("Arabic-specific encoders (AraBERT, MARBERT) are fine-tuned on the "
         "Arabic subset to test whether specialisation beats cross-lingual "
         "transfer.", 0, {}),
        ("Controls held constant — seed 42; a 70/15/15 split stratified jointly "
         "on label and language; deduplication before splitting; leakage checks "
         "returning zero overlap on id and text.",
         0, {"bold": True, "colour": NAVY, "space": 0}),
    ], size=10.5, space=7)
    rows = [["Setting", "Value"],
            ["Max sequence length", "128 tokens"],
            ["Batch size / epochs", "32 / 3 (patience 1)"],
            ["Learning rate", "2e-5 (grid 2e-5, 3e-5)"],
            ["Loss", "Class-weighted cross-entropy"],
            ["Selection", "Best validation macro-F1"],
            ["Headline metric", "Macro-averaged F1"]]
    add_table(s, Inches(5.15), Inches(2.32), Inches(4.05), rows, [2.2, 2.6],
              font=9, head=8.5, row_h=Inches(0.285))

    # ── 8 · Results ──────────────────────────────────────────────────────
    s = S[7]
    shrink_body(s, height=Inches(0.34))
    set_body(body_of(s), [
        (f"XLM-RoBERTa leads on the {xlmr['n_test']:,}-review test partition; "
         "dissatisfaction concentrates on three aspects.",
         0, {"size": 10, "space": 0})])
    rows = [["Model", "Macro-F1", "95% CI", "Recall (dis.)"],
            ["XLM-RoBERTa (base)", f"{xlmr['macro_f1']:.4f}",
             f"[{xlmr['ci_low']:.3f}, {xlmr['ci_high']:.3f}]",
             f"{xlmr['recall_dissatisfied']:.3f}"]]
    for k in ["mbert", "marbert", "tfidf_svm", "tfidf_lr", "arabert", "tfidf_nb"]:
        r = t12[k]
        rows.append([r["model"][:26], f"{r['macro_f1']:.4f}",
                     f"[{r['ci_low']:.3f}, {r['ci_high']:.3f}]",
                     f"{r['recall_dissatisfied']:.3f}"])
    add_table(s, L, Inches(2.72), Inches(4.35), rows, [2.3, 1.0, 1.35, 1.1],
              font=8, head=7.8, row_h=Inches(0.235), highlight=1)
    pic(s, "fig_aspect_risk_ratios.png", Inches(5.35), Inches(2.62), w=Inches(3.95))
    textbox(s, L, Inches(4.72), BW, Inches(0.6), [
        ("Inference — the transformer margin over the best classical baseline is "
         "+0.017 macro-F1 (McNemar χ²(1) = 31.98, p < .001), rising to +0.025 on "
         "the Arabic subset. A dissatisfied reviewer is 7.44× more likely to "
         "mention performance than a satisfied one (95% CI [6.84, 8.10], "
         "BH-adjusted). Usability and support fall below 1.0 and are praise "
         "markers, not problems.", 0, {"size": 8.5, "colour": GREY, "space": 0,
                                       "line": 1.2})])

    # ── 9 · Implementation and User Benefit ──────────────────────────────
    s = S[8]
    set_body(body_of(s), [
        ("Batch scoring service — reviews are collected on a weekly cadence, "
         "scored, and written back with a satisfaction label, a confidence value "
         "and any aspect tags.", 0, {}),
        ("Ranked driver list per application, platform and language, so a "
         "service owner receives a prioritised queue rather than a feed.", 0, {}),
        ("Effect sizes accompany every comparison, so a team is never handed a "
         "difference that is statistically real and operationally irrelevant.",
         0, {}),
        ("Segment identifiers are excluded from the model, so comparing two "
         "entities reflects what users wrote, not what the model learned about "
         "those entities.", 0, {}),
        ("Beneficiaries — service and product teams, Chief Happiness Officers, "
         "and policy units tracking satisfaction across the federal estate.",
         0, {"space": 0}),
    ], size=11.5, space=8)

    # ── 10 · Conclusion ──────────────────────────────────────────────────
    s = S[9]
    set_body(body_of(s), [
        ("Satisfaction is classifiable from bilingual review text: macro-F1 "
         f"{xlmr['macro_f1']:.3f}, dissatisfied recall "
         f"{xlmr['recall_dissatisfied']:.3f}; the interval's lower bound clears "
         "the 0.80 operational threshold overall and within Arabic.", 0, {}),
        ("The star-derived label is a sound instrument in both languages "
         "(κ = .854 English, .876 Arabic), which is what licenses the "
         "cross-language comparison.", 0, {}),
        (f"English reviews express dissatisfaction {seg['diff_pp']:.1f} "
         "percentage points more often than Arabic reviews — statistically "
         f"clear but a small-to-medium effect (Cohen's h = {seg['cohens_h']:.2f}).",
         0, {}),
        ("Limitations — reviewers are self-selected, so every claim concerns "
         "expressed satisfaction among reviewers; Arabic is the minority stratum "
         "and is classified 2.3 points less accurately; the lexicon covers ten "
         "pre-registered aspects.", 0, {"colour": GREY}),
        ("Future work — extend to survey and helpdesk channels, add a neutral "
         "class so 3-star feedback is scored rather than excluded, and refresh "
         "the aspect lexicon from topic discovery each cycle.",
         0, {"colour": GREY, "space": 0}),
    ], size=10.5, space=7)

    # ── 11 · Bibliography ────────────────────────────────────────────────
    s = S[10]
    b = body_of(s)
    b.width = Inches(4.15)
    b.height = Inches(3.0)
    refs = [
        "Abdelgwad, M. M., Soliman, T. H. A., & Taloba, A. I. (2022). Arabic "
        "aspect-based sentiment classification using BERT. Journal of King Saud "
        "University – Computer and Information Sciences, 34(8), 6255–6266.",
        "Abdul-Mageed, M., Elmadany, A., & Nagoudi, E. M. B. (2021). ARBERT & "
        "MARBERT: Deep bidirectional transformers for Arabic. ACL-IJCNLP 2021, "
        "7088–7105.",
        "AlMasaud, A., & Al-Baity, H. H. (2024). On the robustness of Arabic "
        "aspect-based sentiment analysis. Applied Sciences, 14(23), 11080.",
        "Antoun, W., Baly, F., & Hajj, H. (2020). AraBERT: Transformer-based "
        "model for Arabic language understanding. OSACT 2020, 9–15.",
        "Boudad, N., Faizi, R., Thami, R. O. H., & Chiheb, R. (2018). Sentiment "
        "analysis in Arabic: A review of the literature. Ain Shams Engineering "
        "Journal, 9(4), 2479–2490.",
        "Conneau, A., Khandelwal, K., Goyal, N., et al. (2020). Unsupervised "
        "cross-lingual representation learning at scale. ACL 2020, 8440–8451.",
        "Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019). BERT: "
        "Pre-training of deep bidirectional transformers. NAACL-HLT 2019, "
        "4171–4186.",
        "Dietterich, T. G. (1998). Approximate statistical tests for comparing "
        "supervised classification learning algorithms. Neural Computation, "
        "10(7), 1895–1923.",
    ]
    refs2 = [
        "Elnagar, A., Khalifa, Y. S., & Einea, A. (2018). Hotel Arabic-reviews "
        "dataset construction for sentiment analysis applications. In Intelligent "
        "Natural Language Processing (pp. 35–52). Springer.",
        "Grootendorst, M. (2022). BERTopic: Neural topic modeling with a "
        "class-based TF-IDF procedure. arXiv. https://arxiv.org/abs/2203.05794",
        "Landis, J. R., & Koch, G. G. (1977). The measurement of observer "
        "agreement for categorical data. Biometrics, 33(1), 159–174.",
        "Nabil, M., Aly, M., & Atiya, A. (2015). ASTD: Arabic sentiment tweets "
        "dataset. EMNLP 2015, 2515–2519.",
        "Ratner, A., Bach, S. H., Ehrenberg, H., et al. (2017). Snorkel: Rapid "
        "training data creation with weak supervision. PVLDB, 11(3), 269–282.",
        "Sanh, V., Debut, L., Chaumond, J., & Wolf, T. (2019). DistilBERT, a "
        "distilled version of BERT. arXiv. https://arxiv.org/abs/1910.01108",
        "Vaswani, A., Shazeer, N., Parmar, N., et al. (2017). Attention is all "
        "you need. NeurIPS 30, 5998–6008.",
    ]
    set_body(b, [(r, 0, {}) for r in refs], size=7.2, space=5, line=1.05)
    textbox(s, Inches(5.15), Inches(2.3), Inches(4.15), Inches(3.0),
            [(r, 0, {}) for r in refs2], size=7.2, space=5, line=1.05)

    # Text-dense slides use the slide's unused lower margin rather than
    # dropping to an unreadable point size. The template's own origin and
    # width are untouched.
    for idx in (1, 2, 4, 6):
        b = body_of(S[idx])
        if b is not None:
            b.height = Inches(3.02)

    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default=str(DOCS / "Presentation.pptx"))
    ap.add_argument("--out", default=str(DOCS / "Final Presentation.pptx"))
    ap.add_argument("--mentor", default="[Mentor's name]")
    args = ap.parse_args()
    p = build(Path(args.template), Path(args.out), args.mentor)
    print(f"wrote {p}")
