import os
import sys
import pickle
import joblib
import pandas as pd
import networkx as nx
import streamlit as st

# Add project root and src/routing to sys.path for seamless imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UI_DIR = os.path.dirname(__file__)
ROUTING_DIR = os.path.join(PROJECT_ROOT, "src", "routing")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if ROUTING_DIR not in sys.path:
    sys.path.insert(0, ROUTING_DIR)

from geocode import geocode_place
from shortest_path import nearest_node
from generate_candidates import (
    estimate_travel_time,
    estimate_cost,
    estimate_carbon,
)


def load_cached_graph():
    """
    Load the road network graph.
    Tries Hadoop HDFS → Apache Spark pipeline first (live data).
    Falls back to the pre-built road_graph.pkl if Spark/HDFS is unavailable.
    """
    if UI_DIR not in sys.path:
        sys.path.insert(0, UI_DIR)
    from hdfs_loader import load_graph_from_hdfs
    G, source, stats = load_graph_from_hdfs()
    return G


@st.cache_resource
def load_cached_model():
    """
    Load Random Forest model with caching.
    """
    model_path = os.path.join(PROJECT_ROOT, "models", "random_forest.pkl")
    if not os.path.exists(model_path):
        return None
    return joblib.load(model_path)


def check_system_status():
    """
    Check if models, graph, and dependencies are loaded properly.
    Reports whether the graph was loaded live from HDFS or from local cache.
    """
    if UI_DIR not in sys.path:
        sys.path.insert(0, UI_DIR)
    from hdfs_loader import load_graph_from_hdfs
    G, source, stats = load_graph_from_hdfs()
    model = load_cached_model()
    return {
        "graph_loaded": G is not None,
        "model_loaded": model is not None,
        "graph_nodes": len(G.nodes) if G else 0,
        "graph_edges": len(G.edges) if G else 0,
        "system_ok": (G is not None and model is not None),
        "data_source": source,
        "hdfs_path": stats.get("hdfs_path"),
        "spark_master": stats.get("spark_master"),
    }


def generate_candidates_from_distance(distance_km):
    """
    Generate candidate routes using the existing backend candidate generator logic.
    """
    return [
        {
            "mode": "Road",
            "distance_km": round(distance_km, 2),
            "travel_time_hr": round(estimate_travel_time(distance_km, 60), 2),
            "travel_cost": round(estimate_cost(distance_km, 0.12), 2),
            "transfers": 0,
            "delay_probability": 0.10,
            "crowd_level": 0.40,
            "weather_impact": 0.15,
            "safety_score": 0.95,
            "carbon_emission": round(estimate_carbon(distance_km, 0.18), 2),
        },
        {
            "mode": "Road + Rail",
            "distance_km": round(distance_km * 1.08, 2),
            "travel_time_hr": round(estimate_travel_time(distance_km * 1.08, 85), 2),
            "travel_cost": round(estimate_cost(distance_km * 1.08, 0.08), 2),
            "transfers": 1,
            "delay_probability": 0.15,
            "crowd_level": 0.55,
            "weather_impact": 0.12,
            "safety_score": 0.96,
            "carbon_emission": round(estimate_carbon(distance_km * 1.08, 0.07), 2),
        },
        {
            "mode": "Road + Flight",
            "distance_km": round(distance_km * 0.75, 2),
            "travel_time_hr": round(estimate_travel_time(distance_km * 0.75, 600), 2),
            "travel_cost": round(estimate_cost(distance_km * 0.75, 0.45), 2),
            "transfers": 1,
            "delay_probability": 0.22,
            "crowd_level": 0.65,
            "weather_impact": 0.25,
            "safety_score": 0.93,
            "carbon_emission": round(estimate_carbon(distance_km * 0.75, 0.30), 2),
        },
    ]


@st.cache_resource
def get_graph_spatial_index(_G):
    """
    Build a cached cKDTree index over graph nodes for sub-millisecond nearest node lookup.
    """
    import numpy as np
    from scipy.spatial import cKDTree
    node_list = list(_G.nodes)
    # node is (lon, lat) -> convert to (lat, lon) array
    coords = np.array([(n[1], n[0]) for n in node_list])
    tree = cKDTree(coords)
    return tree, node_list


def get_nearest_node(G, latitude, longitude):
    """
    Fast nearest node lookup with fallback to backend nearest_node.
    """
    try:
        tree, node_list = get_graph_spatial_index(G)
        _, idx = tree.query([latitude, longitude])
        return node_list[idx]
    except Exception:
        return nearest_node(G, latitude, longitude)


def calculate_route_recommendation(source_city, dest_city, preference):
    """
    Main function connecting Streamlit UI to recommendation backend.
    """
    src_geo = geocode_place(source_city)
    if not src_geo:
        return {"error": f"Source city '{source_city}' could not be geocoded."}

    dst_geo = geocode_place(dest_city)
    if not dst_geo:
        return {"error": f"Destination city '{dest_city}' could not be geocoded."}

    G = load_cached_graph()
    if G is None:
        return {"error": "Road graph dataset (data/graph/road_graph.pkl) not found."}

    model = load_cached_model()
    if model is None:
        return {"error": "Random Forest model (models/random_forest.pkl) not found."}

    # Find nearest graph nodes
    start_node = get_nearest_node(G, src_geo["latitude"], src_geo["longitude"])
    end_node = get_nearest_node(G, dst_geo["latitude"], dst_geo["longitude"])

    try:
        path = nx.shortest_path(G, start_node, end_node, weight="distance")
        distance_meters = nx.shortest_path_length(G, start_node, end_node, weight="distance")
        distance_km = distance_meters / 1000.0
    except nx.NetworkXNoPath:
        # Fallback to straight-line coordinate distance if no road path connects graph nodes
        from geopy.distance import geodesic
        distance_km = geodesic(
            (src_geo["latitude"], src_geo["longitude"]),
            (dst_geo["latitude"], dst_geo["longitude"])
        ).km
        path = [start_node, end_node]

    # Convert nodes (lon, lat) to (lat, lon) for Folium mapping
    route_coords = [(node[1], node[0]) for node in path]

    # Generate candidates
    routes = generate_candidates_from_distance(distance_km)

    # Evaluate ML prediction score for each candidate route
    evaluated_routes = []
    for route in routes:
        X = pd.DataFrame([[
            route["distance_km"],
            route["travel_time_hr"],
            route["travel_cost"],
            route["transfers"],
            route["delay_probability"],
            route["crowd_level"],
            route["weather_impact"],
            route["safety_score"],
            route["carbon_emission"],
        ]], columns=[
            "distance_km",
            "travel_time_hr",
            "travel_cost",
            "transfers",
            "delay_probability",
            "crowd_level",
            "weather_impact",
            "safety_score",
            "carbon_emission",
        ])

        probability = float(model.predict_proba(X)[0][1])
        r = dict(route)
        r["score"] = round(probability, 4)
        r["score_pct"] = round(probability * 100, 2)
        evaluated_routes.append(r)

    # Sort based on user preference
    if preference == "Fastest":
        sorted_routes = sorted(evaluated_routes, key=lambda x: x["travel_time_hr"])
    elif preference == "Cheapest":
        sorted_routes = sorted(evaluated_routes, key=lambda x: x["travel_cost"])
    elif preference == "Eco Friendly":
        sorted_routes = sorted(evaluated_routes, key=lambda x: x["carbon_emission"])
    else:  # "Balanced"
        sorted_routes = sorted(evaluated_routes, key=lambda x: x["score"], reverse=True)

    best_route = sorted_routes[0]

    return {
        "success": True,
        "src_geo": src_geo,
        "dst_geo": dst_geo,
        "distance_km": round(distance_km, 2),
        "candidates": evaluated_routes,
        "best_route": best_route,
        "route_coords": route_coords,
    }
