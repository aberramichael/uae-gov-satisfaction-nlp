#!/usr/bin/env bash
# Execute the pipeline notebooks in order and refresh the report.
#
#   scripts/run_all.sh                # notebooks 02-06, 08-10 (local)
#   scripts/run_all.sh --post-colab   # only 08 and 10, after copying the notebook 07 outputs into results/
#   REPORT=/path/to/Final_Report.docx scripts/run_all.sh ...   # also populate the report
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.venv/bin/python}
NB="$PY -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3600"

if [[ "${1:-}" == "--post-colab" ]]; then
  for f in xlmr mbert arabert marbert; do
    [[ -f results/predictions/${f}_test.csv ]] || echo "warning: results/predictions/${f}_test.csv not found"
  done
  ORDER="08_model_comparison 10_segmentation"
else
  ORDER="02_clean_normalise 03_eda 04_weak_labels 05_label_validation 06_baselines_tfidf 08_model_comparison 09_aspects_bertopic 10_segmentation"
fi

for n in $ORDER; do
  echo "== notebooks/$n.ipynb"
  (cd notebooks && $NB "$n.ipynb" >/dev/null)
done

if [[ -n "${REPORT:-}" ]]; then
  $PY scripts/fill_report.py --src "$REPORT"
fi
echo "done"
