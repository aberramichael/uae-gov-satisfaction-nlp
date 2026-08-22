Per-model predictions on the fixed test partition, one file per model:

    <model>_test.csv  with columns  review_id, y_true, y_pred, p_dissat

Baselines (tfidf_lr, tfidf_svm, tfidf_nb) are written by notebook 06. The four transformer
files (xlmr, mbert, arabert, marbert) come from notebook 07, which runs on a GPU machine;
copy them here together with `transformer_runs.json` (into results/tables/), then run
`scripts/run_all.sh --post-colab`.
