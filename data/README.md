# data/

This directory contains all datasets used by the Multimodal Transportation Recommendation System.
These files are **not committed to the repository** due to their large size, but the folder structure is preserved below.

---

## Folder Structure

```
data/
├── raw/                          # Original unprocessed OpenStreetMap source file
│   └── central-america-260713.osm.pbf        (743 MB)
│
├── processed/                    # Extracted & converted GeoPackage layers
│   ├── central-america.gpkg                  (5.6 GB)
│   ├── roads.gpkg                            (864 MB)
│   ├── railways.gpkg                         (6.5 MB)
│   └── airports.gpkg                         (3.5 MB)
│
├── regional/                     # Filtered regional subsets for Central America
│   ├── regional_roads.gpkg                   (132 MB)
│   ├── regional_roads_filtered.gpkg          (88  MB)
│   ├── regional_railways.gpkg                (376 KB)
│   └── regional_airports.gpkg                (232 KB)
│
├── network/                      # Final cleaned transport network layers
│   ├── roads_network.gpkg                    (645 MB)
│   └── railways_network.gpkg                 (4.6 MB)
│
├── graph/                        # Pre-built NetworkX road graph (used by UI at runtime)
│   └── road_graph.pkl                        (34  MB)
│
└── journeys/                     # ML training data generated from graph
    ├── candidate_journeys.csv                (generated)
    ├── journey_features.csv                  (generated)
    └── training_dataset.csv                  (244 KB)
```

---

## How to obtain / reproduce these files

1. **Raw OSM data** — Download from [Geofabrik](https://download.geofabrik.de/central-america.html):
   ```
   central-america-YYMMDD.osm.pbf  →  place in data/raw/
   ```

2. **Processed layers** — Run the extraction pipeline:
   ```bash
   python src/conversion/osm_to_gpkg.py
   python src/extraction/extract_transport_layers.py
   python src/preprocessing/refine_roads.py
   ```

3. **NetworkX road graph** — Build the graph:
   ```bash
   python src/routing/build_road_graph.py
   ```

4. **Training data & ML model** — Generate training data and train:
   ```bash
   python src/journey/generate_candidates.py
   python src/journey/feature_engineering.py
   python src/ml/train_random_forest.py
   ```
