# Backend API

Flask REST API for serving College Affordability ML model predictions and institution data.

## 📁 Contents

```
api/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── start.sh            # Startup script
├── test_api.sh         # API testing script
├── venv/               # Python virtual environment (created on first run)
└── README.md           # This file
```

## 🚀 Quick Start

### 1. Start the API

```bash
cd api
chmod +x start.sh
./start.sh
```

The API will be available at: **http://localhost:5000**

### 2. Test the API

In a new terminal:

```bash
cd api
chmod +x test_api.sh
./test_api.sh
```

## 📡 API Endpoints

### GET `/`
**API Home & Information**

Returns API metadata and available endpoints.

```bash
curl http://localhost:5000/
```

---

### GET `/health`
**Health Check**

Returns API health status and loaded resources.

```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "models_available": 5,
  "institutions_loaded": 4800
}
```

---

### GET `/models`
**List Available Models**

Returns information about all loaded ML models.

```bash
curl http://localhost:5000/models
```

**Response:**
```json
{
  "models": {
    "r1a": {
      "loaded": true,
      "type": "RandomForestRegressor",
      "features": ["afford_gap_cont", "admit_rate", ...],
      "n_features": 32,
      "hyperparameters": {...},
      "trained_date": "2025-11-16"
    },
    ...
  },
  "total": 5
}
```

---

### POST `/predict`
**Make Earnings Prediction**

Predict 10-year median earnings using a specified model.

**Request Body:**
```json
{
  "model": "r1a",
  "features": {
    "afford_gap_cont": 5000,
    "admit_rate": 0.65,
    "sat_avg": 1200,
    "act_avg": 25,
    "sat_missing": 0,
    "act_missing": 0,
    "inst_size": 5000,
    "pct_pell": 0.30,
    ...
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d @prediction_request.json
```

**Response:**
```json
{
  "model": "r1a",
  "prediction": 52500.75,
  "prediction_formatted": "$52,501",
  "features_used": ["afford_gap_cont", ...],
  "n_features": 32
}
```

**Available Models:**
- `r1a`: Core model (full features + treatment)
- `r1b`: Baseline (demographics only)
- `r1c`: Interaction model (affordability × selectivity)
- `r1d_high_pell`: Subgroup model for high Pell institutions
- `r1d_low_pell`: Subgroup model for low Pell institutions

---

### GET `/institutions`
**Search Institutions**

Search for institutions by name or state.

**Query Parameters:**
- `name` (string): Partial institution name (case-insensitive)
- `state` (string): State code (e.g., "CA", "NY")
- `limit` (int): Max results (default: 20)

**Examples:**
```bash
# Search by name
curl "http://localhost:5000/institutions?name=harvard"

# Search by state
curl "http://localhost:5000/institutions?state=CA&limit=10"

# Combined search
curl "http://localhost:5000/institutions?name=university&state=NY&limit=5"
```

**Response:**
```json
{
  "count": 3,
  "institutions": [
    {
      "unit_id": 166027,
      "institution_name": "Harvard University",
      "state": "MA",
      "afford_gap_cont": 5234.5,
      "earnings_10yr": 95600,
      "grad_rate_6yr": 97.3,
      ...
    },
    ...
  ]
}
```

---

### GET `/institution/<unit_id>`
**Get Institution Details**

Retrieve all data for a specific institution by its unit_id.

**Example:**
```bash
curl http://localhost:5000/institution/166027
```

**Response:**
```json
{
  "unit_id": 166027,
  "institution_name": "Harvard University",
  "state": "MA",
  "afford_gap_cont": 5234.5,
  "earnings_10yr": 95600,
  "grad_rate_6yr": 97.3,
  "admit_rate": 0.05,
  "sat_avg": 1520,
  ...
}
```

---

## 🔧 Configuration

### Change Port

Edit `app.py`, line 271:

```python
app.run(debug=True, host='0.0.0.0', port=5000)  # Change 5000 to desired port
```

### Data Paths

The API automatically loads data from:
- **Models**: `../outputs/rf_analysis/models/`
- **Data**: `../outputs/data/`

To change these, edit `app.py`, lines 15-16:

```python
MODELS_DIR = BASE_DIR / "outputs" / "rf_analysis" / "models"
DATA_DIR = BASE_DIR / "outputs" / "data"
```

### CORS Configuration

CORS is enabled by default for all origins. To restrict:

```python
from flask_cors import CORS

# Allow only specific origins
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
```

---

## 📦 Dependencies

```txt
flask==3.0.0           # Web framework
flask-cors==4.0.0      # CORS support
pandas>=2.0.0          # Data manipulation
numpy>=1.24.0          # Numerical computing
scikit-learn==1.6.1    # ML models
joblib>=1.2.0          # Model loading
```

**Important:** scikit-learn version must match the version used for training (1.6.1).

---

## 🛠️ Manual Setup

If `start.sh` doesn't work:

```bash
cd api

# Create virtual environment
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API
python app.py
```

---

## 🧪 Testing

### Automated Tests

Run all tests:
```bash
./test_api.sh
```

### Manual Testing

**Test health:**
```bash
curl http://localhost:5000/health
```

**List models:**
```bash
curl http://localhost:5000/models
```

**Search Harvard:**
```bash
curl "http://localhost:5000/institutions?name=harvard"
```

### Browser Testing

Open in browser:
- Home: http://localhost:5000/
- Health: http://localhost:5000/health
- Models: http://localhost:5000/models

---

## 🔗 Integration with Frontend

### Next.js Example

```typescript
// app/api/predict.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export async function predictEarnings(model: string, features: object) {
  const response = await fetch(`${API_URL}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, features })
  });
  
  return response.json();
}

export async function searchInstitutions(name: string) {
  const response = await fetch(`${API_URL}/institutions?name=${name}`);
  return response.json();
}
```

### React Hook Example

```typescript
// hooks/usePredict.ts
import { useState } from 'react';

export function usePredict() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  
  const predict = async (model: string, features: object) => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:5000/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model, features })
      });
      const data = await res.json();
      setResult(data);
    } finally {
      setLoading(false);
    }
  };
  
  return { predict, loading, result };
}
```

---

## 🚧 Troubleshooting

### Issue: Port 5000 already in use

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or change the port in app.py
```

### Issue: scikit-learn version mismatch

**Error:**
```
InconsistentVersionWarning: Trying to unpickle estimator trained with 1.6.1 but current version is X.X.X
```

**Solution:**
```bash
pip install --upgrade scikit-learn==1.6.1
```

### Issue: Models not loading

**Check:**
1. Models exist in `../outputs/rf_analysis/models/`
2. Model files: `model_r1a.pkl`, `model_r1b.pkl`, etc.
3. Metadata file: `model_metadata.json`

**Test:**
```python
import joblib
from pathlib import Path

model_path = Path("../outputs/rf_analysis/models/model_r1a.pkl")
model = joblib.load(model_path)  # Should not raise error
```

### Issue: Institution data not loading

**Check:**
1. Data exists: `../outputs/data/analysis_ready.csv`
2. File is readable
3. CSV format is valid

**Test:**
```python
import pandas as pd

df = pd.read_csv("../outputs/data/analysis_ready.csv")
print(df.shape)  # Should show (N, M)
```

---

## 📊 Performance

- **Model Loading**: ~2-3 seconds on startup
- **Data Loading**: ~1-2 seconds (4800 institutions)
- **Prediction Latency**: ~10-50ms per request
- **Memory Usage**: ~500MB (all models loaded)

---

## 🔮 Future Enhancements

- [ ] Add authentication/API keys
- [ ] Implement caching (Redis)
- [ ] Add rate limiting
- [ ] Create Swagger/OpenAPI documentation
- [ ] Add logging and monitoring
- [ ] Implement batch prediction endpoint
- [ ] Add model versioning
- [ ] Create Docker container
- [ ] Add database support (PostgreSQL)
- [ ] Implement async processing (Celery)

---

## 📝 Notes

- The API runs in **debug mode** by default (auto-reload on code changes)
- For production, set `debug=False` and use a production WSGI server (gunicorn, uwsgi)
- CORS is enabled for all origins - restrict in production
- No authentication implemented - add before deploying publicly

---

## 📚 Related Documentation

- [Main Project README](../README.MD)
- [Project Structure](../PROJECT_STRUCTURE.md)
- [Model Documentation](../outputs/rf_analysis/models/README.md)
- [LLM Module](../llm/README.md)

---

**Last Updated:** November 2025  
**API Version:** 1.0.0  
**Flask Version:** 3.0.0

