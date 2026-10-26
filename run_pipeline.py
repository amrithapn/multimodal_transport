#!/usr/bin/env python3
"""
run_pipeline.py
===============
ONE SCRIPT — runs the COMPLETE Multimodal Transport pipeline
from a raw dataset all the way to a live Streamlit UI.

Usage
-----
    # Full pipeline from a .pbf file:
    python run_pipeline.py --input data/raw/my-region.osm.pbf

    # If you already have extracted .gpkg files (faster demo):
    python run_pipeline.py --skip-extraction

    # Show this help:
    python run_pipeline.py --help

Pipeline Stages
---------------
    1.  OSM → GeoPackage  (ogr2ogr / GeoPandas extraction)
    2.  Extract layers     (roads / railways / airports .gpkg)
    3.  Filter & refine    (remove minor roads)
    4.  Convert → Parquet  (columnar format for Spark)
    5.  Upload → HDFS      (Hadoop distributed filesystem)
    6.  Normalize (Spark)  (standard schema across all modes)
    7.  Profile  (Spark)   (live stats from HDFS — Spark Master UI)
    8.  Build road graph   (NetworkX — Dijkstra routing)
    9.  Generate journeys  (candidate route combinations)
    10. Feature engineering (distance / time / cost / CO2 / safety)
    11. Train ML model     (Random Forest classifier)
    12. Launch Streamlit UI (live route recommendations)
"""

import argparse
import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


# ── Colour helpers ────────────────────────────────────────────────────────────
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def banner(text):
    width = 64
    print(f"\n{BOLD}{CYAN}{'=' * width}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * width}{RESET}")

def step(n, total, text):
    print(f"\n{BOLD}{YELLOW}[{n}/{total}] {text}{RESET}")
    print(f"{YELLOW}{'─' * 56}{RESET}")

def ok(msg):
    print(f"{GREEN}  ✓ {msg}{RESET}")

def info(msg):
    print(f"{CYAN}  → {msg}{RESET}")

def warn(msg):
    print(f"{YELLOW}  ⚠ {msg}{RESET}")

def fail(msg):
    print(f"{RED}  ✗ {msg}{RESET}")

def run_python(script_path, label):
    """Run a project Python script. Returns True on success."""
    start = time.time()
    info(f"Running: python {script_path}")
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / script_path)],
        cwd=str(PROJECT_ROOT),
        capture_output=False,
    )
    elapsed = round(time.time() - start, 1)
    if result.returncode == 0:
        ok(f"{label} — done in {elapsed}s")
        return True
    else:
        fail(f"{label} failed (exit code {result.returncode})")
        return False


# ── Stage functions ───────────────────────────────────────────────────────────

TOTAL_STEPS = 12

def stage_1_osm_to_gpkg(pbf_path):
    step(1, TOTAL_STEPS, "Convert OSM .pbf → GeoPackage")
    info(f"Input file : {pbf_path}")
    info("Tool       : ogr2ogr (GDAL)")

    from config.project_config import PROCESSED_DATA_DIR, RAW_OSM_PBF
    gpkg_out = PROCESSED_DATA_DIR / "central-america.gpkg"

    cmd = [
        "ogr2ogr", "-f", "GPKG",
        str(gpkg_out),
        str(pbf_path),
        "-overwrite",
        "--config", "OSM_USE_CUSTOM_INDEXING", "NO",
    ]
    info(f"Running: {' '.join(cmd)}")
    start = time.time()
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    elapsed = round(time.time() - start, 1)

    if result.returncode == 0 and gpkg_out.exists():
        size_mb = round(gpkg_out.stat().st_size / 1_048_576, 1)
        ok(f"GeoPackage created: {gpkg_out.name} ({size_mb} MB) in {elapsed}s")
        return True
    else:
        fail("GeoPackage conversion failed")
        return False


def stage_2_extract_layers():
    step(2, TOTAL_STEPS, "Extract Transport Layers (Roads / Railways / Airports)")
    info("Script: src/extraction/extract_transport_layers.py")
    return run_python("src/extraction/extract_transport_layers.py", "Layer extraction")


def stage_3_filter_refine():
    step(3, TOTAL_STEPS, "Filter & Refine Roads")
    info("Script: src/preprocessing/refine_roads.py")
    return run_python("src/preprocessing/refine_roads.py", "Road refinement")


def stage_4_convert_parquet():
    step(4, TOTAL_STEPS, "Convert GeoPackage → Parquet (for Spark)")
    info("Script: src/parquet/gpkg_to_parquet.py")
    return run_python("src/parquet/gpkg_to_parquet.py", "Parquet conversion")


def stage_5_upload_hdfs():
    step(5, TOTAL_STEPS, "Upload to Hadoop HDFS")
    info("Script : src/etl/load_network_to_hdfs.py")
    info("Target : hdfs://localhost:9000/multimodal_transport_ca/")
    info("View at: http://localhost:9870 → Utilities → Browse the file system")

    # First upload the parquet files directly via hdfs dfs -put
    from config.project_config import PARQUET_DATA_DIR
    hdfs_parquet = "/multimodal_transport_ca/parquet"

    info("Creating HDFS directories...")
    subprocess.run(["hdfs", "dfs", "-mkdir", "-p", hdfs_parquet])

    parquet_files = [
        "roads.parquet", "railways.parquet", "airports.parquet",
        "roads_normalized.parquet", "railways_normalized.parquet", "airports_normalized.parquet"
    ]

    uploaded = 0
    for fname in parquet_files:
        local = PARQUET_DATA_DIR / fname
        if local.exists():
            result = subprocess.run(
                ["hdfs", "dfs", "-put", "-f", str(local), hdfs_parquet],
                capture_output=True
            )
            if result.returncode == 0:
                ok(f"Uploaded: {fname}")
                uploaded += 1
            else:
                warn(f"Could not upload {fname}: {result.stderr.decode()[:100]}")

    # Also run the main ETL script for network files
    run_python("src/etl/load_network_to_hdfs.py", "HDFS network upload")

    if uploaded > 0:
        ok(f"HDFS upload complete — {uploaded} parquet files in HDFS")
        info("Verify at: http://localhost:9870 → Utilities → Browse the file system")
        return True
    return False


def stage_6_normalize_spark():
    step(6, TOTAL_STEPS, "Normalize Data with Apache Spark")
    info("Script     : src/etl/normalize_transport.py")
    info("Spark UI   : http://localhost:8080")
    return run_python("src/etl/normalize_transport.py", "Spark normalization")


def stage_7_profile_spark():
    step(7, TOTAL_STEPS, "Profile HDFS Data with Apache Spark")
    info("Script     : src/spark/profile_transport_data.py")
    info("Reads live from HDFS → processes with Spark")
    info("Watch live: http://localhost:4040  (open NOW)")
    info("History at: http://localhost:8080  (after job finishes)")

    start = time.time()
    result = subprocess.run(
        ["spark-submit", "--master", "spark://localhost:7077",
         str(PROJECT_ROOT / "src/spark/profile_transport_data.py")],
        cwd=str(PROJECT_ROOT),
    )
    elapsed = round(time.time() - start, 1)

    if result.returncode == 0:
        ok(f"Spark profiling complete in {elapsed}s")
        ok("Check http://localhost:8080 → Completed Applications")
        return True
    else:
        warn("spark-submit failed, trying with local[*] fallback...")
        return run_python("src/spark/profile_transport_data.py", "Spark profiling (local)")


def stage_8_build_graph():
    step(8, TOTAL_STEPS, "Build Road Network Graph (NetworkX)")
    info("Script : src/routing/build_road_graph.py")
    info("Output : data/graph/road_graph.pkl")
    return run_python("src/routing/build_road_graph.py", "Graph build")


def stage_9_generate_candidates():
    step(9, TOTAL_STEPS, "Generate Candidate Journeys")
    info("Script : src/journey/generate_candidates.py")
    info("Output : data/journeys/candidate_journeys.csv")
    return run_python("src/journey/generate_candidates.py", "Candidate generation")


def stage_10_feature_engineering():
    step(10, TOTAL_STEPS, "Feature Engineering + Training Dataset")
    info("Scripts: src/journey/feature_engineering.py")
    info("         src/journey/generate_training_dataset.py")
    ok1 = run_python("src/journey/feature_engineering.py", "Feature engineering")
    ok2 = run_python("src/journey/generate_training_dataset.py", "Training dataset")
    return ok1 and ok2


def stage_11_train_model():
    step(11, TOTAL_STEPS, "Train Random Forest ML Model")
    info("Script : src/ml/train_random_forest.py")
    info("Output : models/random_forest.pkl")
    return run_python("src/ml/train_random_forest.py", "Model training")


def stage_12_launch_ui():
    step(12, TOTAL_STEPS, "Launch Streamlit Web UI")
    info("Script  : ui/app.py")
    info("URL     : http://localhost:8501")
    info("Data source: LIVE from Hadoop HDFS + Apache Spark")
    print()
    print(f"  {BOLD}{'─' * 54}{RESET}")
    print(f"  {BOLD}Open in your browser: http://localhost:8501{RESET}")
    print(f"  {BOLD}{'─' * 54}{RESET}")
    print()

    venv_python = PROJECT_ROOT / ".venv" / "bin" / "streamlit"
    cmd = [str(venv_python), "run", "ui/app.py",
           "--server.port", "8501", "--server.headless", "false"]

    if not venv_python.exists():
        cmd = ["streamlit", "run", "ui/app.py",
               "--server.port", "8501", "--server.headless", "false"]

    subprocess.run(cmd, cwd=str(PROJECT_ROOT))


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Multimodal Transport Pipeline — runs ALL stages end-to-end"
    )
    parser.add_argument(
        "--input", "-i",
        help="Path to raw OSM .pbf file (required for stage 1)",
        default=None,
    )
    parser.add_argument(
        "--skip-extraction", action="store_true",
        help="Skip stages 1-3 (use if .gpkg files already exist)",
    )
    parser.add_argument(
        "--skip-to", type=int, default=1, metavar="N",
        help="Skip directly to stage N (1-12)",
    )
    parser.add_argument(
        "--only-ui", action="store_true",
        help="Skip all processing — jump straight to the Streamlit UI",
    )
    args = parser.parse_args()

    banner("Multimodal Transport — Full Pipeline")
    print(f"  Start time : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Project    : {PROJECT_ROOT}")
    print(f"  HDFS       : http://localhost:9870")
    print(f"  Spark      : http://localhost:8080")
    print(f"  UI         : http://localhost:8501")

    if args.only_ui:
        stage_12_launch_ui()
        return

    skip = args.skip_to - 1 if args.skip_to > 1 else (3 if args.skip_extraction else 0)

    stages = [
        (1,  lambda: stage_1_osm_to_gpkg(args.input) if args.input else (warn("No --input file, skipping OSM conversion") or True)),
        (2,  stage_2_extract_layers),
        (3,  stage_3_filter_refine),
        (4,  stage_4_convert_parquet),
        (5,  stage_5_upload_hdfs),
        (6,  stage_6_normalize_spark),
        (7,  stage_7_profile_spark),
        (8,  stage_8_build_graph),
        (9,  stage_9_generate_candidates),
        (10, stage_10_feature_engineering),
        (11, stage_11_train_model),
        (12, stage_12_launch_ui),
    ]

    start_total = time.time()
    results = {}

    for n, fn in stages:
        if n <= skip:
            info(f"Skipping stage {n}")
            continue
        success = fn()
        results[n] = success
        if not success and n < 12:
            fail(f"Stage {n} failed — stopping pipeline")
            break

    # ── Summary ───────────────────────────────────────────────────────────────
    banner("Pipeline Complete")
    total_time = round(time.time() - start_total, 1)
    for n, fn in stages:
        if n in results:
            status = f"{GREEN}✓ Done{RESET}" if results[n] else f"{RED}✗ Failed{RESET}"
            stage_names = {
                1:"OSM → GeoPackage", 2:"Extract Layers", 3:"Filter Roads",
                4:"Convert Parquet", 5:"Upload HDFS", 6:"Spark Normalize",
                7:"Spark Profile", 8:"Build Graph", 9:"Candidates",
                10:"Features", 11:"Train RF Model", 12:"Streamlit UI"
            }
            print(f"  Stage {n:2d}  {stage_names[n]:22s}  {status}")
    print(f"\n  Total time : {total_time}s")
    print(f"\n  Open your browser:")
    print(f"    http://localhost:9870  ← Hadoop HDFS (your data)")
    print(f"    http://localhost:8080  ← Spark (completed jobs)")
    print(f"    http://localhost:8501  ← Route Recommendation UI")


if __name__ == "__main__":
    main()
