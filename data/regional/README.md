# data/regional/

Regionally filtered transport network files clipped to the Central America study area. Not committed to the repository.

## Files

| File | Size | Description |
|------|------|-------------|
| `regional_roads.gpkg` | 132 MB | Full road network clipped to regional bounding box |
| `regional_roads_filtered.gpkg` | 88 MB | Roads filtered to major highway types only (trunk, primary, secondary) |
| `regional_railways.gpkg` | 376 KB | Railway lines within the regional boundary |
| `regional_airports.gpkg` | 232 KB | Airport points within the regional boundary |

## How to generate

```bash
python src/preprocessing/refine_roads.py
```
