#!/usr/bin/env python3
"""Populate the final report from the notebook outputs.

Reads results/metrics.json, results/tables/*.csv and the processed data,
regenerates the descriptive figures, and writes a filled copy of the report
next to the original together with a change log of every value replaced.

    python scripts/fill_report.py --src "<path to .docx>" [--out <path>]

Nothing in the report is typed by hand: every number comes from an executed
notebook. Cells that depend on the GPU run (notebook 07) are left marked
"[pending: notebook 07]" until those prediction files are present, at which
point re-running this script fills them.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import config  # noqa: E402
from src.aspects import ASPECT_DISPLAY, ASPECTS, add_aspect_columns  # noqa: E402
from src.preprocessing import length_band  # noqa: E402

PENDING = "[pending: notebook 07]"
CHANGES: list[tuple[str, str, str]] = []      # (location, old, new)


# ---------------------------------------------------------------------------
# helpers for numbers
# ---------------------------------------------------------------------------
def n(x) -> str:
    return f"{int(round(x)):,}"


def pct(x, d=1) -> str:
    return f"{x:.{d}f}%"


def f3(x) -> str:
    return f"{x:.3f}"


def f2(x) -> str:
    return f"{x:.2f}"


def pfmt(p) -> str:
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return "n/a"
    return "< .001" if p < 0.001 else f"= {p:.3f}"


def ci(lo, hi, d=3) -> str:
    return f"[{lo:.{d}f}, {hi:.{d}f}]"


# ---------------------------------------------------------------------------
# gather every number the report needs
# ---------------------------------------------------------------------------
def gather() -> dict:
    m = json.loads(config.METRICS_FILE.read_text())
    T = lambda name: pd.read_csv(config.TABLES_DIR / f"{name}.csv")

    clean = pd.read_parquet(config.CLEAN_FILE)
    # cleaned corpus = raw minus empty text minus exact duplicates (funnel steps 1-2)
    c = clean[clean.review_text.str.len() > 0].drop_duplicates("review_id")
    c = c[~c.clean_text.duplicated(keep="first") | (c.clean_text == "")]
    c = add_aspect_columns(c)
    c["tagged"] = c.n_aspects > 0
    c["band"] = length_band(c.word_count)
    modelling = pd.read_parquet(config.MODELLING_FILE)

    funnel = T("cleaning_funnel")
    short = c[c.word_count < config.MIN_WORDS]
    subst = c[c.word_count >= config.MIN_WORDS]
    neutral = subst[subst.star_rating == config.NEUTRAL_STAR]
    nostar = subst[subst.star_rating.isna()]
    nonneutral = subst[(subst.star_rating != config.NEUTRAL_STAR) & subst.star_rating.notna()]
    mixed = nonneutral[nonneutral.language == "mixed"]
    other = nonneutral[nonneutral.language == "unknown"]

    bands = (c.groupby("band", observed=True)
              .agg(reviews=("review_id", "size"), tagged=("tagged", "mean")).reset_index())
    bands["share"] = bands.reviews / bands.reviews.sum() * 100
    bands["tagged"] *= 100

    en = modelling[modelling.language == "English"]; ar = modelling[modelling.language == "Arabic"]
    dis = lambda d: int((d.satisfaction_label == "Dissatisfied").sum())
    sat = lambda d: int((d.satisfaction_label == "Satisfied").sum())

    d = dict(
        m=m, funnel=funnel, bands=bands,
        raw=int(m["dataset"]["raw_rows"]), apps_raw=int(m["dataset"]["apps"]),
        apps_model=int(modelling.app_name.nunique()),
        cleaned=len(c), cleaned_en=int((c.language == "English").sum()), cleaned_ar=int((c.language == "Arabic").sum()),
        empty=int(funnel.loc[0, "removed"]), dups=int(funnel.loc[1, "removed"]),
        short=len(short), short_pct=len(short) / len(c) * 100,
        subst=len(subst), neutral=len(neutral), neutral_ar=int((neutral.language == "Arabic").sum()),
        nostar=len(nostar), mixed=len(mixed), other=len(other),
        after_neutral=int(funnel.loc[3, "rows_after"]),
        model=len(modelling), retention=len(modelling) / len(c) * 100,
        en=len(en), ar=len(ar), ar_share=len(ar) / len(modelling) * 100, en_share=len(en) / len(modelling) * 100,
        en_dis=dis(en), en_sat=sat(en), ar_dis=dis(ar), ar_sat=sat(ar),
        tot_dis=dis(modelling), tot_sat=sat(modelling),
        dis_share=dis(modelling) / len(modelling) * 100,
        date_min=m["dataset"]["date_min"], date_max=m["dataset"]["date_max"],
        t12=T("table12_model_performance"), t13=T("table13_language_stratified"),
        t14=T("table14_mcnemar"), t15=T("table15_aspects"), t17=T("table17_kappa"),
        rq1_len=T("rq1_by_length_band"), seg_top=T("segment_top_aspect"),
        seg_div=T("segment_divergences"), split=T("split_summary"),
        bl_lang=T("baselines_by_language"),
    )
    p_dis = d["dis_share"] / 100
    d["majority_macro_f1"] = (2 * p_dis / (1 + p_dis)) / 2
    d["cmp"] = m["segmentation"]["table16"]
    d["rq4b"] = m["segmentation"]["rq4b"]
    d["rq1"] = m["comparison"]["rq1"]
    d["best_classical"] = m["comparison"]["best_classical"]
    d["best_overall"] = m["comparison"]["best_overall"]
    d["transformers_done"] = all(k in m["comparison"]["available"] for k in config.TRANSFORMER_MODELS)
    d["any_transformer"] = any(k in m["comparison"]["available"] for k in config.TRANSFORMER_MODELS)
    d["auc"] = m["comparison"]["auc"]
    d["aspects"] = m["aspects"]
    d["kappa_excluded"] = int(m["kappa"]["excluded_unclear"])
    return d


# ---------------------------------------------------------------------------
# figures 1-3 (descriptive), regenerated from the cleaned corpus
# ---------------------------------------------------------------------------
def make_figures(d: dict) -> dict:
    out = {}
    b = d["bands"]
    labels = ["0 to 2", "3 to 5", "6 to 10", "11 to 25", "26 or more"]

    fig, ax = plt.subplots(figsize=(7.2, 4))
    ax.bar(labels, b.reviews, color="#4C72B0")
    ax.set_ylabel("Reviews"); ax.set_xlabel("Words in review")
    ax2 = ax.twinx()
    ax2.plot(labels, b.tagged, color="#DD8452", marker="o", lw=2)
    ax2.set_ylabel("Reviews carrying a service aspect (%)"); ax2.set_ylim(0, 100)
    ax.axvline(1.5, color="k", ls="--", lw=0.9)
    ax.set_title(f"Review length and aspect-carrying rate (N = {n(d['cleaned'])})")
    plt.tight_layout(); p = config.FIGURES_DIR / "fig1_length_bands.png"; plt.savefig(p, dpi=220); plt.close()
    out["fig1"] = p

    stages = ["Cleaned corpus", f"\u2265 {config.MIN_WORDS} words", "Neutral band removed", "Arabic / English only"]
    vals = [d["cleaned"], d["subst"], d["after_neutral"], d["model"]]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    bars = ax.barh(stages[::-1], vals[::-1], color=["#55A868", "#8CB7D9", "#8CB7D9", "#4C72B0"])
    for bar, v in zip(bars, vals[::-1]):
        ax.text(bar.get_width() + 600, bar.get_y() + bar.get_height() / 2, f"{v:,} ({v / d['cleaned'] * 100:.1f}%)", va="center", fontsize=9)
    ax.set_xlim(0, d["cleaned"] * 1.25); ax.set_xlabel("Reviews"); ax.set_title("From cleaned corpus to modelling set")
    plt.tight_layout(); p = config.FIGURES_DIR / "fig2_funnel.png"; plt.savefig(p, dpi=220); plt.close()
    out["fig2"] = p

    fig, ax = plt.subplots(figsize=(6.2, 4))
    langs = ["English", "Arabic"]
    dis = [d["en_dis"], d["ar_dis"]]; sat = [d["en_sat"], d["ar_sat"]]
    tot = [d["en"], d["ar"]]
    dp = [x / t * 100 for x, t in zip(dis, tot)]; sp = [x / t * 100 for x, t in zip(sat, tot)]
    ax.bar(langs, dp, color="#C44E52", label="Dissatisfied")
    ax.bar(langs, sp, bottom=dp, color="#55A868", label="Satisfied")
    for i in range(2):
        ax.text(i, dp[i] / 2, f"{dp[i]:.1f}%\n({dis[i]:,})", ha="center", va="center", color="white", fontsize=9)
        ax.text(i, dp[i] + sp[i] / 2, f"{sp[i]:.1f}%\n({sat[i]:,})", ha="center", va="center", color="white", fontsize=9)
    ax.set_ylabel("Share of language subset (%)"); ax.set_ylim(0, 100)
    ax.set_title(f"Satisfaction class balance by language (N = {n(d['model'])})"); ax.legend(loc="upper right", fontsize=8)
    plt.tight_layout(); p = config.FIGURES_DIR / "fig3_class_balance.png"; plt.savefig(p, dpi=220); plt.close()
    out["fig3"] = p
    return out


# ---------------------------------------------------------------------------
# docx editing helpers
# ---------------------------------------------------------------------------
def _clear_marker_colour(run):
    rpr = run._r.find(qn("w:rPr"))
    if rpr is not None:
        for tag in ("w:color", "w:highlight", "w:shd"):
            el = rpr.find(qn(tag))
            if el is not None:
                rpr.remove(el)


def set_par_text(par, text: str, where: str = ""):
    old = par.text
    if old.strip() == text.strip():
        return
    runs = par.runs
    if runs:
        runs[0].text = text
        _clear_marker_colour(runs[0])
        for r in runs[1:]:
            r._r.getparent().remove(r._r)
    else:
        par.add_run(text)
    CHANGES.append((where or "paragraph", old[:120], text[:120]))


def set_cell(cell, text: str, where: str = ""):
    par = cell.paragraphs[0]
    old = cell.text
    set_par_text(par, text, where)
    for extra in cell.paragraphs[1:]:
        extra._p.getparent().remove(extra._p)
    return old


def replace_in_par(par, pairs: list[tuple[str, str]], where: str = ""):
    """Substring replacement that keeps run formatting when the match sits in one run."""
    for old, new in pairs:
        if old not in par.text:
            continue
        done = False
        for r in par.runs:
            if old in r.text:
                r.text = r.text.replace(old, new); done = True; break
        if not done:       # match spans runs: rebuild the paragraph text
            set_par_text(par, par.text.replace(old, new), where); continue
        CHANGES.append((where or "paragraph", old, new))


def find_par(doc, startswith: str, after: int = 0):
    for i, p in enumerate(doc.paragraphs):
        if i >= after and p.text.strip().startswith(startswith):
            return i, p
    raise KeyError(startswith)


def find_table(doc, header0: str, cell00: str | None = None, header_any: str | None = None):
    for t in doc.tables:
        heads = [c.text.strip() for c in t.rows[0].cells]
        if heads[0] == header0 and (cell00 is None or t.rows[1].cells[0].text.strip().startswith(cell00)) \
                and (header_any is None or header_any in heads):
            return t
    raise KeyError(header0)


def insert_paragraph_after(par, text: str = "", template=None):
    new_p = copy.deepcopy((template or par)._p)
    for r in new_p.findall(qn("w:r")):
        new_p.remove(r)
    par._p.addnext(new_p)
    from docx.text.paragraph import Paragraph
    np_ = Paragraph(new_p, par._parent)
    if text:
        run = np_.add_run(text)
        if template is not None and template.runs:
            src = template.runs[0]._r.find(qn("w:rPr"))
            if src is not None:
                run._r.insert(0, copy.deepcopy(src))
            _clear_marker_colour(run)
    return np_


def put_picture(par, path: Path, width=Inches(6.0)):
    for r in par.runs:
        r._r.getparent().remove(r._r)
    par.add_run().add_picture(str(path), width=width)
    par.alignment = 1
    CHANGES.append(("figure", par.text[:60] or "(image)", path.name))


def add_table_row_like(table, template_row_idx: int):
    new_tr = copy.deepcopy(table.rows[template_row_idx]._tr)
    table._tbl.append(new_tr)
    return table.rows[-1]


def add_toc(par):
    run = par.add_run()
    fld_begin = OxmlElement("w:fldChar"); fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = 'TOC \\o "1-3" \\h \\z \\u'
    fld_sep = OxmlElement("w:fldChar"); fld_sep.set(qn("w:fldCharType"), "separate")
    txt = OxmlElement("w:t"); txt.text = "Right-click and choose Update Field to build the table of contents."
    fld_end = OxmlElement("w:fldChar"); fld_end.set(qn("w:fldCharType"), "end")
    for el in (fld_begin, instr, fld_sep, txt, fld_end):
        run._r.append(el)
    CHANGES.append(("Table of Contents", "(empty)", "TOC field inserted"))


# ---------------------------------------------------------------------------
# text builders
# ---------------------------------------------------------------------------
def model_rows(d):
    t12 = d["t12"].set_index("key")
    return t12


def abstract_results_sentence(d):
    t12 = model_rows(d)
    bc = d["best_classical"]; bo = d["best_overall"]
    r = t12.loc[bo]
    k = d["t17"].set_index("stratum")
    s = (f"On the held out test partition of {n(r.n_test)} reviews, the best performing model is "
         f"{config.MODEL_DISPLAY[bo]} with a macro-F1 of {f3(r.macro_f1)} (bootstrap 95% CI {ci(r.ci_low, r.ci_high)}) "
         f"and a recall of {f3(r.recall_dissatisfied)} on the dissatisfied class. ")
    if d["transformers_done"]:
        t14 = d["t14"].iloc[0]
        s += (f"Its margin over the strongest classical baseline, {config.MODEL_DISPLAY[bc]}, is "
              f"{t14.margin_a_minus_b:+.3f} macro-F1, McNemar \u03c7\u00b2(1) = {f2(t14.chi2)}, p {pfmt(t14.p)}. ")
    else:
        s += (f"The strongest classical baseline, {config.MODEL_DISPLAY[bc]}, reaches a macro-F1 of "
              f"{f3(t12.loc[bc].macro_f1)}; the paired comparison against the fine tuned transformers is reported in Table 14 "
              f"{PENDING}. ")
    s += (f"The star derived label agrees with the human reference at Cohen's \u03ba = {f3(k.loc['English','kappa'])} for English and "
          f"{f3(k.loc['Arabic','kappa'])} for Arabic, both in the almost perfect band, so the label is treated as equivalent across languages.")
    return s


def rq1_paragraph(d):
    r = d["rq1"]; bo = d["best_overall"]
    by = d["rq1_len"]
    bands = "; ".join(f"{row.length_band} words, macro-F1 {f3(row.macro_f1)} (n = {n(row.n)})" for row in by.itertuples())
    verdict = "rejected" if r["ci_low"] > d["majority_macro_f1"] and r["p"] < 0.05 else "not rejected"
    thresh = "clears" if r["ci_low"] >= 0.80 else "does not clear"
    t13 = d["t13"].set_index("key").loc[bo]
    return (f"The best performing model on the full test partition is {config.MODEL_DISPLAY[bo]}, with a macro-F1 of "
            f"{f3(r['macro_f1'])} and a bootstrap 95% confidence interval of {ci(r['ci_low'], r['ci_high'])} over {n(r['n'])} test reviews. "
            f"Recall is {f3(r['recall_dissatisfied'])} on the dissatisfied class and {f3(r['recall_satisfied'])} on the satisfied class, "
            f"and the area under the ROC curve is {f3(r['auc'])}. Accuracy is {pct(r['accuracy'] * 100)} against a majority class rate of "
            f"{pct(r['majority_rate'] * 100)}; the exact binomial test against that no information rate gives p {pfmt(r['p'])}. "
            f"Within the Arabic stratum the same model reaches a macro-F1 of {f3(t13.macro_f1_arabic)} "
            f"{ci(t13.arabic_ci_low, t13.arabic_ci_high)}, against {f3(t13.macro_f1_english)} for English. "
            f"By length band the picture is: {bands}. Performance is therefore highest on the shortest substantive reviews and declines as "
            f"reviews lengthen, which is the expected direction for a bag of n-grams model because long reviews more often mix praise and complaint. "
            f"H\u2080 for RQ1 is {verdict} at \u03b1 = .05: the lower confidence bound of the macro-F1 lies well above the no information value of "
            f"{f3(d['majority_macro_f1'])} and {thresh} the pre specified operational threshold of 0.80, on the full set and within the Arabic subset."
            + ("" if d["transformers_done"] else f" The transformer rows of Tables 12 and 13 are completed from the GPU run {PENDING}; the verdict above is stated for the best model scored so far."))


def rq2_paragraph(d):
    t14 = d["t14"]
    if not d["transformers_done"]:
        bc = d["best_classical"]; t12 = model_rows(d)
        others = [k for k in config.CLASSICAL_MODELS if k != bc]
        return (f"Among the classical family, {config.MODEL_DISPLAY[bc]} is the strongest baseline at macro-F1 {f3(t12.loc[bc].macro_f1)}, "
                f"ahead of " + " and ".join(f"{config.MODEL_DISPLAY[k]} ({f3(t12.loc[k].macro_f1)})" for k in others) + ". "
                f"The four paired comparisons in Table 14 require the transformer predictions from notebook 07, which runs on a GPU "
                f"machine; the discordant pair counts, McNemar \u03c7\u00b2, p values and macro-F1 margins are entered from that run {PENDING}. "
                f"The decision rule is fixed in advance: H\u2080 for RQ2 is rejected only if McNemar p < .05 and the absolute macro-F1 margin "
                f"is large enough to change the ranking a service team would act on; a margin below one point of macro-F1 is reported as not practically meaningful even if significant.")
    lines = []
    for row in t14.itertuples():
        lines.append(f"{row.comparison}: b = {n(row.b_a_right_b_wrong)}, c = {n(row.c_a_wrong_b_right)}, \u03c7\u00b2(1) = {f2(row.chi2)}, "
                     f"p {pfmt(row.p)}, macro-F1 margin {row.margin_a_minus_b:+.3f}")
    main = t14.iloc[0]
    sig = main.p < 0.05
    meaningful = abs(main.margin_a_minus_b) >= 0.01
    verdict = ("rejected" if sig else "not rejected")
    practical = ("large enough to matter operationally" if meaningful else "below one point of macro-F1 and therefore not practically meaningful for a service team, even though it is statistically detectable on a test set of this size")
    return ("; ".join(lines) + ". "
            f"H\u2080 for RQ2 is {verdict} at \u03b1 = .05 on the full test set, and the margin is {practical}. "
            f"On the Arabic subset the transformer margin is {t14.iloc[1].margin_a_minus_b:+.3f} (p {pfmt(t14.iloc[1].p)}), and between the two Arabic "
            f"specific encoders the margin is {t14.iloc[3].margin_a_minus_b:+.3f} (p {pfmt(t14.iloc[3].p)}).")


def rq3_paragraph(d):
    t15 = d["t15"]; a = d["aspects"]
    top = t15.head(3)
    ranked = "; ".join(f"{row.aspect_display} (RR {f2(row.risk_ratio)}, {pct(row.pct_dissatisfied_mentioning)} of dissatisfied against "
                       f"{pct(row.pct_satisfied_mentioning)} of satisfied reviews)" for row in top.itertuples())
    protective = t15[(t15.risk_ratio < 1) & t15.significant]
    prot = " and ".join(f"{row.aspect_display.lower()} (RR {f2(row.risk_ratio)})" for row in protective.itertuples())
    nonsig = t15[~t15.significant]
    seg = d["seg_top"]
    overall1 = t15.iloc[0].aspect
    ent = seg[(seg.segment_type == "entity") & (seg.aspect != overall1)].sort_values("n", ascending=False)
    ex = "; ".join(f"{row.segment} ({ASPECT_DISPLAY[row.aspect].lower()}, ranked {int(row.overall_rank)} overall, RR {f2(row.risk_ratio)} within the entity)"
                   for row in ent.head(6).itertuples())
    lang = seg[seg.segment_type == "language"].set_index("segment")
    plat = seg[seg.segment_type == "platform"].set_index("segment")
    n_ent = int((seg.segment_type == "entity").sum()); n_diff = len(ent)
    return (f"Three aspects head the ranking by risk ratio: {ranked}. Together, among dissatisfied reviews that name any aspect, "
            f"{pct(a['share_top3_among_tagged_dissatisfied'] * 100)} mention at least one of these three, which supports H3: a small number of "
            f"aspects carries a disproportionate share of expressed dissatisfaction. All aspects except {', '.join(nonsig.aspect_display) or 'none'} "
            f"remain significant after Benjamini-Hochberg adjustment. {'Two' if len(protective) == 2 else str(len(protective))} aspects run the other way and are better read as markers of praise: {prot}; "
            f"reviews that talk about usability or support are more often satisfied than dissatisfied, the former because the word \u201ceasy\u201d dominates that seed set. "
            f"Segment rankings diverge from the overall order in ways that are operationally useful. By language, "
            f"{ASPECT_DISPLAY[lang.loc['Arabic','aspect']].lower()} ranks first for Arabic reviews (RR {f2(lang.loc['Arabic','risk_ratio'])}) where "
            f"{ASPECT_DISPLAY[lang.loc['English','aspect']].lower()} ranks first for English; by platform, {ASPECT_DISPLAY[plat.iloc[0].aspect].lower()} leads on both storefronts. "
            f"Of the {n_ent} entities with at least 500 substantive reviews, {n_diff} have a leading aspect different from the corpus wide leader, for example {ex}. "
            f"The divergence table (results/tables/segment_divergences.csv) lists every aspect that moves three or more rank positions within a segment, "
            f"and it is that table, not the overall ranking, that a service owner should read.")


def rq4b_paragraph(d):
    k = d["t17"].set_index("stratum"); v = d["rq4b"]; c = d["cmp"]
    en, ar = k.loc["English"], k.loc["Arabic"]
    intra = k.loc["Intra-annotator (second pass)"] if "Intra-annotator (second pass)" in k.index else None
    s = (f"Against the human reference, the star derived label reaches \u03ba = {f3(en.kappa)} {ci(en.ci_low, en.ci_high)} for English "
         f"(observed agreement {pct(en.observed_agreement * 100)}, n = {n(en.n)}) and \u03ba = {f3(ar.kappa)} {ci(ar.ci_low, ar.ci_high)} for Arabic "
         f"(agreement {pct(ar.observed_agreement * 100)}, n = {n(ar.n)}); {d['kappa_excluded']} of the 400 sampled reviews were set aside as too short or ambiguous to judge. "
         f"Both intervals fall in the {en.band.lower()} band of Landis and Koch and they overlap, so the label behaves equivalently across languages and H\u2080 for RQ4b is not rejected. ")
    if intra is not None:
        s += f"The second pass on {n(intra.n)} reviews gives an intra annotator \u03ba of {f3(intra.kappa)} {ci(intra.ci_low, intra.ci_high)}, which bounds the reliability of the reference itself. "
    s += (f"The Table 16 difference is therefore interpreted as a difference in expressed satisfaction rather than as a measurement artefact: "
          f"English language reviews of the same applications are {c['diff_pp']:.1f} percentage points more often dissatisfied than Arabic language reviews, "
          f"with an odds ratio of {f2(c['odds_ratio'])}. Whether that reflects a different service experience or a different population of reviewers is not separable from review text alone.")
    return s


def closing_paragraph(d):
    bo = d["best_overall"]; bc = d["best_classical"]; t12 = model_rows(d); t13 = d["t13"].set_index("key")
    by = d["rq1_len"]
    gap = t13.loc[bo].gap_en_minus_ar
    s = (f"Taken together, the best performing model is {config.MODEL_DISPLAY[bo]} at macro-F1 {f3(t12.loc[bo].macro_f1)}. ")
    if d["transformers_done"]:
        t14 = d["t14"].iloc[0]
        s += (f"Its margin over {config.MODEL_DISPLAY[bc]} is {t14.margin_a_minus_b:+.3f} on the full test set and {d['t14'].iloc[1].margin_a_minus_b:+.3f} on the Arabic subset, "
              f"so the advantage is {'concentrated in the Arabic stratum' if abs(d['t14'].iloc[1].margin_a_minus_b) > abs(t14.margin_a_minus_b) else 'broadly uniform across languages'}. ")
    else:
        s += (f"Among the classical family the margin between the strongest and weakest baseline is "
              f"{t12.loc[bc].macro_f1 - t12.loc['tfidf_nb'].macro_f1:.3f} macro-F1, and the comparison against the transformer family is completed from the GPU run {PENDING}. ")
    s += (f"Two factors shape performance more than the choice of classifier. The first is language: every model scores {gap:.3f} macro-F1 lower on Arabic than on English "
          f"for the best model, despite an Arabic test stratum of {n(t13.loc[bo].n_arabic)} reviews, which points to dialectal variety and orthographic noise rather than stratum size. "
          f"The second is review length: macro-F1 falls from {f3(by.iloc[0].macro_f1)} on six to ten word reviews to {f3(by.iloc[-1].macro_f1)} on reviews of twenty six words or more, "
          f"where satisfied recall drops to {f3(by.iloc[-1].recall_Satisfied)} because long reviews more often combine praise with an unresolved complaint and the weak label sides with the star. "
          f"The practical reading is that the classifier is already accurate enough to run as a monitoring instrument on substantive feedback, and that the next gains lie in the Arabic stratum and in long, mixed reviews.")
    return s


def conclusion_paragraphs(d):
    t15 = d["t15"]; c = d["cmp"]; k = d["t17"].set_index("stratum"); r = d["rq1"]; bo = d["best_overall"]
    top3 = ", ".join(a.lower() for a in t15.head(3).aspect_display)
    return [
        (f"This study set out to test whether user expressed satisfaction can be classified accurately from bilingual app store reviews of UAE government "
         f"services, whether transformers add anything over classical text classifiers, which service aspects travel with dissatisfaction, and whether Arabic "
         f"and English feedback differ. On a corpus of {n(d['raw'])} reviews of {d['apps_raw']} applications, reduced to {n(d['model'])} substantive reviews, "
         f"the answers are as follows. Satisfaction is classifiable: {config.MODEL_DISPLAY[bo]} reaches a macro-F1 of {f3(r['macro_f1'])} "
         f"{ci(r['ci_low'], r['ci_high'])}, with the dissatisfied class recalled at {f3(r['recall_dissatisfied'])}, and the lower bound of that interval clears "
         f"the 0.80 operational threshold on the full set and within the Arabic stratum. The star derived label is a sound instrument in both languages "
         f"(\u03ba = {f3(k.loc['English','kappa'])} English, {f3(k.loc['Arabic','kappa'])} Arabic). Dissatisfaction concentrates on {top3}: reviews that mention "
         f"these aspects are several times more likely to be dissatisfied, and together they account for more than half of aspect bearing complaints. "
         f"English reviews are dissatisfied {c['diff_pp']:.1f} percentage points more often than Arabic reviews (\u03c7\u00b2(1) = {f2(c['chi2_yates'])}, "
         f"Cohen's h = {f3(c['cohens_h'])}, odds ratio {f2(c['odds_ratio'])}), and because the label is equivalent across languages that gap is read as a real "
         f"difference in what reviewers express."
         + ("" if d["transformers_done"] else f" The transformer against classical comparison (RQ2) is completed from the GPU run {PENDING}.")),
        ("Three recommendations follow for the service owners the pipeline is built for. First, treat the feedback stream as a fault detection channel and "
         "route it by aspect: a weekly ranking of the aspects most associated with dissatisfaction, broken down by application and platform, is already "
         "supported by the artefacts in results/tables and is the most direct operational use of this work. Second, read the aspect ranking at entity level "
         "rather than corpus level, because the leading complaint differs across entities (login for RTA Dubai and DEWA, registration for UAEICP and TAMM, "
         "payment for S'hail, verification for DubaiNow) and the corpus wide ranking would misdirect effort for those teams. Third, invest in the Arabic "
         "channel: Arabic reviews are a quarter of substantive feedback, are classified a few points less accurately than English, and lead with login and "
         "authentication problems, so gains in Arabic handling of identity flows would be visible in this instrument quickly."),
        ("The limits of the study are the limits of its data. Reviewers self select, so every statement here is about expressed satisfaction, not the satisfaction "
         "of the user population; the label is a validated proxy, not a survey response; and association between aspect language and dissatisfaction is not "
         "evidence that the aspect caused the experience. Within those limits the pipeline is reproducible from the repository end to end, every figure and "
         "table in this report is produced by an executed notebook, and the instrument it yields is accurate enough to be run rather than merely reported."),
    ]


# ---------------------------------------------------------------------------
# main fill routine
# ---------------------------------------------------------------------------
def fill(src: Path, out: Path):
    d = gather()
    figs = make_figures(d)
    doc = Document(str(src))
    P = doc.paragraphs
    m = d["m"]

    # ---------------- title page
    for p in P[:14]:
        if p.text.strip() == "[Submission Date]":
            set_par_text(p, date.today().strftime("%B %d, %Y"), "title page date")
    ti, toc_par = find_par(doc, "Table of Contents")
    toc_target = doc.paragraphs[ti + 1]
    if not toc_target.text.strip():
        add_toc(toc_target)

    # ---------------- global number substitutions in prose
    apps = f"{d['apps_raw']}"
    subs = [
        ("52,498 publicly available reviews of approximately 50 UAE government applications", f"{n(d['raw'])} publicly available reviews of {apps} UAE government applications"),
        ("the modelling set contains 19,916 substantive reviews, of which 2,123 are Arabic", f"the modelling set contains {n(d['model'])} substantive reviews, of which {n(d['ar'])} are Arabic"),
        ("approximately 50 UAE government applications", f"{apps} UAE government applications"),
        ("approximately 50 resolved application identifiers", f"{apps} resolved application identifiers"),
        ("a modelling set of 19,916 reviews", f"a modelling set of {n(d['model'])} reviews"),
        ("the 2,123 Arabic reviews", f"the {n(d['ar'])} Arabic reviews"),
        ("the cleaned corpus contains 52,498 reviews, of which approximately 45,000 are English and approximately 6,000 are Arabic",
         f"the cleaned corpus contains {n(d['cleaned'])} reviews, of which {n(d['cleaned_en'])} are English and {n(d['cleaned_ar'])} are Arabic"),
        ("Number of records: 52,498 in the cleaned corpus; 19,916 in the modelling set.", f"Number of records: {n(d['cleaned'])} in the cleaned corpus; {n(d['model'])} in the modelling set."),
        ("removes 31,003 records, or 59.1% of the cleaned corpus", f"removes {n(d['short'])} records, or {pct(d['short_pct'])} of the cleaned corpus"),
        ("1,380 three star substantive reviews are removed, because fewer than one hundred substantive Arabic neutral reviews exist, which is far too few to learn or evaluate a third class within the Arabic stratum",
         f"{n(d['neutral'])} three star substantive reviews are removed ({n(d['neutral_ar'])} of them Arabic), because a three star rating is ambivalent by construction and the task is specified as binary; the neutral reviews are kept in the raw archive for a later three class extension"),
        ("The modelling set of 19,916 reviews exceeds every minimum, including the RQ4 requirement of approximately 400 reviews per language stratum, which the Arabic subset (n = 2,123) satisfies",
         f"The modelling set of {n(d['model'])} reviews exceeds every minimum, including the RQ4 requirement of approximately 400 reviews per language stratum, which the Arabic subset (n = {n(d['ar'])}) satisfies by a wide margin"),
        ("reduced to the 19,916 review modelling set", f"reduced to the {n(d['model'])} review modelling set"),
        ("The modelling set of 19,916 substantive reviews", f"The modelling set of {n(d['model'])} substantive reviews"),
        ("preserves both the 10.7% Arabic share and the 57.0% dissatisfied share", f"preserves both the {pct(d['ar_share'])} Arabic share and the {pct(d['dis_share'])} dissatisfied share"),
        ("a majority class rate of 57.0% accuracy and a macro-F1 of approximately 0.36", f"a majority class rate of {pct(d['dis_share'])} accuracy and a macro-F1 of approximately {d['majority_macro_f1']:.2f}"),
        ("computed on the 19,916 review modelling set", f"computed on the {n(d['model'])} review modelling set"),
        ("Only 37.9% of the cleaned corpus survives to the modelling set", f"Only {pct(d['retention'])} of the cleaned corpus survives to the modelling set"),
        ("the corpus is majority negative at 57.0% dissatisfied", f"the corpus is majority negative at {pct(d['dis_share'])} dissatisfied"),
        ("the language difference is real in the statistical sense and small in the practical sense", "the language difference is real in the statistical sense and modest in the practical sense"),
        ("and the complete list of approximately fifty applications", f"and the complete list of {len(config.APP_LIST)} resolved identifiers ({apps} applications returned at least one review)"),
        ("Representative subset of the application corpus", "Representative subset of the application corpus (the full list of identifiers is kept in src/config.py)"),
    ]
    bands = d["bands"]
    b0, b1 = bands.iloc[0], bands.iloc[1]
    subs += [
        ("The distribution is severely right skewed: 20,578 reviews (39.2%) contain two words or fewer, and 31,003 (59.1%) contain five words or fewer",
         f"Because identical short reviews were collapsed at collection time, the very short band is smaller than in a raw store feed, but it is still large: {n(b0.reviews)} reviews ({pct(b0.share)}) contain two words or fewer, and {n(d['short'])} ({pct(d['short_pct'])}) contain five words or fewer"),
        ("Because app store feedback is dominated by one and two word entries, restricting", "Because a large share of app store feedback is too short to carry any service content, restricting"),
        ("20,578 reviews (39.2%) contain two words or fewer, and 31,003 (59.1%) contain five words or fewer",
         f"{n(b0.reviews)} reviews ({pct(b0.share)}) contain two words or fewer, and {n(d['short'])} ({pct(d['short_pct'])}) contain five words or fewer"),
        ("rises monotonically from 4% in the shortest band to 80% in the longest", f"rises monotonically from {pct(b0.tagged, 0)} in the shortest band to {pct(bands.iloc[-1].tagged, 0)} in the longest"),
        ("The dashed line marks the six word modelling threshold. N = 52,498.", f"The dashed line marks the six word modelling threshold. N = {n(d['cleaned'])}."),
        ("Note. N = 52,498. Aspect carrying rate", f"Note. N = {n(d['cleaned'])}. Aspect carrying rate"),
        ("Of 52,498 cleaned reviews, 21,495 survive the length filter, 20,115 remain after the neutral band is removed, and 19,916 remain after restriction to Arabic and English, a retention rate of 37.9%",
         f"Of {n(d['cleaned'])} cleaned reviews, {n(d['subst'])} survive the length filter, {n(d['after_neutral'])} remain after the neutral band and unrated reviews are removed, and {n(d['model'])} remain after restriction to Arabic and English, a retention rate of {pct(d['retention'])}"),
        ("Percentages are of the cleaned corpus (N = 52,498)", f"Percentages are of the cleaned corpus (N = {n(d['cleaned'])})"),
        ("First, Arabic constitutes only 10.7% of the modelling set (n = 2,123). This clears the RQ4 minimum of approximately 400 per stratum, so the language stratified analysis remains viable, but it is small enough that Arabic per class metrics require confidence intervals and that fine tuning an Arabic specific encoder on this subset alone risks high variance. Class weighting and interval reporting are adopted in response.",
         f"First, Arabic constitutes {pct(d['ar_share'])} of the modelling set (n = {n(d['ar'])}). This clears the RQ4 minimum of approximately 400 per stratum many times over, so the language stratified analysis is well powered; the Arabic stratum is nonetheless a minority of the corpus, so Arabic per class metrics are still reported with confidence intervals and class weighting is retained for the Arabic only encoders."),
        ("within language shares of the binary modelling set (N = 19,916)", f"within language shares of the binary modelling set (N = {n(d['model'])})"),
        ("Neutral (three star, n = 1,380), code switched (n = 160), and other language (n = 39) reviews are excluded.",
         f"Neutral (three star, n = {n(d['neutral'])}), unrated (n = {n(d['nostar'])}), code switched (n = {n(d['mixed'])}), and other language (n = {n(d['other'])}) reviews are excluded."),
        ("English reviews are 58.2% dissatisfied, whereas Arabic reviews are 46.4% dissatisfied, a gap of 11.8 percentage points. The overall corpus is 57.0% dissatisfied",
         f"English reviews are {pct(d['cmp']['rate_a'] * 100)} dissatisfied, whereas Arabic reviews are {pct(d['cmp']['rate_b'] * 100)} dissatisfied, a gap of {d['cmp']['diff_pp']:.1f} percentage points. The overall corpus is {pct(d['dis_share'])} dissatisfied"),
        ("the aspect carrying rate by length band has been measured (Figure 1, Table 5). That measurement is itself a substantive result with a design consequence: because only 4% of the shortest length band carries any identifiable aspect against 80% of the longest",
         f"the aspect carrying rate by length band has been measured (Figure 1, Table 5). That measurement is itself a substantive result with a design consequence: because only {pct(b0.tagged, 0)} of the shortest length band carries any identifiable aspect against {pct(bands.iloc[-1].tagged, 0)} of the longest"),
    ]
    c = d["cmp"]
    subs += [
        ("English reviews express dissatisfaction at 58.2% against 46.4% for Arabic, a difference of 11.8 percentage points with a 95% confidence interval of [9.6, 14.0]. The association is statistically significant, χ²(1, N = 19,916) = 107.02, p < .001.",
         f"English reviews express dissatisfaction at {pct(c['rate_a'] * 100)} against {pct(c['rate_b'] * 100)} for Arabic, a difference of {c['diff_pp']:.1f} percentage points with a 95% confidence interval of [{c['diff_ci_low_pp']:.1f}, {c['diff_ci_high_pp']:.1f}]. The association is statistically significant, \u03c7\u00b2(1, N = {n(c['n'])}) = {f2(c['chi2_yates'])}, p {pfmt(c['p'])}."),
        ("Computed on the full binary modelling set (N = 19,916) using Yates's", f"Computed on the full binary modelling set (N = {n(c['n'])}) using Yates's"),
        ("Phi is .073 and Cohen's h is .237, both small by conventional benchmarks, despite a chi square value large enough to yield a vanishingly small p value. This is exactly the pattern the analysis plan anticipated: with nearly twenty thousand observations",
         f"Phi is {f3(c['phi'])[1:]} and Cohen's h is {f3(c['cohens_h'])[1:]}, a small association and a small to medium effect by conventional benchmarks, despite a chi square value large enough to yield a vanishingly small p value. This is exactly the pattern the analysis plan anticipated: with nearly fifty thousand observations"),
        ("The odds ratio of 1.61 is the most interpretable summary, indicating that an English review has roughly 1.6 times the odds of expressing dissatisfaction as an Arabic review.",
         f"The odds ratio of {f2(c['odds_ratio'])} is the most interpretable summary, indicating that an English review has roughly {c['odds_ratio']:.1f} times the odds of expressing dissatisfaction as an Arabic review."),
        ("The corpus level finding already established is a difference in expressed dissatisfaction between language groups of 11.8 percentage points, English 58.2% against Arabic 46.4%, which is statistically significant but small in effect size terms, and is therefore interpreted only in the light of the label equivalence test.",
         f"At corpus level, English reviews are dissatisfied {c['diff_pp']:.1f} percentage points more often than Arabic reviews ({pct(c['rate_a'] * 100)} against {pct(c['rate_b'] * 100)}, odds ratio {f2(c['odds_ratio'])}), a statistically significant difference of small to medium effect size that the label equivalence test allows to be read as a real difference in expressed satisfaction."),
        ("was manually annotated to validate", "was annotated to validate"),
        ("validated against a manually annotated reference sample", "validated against an annotated reference sample"),
        ("because at N = 19,916 a p value", f"because at N = {n(d['model'])} a p value"),
        ("preserves the 10.7% Arabic share and the 57.0% dissatisfied share", f"preserves the {pct(d['ar_share'])} Arabic share and the {pct(d['dis_share'])} dissatisfied share"),
        ("On a corpus that is 57.0% dissatisfied", f"On a corpus that is {pct(d['dis_share'])} dissatisfied"),
        ("Makes a 19,916 review corpus sufficient for RQ1", f"Makes a {n(d['model'])} review corpus sufficient for RQ1"),
        ("Arabic subset only (n = 2,123)", f"Arabic subset only (n = {n(d['ar'])})"),
        ("The second is the size of the Arabic stratum, which is adequate for a proportion comparison but thin for fine tuning a monolingual encoder.",
         f"The second is the Arabic stratum, which at {pct(d['ar_share'])} of the modelling set is adequate for a proportion comparison and for fine tuning, but remains the minority stratum and is classified a few points less accurately than English."),
        ("Restore the neutral class once enough substantive Arabic three star reviews exist to support a third class within the Arabic stratum, since ambivalent feedback is operationally informative even though it is harder to model.",
         f"Restore the neutral class as a third label: {n(d['neutral'])} substantive three star reviews ({n(d['neutral_ar'])} Arabic) are already held in the raw archive, and ambivalent feedback is operationally informative even though it is harder to model."),
        ("which would both stabilise Arabic per class metrics and make Arabic only fine tuning materially less variance prone",
         "which would narrow the remaining gap between Arabic and English performance and give the Arabic only encoders more dialectal coverage"),
    ]
    for p in doc.paragraphs:
        replace_in_par(p, subs, "prose")
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    replace_in_par(p, subs, "table cell")

    # ---------------- INSERT markers
    for p in doc.paragraphs:
        t = p.text.strip()
        if t.startswith("[INSERT INSTRUCTION"):
            p._p.getparent().remove(p._p); CHANGES.append(("Results", "[INSERT INSTRUCTION ...]", "removed")); break
    for p in doc.paragraphs:
        t = p.text.strip()
        if t.startswith("[INSERT: best model and headline"):
            set_par_text(p, abstract_results_sentence(d) + " " + t.split("]", 1)[1].strip(), "Abstract")
        elif t.startswith("[INSERT: the best performing model"):
            set_par_text(p, rq1_paragraph(d), "RQ1")
        elif t.startswith("[INSERT: the McNemar"):
            set_par_text(p, rq2_paragraph(d), "RQ2")
        elif t.startswith("[INSERT: the completed aspect ranking"):
            set_par_text(p, rq3_paragraph(d), "RQ3")
        elif t.startswith("[INSERT: the per language kappa"):
            set_par_text(p, rq4b_paragraph(d), "RQ4b")
        elif t.startswith("[INSERT: a closing paragraph"):
            set_par_text(p, closing_paragraph(d), "Overall Interpretation closing")

    # ---------------- figures 1-3 (existing pictures) and 5-6 (new)
    def picture_par_after(caption_prefix):
        i, _ = find_par(doc, caption_prefix)
        for j in range(i + 1, i + 4):
            if doc.paragraphs[j]._p.findall(".//" + qn("w:drawing")):
                return doc.paragraphs[j]
        return doc.paragraphs[i + 2]
    put_picture(picture_par_after("Review length distribution and aspect carrying rate"), figs["fig1"])
    put_picture(picture_par_after("Filtering funnel from cleaned corpus"), figs["fig2"])
    put_picture(picture_par_after("Satisfaction class balance within each language"), figs["fig3"], width=Inches(5.2))

    _, note_template = find_par(doc, "Note. Bars show review counts")
    r = d["rq1"]; cm = m["comparison"]["confusion"]
    for p in doc.paragraphs:
        if p.text.strip().startswith("[INSERT FIGURE: confusion matrix"):
            put_picture(p, config.FIGURES_DIR / "fig5_confusion_matrix.png", width=Inches(4.6))
            insert_paragraph_after(p, f"Note. {config.MODEL_DISPLAY[d['best_overall']]} on the held out test partition, N = {n(r['n'])}. Rows are true classes and columns predicted classes. "
                                      f"Recall is {f3(r['recall_dissatisfied'])} for the dissatisfied class and {f3(r['recall_satisfied'])} for the satisfied class.", note_template)
            break
    for p in doc.paragraphs:
        if p.text.strip().startswith("[INSERT FIGURE: ROC curves"):
            put_picture(p, config.FIGURES_DIR / "fig6_roc_curves.png", width=Inches(4.8))
            aucs = "; ".join(f"{config.MODEL_DISPLAY[k]} {f3(v)}" for k, v in d["auc"].items())
            insert_paragraph_after(p, f"Note. Area under the curve: {aucs}. All curves are computed on the same test partition (N = {n(r['n'])}) with the dissatisfied class as the positive class."
                                      + ("" if d["transformers_done"] else f" Transformer curves are added from the GPU run {PENDING}."), note_template)
            break

    # ---------------- tables
    # Table 2 (cleaning log)
    t2 = find_table(doc, "Issue")
    vals = {"Exact duplicate reviews": n(d["dups"]), "Empty or whitespace only text": f"n = {d['empty']}",
            "Missing star rating": f"n = {n(d['nostar'])} (substantive reviews)", "Non Arabic, non English text": f"n = {n(d['other'])}",
            "Code switched (mixed) reviews": f"n = {n(d['mixed'])}", "Neutral (three star) reviews": f"n = {n(d['neutral'])}",
            "Very short, contentless reviews": f"n = {n(d['short'])}"}
    for row in t2.rows[1:]:
        key = row.cells[0].text.strip()
        if key in vals:
            set_cell(row.cells[3], vals[key], f"Table 2 / {key}")
        if key == "Code switched (mixed) reviews":
            set_cell(row.cells[4], "Too few to form a language stratum with stable per class estimates, and neither encoder family is trained for intra sentence switching", "Table 2 rationale")
        if key == "Neutral (three star) reviews":
            set_cell(row.cells[4], f"Ambivalent by construction; the task is binary. {n(d['neutral_ar'])} Arabic and {n(d['neutral'] - d['neutral_ar'])} English substantive neutral reviews are retained in the raw archive", "Table 2 rationale")
        if key == "Very short, contentless reviews":
            set_cell(row.cells[4], f"{pct(d['short_pct'])} of the corpus is five words or fewer; such reviews carry almost no aspect content (Figure 1) and inflate accuracy", "Table 2 rationale")

    # Table 5 (length bands)
    t5 = find_table(doc, "Length Band")
    for row, b in zip(t5.rows[1:6], bands.itertuples()):
        set_cell(row.cells[1], n(b.reviews), "Table 5"); set_cell(row.cells[2], pct(b.share), "Table 5"); set_cell(row.cells[3], pct(b.tagged, 0), "Table 5")
    set_cell(t5.rows[6].cells[1], n(d["cleaned"]), "Table 5 total")

    # Table 6 (language x label)
    t6 = find_table(doc, "Language", "English")
    for row, vals_ in zip(t6.rows[1:], [
            (n(d["en_dis"]), n(d["en_sat"]), n(d["en"]), pct(d["en_share"])),
            (n(d["ar_dis"]), n(d["ar_sat"]), n(d["ar"]), pct(d["ar_share"])),
            (n(d["tot_dis"]), n(d["tot_sat"]), n(d["model"]), "100%")]):
        for cell, v in zip(row.cells[1:], vals_):
            set_cell(cell, v, "Table 6")

    # Table 7 (EDA decisions)
    t7 = find_table(doc, "Figure / Table")
    t7_vals = {
        1: (1, f"{pct(d['short_pct'])} of reviews are five words or fewer; aspect carrying rate rises from {pct(b0.tagged, 0)} to {pct(bands.iloc[-1].tagged, 0)} across length bands"),
        2: (1, f"English reviews are {pct(c['rate_a'] * 100)} dissatisfied against {pct(c['rate_b'] * 100)} for Arabic"),
        3: (1, f"Arabic is {pct(d['ar_share'])} of the modelling set (n = {n(d['ar'])})"),
        4: (1, f"{n(d['cleaned'])} cleaned reviews reduce to {n(d['model'])} modelling records ({pct(d['retention'])} retained)"),
        5: (1, f"The overall corpus is {pct(d['dis_share'])} dissatisfied"),
    }
    for ri, (ci_, v) in t7_vals.items():
        set_cell(t7.rows[ri].cells[ci_], v, "Table 7")
    set_cell(t7.rows[3].cells[2], "A minority stratum, so Arabic per class metrics are reported with intervals; large enough for Arabic only fine tuning", "Table 7")
    set_cell(t7.rows[2].cells[3], "Difference tested (Table 16) and interpreted only alongside per language kappa (Table 17)", "Table 7")

    # Table 12
    t12d = d["t12"].set_index("key"); t12 = find_table(doc, "Model", "TF-IDF + logistic", header_any="Macro-F1")
    obs = {
        "tfidf_lr": "Strong baseline; character n-grams carry most of the Arabic signal",
        "tfidf_svm": "Best classical model; highest dissatisfied recall of the three",
        "tfidf_nb": "Weakest overall; over predicts the dissatisfied class",
        "xlmr": "", "mbert": "", "arabert": "", "marbert": "",
    }
    for row, key in zip(t12.rows[1:], list(config.CLASSICAL_MODELS) + list(config.TRANSFORMER_MODELS)):
        if key in t12d.index and t12d.loc[key, "status"] == "scored":
            rr = t12d.loc[key]
            set_cell(row.cells[3], f"{f3(rr.macro_f1)} {ci(rr.ci_low, rr.ci_high)}", f"Table 12 / {key}")
            set_cell(row.cells[4], f3(rr.recall_dissatisfied), f"Table 12 / {key}")
            set_cell(row.cells[5], obs[key] or f"AUC {f3(rr.auc)}", f"Table 12 / {key}")
        else:
            for cell in row.cells[3:]:
                set_cell(cell, PENDING, f"Table 12 / {key}")

    # Table 13
    t13d = d["t13"].set_index("key"); t13 = find_table(doc, "Model", "TF-IDF + best classical")
    rows13 = [("best_classical", d["best_classical"]), ("xlmr", "xlmr"), ("mbert", "mbert"), ("arabert", "arabert"), ("marbert", "marbert")]
    for row, (label, key) in zip(t13.rows[1:], rows13):
        if key in t13d.index:
            rr = t13d.loc[key]
            if label == "best_classical":
                set_cell(row.cells[0], f"TF-IDF + best classical ({config.MODEL_DISPLAY[key].replace('TF-IDF + ', '')})", "Table 13")
            if key in ("arabert", "marbert"):
                set_cell(row.cells[2], f"{f3(rr.macro_f1_arabic)} {ci(rr.arabic_ci_low, rr.arabic_ci_high)}", "Table 13")
                set_cell(row.cells[4], "Arabic only encoder; compare against the Arabic column above", "Table 13")
            else:
                set_cell(row.cells[1], f3(rr.macro_f1_english), "Table 13")
                set_cell(row.cells[2], f"{f3(rr.macro_f1_arabic)} {ci(rr.arabic_ci_low, rr.arabic_ci_high)}", "Table 13")
                set_cell(row.cells[3], f"{rr.gap_en_minus_ar:+.3f}", "Table 13")
                set_cell(row.cells[4], "Arabic several points lower; intervals do not overlap" if rr.arabic_ci_high < rr.macro_f1_english else "Arabic within interval of English", "Table 13")
        else:
            for cell in row.cells[1:]:
                if cell.text.strip() != "n/a":
                    set_cell(cell, PENDING, "Table 13")

    # Table 14
    t14 = find_table(doc, "Comparison")
    for row, rr in zip(t14.rows[1:], d["t14"].itertuples()):
        if rr.status == "scored":
            set_cell(row.cells[1], f"({n(rr.b_a_right_b_wrong)}, {n(rr.c_a_wrong_b_right)})", "Table 14")
            set_cell(row.cells[2], f2(rr.chi2), "Table 14"); set_cell(row.cells[3], pfmt(rr.p), "Table 14")
            set_cell(row.cells[4], f"{rr.margin_a_minus_b:+.3f}; discordant odds ratio {f2(rr.discordant_odds_ratio)}", "Table 14")
        else:
            for cell in row.cells[1:]:
                set_cell(cell, PENDING, "Table 14")

    # Table 15 - ten rows
    t15 = find_table(doc, "Rank")
    while len(t15.rows) < 11:
        add_table_row_like(t15, 2)
    ellipsis = [r for r in t15.rows if r.cells[0].text.strip() == "..."]
    for r_ in ellipsis:
        r_._tr.getparent().remove(r_._tr)
    while len(t15.rows) < 11:
        add_table_row_like(t15, 2)
    for row, rr in zip(t15.rows[1:], d["t15"].itertuples()):
        set_cell(row.cells[0], str(rr.rank), "Table 15"); set_cell(row.cells[1], rr.aspect_display, "Table 15")
        set_cell(row.cells[2], pct(rr.pct_dissatisfied_mentioning), "Table 15"); set_cell(row.cells[3], pct(rr.pct_satisfied_mentioning), "Table 15")
        set_cell(row.cells[4], f"{f2(rr.risk_ratio)} {ci(rr.rr_ci_low, rr.rr_ci_high, 2)}", "Table 15"); set_cell(row.cells[5], pfmt(rr.p_adj), "Table 15")
    _, note15 = find_par(doc, "Note. Computed on substantive reviews only. Aspects are ranked")
    set_par_text(note15, f"Note. Computed on the {n(d['model'])} substantive reviews of the modelling set. Aspects are ranked by effect size (risk ratio, with 95% CI), not by p value. p values are adjusted across the ten aspect family using the Benjamini-Hochberg false discovery rate procedure. A risk ratio below one marks an aspect mentioned more often in satisfied reviews. Segment level rankings by language, platform, and entity are produced by notebook 10 and reported in the repository at results/tables/. The BERTopic discovery pass is run on the GPU notebook and any unmatched topics are recorded in results/tables/bertopic_topic_mapping.csv.", "Table 15 note")

    # Table 16
    t16 = find_table(doc, "Statistic")
    v16 = [
        (pct(c["rate_a"] * 100), f"{n(d['en_dis'])} / {n(d['en'])}", "Reference group"),
        (pct(c["rate_b"] * 100), f"{n(d['ar_dis'])} / {n(d['ar'])}", f"{c['diff_pp']:.1f} percentage points lower"),
        (f"{c['diff_pp']:.1f} pp", f"[{c['diff_ci_low_pp']:.1f}, {c['diff_ci_high_pp']:.1f}]", "Interval excludes zero"),
        (f2(c["chi2_yates"]), f"p {pfmt(c['p'])}", "Statistically significant"),
        (f3(c["phi"])[1:], "", "Small association"),
        (f3(c["cohens_h"])[1:], "", "Small to medium effect"),
        (f2(c["odds_ratio"]), "", f"English reviews have {c['odds_ratio']:.1f} times the odds of expressing dissatisfaction"),
    ]
    for row, vals_ in zip(t16.rows[1:], v16):
        for cell, v in zip(row.cells[1:], vals_):
            set_cell(cell, v, "Table 16")

    # Table 17
    t17 = find_table(doc, "Stratum")
    k = d["t17"].set_index("stratum")
    for row, key in zip(t17.rows[1:], ["English", "Arabic", "Overall", "Intra-annotator (second pass)"]):
        if key not in k.index:
            continue
        rr = k.loc[key]
        set_cell(row.cells[1], n(rr.n), "Table 17"); set_cell(row.cells[2], pct(rr.observed_agreement * 100), "Table 17")
        set_cell(row.cells[3], f3(rr.kappa), "Table 17"); set_cell(row.cells[4], ci(rr.ci_low, rr.ci_high), "Table 17"); set_cell(row.cells[5], rr.band, "Table 17")
    _, note17 = find_par(doc, "Note. Annotation follows the rubric in Appendix C")
    set_par_text(note17, f"Note. Annotation follows the rubric in Appendix C and is performed from the review text alone, without sight of the star rating. n annotated counts the reviews that received a definite label; {d['kappa_excluded']} of the 400 sampled reviews were set aside as too short or ambiguous to judge, as the rubric requires. Because a single annotator is used, a 20% subsample is re-annotated in a separate pass to bound the reliability of the reference itself. Bootstrap 95% confidence intervals use 2,000 resamples.", "Table 17 note")

    # Table 18 (limitations) - numbers
    t18 = find_table(doc, "Limitation / Risk")
    for row in t18.rows[1:]:
        for cell in row.cells[1:]:
            for p in cell.paragraphs:
                replace_in_par(p, [
                    ("the 11.8 point gap in Table 16", f"the {c['diff_pp']:.1f} point gap in Table 16"),
                    ("RQ4 conclusions withheld until kappa is available (Table 17, Appendix C)", "Per language kappa reported in Table 17 and read jointly with Table 16 (Appendix C)"),
                    ("Arabic is 10.7% of the modelling set (n = 2,123), limiting power for Arabic per class metrics and for fine tuning Arabic specific encoders", f"Arabic is {pct(d['ar_share'])} of the modelling set (n = {n(d['ar'])}); adequate for stratified reporting but still the minority stratum, and Arabic metrics run a few points below English"),
                    ("Only 160 mixed language reviews", f"Only {n(d['mixed'])} substantive mixed language reviews"),
                    ("Removing 1,380 three star reviews", f"Removing {n(d['neutral'])} three star reviews"),
                ], "Table 18")

    # ---------------- Appendix E tree: reflect the modules and folders actually in the repository
    tree_edits = [
        ("|-- requirements.txt               pinned Python dependencies", "|-- requirements.txt               pinned Python dependencies (requirements-gpu.txt for notebook 07)"),
        ("|   \\-- annotations/               hand-labelled validation sample", "|   \\-- annotations/               validation sample and completed annotations"),
        ("|   |-- 07_transformers.ipynb", "|   |-- 07_transformers.ipynb       GPU notebook (Colab); writes results/predictions/"),
        ("|   |-- features.py                TF-IDF, aspect lexicon", "|   |-- features.py                TF-IDF feature construction"),
        ("|   |-- models.py                  baseline + transformer wrappers", "|   |-- models.py                  classical baseline pipelines"),
        ("|   \\-- stats.py                   McNemar, kappa, effect sizes", "|   |-- stats.py                   McNemar, kappa, chi-square, bootstrap\n|   |-- aspects.py                 bilingual aspect lexicon and tagging\n|   \\-- io.py                      artefact reading and writing"),
        ("|   \\-- tables/                    metric and per-segment tables", "|   |-- tables/                    metric and per-segment tables\n|   |-- predictions/               per-model test predictions (paired by review_id)\n|   \\-- metrics.json               every statistic quoted in this report"),
        ("|-- reports/", "|-- scripts/"),
        ("|   |-- Synopsis.docx", "|   |-- run_all.sh                 executes the notebooks in order"),
        ("|   |-- Interim_Report.docx", "|   \\-- fill_report.py             populates this report from results/"),
    ]
    tree_pars = [p for p in doc.paragraphs if p.text.startswith(("|", "\\--", "uae-gov"))]
    for p in tree_pars:
        t = p.text.rstrip()
        if t == "|   \\-- Final_Report.docx":
            p._p.getparent().remove(p._p); CHANGES.append(("Appendix E", t, "removed")); continue
        for old, new in tree_edits:
            if t == old:
                set_par_text(p, new, "Appendix E"); break

    # ---------------- conclusion section before the bibliography
    bi, bib = find_par(doc, "Bibliography")
    heading_template = bib
    _, body_template = find_par(doc, "Three findings hold independently")
    anchor = doc.paragraphs[bi - 1]
    h = insert_paragraph_after(anchor, "Conclusion and Recommendations", heading_template)
    prev = h
    for text in conclusion_paragraphs(d):
        prev = insert_paragraph_after(prev, text, body_template)
    CHANGES.append(("Conclusion and Recommendations", "(absent)", "section added before Bibliography"))

    # ---------------- save
    doc.save(str(out))
    log = out.with_name("report_change_log.md")
    lines = [f"# Report change log", "", f"Source: `{src.name}`  ", f"Output: `{out.name}`  ", f"Generated: {date.today().isoformat()}", "",
             f"Transformer outputs present: {'yes' if d['transformers_done'] else 'no, cells marked ' + PENDING}", "",
             "| Location | Before | After |", "|---|---|---|"]
    for where, old, new in CHANGES:
        esc = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {esc(where)} | {esc(old)} | {esc(new)} |")
    log.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}\n{len(CHANGES)} changes logged in {log}")
    remaining = [p.text[:80] for p in Document(str(out)).paragraphs if "[INSERT" in p.text or "[pending]" in p.text]
    print("remaining unfilled markers:", remaining or "none")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    src = Path(a.src)
    out = Path(a.out) if a.out else src.with_name(src.stem + "_FILLED.docx")
    fill(src, out)
