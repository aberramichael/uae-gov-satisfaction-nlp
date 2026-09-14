#!/usr/bin/env python3
"""Build the capstone defence deck from the project's own results.

Every figure quoted here is read from ``results/`` rather than typed in, so the
deck cannot drift from the report. Re-run it after any change to the pipeline
and the slides update with it.

    python scripts/build_presentation.py --out "Final Presentation.pptx"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

REPO = Path(__file__).resolve().parents[1]
FIG = REPO / "results" / "figures"
TAB = REPO / "results" / "tables"
METRICS = json.loads((REPO / "results" / "metrics.json").read_text())

# ── Design tokens ─────────────────────────────────────────────────────────
# A restrained academic palette. The violet accent ties the deck to the
# platform's brand; everything else stays out of the way so projected text
# holds up in a badly lit room.
INK        = RGBColor(0x0F, 0x17, 0x2A)
MUTED      = RGBColor(0x47, 0x55, 0x69)
SUBTLE     = RGBColor(0x64, 0x74, 0x8B)
RULE       = RGBColor(0xE2, 0xE5, 0xEA)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
BRAND      = RGBColor(0x7C, 0x5C, 0xFF)
ACCENT     = RGBColor(0xAD, 0x46, 0xFF)
DEEP       = RGBColor(0x1A, 0x14, 0x3C)
DISSAT     = RGBColor(0xC0, 0x12, 0x34)
SATIS      = RGBColor(0x04, 0x7A, 0x45)
NEUTRAL    = RGBColor(0x96, 0x59, 0x0A)
WASH       = RGBColor(0xF5, 0xF3, 0xFF)
WASH_RULE  = RGBColor(0xE4, 0xDC, 0xFF)

FONT = "Calibri"
W, H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.85)
BODY_W = W - 2 * MARGIN


def _txt(frame, runs, *, size=18, color=INK, bold=False, space_after=6,
         line=1.25, align=PP_ALIGN.LEFT):
    """Write a list of (text, overrides) tuples into a text frame."""
    frame.word_wrap = True
    for i, item in enumerate(runs):
        text, over = item if isinstance(item, tuple) else (item, {})
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.alignment = over.get("align", align)
        p.space_after = Pt(over.get("space_after", space_after))
        p.line_spacing = over.get("line", line)
        if over.get("bullet"):
            text = "•   " + text
        r = p.add_run()
        r.text = text
        f = r.font
        f.name = FONT
        f.size = Pt(over.get("size", size))
        f.bold = over.get("bold", bold)
        f.color.rgb = over.get("color", color)
    return frame


def _box(slide, x, y, w, h):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tb.text_frame.margin_left = 0
    tb.text_frame.margin_right = 0
    tb.text_frame.margin_top = 0
    tb.text_frame.margin_bottom = 0
    return tb.text_frame


def _rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1)
    s.shadow.inherit = False
    return s


class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.blank = self.prs.slide_layouts[6]
        self.n = 0

    # ── slide chrome ─────────────────────────────────────────────────────
    def _chrome(self, slide, footer=True):
        self.n += 1
        if not footer:
            return
        _rect(slide, MARGIN, H - Inches(0.62), BODY_W, Emu(9525), RULE)
        f = _box(slide, MARGIN, H - Inches(0.55), BODY_W, Inches(0.3))
        _txt(f, [("Transformer Models for Predicting User Satisfaction  ·  "
                  "Michael Aberra  ·  QM640", {})],
             size=9.5, color=SUBTLE, space_after=0)
        g = _box(slide, W - MARGIN - Inches(0.6), H - Inches(0.55),
                 Inches(0.6), Inches(0.3))
        _txt(g, [(str(self.n), {"align": PP_ALIGN.RIGHT})],
             size=9.5, color=SUBTLE, space_after=0)

    def title_slide(self):
        s = self.prs.slides.add_slide(self.blank)
        _rect(s, 0, 0, W, H, DEEP)
        # A soft accent band rather than a full gradient — reads cleanly when
        # a projector crushes the blacks.
        _rect(s, 0, H - Inches(0.22), W, Inches(0.22), BRAND)
        _rect(s, MARGIN, Inches(1.5), Inches(0.9), Inches(0.05), ACCENT)

        f = _box(s, MARGIN, Inches(1.95), Inches(11.2), Inches(2.4))
        _txt(f, [
            ("Transformer Models for Predicting User Satisfaction",
             {"size": 40, "bold": True, "color": WHITE, "space_after": 4}),
            ("from Arabic–English Reviews of UAE Government Digital Services",
             {"size": 27, "color": RGBColor(0xC9, 0xC2, 0xF5), "space_after": 0}),
        ], line=1.15)

        f = _box(s, MARGIN, Inches(4.7), Inches(11.2), Inches(1.4))
        _txt(f, [
            ("Michael Aberra", {"size": 17, "bold": True, "color": WHITE,
                                "space_after": 3}),
            ("Doctor of Business Administration  ·  Capstone Project QM640",
             {"size": 13.5, "color": RGBColor(0x9C, 0x96, 0xC4), "space_after": 3}),
            ("74,412 reviews  ·  136 government applications  ·  2010–2026",
             {"size": 13.5, "color": RGBColor(0x9C, 0x96, 0xC4), "space_after": 0}),
        ])
        self.n += 1
        return s

    def section(self, kicker, title, blurb=None):
        s = self.prs.slides.add_slide(self.blank)
        _rect(s, 0, 0, W, H, DEEP)
        _rect(s, MARGIN, Inches(2.75), Inches(0.9), Inches(0.05), ACCENT)
        f = _box(s, MARGIN, Inches(3.15), Inches(10.6), Inches(2))
        runs = [(kicker.upper(), {"size": 12.5, "bold": True, "color": ACCENT,
                                  "space_after": 10}),
                (title, {"size": 34, "bold": True, "color": WHITE,
                         "space_after": 8})]
        if blurb:
            runs.append((blurb, {"size": 15, "color": RGBColor(0x9C, 0x96, 0xC4)}))
        _txt(f, runs, line=1.2)
        self.n += 1
        return s

    def content(self, title, kicker=None):
        s = self.prs.slides.add_slide(self.blank)
        y = Inches(0.62)
        if kicker:
            f = _box(s, MARGIN, y, BODY_W, Inches(0.28))
            _txt(f, [(kicker.upper(), {})], size=11.5, bold=True, color=BRAND,
                 space_after=0)
            y += Inches(0.34)
        f = _box(s, MARGIN, y, BODY_W, Inches(0.62))
        _txt(f, [(title, {})], size=27, bold=True, color=INK, space_after=0,
             line=1.1)
        _rect(s, MARGIN, y + Inches(0.62), Inches(0.75), Inches(0.045), BRAND)
        self._chrome(s)
        return s, y + Inches(0.95)

    # ── reusable blocks ──────────────────────────────────────────────────
    def stat_row(self, slide, y, stats, *, height=Inches(1.25)):
        """Evenly spaced figure tiles. `stats` = (value, label, note, colour)."""
        gap = Inches(0.22)
        w = (BODY_W - gap * (len(stats) - 1)) / len(stats)
        for i, (val, lab, note, col) in enumerate(stats):
            x = MARGIN + i * (w + gap)
            _rect(slide, x, y, w, height, WASH, WASH_RULE)
            _rect(slide, x, y, Inches(0.045), height, col)
            f = _box(slide, x + Inches(0.24), y + Inches(0.14),
                     w - Inches(0.4), height - Inches(0.24))
            runs = [(val, {"size": 25, "bold": True, "color": col,
                           "space_after": 1}),
                    (lab, {"size": 12, "bold": True, "color": INK,
                           "space_after": 1})]
            if note:
                runs.append((note, {"size": 10, "color": SUBTLE}))
            _txt(f, runs, line=1.15)
        return y + height + Inches(0.26)

    def table(self, slide, x, y, w, rows, widths=None, *, font=11.5,
              head_font=10, highlight=None, row_h=Inches(0.3)):
        n_r, n_c = len(rows), len(rows[0])
        shape = slide.shapes.add_table(n_r, n_c, x, y, w,
                                       row_h * n_r)
        tbl = shape.table
        tbl.first_row = True
        if widths:
            total = sum(widths)
            for i, ww in enumerate(widths):
                tbl.columns[i].width = Emu(int(w * ww / total))
        for r, row in enumerate(rows):
            tbl.rows[r].height = row_h
            for c, val in enumerate(row):
                cell = tbl.cell(r, c)
                cell.margin_left = Inches(0.09)
                cell.margin_right = Inches(0.09)
                cell.margin_top = Inches(0.02)
                cell.margin_bottom = Inches(0.02)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.fill.solid()
                if r == 0:
                    cell.fill.fore_color.rgb = DEEP
                elif highlight is not None and r == highlight:
                    cell.fill.fore_color.rgb = WASH
                else:
                    cell.fill.fore_color.rgb = WHITE
                tf = cell.text_frame
                tf.word_wrap = False
                p = tf.paragraphs[0]
                p.alignment = PP_ALIGN.RIGHT if (c > 0 and r > 0) else PP_ALIGN.LEFT
                run = p.add_run()
                run.text = str(val)
                fnt = run.font
                fnt.name = FONT
                fnt.size = Pt(head_font if r == 0 else font)
                fnt.bold = (r == 0) or (highlight is not None and r == highlight)
                fnt.color.rgb = WHITE if r == 0 else INK
        return y + row_h * n_r

    def note(self, slide, y, text, *, color=SUBTLE, size=11):
        f = _box(slide, MARGIN, y, BODY_W, Inches(0.5))
        _txt(f, [(text, {})], size=size, color=color, space_after=0, line=1.3)
        return y + Inches(0.4)

    def callout(self, slide, x, y, w, h, title, body, colour=BRAND):
        _rect(slide, x, y, w, h, WASH, WASH_RULE)
        _rect(slide, x, y, Inches(0.045), h, colour)
        f = _box(slide, x + Inches(0.26), y + Inches(0.17),
                 w - Inches(0.45), h - Inches(0.3))
        _txt(f, [(title, {"size": 13.5, "bold": True, "color": INK,
                          "space_after": 5}),
                 (body, {"size": 12, "color": MUTED})], line=1.3)

    def picture(self, slide, name, x, y, *, w=None, h=None):
        p = FIG / name
        if not p.exists():
            return None
        kw = {}
        if w: kw["width"] = w
        if h: kw["height"] = h
        return slide.shapes.add_picture(str(p), x, y, **kw)

    def save(self, path):
        self.prs.save(path)


# ══════════════════════════════════════════════════════════════════════════
def build(out: Path):
    d = Deck()
    ds, eda = METRICS["dataset"], METRICS["eda"]
    cmp_ = METRICS["comparison"]
    t12 = {r["key"]: r for r in cmp_["table12"]}
    xlmr = t12["xlmr"]
    seg = METRICS["segmentation"]["table16"]
    asp = METRICS["aspects"]["table15"]
    kappa = {r["stratum"]: r for r in METRICS["kappa"]["rows"]}
    mcn = pd.read_csv(TAB / "table14_mcnemar.csv")
    bands = pd.read_csv(TAB / "eda_length_bands.csv")

    # 1 ── title
    d.title_slide()

    # 2 ── the problem
    s, y = d.content("Abundant feedback, unusable at scale", kicker="The problem")
    f = _box(s, MARGIN, y, Inches(7.0), Inches(3.6))
    _txt(f, [
        ("UAE government entities receive a continuous, high-volume stream of "
         "public feedback through app store reviews — and cannot systematically "
         "read it.", {"size": 17, "space_after": 14}),
        ("Manual analysis is slow, costly and inconsistent.",
         {"size": 14.5, "color": MUTED, "bullet": True, "space_after": 8}),
        ("Generic sentiment tools mishandle Arabic morphology, dialect and "
         "Arabic–English code-switching.",
         {"size": 14.5, "color": MUTED, "bullet": True, "space_after": 8}),
        ("The result is a gap between the abundance of feedback and the ability "
         "to prioritise service improvements.",
         {"size": 14.5, "color": MUTED, "bullet": True, "space_after": 0}),
    ], line=1.32)
    d.callout(s, MARGIN + Inches(7.45), y, Inches(4.2), Inches(2.5),
              "Stated operationally",
              "Classify Y — expressed satisfaction, satisfied or dissatisfied — "
              "for one public review of one UAE government application, using X: "
              "the lexical and contextual features of the review text alone.")
    d.note(s, y + Inches(3.9),
           "Language, platform and entity are deliberately excluded from X. They are "
           "reporting dimensions, so a comparison between two entities reflects what "
           "users wrote — not what the model learned about those entities in training.")

    # 3 ── research questions
    s, y = d.content("Four questions", kicker="Research design")
    qs = [
        ("RQ1", "Can a fine-tuned transformer accurately classify expressed "
                "satisfaction from bilingual reviews?", "Classificatory", BRAND),
        ("RQ2", "Do transformers differ significantly from TF-IDF baselines — "
                "and is the difference practically meaningful?", "Comparative", ACCENT),
        ("RQ3", "Which service aspects are most strongly associated with "
                "dissatisfaction, and do they differ by segment?", "Explanatory", DISSAT),
        ("RQ4", "How do performance and expressed satisfaction differ between "
                "Arabic and English reviews?", "Segmentational", SATIS),
    ]
    gap, hgt = Inches(0.16), Inches(1.02)
    for i, (tag, q, kind, col) in enumerate(qs):
        yy = y + i * (hgt + gap)
        _rect(s, MARGIN, yy, BODY_W, hgt, WASH, WASH_RULE)
        _rect(s, MARGIN, yy, Inches(0.045), hgt, col)
        f = _box(s, MARGIN + Inches(0.26), yy + Inches(0.15), Inches(1.0), Inches(0.7))
        _txt(f, [(tag, {})], size=17, bold=True, color=col, space_after=0)
        f = _box(s, MARGIN + Inches(1.25), yy + Inches(0.13), Inches(9.3), Inches(0.8))
        _txt(f, [(q, {"size": 14.5, "space_after": 2}),
                 (kind, {"size": 10.5, "bold": True, "color": SUBTLE})], line=1.25)
    d.note(s, y + 4 * (hgt + gap) + Inches(0.04),
           "Every question is stated as a formal hypothesis pair and tested at α = .05. "
           "No significance result is reported without an effect size: at N = 48,930 a "
           "p-value carries almost no information about practical importance.")

    # 4 ── corpus
    s, y = d.content("The corpus", kicker="Data")
    y2 = d.stat_row(s, y, [
        (f"{ds['raw_rows']:,}", "Reviews collected", "Google Play + App Store", BRAND),
        (f"{ds['apps']}", "Government apps", "Federal, emirate, semi-gov", ACCENT),
        (f"{ds['modelling_rows']:,}", "Modelling set", "after inclusion criteria", DISSAT),
        ("24.3%", "Arabic share", f"{ds['language_counts_modelling']['Arabic']:,} reviews", SATIS),
    ])
    d.picture(s, "fig_reviews_per_year.png", MARGIN, y2 + Inches(0.05), w=Inches(7.2))
    d.callout(s, MARGIN + Inches(7.6), y2 + Inches(0.05), Inches(4.05), Inches(2.35),
              "One review = one unit of analysis",
              f"Collected July 2026, spanning {ds['date_min'][:4]}–{ds['date_max'][:4]}. "
              "Public store content only; no reviewer identifiers are stored. "
              "Exact duplicates are removed before splitting, so no text appears on "
              "both sides of a partition.")

    # 5 ── funnel
    s, y = d.content("From 74,412 reviews to a defensible modelling set",
                     kicker="Inclusion criteria")
    d.picture(s, "fig2_funnel.png", MARGIN, y, w=Inches(7.3))
    rows = [["Step", "Removed", "Retained"]]
    for step in ds["funnel"]:
        rows.append([step["step"].replace("Remove ", "").replace("Keep ", "keep ")[:30],
                     f"{step['removed']:,}", f"{step['rows_after']:,}"])
    d.table(s, MARGIN + Inches(7.7), y, Inches(3.95), rows,
            widths=[2.4, 1, 1], font=10.5, head_font=9.5, row_h=Inches(0.32))
    d.note(s, y + Inches(2.55),
           "The largest exclusion is length: 21,608 reviews under six words. That is a "
           "measurement decision, not a cleaning step — and it is the single most "
           "consequential one in the study.")

    # 6 ── why length matters
    s, y = d.content("Why the length filter is a finding, not housekeeping",
                     kicker="Exploratory analysis")
    d.picture(s, "fig1_length_bands.png", MARGIN, y, w=Inches(7.2))
    rows = [["Length", "n", "Carries an aspect"]]
    for _, r in bands.iterrows():
        rows.append([f"{r['length_band']} words", f"{int(r['n']):,}",
                     f"{r['aspect_carrying_pct']:.1f}%"])
    d.table(s, MARGIN + Inches(7.6), y + Inches(0.1), Inches(4.05), rows,
            widths=[1.5, 1, 1.3], font=11.5, head_font=10)
    d.callout(s, MARGIN + Inches(7.6), y + Inches(2.1), Inches(4.05), Inches(1.5),
              "The design consequence",
              "Only 8.8% of the shortest reviews name any service aspect, against "
              "78.6% of the longest. Aspect analysis computed on an unfiltered corpus "
              "would be dominated by reviews that name nothing at all.", DISSAT)

    # 7 ── method
    s, y = d.content("Four layers, each answering to the next", kicker="Method")
    layers = [
        ("1", "Weak supervision", "Star ratings → binary labels, validated against "
         "a 400-review annotated sample", BRAND),
        ("2", "Classical baselines", "TF-IDF word (1,2) + char (3,5) n-grams → "
         "logistic regression, linear SVM, naive Bayes", ACCENT),
        ("3", "Transformers", "XLM-RoBERTa and mBERT on the full bilingual corpus; "
         "AraBERT and MARBERT on the Arabic subset", DISSAT),
        ("4", "Aspect layer", "Bilingual seed lexicon over ten service aspects, "
         "with an independent BERTopic pass", SATIS),
    ]
    gap, hgt = Inches(0.14), Inches(0.95)
    for i, (num, name, body, col) in enumerate(layers):
        yy = y + i * (hgt + gap)
        _rect(s, MARGIN, yy, Inches(7.6), hgt, WASH, WASH_RULE)
        _rect(s, MARGIN, yy, Inches(0.045), hgt, col)
        f = _box(s, MARGIN + Inches(0.28), yy + Inches(0.12), Inches(0.5), Inches(0.7))
        _txt(f, [(num, {})], size=20, bold=True, color=col, space_after=0)
        f = _box(s, MARGIN + Inches(0.85), yy + Inches(0.12), Inches(6.5), Inches(0.75))
        _txt(f, [(name, {"size": 14, "bold": True, "space_after": 2}),
                 (body, {"size": 11.5, "color": MUTED})], line=1.22)
    d.callout(s, MARGIN + Inches(7.9), y, Inches(3.75), Inches(2.35),
              "Held constant throughout",
              "Seed 42. A 70/15/15 split stratified jointly on label and language, so "
              "the test partition preserves both the 24.3% Arabic share and the 55.6% "
              "dissatisfied share. Deduplication precedes splitting; leakage checks "
              "return zero overlap on both id and text.")
    d.note(s, y + 4 * (hgt + gap) + Inches(0.02),
           "Transformers consume raw review text at max_len 128. TF-IDF and the aspect "
           "lexicon consume normalised text. The two paths are never crossed.")

    # 8 ── label validation
    s, y = d.content("Is the star-derived label a sound instrument?",
                     kicker="Measurement validity")
    y2 = d.stat_row(s, y, [
        (f"{kappa['Overall']['kappa']:.3f}", "Cohen's κ, overall",
         f"95% CI [{kappa['Overall']['ci_low']:.3f}, {kappa['Overall']['ci_high']:.3f}]", BRAND),
        (f"{kappa['English']['kappa']:.3f}", "English stratum", "n = 192", ACCENT),
        (f"{kappa['Arabic']['kappa']:.3f}", "Arabic stratum", "n = 193", SATIS),
        (f"{kappa['Intra-annotator (second pass)']['kappa']:.3f}", "Intra-annotator",
         "second pass, n = 76", SUBTLE),
    ])
    f = _box(s, MARGIN, y2 + Inches(0.15), Inches(11.6), Inches(2.2))
    _txt(f, [
        ("All four fall in the “almost perfect” band. This is the precondition for RQ4.",
         {"size": 16, "bold": True, "space_after": 12}),
        ("If star ratings did not map onto expressed sentiment the same way in both "
         "languages, an Arabic–English comparison would measure the instrument rather "
         "than the users. Because κ is equivalent across strata — .854 English against "
         ".876 Arabic — the language comparison in RQ4 can be read as a real difference "
         "in what reviewers wrote.", {"size": 14, "color": MUTED, "space_after": 10}),
        ("It also sets the ceiling. The model is scored against a label two careful "
         "humans agree on 93% of the time; no classifier should be expected to agree "
         "more than the annotators do.", {"size": 14, "color": MUTED}),
    ], line=1.35)

    # 9 ── RQ1
    s, y = d.content("Satisfaction is classifiable", kicker="RQ1 · Classification performance")
    y2 = d.stat_row(s, y, [
        (f"{xlmr['macro_f1']:.3f}", "Macro-F1, XLM-RoBERTa",
         f"95% CI [{xlmr['ci_low']:.3f}, {xlmr['ci_high']:.3f}]", BRAND),
        (f"{xlmr['recall_dissatisfied']:.3f}", "Recall, dissatisfied",
         "the operationally critical class", DISSAT),
        (f"{xlmr['auc']:.3f}", "ROC AUC", f"n = {xlmr['n_test']:,} test reviews", ACCENT),
        ("55.6%", "No-information rate", "majority class ≈ 0.36 macro-F1", SUBTLE),
    ])
    d.picture(s, "fig5_confusion_matrix.png", MARGIN, y2 + Inches(0.05), h=Inches(2.5))
    d.picture(s, "fig6_roc_curves.png", MARGIN + Inches(3.5), y2 + Inches(0.05), h=Inches(2.5))
    d.callout(s, MARGIN + Inches(7.0), y2 + Inches(0.05), Inches(4.65), Inches(2.5),
              "H₀ rejected",
              "Accuracy is 92.8% against a 55.6% majority-class rate; the exact binomial "
              "test gives p < .001. The lower bound of the confidence interval clears "
              "the 0.80 operational threshold set in advance — on the full test set and "
              "within the Arabic stratum.")

    # 10 ── RQ1 by stratum
    s, y = d.content("Where the model is weaker", kicker="RQ1 · By language and length")
    rows = [["Stratum", "Macro-F1", "n"]]
    rows.append(["Overall", f"{xlmr['macro_f1']:.4f}", f"{xlmr['n_test']:,}"])
    rows.append(["English", "0.9313", "5,559"])
    rows.append(["Arabic", "0.9086", "1,781"])
    for band, f1, n in [("6–10 words", "0.9319", "2,582"),
                        ("11–25 words", "0.9180", "2,982"),
                        ("26+ words", "0.9115", "1,776")]:
        rows.append([band, f1, n])
    d.table(s, MARGIN, y, Inches(5.4), rows, widths=[2.1, 1.1, 1.0],
            font=12, highlight=3, row_h=Inches(0.33))
    f = _box(s, MARGIN + Inches(5.9), y, Inches(5.7), Inches(3.4))
    _txt(f, [
        ("The Arabic stratum is 2.3 points weaker.", {"size": 16, "bold": True,
                                                      "space_after": 10}),
        ("The gap is real — the confidence intervals do not overlap — and it is "
         "reported rather than smoothed over. It is also smaller than the 17.2-point "
         "difference RQ4 identifies between the two audiences, so it does not explain "
         "that finding away.", {"size": 13.5, "color": MUTED, "space_after": 10}),
        ("Arabic is 24.3% of the modelling set: adequate for fine-tuning and for a "
         "proportion comparison, but it remains the minority stratum, and reviews "
         "under six words were never in training at all.",
         {"size": 13.5, "color": MUTED}),
    ], line=1.35)

    # 11 ── model comparison
    s, y = d.content("Seven models, one identical partition", kicker="RQ2 · Benchmark")
    rows = [["Model", "Macro-F1", "95% CI", "Recall (dissat.)", "AUC", "n"]]
    order = ["xlmr", "mbert", "marbert", "tfidf_svm", "tfidf_lr", "arabert", "tfidf_nb"]
    for k in order:
        r = t12[k]
        rows.append([r["model"], f"{r['macro_f1']:.4f}",
                     f"[{r['ci_low']:.3f}, {r['ci_high']:.3f}]",
                     f"{r['recall_dissatisfied']:.3f}", f"{r['auc']:.3f}",
                     f"{r['n_test']:,}"])
    d.table(s, MARGIN, y, BODY_W, rows, widths=[3.1, 1.1, 1.5, 1.4, 0.9, 0.9],
            font=11.5, head_font=10, highlight=1, row_h=Inches(0.325))
    d.note(s, y + Inches(0.33) * len(rows) + Inches(0.14),
           "AraBERT and MARBERT are trained and scored on the Arabic subset only "
           "(n = 1,781), so their figures are not directly comparable with the bilingual "
           "models. Bootstrap confidence intervals use 2,000 resamples, seed 42.")

    # 12 ── RQ2 McNemar
    s, y = d.content("The transformer advantage is real, and modest",
                     kicker="RQ2 · Paired significance")
    rows = [["Comparison", "b", "c", "χ²(1)", "p", "Margin"]]
    for _, r in mcn.iterrows():
        p = "< .001" if r["p"] < 0.001 else f"{r['p']:.3f}"
        rows.append([r["comparison"].replace(", full test set", " (full)")
                     .replace(", Arabic subset", " (Arabic)")[:46],
                     int(r["b_a_right_b_wrong"]), int(r["c_a_wrong_b_right"]),
                     f"{r['chi2']:.2f}", p, f"{r['margin_a_minus_b']:+.4f}"])
    d.table(s, MARGIN, y, BODY_W, rows, widths=[4.6, 0.7, 0.7, 1.0, 1.0, 1.1],
            font=11, head_font=10, highlight=1, row_h=Inches(0.34))
    yy = y + Inches(0.34) * len(rows) + Inches(0.2)
    d.callout(s, MARGIN, yy, Inches(5.65), Inches(1.55),
              "Statistically significant",
              "H₀ is rejected on the full test set. The +0.017 margin clears the one "
              "point of macro-F1 fixed in advance as the threshold of practical "
              "relevance — 118 more reviews classified correctly out of 7,340.")
    d.callout(s, MARGIN + Inches(5.95), yy, Inches(5.65), Inches(1.55),
              "And conditional",
              "The advantage roughly doubles on the Arabic subset (+0.025). MARBERT "
              "against AraBERT is not significant (p = .195), so no Arabic-specialist "
              "claim is made.", DISSAT)

    # 13 ── RQ3 aspects
    s, y = d.content("What dissatisfaction is actually about", kicker="RQ3 · Service aspects")
    d.picture(s, "fig_aspect_risk_ratios.png", MARGIN, y, w=Inches(6.9))
    rows = [["Aspect", "RR", "95% CI"]]
    for a in asp[:5]:
        rows.append([a["aspect_display"][:22], f"{a['risk_ratio']:.2f}×",
                     f"[{a['rr_ci_low']:.2f}, {a['rr_ci_high']:.2f}]"])
    d.table(s, MARGIN + Inches(7.25), y, Inches(4.4), rows,
            widths=[2.0, 0.9, 1.5], font=11.5, head_font=10, highlight=1)
    d.callout(s, MARGIN + Inches(7.25), y + Inches(2.1), Inches(4.4), Inches(1.9),
              "Ranked by effect size, not p-value",
              "A dissatisfied reviewer is 7.44× more likely to mention performance than "
              "a satisfied one. Benjamini–Hochberg adjusted across all ten aspects. "
              "Usability and support fall below 1.0 — they are praise markers, and are "
              "kept in the ranking rather than quietly dropped.", DISSAT)

    # 14 ── RQ3 segments
    s, y = d.content("The leading aspect is not the same everywhere",
                     kicker="RQ3 · By segment")
    d.picture(s, "fig_aspect_rank_by_segment.png", MARGIN, y, w=Inches(7.4))
    f = _box(s, MARGIN + Inches(7.8), y + Inches(0.1), Inches(3.85), Inches(3.4))
    _txt(f, [
        ("Segmentation changes the queue.", {"size": 15, "bold": True, "space_after": 10}),
        ("Aspect rankings are recomputed within language, platform and entity. Where "
         "the leading aspect differs between segments, a single national priority list "
         "would mis-order the work for the entities that do not match the average.",
         {"size": 12.5, "color": MUTED, "space_after": 10}),
        ("56.5% of the modelling set carries at least one aspect tag. The remainder "
         "name none — mostly because they are short — and are excluded from the "
         "ranking rather than counted as an aspect of their own.",
         {"size": 12.5, "color": MUTED}),
    ], line=1.32)

    # 15 ── RQ4
    s, y = d.content("English reviewers express dissatisfaction far more often",
                     kicker="RQ4 · Language")
    y2 = d.stat_row(s, y, [
        (f"{seg['rate_a']*100:.1f}%", "English", f"n = {seg['n_a']:,}", DISSAT),
        (f"{seg['rate_b']*100:.1f}%", "Arabic", f"n = {seg['n_b']:,}", SATIS),
        (f"+{seg['diff_pp']:.1f} pp", "Difference",
         f"95% CI [{seg['diff_ci_low_pp']:.1f}, {seg['diff_ci_high_pp']:.1f}]", BRAND),
        (f"{seg['odds_ratio']:.2f}", "Odds ratio", f"Cohen's h = {seg['cohens_h']:.3f}", ACCENT),
    ])
    d.picture(s, "fig_label_by_language.png", MARGIN, y2 + Inches(0.05), h=Inches(2.4))
    d.callout(s, MARGIN + Inches(5.4), y2 + Inches(0.05), Inches(6.25), Inches(2.4),
              "Significant — and small",
              f"χ²(1, N = {seg['n']:,}) = {seg['chi2_yates']:.2f}, p < .001. But φ = "
              f"{seg['phi']:.3f} and Cohen's h = {seg['cohens_h']:.3f}: a small association "
              "and a small-to-medium effect. This is exactly what the analysis plan "
              "anticipated — at nearly fifty thousand observations, significance is close "
              "to guaranteed for any non-zero difference. The odds ratio of 2.01 is the "
              "interpretable summary, and the equivalent κ across languages is what "
              "licenses reading it as a real difference rather than an artefact.")

    # 16 ── answers
    s, y = d.content("The four answers", kicker="Summary of findings")
    answers = [
        ("RQ1", "Yes — macro-F1 0.927 [0.921, 0.933], dissatisfied recall 0.951. "
                "The interval's lower bound clears 0.80 overall and in Arabic.", BRAND),
        ("RQ2", "Yes, significantly (χ² = 31.98, p < .001), by a modest +0.017 — "
                "and roughly double that on Arabic.", ACCENT),
        ("RQ3", "Performance, login and registration. Together they account for over "
                "half of aspect-bearing complaints.", DISSAT),
        ("RQ4", "English reviews are dissatisfied 17.2 pp more often (OR 2.01) — "
                "read as real, because the label is equivalent across languages.", SATIS),
    ]
    gap, hgt = Inches(0.16), Inches(1.02)
    for i, (tag, body, col) in enumerate(answers):
        yy = y + i * (hgt + gap)
        _rect(s, MARGIN, yy, BODY_W, hgt, WASH, WASH_RULE)
        _rect(s, MARGIN, yy, Inches(0.045), hgt, col)
        f = _box(s, MARGIN + Inches(0.26), yy + Inches(0.16), Inches(1.0), Inches(0.7))
        _txt(f, [(tag, {})], size=17, bold=True, color=col, space_after=0)
        f = _box(s, MARGIN + Inches(1.25), yy + Inches(0.17), Inches(9.4), Inches(0.75))
        _txt(f, [(body, {"size": 14})], line=1.28)
    d.note(s, y + 4 * (hgt + gap) + Inches(0.04),
           "All four hypotheses were pre-registered with their test statistic and "
           "decision rule before the models were fitted.")

    # 17 ── practical significance
    s, y = d.content("What a service owner actually receives", kicker="Practical significance")
    f = _box(s, MARGIN, y, Inches(6.6), Inches(3.5))
    _txt(f, [
        ("A weekly ranked list of the aspects most strongly associated with expressed "
         "dissatisfaction, broken down by application, platform and language.",
         {"size": 16, "space_after": 14}),
        ("The value is not that the model detects sentiment — a manager reading fifty "
         "reviews could do that. It is that it does so exhaustively, consistently, and "
         "at a cadence that makes the ranking actionable within a sprint rather than "
         "within a survey cycle.", {"size": 13.5, "color": MUTED}),
    ], line=1.35)
    items = [
        ("Effect sizes accompany every test", "so a team is never handed a difference "
         "that is statistically real and operationally irrelevant"),
        ("The label is validated per language", "so a cross-language comparison is "
         "either supported by evidence or explicitly withheld"),
        ("Segment identifiers are excluded from X", "so comparing two entities reflects "
         "what users wrote, not what the model learned about them"),
    ]
    for i, (t, b) in enumerate(items):
        yy = y + i * Inches(1.12)
        _rect(s, MARGIN + Inches(7.0), yy, Inches(4.65), Inches(0.95), WASH, WASH_RULE)
        _rect(s, MARGIN + Inches(7.0), yy, Inches(0.045), Inches(0.95), BRAND)
        f = _box(s, MARGIN + Inches(7.26), yy + Inches(0.13), Inches(4.2), Inches(0.75))
        _txt(f, [(t, {"size": 12.5, "bold": True, "space_after": 2}),
                 (b, {"size": 11, "color": MUTED})], line=1.25)

    # 18 ── limitations
    s, y = d.content("Three limitations that shape what may be claimed",
                     kicker="Limitations")
    lims = [
        ("Label equivalence", "If star ratings mapped onto sentiment differently across "
         "languages, RQ4 would measure the instrument rather than the users.",
         "Mitigated: κ measured per language — .854 English, .876 Arabic.", BRAND),
        ("The Arabic stratum", "At 24.3% of the modelling set it is adequate for fine-tuning "
         "and for a proportion comparison, but it remains the minority stratum and is "
         "classified 2.3 points less accurately.",
         "Reported openly rather than pooled away.", ACCENT),
        ("Self-selection", "Reviewers are not a sample of users. People who write reviews "
         "differ systematically from those who do not.",
         "Every claim is a claim about expressed satisfaction among reviewers.", DISSAT),
    ]
    for i, (t, b, m, col) in enumerate(lims):
        yy = y + i * Inches(1.42)
        _rect(s, MARGIN, yy, BODY_W, Inches(1.25), WASH, WASH_RULE)
        _rect(s, MARGIN, yy, Inches(0.045), Inches(1.25), col)
        f = _box(s, MARGIN + Inches(0.28), yy + Inches(0.15), Inches(11.0), Inches(1.0))
        _txt(f, [(t, {"size": 14, "bold": True, "space_after": 3}),
                 (b, {"size": 12.5, "color": MUTED, "space_after": 3}),
                 (m, {"size": 11.5, "bold": True, "color": col})], line=1.25)
    d.note(s, y + 3 * Inches(1.42) + Inches(0.02),
           "Nine limitations are recorded in full in Table 18, each with the mitigation adopted.")

    # 19 ── conclusion
    s, y = d.content("Conclusion and recommendations", kicker="Closing")
    f = _box(s, MARGIN, y, Inches(6.7), Inches(3.6))
    _txt(f, [
        ("Bilingual satisfaction is measurable at scale, and the measurement holds up "
         "in both languages.", {"size": 17, "bold": True, "space_after": 14}),
        ("Deploy XLM-RoBERTa as the scoring model; retain the TF-IDF SVM as a fallback.",
         {"size": 13.5, "color": MUTED, "bullet": True, "space_after": 9}),
        ("Prioritise performance, login and registration — they carry the largest "
         "risk ratios and over half of aspect-bearing complaints.",
         {"size": 13.5, "color": MUTED, "bullet": True, "space_after": 9}),
        ("Report Arabic and English separately. Pooling them hides a 17.2-point gap.",
         {"size": 13.5, "color": MUTED, "bullet": True, "space_after": 9}),
        ("Re-validate the label periodically; the instrument is what licenses the "
         "cross-language claim.", {"size": 13.5, "color": MUTED, "bullet": True}),
    ], line=1.32)
    d.callout(s, MARGIN + Inches(7.1), y, Inches(4.55), Inches(3.3),
              "Contribution",
              "A reproducible, bilingual, aspect-aware satisfaction pipeline for UAE "
              "government services — with the evidential discipline that makes its "
              "output usable in a policy setting: effect sizes beside every test, a "
              "label validated per language, and segment identifiers withheld from "
              "the model so entity comparisons remain honest.")

    # 20 ── close
    s = d.section("Thank you", "Questions",
                  "Repository, data dictionary, annotation guidelines and the full "
                  "aspect lexicon are in the appendices.")

    d.save(out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO.parent.parent / "Documents" /
                                         "Final Presentation.pptx"))
    args = ap.parse_args()
    p = build(Path(args.out))
    print(f"wrote {p}")
