# Scalable Multimodal Transportation Recommendation System

A big data pipeline and recommendation engine for finding the fastest, cheapest, or most eco-friendly transport routes across Central America.

## Overview

This project implements a scalable pipeline to process massive OpenStreetMap (OSM) datasets using Hadoop and Spark, build a routing graph, and train a Random Forest machine learning model to recommend the best multimodal routes (Road, Rail, Flight) between cities based on user preferences.

It features a modern, interactive Streamlit frontend for users to query the recommendation engine in real-time.

---

## 🏗️ Architecture & Tech Stack

### Phase 1: Data Pipeline & Big Data (Offline)
- **Data Source**: OpenStreetMap `.pbf` planet extracts (Central America)
- **Big Data**: Hadoop HDFS (Storage), Apache Spark (Profiling & Validation)
- **Geospatial Processing**: GeoPandas, GDAL (ogr2ogr)
- **Graph Processing**: NetworkX

### Phase 2: Machine Learning (Offline)
- **Algorithm**: Random Forest Classifier
- **Features**: Distance, Travel Time, Cost, Transfers, Delay Probability, Carbon Emission, Crowd Level, Weather Impact, Safety Score.

### Phase 3: Web Application (Real-time UI)
- **Framework**: Streamlit
- **Mapping**: Folium
- **Optimization**: cKDTree for sub-millisecond geospatial nearest-node search

---

## 📁 Project Structure

```
multimodal_transport_ca/
├── config/              # Centralized configuration and path constants
├── data/                # Datasets (See data/README.md for details)
│   ├── graph/           # Pre-built NetworkX road graph
│   ├── journeys/        # ML training data
│   ├── network/         # Final cleaned transport network layers
│   ├── processed/       # Extracted & converted GeoPackage layers
│   ├── raw/             # Original unprocessed OSM source file
│   └── regional/        # Filtered regional subsets
├── models/              # Pickled ML models (Random Forest)
├── scripts/             # Utility and test scripts
├── sql/                 # SQL queries for geospatial filtering
├── src/                 # Backend source code
│   ├── cleaning/        # Data cleaning scripts
│   ├── conversion/      # OSM to GeoPackage conversion
│   ├── data_processing/ # Generic data processing utils
│   ├── etl/             # Hadoop HDFS loading scripts
│   ├── extraction/      # Layer extraction from GeoPackage
│   ├── graph/           # Generic graph utilities
│   ├── journey/         # ML feature engineering and candidate generation
│   ├── ml/              # Random Forest training and evaluation
│   ├── parquet/         # GeoPackage to Parquet conversion
│   ├── preprocessing/   # Data filtering (e.g. major roads only)
│   ├── routing/         # NetworkX routing and geocoding
│   └── spark/           # Apache Spark profiling and session management
├── ui/                  # Streamlit Web Application
│   ├── app.py           # Main entry point for the UI
│   ├── components.py    # Reusable UI components (charts, tickets, maps)
│   └── utils.py         # UI helper functions and graph lookups
└── requirements.txt     # Python dependencies
```

---

## 🚀 Running the Web App

The web application runs entirely independently of the Hadoop/Spark data pipeline. It directly loads the pre-built `road_graph.pkl` and `random_forest.pkl` files.

### Prerequisites

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Launch the App

```bash
streamlit run ui/app.py
```

---

## 📊 Running the Data Pipeline (Development)

If you wish to rebuild the datasets, graph, and ML model from scratch, you must have Hadoop and Spark installed and configured.

1. **Download Data**: Place the `central-america-latest.osm.pbf` file in `data/raw/`
2. **Extract & Convert**:
   ```bash
   python src/conversion/osm_to_gpkg.py
   python src/extraction/extract_transport_layers.py
   ```
3. **Filter**:
   ```bash
   python src/preprocessing/refine_roads.py
   ```
4. **Hadoop / Spark ETL**:
   ```bash
   python src/etl/normalize_transport.py
   python src/etl/load_network_to_hdfs.py
   python src/spark/profile_transport_data.py
   ```
5. **Build Graph**:
   ```bash
   python src/routing/build_road_graph.py
   ```
6. **Train Model**:
   ```bash
   python src/journey/generate_candidates.py
   python src/journey/feature_engineering.py
   python src/ml/train_random_forest.py
   ```
