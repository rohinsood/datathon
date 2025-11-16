"""
ML Model API Server for Random Forest Earnings Predictions
===========================================================

Flask API that serves the trained Random Forest models to the Next.js frontend.

Endpoints:
- GET  /health - Health check
- GET  /api/models/info - Get model information
- POST /api/predict - Make earnings prediction
- GET  /api/institutions/<unit_id> - Get institution data
- GET  /api/institutions/search - Search institutions
- GET  /api/feature-importance - Get feature importance data

Author: Data Science Team
Date: November 2025
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import json
import os
import sys

app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js frontend

# Paths relative to api-backend directory
BASE_PATH = "../../outputs/rf_analysis/models"
DATA_PATH = "../../outputs/data/analysis_ready.csv"
IMPORTANCE_PATH = "../../outputs/rf_analysis"

# ============================================================================
# LOAD MODELS AND DATA AT STARTUP
# ============================================================================
print("\n" + "="*70)
print("🤖 ML MODEL API - INITIALIZING")
print("="*70)

try:
    print("\n📦 Loading trained models...")
    models = {
        "r1a_full": joblib.load(f"{BASE_PATH}/model_r1a_full.pkl"),
        "r1b_no_afford": joblib.load(f"{BASE_PATH}/model_r1b_no_afford.pkl"),
        "r1c_interactions": joblib.load(f"{BASE_PATH}/model_r1c_interactions.pkl"),
        "r1d_high_pell": joblib.load(f"{BASE_PATH}/model_r1d_high_pell.pkl"),
        "r1d_low_pell": joblib.load(f"{BASE_PATH}/model_r1d_low_pell.pkl")
    }
    print(f"✓ Loaded {len(models)} models successfully")
    
    print("\n📊 Loading metadata...")
    with open(f"{BASE_PATH}/model_metadata.json", "r") as f:
        metadata = json.load(f)
    print(f"✓ Metadata loaded: {len(metadata['numeric_features'])} numeric features, {len(metadata['categorical_features'])} categorical features")
    
    print("\n📁 Loading institution data...")
    df = pd.read_csv(DATA_PATH)
    # Rename affordability column to match training
    AFFORD_FULL_NAME = 'Affordability Gap (net price minus income earned working 10 hrs at min wage)'
    if AFFORD_FULL_NAME in df.columns:
        df = df.rename(columns={AFFORD_FULL_NAME: 'afford_gap_cont'})
    print(f"✓ Loaded {len(df):,} institutions")
    
    print("\n✅ INITIALIZATION COMPLETE")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ ERROR DURING INITIALIZATION: {e}")
    print("="*70)
    sys.exit(1)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "models_loaded": len(models),
        "institutions_available": len(df),
        "version": "1.0"
    })

@app.route('/api/models/info', methods=['GET'])
def models_info():
    """Get information about available models and their performance"""
    return jsonify({
        "models": {
            "r1a_full": {
                "name": "Full Model (R1a)",
                "description": "Complete model with affordability gap and all institutional factors",
                "performance": {"r2": 0.9537, "rmse": 2767, "mae": 1581},
                "features_count": len(metadata["numeric_features"] + metadata["categorical_features"]),
                "best_for": "General-purpose predictions across all institution types"
            },
            "r1b_no_afford": {
                "name": "No Affordability Baseline (R1b)",
                "description": "Model without affordability gap, used to quantify affordability's contribution",
                "performance": {"r2": 0.9643, "rmse": 2430, "mae": None},
                "features_count": len([f for f in metadata["numeric_features"] if f != "afford_gap_cont"]) + len(metadata["categorical_features"]),
                "best_for": "Comparing predictions with/without affordability factor"
            },
            "r1c_interactions": {
                "name": "Interaction Model (R1c)",
                "description": "Model with affordability × Pell and affordability × URM interaction terms",
                "performance": {"r2": 0.9328, "rmse": 3331, "mae": None},
                "features_count": len(metadata["numeric_features"]) + 2 + len(metadata["categorical_features"]),
                "best_for": "Understanding how affordability effects vary by demographics"
            },
            "r1d_high_pell": {
                "name": "High-Pell Subgroup (R1d)",
                "description": "Specialized model for institutions serving ≥44% Pell students",
                "performance": {"r2": 0.7330, "rmse": 5126, "mae": None},
                "features_count": len(metadata["numeric_features"] + metadata["categorical_features"]),
                "best_for": "Predictions for equity-serving institutions"
            },
            "r1d_low_pell": {
                "name": "Low-Pell Subgroup (R1d)",
                "description": "Specialized model for selective institutions with <44% Pell students",
                "performance": {"r2": 0.9381, "rmse": 3301, "mae": None},
                "features_count": len(metadata["numeric_features"] + metadata["categorical_features"]),
                "best_for": "Predictions for selective/low-Pell institutions"
            }
        },
        "metadata": {
            "training_date": metadata["training_date"],
            "median_pell_threshold": metadata["median_pell_threshold"],
            "n_estimators": metadata["n_estimators"],
            "max_depth": metadata["max_depth"]
        },
        "feature_lists": {
            "numeric": metadata["numeric_features"],
            "categorical": metadata["categorical_features"]
        }
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Make earnings prediction for an institution
    
    Expected POST body:
    {
        "model": "r1a_full",
        "features": { <feature_name>: <value>, ... }
    }
    """
    try:
        data = request.json
        model_name = data.get("model", "r1a_full")
        features = data.get("features", {})
        
        # Validate model name
        if model_name not in models:
            return jsonify({
                "error": f"Model '{model_name}' not found",
                "available_models": list(models.keys())
            }), 400
        
        # Determine feature list based on model
        if model_name == "r1b_no_afford":
            # Exclude affordability from features
            feature_list = [f for f in metadata["numeric_features"] if f != "afford_gap_cont"] + metadata["categorical_features"]
        elif model_name == "r1c_interactions":
            # Add interaction terms
            if "afford_gap_cont" in features and "pct_pell_imputed" in features:
                features["afford_x_pell"] = features["afford_gap_cont"] * features["pct_pell_imputed"]
            if "afford_gap_cont" in features and "pct_urm" in features:
                features["afford_x_urm"] = features["afford_gap_cont"] * features["pct_urm"]
            feature_list = metadata["numeric_features"] + ["afford_x_pell", "afford_x_urm"] + metadata["categorical_features"]
        else:
            feature_list = metadata["numeric_features"] + metadata["categorical_features"]
        
        # Create feature dataframe
        feature_df = pd.DataFrame([features])
        
        # Check for missing features
        missing_features = [f for f in feature_list if f not in feature_df.columns]
        if missing_features:
            return jsonify({
                "error": f"Missing required features: {missing_features}",
                "required_features": feature_list,
                "provided_features": list(features.keys())
            }), 400
        
        # Select features in correct order
        X = feature_df[feature_list]
        
        # Make prediction
        prediction = models[model_name].predict(X)[0]
        
        # Get performance metrics
        perf_map = {
            "r1a_full": {"r2": 0.9537, "rmse": 2767, "mae": 1581},
            "r1b_no_afford": {"r2": 0.9643, "rmse": 2430, "mae": None},
            "r1c_interactions": {"r2": 0.9328, "rmse": 3331, "mae": None},
            "r1d_high_pell": {"r2": 0.7330, "rmse": 5126, "mae": None},
            "r1d_low_pell": {"r2": 0.9381, "rmse": 3301, "mae": None}
        }
        
        return jsonify({
            "success": True,
            "model": model_name,
            "predicted_earnings": float(prediction),
            "prediction_range": {
                "lower": float(prediction - perf_map[model_name]["rmse"]),
                "upper": float(prediction + perf_map[model_name]["rmse"])
            },
            "performance": perf_map[model_name],
            "features_used": len(feature_list)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/institutions/<int:unit_id>', methods=['GET'])
def get_institution(unit_id):
    """Get detailed information and prediction for a specific institution"""
    inst = df[df['unit_id'] == unit_id]
    
    if len(inst) == 0:
        return jsonify({"error": f"Institution with unit_id {unit_id} not found"}), 404
    
    inst_row = inst.iloc[0]
    
    # Prepare features for prediction
    feature_list = metadata["numeric_features"] + metadata["categorical_features"]
    features = {}
    for f in feature_list:
        if f in inst_row.index:
            val = inst_row[f]
            features[f] = float(val) if pd.notna(val) else 0.0
        else:
            features[f] = 0.0
    
    # Make prediction with R1a model
    try:
        X = pd.DataFrame([features])[feature_list]
        prediction_r1a = models["r1a_full"].predict(X)[0]
    except:
        prediction_r1a = None
    
    return jsonify({
        "unit_id": int(unit_id),
        "name": str(inst_row["Institution Name_aff"]),
        "state": str(inst_row["State Abbreviation"]) if "State Abbreviation" in inst_row.index else None,
        "sector": str(inst_row["Sector Name"]) if "Sector Name" in inst_row.index else None,
        "actual_earnings": float(inst_row["earnings_10yr"]) if "earnings_10yr" in inst_row.index and pd.notna(inst_row["earnings_10yr"]) else None,
        "predicted_earnings": float(prediction_r1a) if prediction_r1a else None,
        "affordability_gap": float(inst_row["afford_gap_cont"]) if "afford_gap_cont" in inst_row.index else None,
        "pct_pell": float(inst_row["pct_pell_imputed"]) if "pct_pell_imputed" in inst_row.index else None,
        "admit_rate": float(inst_row["admit_rate_imputed"]) if "admit_rate_imputed" in inst_row.index else None,
        "grad_rate": float(inst_row["grad_rate_6yr"]) if "grad_rate_6yr" in inst_row.index and pd.notna(inst_row["grad_rate_6yr"]) else None,
        "features": features
    })

@app.route('/api/institutions/search', methods=['GET'])
def search_institutions():
    """Search institutions by name, state, or other criteria"""
    query = request.args.get('q', '').lower()
    state = request.args.get('state', '')
    min_pell = request.args.get('min_pell', type=float)
    max_pell = request.args.get('max_pell', type=float)
    limit = int(request.args.get('limit', 50))
    
    filtered = df.copy()
    
    # Filter by name
    if query:
        filtered = filtered[filtered['Institution Name_aff'].str.lower().str.contains(query, na=False)]
    
    # Filter by state
    if state:
        filtered = filtered[filtered['State Abbreviation'] == state.upper()]
    
    # Filter by Pell percentage
    if min_pell is not None:
        filtered = filtered[filtered['pct_pell_imputed'] >= min_pell]
    if max_pell is not None:
        filtered = filtered[filtered['pct_pell_imputed'] <= max_pell]
    
    # Limit results
    results = filtered.head(limit)
    
    return jsonify({
        "count": len(results),
        "total_matches": len(filtered),
        "institutions": [
            {
                "unit_id": int(row["unit_id"]),
                "name": str(row["Institution Name_aff"]),
                "state": str(row["State Abbreviation"]) if "State Abbreviation" in row.index else None,
                "sector": str(row["Sector Name"]) if "Sector Name" in row.index else None,
                "afford_gap": float(row["afford_gap_cont"]) if "afford_gap_cont" in row.index else None,
                "pct_pell": float(row["pct_pell_imputed"]) if "pct_pell_imputed" in row.index else None,
                "actual_earnings": float(row["earnings_10yr"]) if "earnings_10yr" in row.index and pd.notna(row["earnings_10yr"]) else None
            }
            for _, row in results.iterrows()
        ]
    })

@app.route('/api/feature-importance', methods=['GET'])
def feature_importance():
    """Get feature importance rankings for a specific model"""
    model_name = request.args.get('model', 'r1a')
    
    importance_files = {
        'r1a': f'{IMPORTANCE_PATH}/feature_importance_r1a.csv',
        'r1c': f'{IMPORTANCE_PATH}/feature_importance_r1c.csv',
        'high_pell': f'{IMPORTANCE_PATH}/feature_importance_high_pell.csv',
        'low_pell': f'{IMPORTANCE_PATH}/feature_importance_low_pell.csv'
    }
    
    if model_name not in importance_files:
        return jsonify({
            "error": f"Model '{model_name}' not found",
            "available": list(importance_files.keys())
        }), 400
    
    try:
        df_importance = pd.read_csv(importance_files[model_name])
        
        return jsonify({
            "model": model_name,
            "total_features": len(df_importance),
            "features": [
                {
                    "rank": idx + 1,
                    "name": row["feature"],
                    "importance": float(row["importance"]),
                    "importance_pct": float(row["importance"] * 100)
                }
                for idx, row in df_importance.iterrows()
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get aggregate statistics about the dataset"""
    return jsonify({
        "total_institutions": len(df),
        "affordability_gap": {
            "mean": float(df["afford_gap_cont"].mean()),
            "median": float(df["afford_gap_cont"].median()),
            "min": float(df["afford_gap_cont"].min()),
            "max": float(df["afford_gap_cont"].max())
        },
        "pct_pell": {
            "mean": float(df["pct_pell_imputed"].mean() * 100),
            "median": float(df["pct_pell_imputed"].median() * 100)
        },
        "earnings_10yr": {
            "mean": float(df["earnings_10yr"].mean()),
            "median": float(df["earnings_10yr"].median()),
            "available": int(df["earnings_10yr"].notna().sum())
        } if "earnings_10yr" in df.columns else None
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 ML API SERVER STARTING...")
    print("="*70)
    print(f"\nModels loaded: {list(models.keys())}")
    print(f"Institutions available: {len(df):,}")
    print(f"\n📡 API Endpoints:")
    print("  GET  /health")
    print("  GET  /api/models/info")
    print("  POST /api/predict")
    print("  GET  /api/institutions/<unit_id>")
    print("  GET  /api/institutions/search?q=<query>&state=<state>&limit=<N>")
    print("  GET  /api/feature-importance?model=<r1a|r1c|high_pell|low_pell>")
    print("  GET  /api/stats")
    print(f"\n🌐 Server URL: http://localhost:5000")
    print("="*70 + "\n")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)

