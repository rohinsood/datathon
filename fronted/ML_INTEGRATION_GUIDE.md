# 🤖 Random Forest Model Integration Guide

## Overview

This guide explains how to integrate the trained Random Forest earnings prediction models into your Next.js frontend application.

**Current Status**: Predictions page uses mock data  
**Goal**: Connect to real trained models with 95%+ accuracy

---

## 📋 Integration Architecture

```
Frontend (Next.js)          Backend (Python API)        ML Models
─────────────────────      ──────────────────────      ────────────────
┌─────────────────┐        ┌──────────────────┐       ┌──────────────┐
│ /predictions    │──POST─→│ /api/predict     │──load─→│ R1a model    │
│ (React form)    │←──JSON─│ (Flask/FastAPI)  │←─pred─│ (54 MB .pkl) │
└─────────────────┘        └──────────────────┘       └──────────────┘
                                    │
                           ┌────────┴────────┐
                           ↓                 ↓
                    ┌─────────────┐  ┌──────────────┐
                    │ analysis_   │  │ variable_    │
                    │ ready.csv   │  │ lists.json   │
                    └─────────────┘  └──────────────┘
```

---

## 🚀 Step 1: Create Python API Backend

### Option A: Flask API (Recommended for simplicity)

Create `my-app/api-backend/app.py`:

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js

# Load models at startup
print("Loading ML models...")
BASE_PATH = "../../outputs/rf_analysis/models"

models = {
    "r1a_full": joblib.load(f"{BASE_PATH}/model_r1a_full.pkl"),
    "r1b_no_afford": joblib.load(f"{BASE_PATH}/model_r1b_no_afford.pkl"),
    "r1c_interactions": joblib.load(f"{BASE_PATH}/model_r1c_interactions.pkl"),
    "r1d_high_pell": joblib.load(f"{BASE_PATH}/model_r1d_high_pell.pkl"),
    "r1d_low_pell": joblib.load(f"{BASE_PATH}/model_r1d_low_pell.pkl")
}

# Load metadata
with open(f"{BASE_PATH}/model_metadata.json", "r") as f:
    metadata = json.load(f)

# Load analysis data for feature ranges
df = pd.read_csv("../../outputs/data/analysis_ready.csv")
df = df.rename(columns={
    'Affordability Gap (net price minus income earned working 10 hrs at min wage)': 'afford_gap_cont'
})

print(f"✓ Loaded {len(models)} models")
print(f"✓ Loaded data: {len(df)} institutions")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "models_loaded": len(models)})

@app.route('/api/models/info', methods=['GET'])
def models_info():
    """Get information about available models"""
    return jsonify({
        "models": {
            "r1a_full": {
                "name": "Full Model (R1a)",
                "description": "Complete model with affordability and all factors",
                "performance": {"r2": 0.9537, "rmse": 2767},
                "features": metadata["numeric_features"] + metadata["categorical_features"]
            },
            "r1b_no_afford": {
                "name": "No Affordability Baseline (R1b)",
                "description": "Model without affordability gap for comparison",
                "performance": {"r2": 0.9643, "rmse": 2430},
                "features": [f for f in metadata["numeric_features"] if f != "afford_gap_cont"] + metadata["categorical_features"]
            },
            "r1c_interactions": {
                "name": "Interaction Model (R1c)",
                "description": "Model with affordability × demographics interactions",
                "performance": {"r2": 0.9328, "rmse": 3331},
                "features": metadata["numeric_features"] + ["afford_x_pell", "afford_x_urm"] + metadata["categorical_features"]
            },
            "r1d_high_pell": {
                "name": "High-Pell Subgroup (R1d)",
                "description": "Specialized model for institutions with ≥44% Pell students",
                "performance": {"r2": 0.7330, "rmse": 5126},
                "features": metadata["numeric_features"] + metadata["categorical_features"]
            },
            "r1d_low_pell": {
                "name": "Low-Pell Subgroup (R1d)",
                "description": "Specialized model for institutions with <44% Pell students",
                "performance": {"r2": 0.9381, "rmse": 3301},
                "features": metadata["numeric_features"] + metadata["categorical_features"]
            }
        },
        "metadata": metadata
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Make earnings prediction for an institution
    
    Request body:
    {
        "model": "r1a_full",  // or r1b_no_afford, r1c_interactions, etc.
        "features": {
            "afford_gap_cont": 15000,
            "admit_rate_imputed": 0.65,
            "sat_composite_25_imputed": 1100,
            // ... all other required features
        }
    }
    """
    try:
        data = request.json
        model_name = data.get("model", "r1a_full")
        features = data.get("features", {})
        
        if model_name not in models:
            return jsonify({"error": f"Model '{model_name}' not found"}), 400
        
        # Get feature list for this model
        if model_name == "r1b_no_afford":
            feature_list = [f for f in metadata["numeric_features"] if f != "afford_gap_cont"] + metadata["categorical_features"]
        elif model_name == "r1c_interactions":
            # Add interaction terms
            features["afford_x_pell"] = features.get("afford_gap_cont", 0) * features.get("pct_pell_imputed", 0)
            features["afford_x_urm"] = features.get("afford_gap_cont", 0) * features.get("pct_urm", 0)
            feature_list = metadata["numeric_features"] + ["afford_x_pell", "afford_x_urm"] + metadata["categorical_features"]
        else:
            feature_list = metadata["numeric_features"] + metadata["categorical_features"]
        
        # Create feature dataframe
        feature_df = pd.DataFrame([features])
        
        # Ensure all required features are present
        missing_features = [f for f in feature_list if f not in feature_df.columns]
        if missing_features:
            return jsonify({
                "error": f"Missing required features: {missing_features}",
                "required_features": feature_list
            }), 400
        
        # Select features in correct order
        X = feature_df[feature_list]
        
        # Make prediction
        prediction = models[model_name].predict(X)[0]
        
        return jsonify({
            "model": model_name,
            "predicted_earnings": float(prediction),
            "features_used": feature_list,
            "performance": {
                "typical_error": 2767 if model_name == "r1a_full" else 
                                2430 if model_name == "r1b_no_afford" else
                                3331 if model_name == "r1c_interactions" else
                                5126 if model_name == "r1d_high_pell" else 3301
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/institutions/<int:unit_id>', methods=['GET'])
def get_institution(unit_id):
    """Get institution data and prediction"""
    inst = df[df['unit_id'] == unit_id]
    
    if len(inst) == 0:
        return jsonify({"error": "Institution not found"}), 404
    
    inst_row = inst.iloc[0]
    
    # Prepare features for prediction
    feature_list = metadata["numeric_features"] + metadata["categorical_features"]
    features = {f: float(inst_row[f]) if pd.notna(inst_row[f]) else 0 for f in feature_list}
    
    # Make prediction
    X = pd.DataFrame([features])[feature_list]
    prediction_r1a = models["r1a_full"].predict(X)[0]
    
    return jsonify({
        "unit_id": int(unit_id),
        "name": inst_row["Institution Name_aff"],
        "state": inst_row["State Abbreviation"],
        "sector": inst_row["Sector Name"],
        "actual_earnings": float(inst_row["earnings_10yr"]) if pd.notna(inst_row["earnings_10yr"]) else None,
        "predicted_earnings": float(prediction_r1a),
        "affordability_gap": float(inst_row["afford_gap_cont"]),
        "pct_pell": float(inst_row["pct_pell_imputed"]),
        "admit_rate": float(inst_row["admit_rate_imputed"]),
        "grad_rate": float(inst_row["grad_rate_6yr"]) if pd.notna(inst_row["grad_rate_6yr"]) else None,
        "features": features
    })

@app.route('/api/institutions/search', methods=['GET'])
def search_institutions():
    """Search institutions by name or state"""
    query = request.args.get('q', '').lower()
    state = request.args.get('state', '')
    limit = int(request.args.get('limit', 20))
    
    filtered = df.copy()
    
    if query:
        filtered = filtered[filtered['Institution Name_aff'].str.lower().str.contains(query, na=False)]
    
    if state:
        filtered = filtered[filtered['State Abbreviation'] == state.upper()]
    
    results = filtered.head(limit)
    
    return jsonify({
        "count": len(results),
        "institutions": [
            {
                "unit_id": int(row["unit_id"]),
                "name": row["Institution Name_aff"],
                "state": row["State Abbreviation"],
                "sector": row["Sector Name"],
                "afford_gap": float(row["afford_gap_cont"]),
                "pct_pell": float(row["pct_pell_imputed"]),
                "actual_earnings": float(row["earnings_10yr"]) if pd.notna(row["earnings_10yr"]) else None
            }
            for _, row in results.iterrows()
        ]
    })

@app.route('/api/feature-importance', methods=['GET'])
def feature_importance():
    """Get feature importance data"""
    model_name = request.args.get('model', 'r1a')
    
    importance_files = {
        'r1a': '../../outputs/rf_analysis/feature_importance_r1a.csv',
        'r1c': '../../outputs/rf_analysis/feature_importance_r1c.csv',
        'high_pell': '../../outputs/rf_analysis/feature_importance_high_pell.csv',
        'low_pell': '../../outputs/rf_analysis/feature_importance_low_pell.csv'
    }
    
    if model_name not in importance_files:
        return jsonify({"error": "Invalid model name"}), 400
    
    df_importance = pd.read_csv(importance_files[model_name])
    
    return jsonify({
        "model": model_name,
        "features": [
            {
                "name": row["feature"],
                "importance": float(row["importance"]),
                "rank": idx + 1
            }
            for idx, row in df_importance.iterrows()
        ]
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 ML API Server Starting...")
    print("="*60)
    print(f"Models loaded: {list(models.keys())}")
    print(f"Institutions available: {len(df)}")
    print("\nEndpoints:")
    print("  GET  /health")
    print("  GET  /api/models/info")
    print("  POST /api/predict")
    print("  GET  /api/institutions/<unit_id>")
    print("  GET  /api/institutions/search?q=<query>")
    print("  GET  /api/feature-importance?model=<r1a|r1c|high_pell|low_pell>")
    print("\n" + "="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### Install Dependencies

Create `my-app/api-backend/requirements.txt`:

```
flask==3.0.0
flask-cors==4.0.0
joblib==1.3.2
pandas==2.1.4
numpy==1.26.2
scikit-learn==1.3.2
```

Install:
```bash
cd my-app/api-backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Run the API:
```bash
python app.py
```

The API will start on `http://localhost:5000`

---

## 🎨 Step 2: Update Frontend Predictions Page

Replace the mock prediction logic in `app/predictions/page.tsx`:

```typescript
// Add at the top of the file
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// Replace the handlePredict function
const handlePredict = async () => {
  setLoading(true);
  setError(null);
  
  try {
    // Map form data to model features
    const features = {
      afford_gap_cont: parseFloat(formData.affordability_gap) || 0,
      admit_rate_imputed: parseFloat(formData.admission_rate) / 100 || 0,
      sat_composite_25_imputed: parseFloat(formData.sat_avg) || 0,
      act_composite_25_imputed: parseFloat(formData.act_avg) || 0,
      sat_missing: formData.sat_avg ? 0 : 1,
      act_missing: formData.act_avg ? 0 : 1,
      log_instructional_exp: Math.log(parseFloat(formData.instructional_exp) + 1) || 0,
      log_endowment: Math.log(parseFloat(formData.endowment) + 1) || 0,
      has_endowment: parseFloat(formData.endowment) > 0 ? 1 : 0,
      pct_pell_imputed: parseFloat(formData.pell_percentage) / 100 || 0,
      pct_urm: parseFloat(formData.urm_percentage) / 100 || 0,
      pct_white_imputed: parseFloat(formData.white_percentage) / 100 || 0,
      pct_women_imputed: parseFloat(formData.women_percentage) / 100 || 0,
      is_hbcu: parseInt(formData.historically_black) || 0,
      is_hsi: parseInt(formData.hispanic_serving) || 0,
      is_tcu: parseInt(formData.tribal) || 0,
      is_aanapisi: parseInt(formData.aanapisi) || 0,
      is_pbi: parseInt(formData.pbi) || 0,
      sector: formData.sector,
      size_category: formData.size_category,
      region: formData.region
    };

    // Call the real API
    const response = await fetch(`${API_BASE_URL}/api/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: selectedModel,  // r1a_full, r1b_no_afford, etc.
        features: features
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Prediction failed');
    }

    const result = await response.json();
    
    setPrediction({
      earnings: Math.round(result.predicted_earnings),
      model: result.model,
      confidence: 95,  // Based on R² = 0.9537
      typical_error: result.performance.typical_error
    });
    
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
};
```

---

## 📊 Step 3: Create Model Analytics Dashboard

Create `app/analytics/rf-models/page.tsx`:

```typescript
"use client";

import { useEffect, useState } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export default function RFModelsAnalytics() {
  const [featureImportance, setFeatureImportance] = useState(null);
  const [selectedModel, setSelectedModel] = useState('r1a');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFeatureImportance();
  }, [selectedModel]);

  const fetchFeatureImportance = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/feature-importance?model=${selectedModel}`);
      const data = await response.json();
      setFeatureImportance(data);
    } catch (error) {
      console.error('Error fetching feature importance:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartData = featureImportance ? {
    labels: featureImportance.features.slice(0, 15).map(f => f.name),
    datasets: [{
      label: 'Feature Importance',
      data: featureImportance.features.slice(0, 15).map(f => f.importance * 100),
      backgroundColor: 'rgba(139, 92, 246, 0.6)',
      borderColor: 'rgba(139, 92, 246, 1)',
      borderWidth: 1,
    }]
  } : null;

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Random Forest Model Analytics</h1>
        
        {/* Model selector */}
        <div className="mb-6 flex space-x-4">
          {['r1a', 'r1c', 'high_pell', 'low_pell'].map((model) => (
            <button
              key={model}
              onClick={() => setSelectedModel(model)}
              className={`px-4 py-2 rounded-lg ${
                selectedModel === model
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-700'
              }`}
            >
              {model.toUpperCase().replace('_', ' ')}
            </button>
          ))}
        </div>

        {/* Feature Importance Chart */}
        {!loading && chartData && (
          <div className="bg-white rounded-lg p-6 shadow">
            <h2 className="text-xl font-bold mb-4">Top 15 Features - {selectedModel.toUpperCase()}</h2>
            <Bar 
              data={chartData}
              options={{
                indexAxis: 'y',
                responsive: true,
                plugins: {
                  legend: { display: false },
                  title: { display: true, text: 'Feature Importance (%)' }
                }
              }}
            />
          </div>
        )}

        {/* Feature Importance Table */}
        {!loading && featureImportance && (
          <div className="mt-6 bg-white rounded-lg p-6 shadow">
            <h2 className="text-xl font-bold mb-4">All Features Ranked</h2>
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Rank</th>
                  <th className="text-left p-2">Feature</th>
                  <th className="text-right p-2">Importance (%)</th>
                </tr>
              </thead>
              <tbody>
                {featureImportance.features.map((feature, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="p-2">#{idx + 1}</td>
                    <td className="p-2 font-medium">{feature.name}</td>
                    <td className="p-2 text-right">{(feature.importance * 100).toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}
```

---

## 🔍 Step 4: Create Institution Search & Prediction

Create `app/institutions/search/page.tsx`:

```typescript
"use client";

import { useState } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export default function InstitutionSearch() {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [selectedInst, setSelectedInst] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!searchQuery) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/institutions/search?q=${encodeURIComponent(searchQuery)}`
      );
      const data = await response.json();
      setResults(data.institutions);
    } catch (error) {
      console.error('Error searching:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadInstitution = async (unitId) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/institutions/${unitId}`);
      const data = await response.json();
      setSelectedInst(data);
    } catch (error) {
      console.error('Error loading institution:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Institution Earnings Predictor</h1>
        
        {/* Search */}
        <div className="bg-white rounded-lg p-6 shadow mb-6">
          <div className="flex space-x-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search by institution name..."
              className="flex-1 px-4 py-2 border rounded-lg"
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700"
            >
              Search
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Search Results */}
          <div className="bg-white rounded-lg p-6 shadow">
            <h2 className="text-xl font-bold mb-4">Search Results ({results.length})</h2>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {results.map((inst) => (
                <div
                  key={inst.unit_id}
                  onClick={() => loadInstitution(inst.unit_id)}
                  className="p-3 border rounded hover:bg-purple-50 cursor-pointer"
                >
                  <div className="font-semibold">{inst.name}</div>
                  <div className="text-sm text-gray-600">
                    {inst.state} • {inst.sector}
                  </div>
                  <div className="text-sm text-gray-500">
                    Affordability Gap: ${inst.afford_gap.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Selected Institution */}
          {selectedInst && (
            <div className="bg-white rounded-lg p-6 shadow">
              <h2 className="text-xl font-bold mb-4">{selectedInst.name}</h2>
              
              <div className="space-y-4">
                <div className="border-b pb-3">
                  <div className="text-sm text-gray-600">Predicted 10-Year Earnings</div>
                  <div className="text-3xl font-bold text-purple-600">
                    ${Math.round(selectedInst.predicted_earnings).toLocaleString()}
                  </div>
                  {selectedInst.actual_earnings && (
                    <div className="text-sm text-gray-500">
                      Actual: ${Math.round(selectedInst.actual_earnings).toLocaleString()}
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-600">Affordability Gap</div>
                    <div className="font-semibold">${selectedInst.affordability_gap.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">% Pell Students</div>
                    <div className="font-semibold">{(selectedInst.pct_pell * 100).toFixed(1)}%</div>
                  </div>
                  <div>
                    <div className="text-gray-600">Admission Rate</div>
                    <div className="font-semibold">{(selectedInst.admit_rate * 100).toFixed(1)}%</div>
                  </div>
                  {selectedInst.grad_rate && (
                    <div>
                      <div className="text-gray-600">Graduation Rate</div>
                      <div className="font-semibold">{(selectedInst.grad_rate * 100).toFixed(1)}%</div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
```

---

## 🔧 Step 5: Environment Configuration

Create `.env.local` in `my-app/`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:5000
```

For production:
```bash
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

---

## 🚀 Step 6: Running Everything

### Terminal 1: Start Python API
```bash
cd my-app/api-backend
source venv/bin/activate
python app.py
```

### Terminal 2: Start Next.js Frontend
```bash
cd my-app
npm run dev
```

### Test the Integration
1. Navigate to `http://localhost:3000/predictions`
2. Fill in institution parameters
3. Click "Generate Prediction"
4. See real ML model predictions!

---

## 📊 Step 7: Add to Navigation

Update `app/layout.tsx` or create a navigation component:

```typescript
const navigation = [
  { name: 'Home', href: '/' },
  { name: 'Dashboard', href: '/dashboard' },
  { name: 'Predictions', href: '/predictions' },
  { name: 'Model Analytics', href: '/analytics/rf-models' },  // NEW
  { name: 'Institution Search', href: '/institutions/search' },  // NEW
  { name: 'Demo', href: '/demo' }
];
```

---

## 🎯 Integration Checklist

- [ ] Create `api-backend/` directory
- [ ] Install Flask + dependencies
- [ ] Create `app.py` with ML endpoints
- [ ] Test API with `curl` or Postman
- [ ] Update predictions page to call real API
- [ ] Create model analytics page
- [ ] Create institution search page
- [ ] Add environment variables
- [ ] Update navigation
- [ ] Test end-to-end integration

---

## 🔍 API Testing

### Test health endpoint:
```bash
curl http://localhost:5000/health
```

### Test prediction:
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model": "r1a_full",
    "features": {
      "afford_gap_cont": 15000,
      "admit_rate_imputed": 0.65,
      "sat_composite_25_imputed": 1100,
      "act_composite_25_imputed": 20,
      "sat_missing": 0,
      "act_missing": 0,
      "log_instructional_exp": 9.5,
      "log_endowment": 10.2,
      "has_endowment": 1,
      "pct_pell_imputed": 0.45,
      "pct_urm": 0.30,
      "pct_white_imputed": 0.50,
      "pct_women_imputed": 0.55,
      "is_hbcu": 0,
      "is_hsi": 0,
      "is_tcu": 0,
      "is_aanapisi": 0,
      "is_pbi": 0,
      "sector": "Public, 4-year or above",
      "size_category": "10,000 - 19,999",
      "region": "South"
    }
  }'
```

### Test institution search:
```bash
curl "http://localhost:5000/api/institutions/search?q=harvard"
```

---

## 🎨 Next Steps

1. **Enhance Visualizations**: Add Chart.js charts for model performance
2. **Comparison Tool**: Compare multiple institutions side-by-side
3. **Feature Sensitivity**: Show how changing features affects predictions
4. **Export Reports**: Generate PDF reports with predictions
5. **Batch Predictions**: Upload CSV and get predictions for multiple institutions
6. **A/B Testing**: Compare R1a vs R1b predictions to show affordability impact

---

## 📚 Additional Resources

- Flask Documentation: https://flask.palletsprojects.com/
- Next.js API Routes: https://nextjs.org/docs/api-routes/introduction
- scikit-learn Deployment: https://scikit-learn.org/stable/model_persistence.html
- Chart.js React: https://react-chartjs-2.js.org/

---

**Status**: Ready to integrate! 🚀  
**Models**: 5 trained RF models (175 MB)  
**Performance**: R² = 0.9537, RMSE = $2,767  
**Data**: 5,013 institutions ready for predictions

