# ML Model API Backend

Flask API server that serves Random Forest earnings prediction models to the Next.js frontend.

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python app.py
```

The API will start on `http://localhost:5000`

## API Endpoints

### Health Check
```
GET /health
```

### Get Model Information
```
GET /api/models/info
```

### Make Prediction
```
POST /api/predict
Content-Type: application/json

{
  "model": "r1a_full",
  "features": {
    "afford_gap_cont": 15000,
    "admit_rate_imputed": 0.65,
    ...
  }
}
```

### Search Institutions
```
GET /api/institutions/search?q=harvard&limit=10
```

### Get Institution Details
```
GET /api/institutions/<unit_id>
```

### Get Feature Importance
```
GET /api/feature-importance?model=r1a
```

### Get Dataset Stats
```
GET /api/stats
```

## Testing

Test the health endpoint:
```bash
curl http://localhost:5000/health
```

Test a prediction (example):
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d @test_prediction.json
```

## Files

- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Notes

- The API loads all 5 Random Forest models at startup (~175 MB)
- Institution data loaded from `../../outputs/data/analysis_ready.csv`
- CORS enabled for Next.js frontend (`http://localhost:3000`)
- All predictions use the pipeline (preprocessing + model)

## Troubleshooting

**Models not loading?**
- Ensure paths to `../../outputs/rf_analysis/models/` are correct
- Check that all `.pkl` files exist

**Data not found?**
- Verify `../../outputs/data/analysis_ready.csv` exists
- Run data preparation script if needed

**CORS errors?**
- Check that `flask-cors` is installed
- Verify frontend URL is `http://localhost:3000`

