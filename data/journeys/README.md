# data/journeys/

Machine learning datasets for training the route recommendation model. The smaller training dataset is included in the repository, but larger intermediate files are not.

## Files

| File | Size | Description |
|------|------|-------------|
| `candidate_journeys.csv` | ~ | Intermediate generated candidate journeys (Not committed) |
| `journey_features.csv` | ~ | Feature-engineered candidate journeys (Not committed) |
| `training_dataset.csv` | 244 KB | Final training dataset with labels, used to train the Random Forest model (Committed) |

## How to generate

```bash
python src/journey/generate_candidates.py
python src/journey/feature_engineering.py
python src/journey/generate_training_dataset.py
```
