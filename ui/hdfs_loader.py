"""
hdfs_loader.py
==============
Integrates Hadoop HDFS + Apache Spark into the live UI pipeline.

Flow:
    1.  PySpark connects to spark://localhost:7077
    2.  Reads all 3 transport Parquet files from HDFS
        (roads_normalized, railways_normalized, airports_normalized)
    3.  Computes live statistics (record counts, transport types)
    4.  Returns those stats PLUS the road graph (from local pkl)

The graph itself is built offline from the full 645 MB GeoPackage
(also stored in HDFS at /multimodal_transport_ca/network/).
Building it live every UI load would take several minutes, so the
pre-built pkl is used for routing while Spark proves the data is live.

Data source banner in the UI will show:
    "📡 Live from HDFS + Spark"  when Spark/HDFS succeed
    "💾 Local cache"             when Spark/HDFS are unavailable
"""

import os
import sys
import pickle

import networkx as nx
import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── Configuration ────────────────────────────────────────────────────────────
HDFS_NAMENODE = "hdfs://localhost:9000"
HDFS_PARQUET  = f"{HDFS_NAMENODE}/multimodal_transport_ca/parquet"
SPARK_MASTER  = "spark://localhost:7077"

FALLBACK_GRAPH = os.path.join(PROJECT_ROOT, "data", "graph", "road_graph.pkl")

PARQUET_FILES = {
    "roads":    "roads_normalized.parquet",
    "railways": "railways_normalized.parquet",
    "airports": "airports_normalized.parquet",
}


def _create_spark_session():
    """Create a PySpark SparkSession pointing at the standalone cluster."""
    try:
        from pyspark.sql import SparkSession
        spark = (
            SparkSession.builder
            .appName("MultimodalTransport-UI-LiveLoad")
            .master(SPARK_MASTER)
            .config("spark.ui.port", "4040")
            .config("spark.executor.memory", "1g")
            .config("spark.driver.memory", "1g")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("WARN")
        return spark
    except Exception:
        return None


def _read_hdfs_stats(spark) -> dict:
    """
    Use Spark to read all 3 transport Parquet files from HDFS and
    return live record counts and transport-type distributions.
    """
    from pyspark.sql.functions import col, count as spark_count

    stats = {}
    for key, filename in PARQUET_FILES.items():
        path = f"{HDFS_PARQUET}/{filename}"
        df = spark.read.parquet(path)
        total = df.count()
        transport_types = (
            df.groupBy("transport_type")
            .agg(spark_count("*").alias("count"))
            .toPandas()
            .set_index("transport_type")["count"]
            .to_dict()
        )
        stats[key] = {"total": total, "types": transport_types, "path": path}
    return stats


def _load_graph() -> nx.Graph:
    """Load the pre-built NetworkX routing graph from disk."""
    if os.path.exists(FALLBACK_GRAPH):
        with open(FALLBACK_GRAPH, "rb") as f:
            return pickle.load(f)
    return None


@st.cache_resource(show_spinner="🔄 Connecting to Hadoop HDFS & Apache Spark — loading live transport data…")
def load_graph_from_hdfs():
    """
    Primary entry point used by the Streamlit UI.

    Returns
    -------
    G      : nx.Graph   — The NetworkX routing graph (from pkl)
    source : str        — "HDFS (live via Spark)" or "Local cache (pkl)"
    stats  : dict       — Counts, paths, and metadata for the status banner
    """
    G = _load_graph()
    if G is None:
        return None, "unavailable", {}

    base_stats = {
        "nodes": len(G.nodes),
        "edges": len(G.edges),
        "source": "local",
        "hdfs_path": None,
        "spark_master": None,
        "hdfs_records": {},
    }

    # ── Try live Spark + HDFS read ───────────────────────────────────────────
    spark = _create_spark_session()
    if spark is not None:
        try:
            hdfs_stats = _read_hdfs_stats(spark)
            total_records = sum(v["total"] for v in hdfs_stats.values())
            return G, "HDFS (live via Spark)", {
                **base_stats,
                "source": "HDFS",
                "hdfs_path": HDFS_PARQUET,
                "spark_master": SPARK_MASTER,
                "hdfs_records": {
                    k: v["total"] for k, v in hdfs_stats.items()
                },
                "hdfs_total": total_records,
            }
        except Exception as e:
            # Spark connected but HDFS read failed — fall through to local
            pass
        finally:
            try:
                spark.stop()
            except Exception:
                pass

    # ── Fallback: graph is already loaded, just mark source as local ─────────
    return G, "Local cache (pkl)", base_stats
