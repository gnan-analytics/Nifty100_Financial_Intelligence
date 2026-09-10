import shutil
from pathlib import Path

ROOT = Path.cwd()
DEST = ROOT / "output" / "final_deliverables"

if DEST.exists():
    shutil.rmtree(DEST)

DEST.mkdir(parents=True)

deliverables = [
    # Sprint 6 explicitly listed
    ("01_cluster_labels.csv", "output/cluster_labels.csv"),
    ("02_elbow_plot.png", "reports/elbow_plot.png"),
    ("03_correlation_heatmap.png", "reports/correlation_heatmap.png"),
    ("04_outlier_report.csv", "output/outlier_report.csv"),
    ("05_portfolio_stats.csv", "output/portfolio_stats.csv"),
    ("06_api_server", "src/api"),
    ("07_openapi.json", "docs/openapi.json"),
    ("08_pytest_report.html", "reports/pytest_report.html"),
    ("09_analyst_guide.pdf", "docs/analyst_guide.pdf"),
    # Major completed platform deliverables
    (
        "10_postman_collection.json",
        "docs/Nifty100_Financial_Intelligence.postman_collection.json",
    ),
    ("11_screener_output.xlsx", "output/screener_output.xlsx"),
    ("12_peer_comparison.xlsx", "output/peer_comparison.xlsx"),
    ("13_valuation_summary.xlsx", "output/valuation_summary.xlsx"),
    ("14_valuation_flags.csv", "output/valuation_flags.csv"),
    ("15_cashflow_intelligence.xlsx", "output/cashflow_intelligence.xlsx"),
    ("16_capital_allocation.csv", "output/capital_allocation.csv"),
    ("17_pros_cons_generated.csv", "output/pros_cons_generated.csv"),
    ("18_analysis_parsed.csv", "output/analysis_parsed.csv"),
    ("19_validation_failures.csv", "output/validation_failures.csv"),
    ("20_tearsheets", "reports/tearsheets"),
    ("21_sector_reports", "reports/sector"),
    ("22_portfolio_summary.pdf", "reports/portfolio/portfolio_summary.pdf"),
    ("23_performance_notes.md", "output/perf_notes.md"),
]

missing = []

for archive_name, source_name in deliverables:
    source = ROOT / source_name
    target = DEST / archive_name

    if not source.exists():
        missing.append(source_name)
        print(f"MISSING: {source_name}")
        continue

    if source.is_dir():
        shutil.copytree(
            source,
            target,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                "*.pyc",
                "*.pyo",
            ),
        )
    else:
        shutil.copy2(source, target)

    print(f"OK: {archive_name}")

print()
print("=" * 65)
print(f"Expected deliverables : {len(deliverables)}")
print(f"Present deliverables  : {len(deliverables) - len(missing)}")
print(f"Missing deliverables  : {len(missing)}")

if missing:
    print()
    print("ARCHIVE STATUS: FAIL")
    for item in missing:
        print(f"  - {item}")
    raise SystemExit(1)

print("ARCHIVE STATUS: PASS")
print(f"Archive directory: {DEST}")

print()
print("=== ARCHIVE CONTENTS ===")

for number, item in enumerate(sorted(DEST.iterdir()), start=1):
    if item.is_dir():
        files = list(item.rglob("*"))
        file_count = sum(1 for x in files if x.is_file())
        size = sum(x.stat().st_size for x in files if x.is_file())

        print(
            f"{number:02d}. {item.name:<35} "
            f"DIR  files={file_count:<4} size={size:,} bytes"
        )
    else:
        print(
            f"{number:02d}. {item.name:<35} " f"FILE size={item.stat().st_size:,} bytes"
        )

top_level = list(DEST.iterdir())

print()
print(f"Top-level deliverable count: {len(top_level)}")
print(
    "23-deliverable requirement:",
    "PASS" if len(top_level) == 23 else "FAIL",
)
