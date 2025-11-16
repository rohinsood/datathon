"""
Flask API Backend for College Affordability ML Models
Serves predictions from trained Random Forest models
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import joblib
import json
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Paths
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "outputs" / "rf_analysis" / "models"
DATA_DIR = BASE_DIR / "outputs" / "data"

# Load models and metadata on startup
models = {}
metadata = {}

def load_models():
    """Load all trained models and metadata"""
    global models, metadata
    
    print("Loading models...")
    
    # Load metadata
    metadata_path = MODELS_DIR / "model_metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        print(f"✓ Loaded metadata for {len(metadata)} models")
    
    # Load model files
    for model_name in ['r1a', 'r1b', 'r1c', 'r1d_high_pell', 'r1d_low_pell']:
        model_path = MODELS_DIR / f"model_{model_name}.pkl"
        if model_path.exists():
            try:
                models[model_name] = joblib.load(model_path)
                print(f"✓ Loaded model: {model_name}")
            except Exception as e:
                print(f"✗ Failed to load {model_name}: {e}")
    
    print(f"Loaded {len(models)} models successfully\n")

# Load models on startup
load_models()

# Load institution data
institutions_df = None
try:
    data_path = DATA_DIR / "analysis_ready.csv"
    if data_path.exists():
        institutions_df = pd.read_csv(data_path)
        print(f"✓ Loaded {len(institutions_df)} institutions\n")
except Exception as e:
    print(f"✗ Failed to load institution data: {e}\n")


@app.route('/')
def home():
    """API home endpoint"""
    return jsonify({
        "name": "College Affordability ML API",
        "version": "1.0.0",
        "status": "running",
        "models_loaded": list(models.keys()),
        "endpoints": {
            "/": "API information",
            "/health": "Health check",
            "/models": "List available models",
            "/predict": "Make predictions (POST)",
            "/institutions": "Search institutions (GET)",
            "/institution/<id>": "Get institution details"
        }
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "models_available": len(models),
        "institutions_loaded": len(institutions_df) if institutions_df is not None else 0
    })


@app.route('/models')
def list_models():
    """List available models with metadata"""
    model_info = {}
    
    for model_name in models.keys():
        info = {
            "loaded": True,
            "type": "RandomForestRegressor"
        }
        
        # Add metadata if available
        if model_name in metadata:
            info.update({
                "features": metadata[model_name].get("features", []),
                "n_features": len(metadata[model_name].get("features", [])),
                "hyperparameters": metadata[model_name].get("hyperparameters", {}),
                "trained_date": metadata[model_name].get("trained_date", "unknown")
            })
        
        model_info[model_name] = info
    
    return jsonify({
        "models": model_info,
        "total": len(models)
    })


@app.route('/predict', methods=['POST'])
def predict():
    """
    Make earnings predictions using specified model
    
    Request body:
    {
        "model": "r1a",  # Model to use (r1a, r1b, r1c, r1d_high_pell, r1d_low_pell)
        "features": {
            "afford_gap_cont": 5000,
            "admit_rate": 0.65,
            "sat_avg": 1200,
            ...
        }
    }
    """
    try:
        data = request.json
        model_name = data.get('model', 'r1a')
        features = data.get('features', {})
        
        # Validate model exists
        if model_name not in models:
            return jsonify({
                "error": f"Model '{model_name}' not found",
                "available_models": list(models.keys())
            }), 404
        
        # Get required features for this model
        if model_name not in metadata:
            return jsonify({
                "error": f"Metadata for model '{model_name}' not found"
            }), 500
        
        required_features = metadata[model_name].get('features', [])
        
        # Validate all required features are provided
        missing_features = [f for f in required_features if f not in features]
        if missing_features:
            return jsonify({
                "error": "Missing required features",
                "missing": missing_features,
                "required": required_features
            }), 400
        
        # Prepare feature vector in correct order
        X = pd.DataFrame([features])[required_features]
        
        # Make prediction
        model = models[model_name]
        prediction = model.predict(X)[0]
        
        return jsonify({
            "model": model_name,
            "prediction": float(prediction),
            "prediction_formatted": f"${prediction:,.0f}",
            "features_used": required_features,
            "n_features": len(required_features)
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500


@app.route('/institutions')
def search_institutions():
    """
    Search institutions by name, state, or other criteria
    
    Query params:
    - name: Institution name (partial match)
    - state: State code (e.g., "CA", "NY")
    - limit: Max results (default 20)
    """
    if institutions_df is None:
        return jsonify({"error": "Institution data not loaded"}), 500
    
    try:
        # Get query parameters
        name_query = request.args.get('name', '').lower()
        state_query = request.args.get('state', '').upper()
        limit = int(request.args.get('limit', 20))
        
        # Filter dataframe
        df = institutions_df.copy()
        
        if name_query:
            df = df[df['institution_name'].str.lower().str.contains(name_query, na=False)]
        
        if state_query and 'state' in df.columns:
            df = df[df['state'].str.upper() == state_query]
        
        # Limit results
        df = df.head(limit)
        
        # Convert to list of dicts
        results = df.to_dict('records')
        
        return jsonify({
            "count": len(results),
            "institutions": results
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500


@app.route('/institution/<int:unit_id>')
def get_institution(unit_id):
    """Get details for a specific institution by unit_id"""
    if institutions_df is None:
        return jsonify({"error": "Institution data not loaded"}), 500
    
    try:
        institution = institutions_df[institutions_df['unit_id'] == unit_id]
        
        if len(institution) == 0:
            return jsonify({"error": f"Institution with unit_id {unit_id} not found"}), 404
        
        return jsonify(institution.iloc[0].to_dict())
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("College Affordability ML API")
    print("=" * 60)
    print(f"Models directory: {MODELS_DIR}")
    print(f"Data directory: {DATA_DIR}")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)

