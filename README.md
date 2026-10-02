# Multimodal Transport Route Recommendation (Central America)

This project builds a data pipeline and machine learning system to recommend optimal multimodal transport routes across Central America. It processes raw OpenStreetMap (OSM) data, stores it in a distributed Hadoop HDFS cluster, processes it with Apache Spark, builds a routing graph with NetworkX, trains a Random Forest model with scikit-learn, and serves real-time recommendations via a Streamlit web application.

## 🏗️ Architecture & Tech Stack

- **Data Ingestion:** GDAL (`ogr2ogr`), GeoPandas (extracting from OSM `.pbf`)
- **Data Storage:** Apache Hadoop HDFS
- **Big Data Processing:** Apache Spark (PySpark)
- **Routing Engine:** NetworkX (Dijkstra's shortest path algorithm)
- **Machine Learning:** Scikit-learn (Random Forest Classifier)
- **Web UI:** Streamlit

---

## 🗺️ Complete End-to-End Workflow

To run this project on a new dataset, follow these exact steps in order.

### Phase 1: Data Preparation
1. **Raw Data:** Place your OSM `.pbf` file (e.g., `central-america.osm.pbf`) in `data/raw/` and update `config/project_config.py`.
2. **Convert to GeoPackage:** 
   ```bash
   python src/conversion/osm_to_gpkg.py
   ```
3. **Extract Transport Layers** (Roads, Railways, Airports):
   ```bash
   python src/extraction/extract_transport_layers.py
   ```
4. **Refine & Filter:** Clip to the region boundary and filter out minor roads.
   ```bash
   python src/preprocessing/refine_roads.py
   python src/preprocessing/filters.py
   ```
5. **Convert to Parquet:** For efficient Spark processing.
   ```bash
   python src/parquet/gpkg_to_parquet.py
   ```

### Phase 2: Hadoop & Spark (Big Data Layer)
6. **Upload to HDFS:** Push the processed data into the Hadoop distributed filesystem.
   ```bash
   python src/etl/load_network_to_hdfs.py
   ```
7. **Normalize with Spark:** Standardize schemas across all transport modes.
   ```bash
   python src/etl/normalize_transport.py
   ```
8. **Profile Data:** Run Spark quality checks.
   ```bash
   python src/spark/profile_transport_data.py
   ```

### Phase 3: Routing Graph & Machine Learning
9. **Build Network Graph:** Create a NetworkX graph from the road segments.
   ```bash
   python src/routing/build_road_graph.py
   ```
10. **Generate Candidate Journeys:** Simulate random trips to generate training data.
    ```bash
    python src/journey/generate_candidates.py
    ```
11. **Feature Engineering:** Calculate route statistics (distance, time, cost, emissions).
    ```bash
    python src/journey/feature_engineering.py
    python src/journey/generate_training_dataset.py
    ```
12. **Train Model:** Train a Random Forest model to recommend the best route option.
    ```bash
    python src/ml/train_random_forest.py
    ```

### Phase 4: Web Application
13. **Launch Streamlit UI:** Serve live recommendations.
    ```bash
    streamlit run ui/app.py
    ```

---

## 📂 Source Code Structure (`src/`)

The `src/` directory contains all the Python modules for the pipeline. Here is a thorough explanation of what each module does:

### `src/cleaning/`
- **`clean_transport_data.py`**: Handles basic data cleaning tasks, such as removing null geometries or invalid coordinates from the raw extracted layers.

### `src/conversion/`
- **`osm_to_gpkg.py`**: Uses `ogr2ogr` to convert the raw OSM `.pbf` binary file into a more manageable GeoPackage (`.gpkg`) format.
- **`network_to_parquet.py`**: Converts finalized network `.gpkg` files into the Parquet columnar format.

### `src/data_processing/`
- **`inspect_gpkg.py`**: A utility script to quickly inspect the layers and schema of a GeoPackage file during development.

### `src/etl/`
- **`load_network_to_hdfs.py`**: Executes Hadoop shell commands (`hdfs dfs -put`) to upload the Parquet and GeoPackage files from the local filesystem to the HDFS cluster.
- **`normalize_transport.py`**: A Spark script that reads Parquet files from HDFS, normalizes their schemas (ensuring consistent column names like `transport_type`, `name`, `osm_id`), and writes them back to HDFS.
- **`check_normalized.py`**: A utility to verify that the normalized data in HDFS has the expected schema and row counts.

### `src/extraction/`
- **`extract_transport_layers.py`**: Uses GeoPandas to split the monolithic `.gpkg` file into separate specialized files: `roads.gpkg`, `railways.gpkg`, and `airports.gpkg`.

### `src/graph/` (Core Graph Utilities)
- **`build_graph.py`**: Core functions for constructing a directed graph from GeoDataFrames.
- **`check_graph.py`**: Diagnostics for validating graph connectivity and detecting isolated nodes.
- **`graph_utils.py`**: Helper functions for graph traversal, edge weight calculations, and distance heuristic calculations.

### `src/journey/` (Training Data Generation)
- **`generate_candidates.py`**: Generates synthetic multimodal journey options between random start/end points using the graph.
- **`feature_engineering.py`**: Computes ML features for journeys (e.g., predicted delays, crowd levels, carbon emissions, safety scores).
- **`generate_training_dataset.py`**: Combines features and assigns the target label (`recommended = 1` or `0`) based on optimization criteria to create `training_dataset.csv`.
- **`check_candidates.py`**: Verifies the sanity of the generated candidate journeys.

### `src/ml/` (Machine Learning)
- **`train_random_forest.py`**: Trains the main `RandomForestClassifier` on `training_dataset.csv` and saves the serialized model to `models/random_forest.pkl`.
- **`evaluate_model.py` / `model_evaluation.py`**: Scripts to generate evaluation metrics (accuracy, F1-score, confusion matrix) for the trained model.
- **`feature_importance.py`**: Analyzes and plots which journey features the Random Forest model relies on most.
- **`recommend_trip.py`**: A standalone CLI testing script to feed a single trip through the ML model and print the recommendation.

### `src/parquet/`
- **`gpkg_to_parquet.py`**: A dedicated utility pipeline script for batch converting multiple GeoPackage layers into Parquet files.
- **`check_parquet.py`**: Utility to inspect Parquet metadata and schemas locally before uploading to HDFS.

### `src/preprocessing/`
- **`refine_roads.py`**: Filters the massive raw road network down to relevant highway types (e.g., dropping pedestrian paths or residential streets if they aren't needed for long-distance routing).
- **`filters.py`**: Contains spatial filtering logic, such as clipping the data strictly to the Central America bounding box.

### `src/routing/` (Routing Engine)
- **`build_road_graph.py`**: The main executable script that builds `road_graph.pkl` from the processed road network.
- **`shortest_path.py`**: Implements Dijkstra's and A* search algorithms to find the fastest path between two nodes on the graph.
- **`geocode.py`**: Helper functions to convert city names into latitude/longitude coordinates (used by the UI).
- **`generate_candidates.py`**: Similar to the one in `journey/`, but used during inference (UI runtime) rather than training data generation.
- **`recommend_route.py`**: The runtime routing engine that ties together geocoding, graph traversal, and ML model inference to produce the final UI result.
- **`filter_roads.py` / `region_extractor.py`**: Additional spatial utilities for subsetting the routing network dynamically.
- **`check_graph.py`**: Validates the serialized `road_graph.pkl` used by the UI.

### `src/spark/`
- **`profile_transport_data.py`**: A heavy PySpark script that performs deep analytics on the HDFS data (e.g., counting highway types, checking null distributions) to prove data integrity.
- **`load_hdfs_data.py`**: Utilities for reading HDFS data into Spark DataFrames.
- **`spark_session.py`**: A centralized configuration file for initializing the `SparkSession` with the correct Master URL (`spark://localhost:7077`) and UI port settings.
