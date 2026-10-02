# data/processed/

Processed GeoPackage layers extracted from the raw OSM `.pbf` file. Not committed to the repository.

## Files

| File | Size | Description |
|------|------|-------------|
| `central-america.gpkg` | 5.6 GB | Full Central America GeoPackage with all OSM layers |
| `roads.gpkg` | 864 MB | Road network layer extracted from the full GeoPackage |
| `railways.gpkg` | 6.5 MB | Railway network layer extracted from the full GeoPackage |
| `airports.gpkg` | 3.5 MB | Airport layer extracted from the full GeoPackage |

## How to generate

```bash
python src/conversion/osm_to_gpkg.py
python src/extraction/extract_transport_layers.py
```
