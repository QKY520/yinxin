"""Render public aggregate data to a NEW output directory; no model calls.

Derived from the local aggregate/case renderer, with all case rendering removed.
Usage: python scripts/build_public_tables.py NEW_OUTPUT_DIRECTORY
"""
from pathlib import Path
import csv
import hashlib
import json
import sys

root = Path(__file__).resolve().parent.parent
ev = root / "data"
if len(sys.argv) != 2:
    raise SystemExit("Usage: python scripts/build_public_tables.py NEW_OUTPUT_DIRECTORY")
out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=False)

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def escape(text):
    mapping = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%",
               "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{",
               "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    # Display substitutions preserve the original source files and offsets.
    mapping.update({"℃": r"\ensuremath{{}^{\circ}\mathrm{C}}",
                    "°": r"\ensuremath{{}^{\circ}}", "×": r"\ensuremath{\times}",
                    "Ⅳ": "IV", "Ⅲ": "III", "ö": r'\"o', "・": "·"})
    return "".join(mapping.get(c, c) for c in str(text))

def table(filename, caption, label, columns, header, rows, size=r"\small"):
    content = [r"\begin{table}[H]", r"\caption{" + caption + "}",
               r"\label{" + label + "}", r"\centering" + size,
               r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{" + columns + "}",
               r"\toprule", header + r" \\", r"\midrule"]
    content += [" & ".join(row) + r" \\" for row in rows]
    content += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    (out / filename).write_text("\n".join(content) + "\n", encoding="utf-8")

labels = {"zero": "Qwen zero-shot", "bm25": "BM25-only", "dense": "Dense RAG-only",
          "full": "EC-FSIE-full", "glossary": "Glossary-only",
          "random42": "Random (selection 42)", "random43": "Random (selection 43)",
          "random44": "Random (selection 44)", "knn": "kNN few-shot", "knn_g": "kNN+G",
          "uie_zs": "UIE zero-shot", "uie_ft42": "UIE FT30 (42)",
          "uie_ft43": "UIE FT30 (43)", "uie_ft44": "UIE FT30 (44)"}
metrics = list(csv.DictReader((ev / "raw_metrics_14_systems.csv").open(encoding="utf-8-sig")))
assert len(metrics) == 14
for m in metrics:
    tp, fp, fn = (int(m[k]) for k in ("tp", "fp", "fn"))
    assert int(m["texts"]) == 170 and tp + fn == 954
    assert abs(2 * tp / (2 * tp + fp + fn) - float(m["f1"])) < 1e-12
table("round2_counts.tex", "All 14 sealed prediction sets on the same 170 texts and 954 gold mentions. Qwen generation seed is 42; parenthesized seeds distinguish example selection or UIE training. UIE has native offsets rather than JSON parsing.",
      "tab:s-all-counts", "lrrrcccr", "System & TP & FP & FN & P & R & F1 & Parse failures",
      [[labels[m["system"]]] + [m[k] for k in ("tp", "fp", "fn")] +
       [f'{float(m[k]):.6f}' for k in ("precision", "recall", "f1")] +
       (["--"] if m["system"].startswith("uie") else [m["parse_failures"] + "/170"]) for m in metrics], r"\footnotesize")

stats = read_json(ev / "comparisons.json")
assert len(stats["f1_family"]) == 13 and len(stats["rag_secondary_family"]) == 3
short = dict(labels, full="Full", random42="Random42", uie_ft42="UIE FT30 (42)")
table("round2_f1_13.tex", "Complete prespecified 13-contrast F1 family. Differences are left minus right. Intervals are marginal percentile 95\\% paired-text bootstrap CIs; two-sided randomization uses 10,000 replicates. Adjusted values use Holm across all 13 contrasts.",
      "tab:s-f1-13", "lcccc", "Contrast & $\\Delta$F1 & 95\\% CI & Raw $p$ & Holm $p$ (13)",
      [[short[s["left"]] + " $-$ " + short[s["right"]], f'{s["difference_left_minus_right"]:+.6f}',
        f'[{s["ci95"][0]:.6f}, {s["ci95"][1]:.6f}]', f'{s["p_two_sided"]:.6f}', f'{s["p_holm_13"]:.6f}'] for s in stats["f1_family"]], r"\footnotesize")
table("round2_rag_3.tex", "Independent three-endpoint secondary family for Full minus kNN+G. Both conditions share per-query demonstrations and glossary. Holm correction covers these three endpoints only; intervals are marginal paired-text bootstrap CIs.",
      "tab:s-rag-3", "lcccc", "Endpoint & Difference & 95\\% CI & Raw $p$ & Holm $p$ (3)",
      [[s["metric"].upper() if s["metric"] == "fp" else s["metric"].capitalize(),
        f'{s["difference_left_minus_right"]:+.6f}' if s["metric"] != "fp" else "-79",
        f'[{s["ci95"][0]:.6f}, {s["ci95"][1]:.6f}]' if s["metric"] != "fp" else "[-120, -38]",
        f'{s["p_two_sided"]:.6f}', f'{s["p_holm_3"]:.6f}'] for s in stats["rag_secondary_family"]])
table("round2_seed_summary.tex", "Descriptive means and sample SD over seeds 42/43/44 on the same test170. Random varies example selection with generation fixed at 42; UIE varies training. These are not 510 independent texts.",
      "tab:s-seed-summary", "lcccc", "Condition & Precision & Recall & F1 & FP count",
      [[name] + [f'${stats["seed_descriptive"][key][k]["mean"]:.6f}\\pm{stats["seed_descriptive"][key][k]["sample_sd"]:.6f}$'
                  for k in ("precision", "recall", "f1")] +
       [f'${stats["seed_descriptive"][key]["fp"]["mean"]:.3f}\\pm{stats["seed_descriptive"][key]["fp"]["sample_sd"]:.3f}$']
       for key, name in (("random", "Random few-shot"), ("uie_ft", "UIE FT30"))], r"\footnotesize")
cal = read_json(ev / "agreement_ci.json")
assert cal["texts"] == 100 and cal["labels_changed"] is False
table("round2_calibration.tex", "Two-human non-test calibration on 100 texts; some questions involved AI consultation. Agreement F1 is $2M/(N_A+N_B)$. Intervals resample complete paired texts 10,000 times (seed 20261010); the process is not certified as independent blind annotation or test-set IAA.",
      "tab:s-calibration100", "lrrrcc", "Type & A & B & Exact matches & F1 & 95\\% CI",
      [[escape(k) if k != "ALL" else "All", str(v["a"]), str(v["b"]), str(v["matched"]),
        f'{v["f1"]:.6f}', f'[{v["ci95"][0]:.6f}, {v["ci95"][1]:.6f}]']
       for k in ("EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC", "ALL") for v in [cal["results"][k]]])


print(json.dumps({"model_calls": 0, "render_only": True, "generated_files": sorted(p.name for p in out.glob("*.tex"))}, indent=2))
