# data/graph/

Pre-built graph representations of the road network used for routing. Not committed to the repository due to size.

## Files

| File | Size | Description |
|------|------|-------------|
| `road_graph.pkl` | 34 MB | NetworkX graph object (Pickled) used by the Streamlit UI for runtime route calculation |

## How to generate

```bash
python src/routing/build_road_graph.py
```
