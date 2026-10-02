# data/network/

Final cleaned and normalized transport network layers. Not committed to the repository.

## Files

| File | Size | Description |
|------|------|-------------|
| `roads_network.gpkg` | 645 MB | Final cleaned road network ready for graph building and HDFS loading |
| `railways_network.gpkg` | 4.6 MB | Final cleaned railway network |

## How to generate

```bash
# Loaded via Spark / Hadoop ETL
python src/etl/normalize_transport.py
```
