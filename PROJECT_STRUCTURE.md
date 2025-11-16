# Project Structure

This document describes the organization of the DATATHON project after refactoring.

## 📂 Root Directory Layout

```
datathon/
├── api/                    # Flask backend API for ML models
├── llm/                    # LLM and chatbot modules
├── src/                    # Data preparation and ML training scripts
├── outputs/                # Analysis results, figures, and trained models
├── fronted/                # Next.js frontend application
├── tasks/                  # Project task lists and documentation
├── venv/                   # Python virtual environment
├── requirements.txt        # Python dependencies
├── README.MD               # Main project README
├── PROJECT_STRUCTURE.md    # This file
└── *.csv, *.xlsx           # Source data files
```

## 🔍 Detailed Directory Structure

### `/api/` - Backend API
**Purpose**: Flask REST API for serving ML model predictions and institution data

```
api/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies (Flask, scikit-learn, etc.)
├── start.sh            # Startup script
├── test_api.sh         # API testing script
├── venv/               # Python virtual environment
└── README.md           # API documentation
```

**Key Features**:
- RESTful API endpoints for model predictions
- Institution search and retrieval
- Model metadata and health monitoring
- CORS enabled for frontend integration

**Endpoints**:
- `GET /` - API information
- `GET /health` - Health check
- `GET /models` - List available models
- `POST /predict` - Make predictions
- `GET /institutions` - Search institutions
- `GET /institution/<id>` - Get institution details

**Running**:
```bash
cd api
./start.sh
# Visit http://localhost:5000
```

📖 [API Documentation](./api/README.md)

---

### `/llm/` - LLM & Chatbot Module
**Purpose**: LLM-powered chatbot and college analysis tools

```
llm/
├── college_chatbot_web.py       # Web chatbot (port 8000)
├── college_chatbot.py           # CLI chatbot
├── college_search.py            # Interactive search tool
├── college_comparison.py        # Comparison utilities
├── analyze_colleges.py          # Basic analysis
├── simple_college_analysis.py   # Comprehensive analysis
├── setup-ollama.sh              # Ollama setup script
└── README.md                    # LLM module documentation
```

**Key Features**:
- Web-based and CLI chatbot interfaces
- Natural language queries about colleges
- Interactive search and comparison tools
- Data analysis utilities

**Data Source**: `../fronted/data/merged_clean.csv`

---

### `/src/` - Data Pipeline & ML Training
**Purpose**: Data preparation, feature engineering, and model training

```
src/
├── 01_data_preparation.py           # Data loading, cleaning, merging
├── earnings_mobility_rf_analysis.py # Random Forest analysis
├── load_and_predict.py              # Model loading and prediction
└── [other analysis scripts]
```

**Key Outputs**:
- Cleaned datasets → `/outputs/data/`
- Trained models → `/outputs/rf_analysis/models/`
- Analysis reports → `/outputs/rf_analysis/`

---

### `/outputs/` - Results & Artifacts
**Purpose**: Store all analysis outputs, models, and visualizations

```
outputs/
├── data/
│   ├── merged_clean.csv           # Cleaned merged dataset
│   ├── analysis_ready.csv         # Feature-engineered dataset
│   └── variable_lists.json        # Variable metadata
├── figures/
│   ├── treatment_distribution.png
│   ├── graduation_rate_distribution.png
│   └── earnings_distribution.png
├── rf_analysis/
│   ├── models/
│   │   ├── model_r1a.pkl         # Core model
│   │   ├── model_r1b.pkl         # Baseline model
│   │   ├── model_r1c.pkl         # Interaction model
│   │   ├── model_r1d_*.pkl       # Subgroup models
│   │   ├── model_metadata.json   # Model specs
│   │   └── README.md             # Model documentation
│   ├── feature_importance_*.csv   # Feature rankings
│   ├── model_summary.csv          # Performance metrics
│   ├── SUMMARY_REPORT.md          # Analysis findings
│   └── PERFORMANCE_IMPROVEMENTS.md
└── logs/
    ├── analysis_log.md            # Detailed analysis log
    └── task_2.0_stop_and_think_review.md
```

---

### `/fronted/` - Frontend Application
**Purpose**: Next.js web application for data visualization and interaction

```
fronted/
├── app/                    # Next.js app router
├── public/                 # Static assets
├── data/                   # Frontend data files
│   └── merged_clean.csv
├── node_modules/           # npm dependencies
├── package.json            # Node dependencies
├── next.config.js          # Next.js configuration
├── tailwind.config.js      # Tailwind CSS config
└── README.md               # Frontend documentation
```

**Tech Stack**:
- Next.js 15+ (React framework)
- Tailwind CSS (styling)
- TypeScript (type safety)

**Running**:
```bash
cd fronted
npm install  # If not already done
npm run dev  # Start dev server (port 3000)
```

---

### `/tasks/` - Documentation & Task Lists
**Purpose**: Project planning and task tracking

```
tasks/
├── tasks-affordability-mobility-causal-analysis.md  # Main task list
└── [other task documentation]
```

---

## 🔄 Data Flow

```
┌─────────────────┐
│  Source Data    │ (Root: *.csv, *.xlsx)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  src/01_data_   │ Data cleaning, merging,
│  preparation.py │ feature engineering
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  outputs/data/  │ merged_clean.csv
│                 │ analysis_ready.csv
└────────┬────────┘
         │
         ├──────────────────┬────────────────┐
         │                  │                │
         ▼                  ▼                ▼
┌────────────────┐  ┌────────────┐  ┌─────────────┐
│ ML Training    │  │ LLM Tools  │  │ Frontend    │
│ (src/*.py)     │  │ (llm/*.py) │  │ (fronted/)  │
└───────┬────────┘  └────────────┘  └─────────────┘
        │
        ▼
┌────────────────┐
│ Trained Models │
│ (outputs/      │
│  rf_analysis/) │
└────────────────┘
```

## 🚀 Quick Start Guide

### 1. **Setup Python Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. **Run Data Preparation** (if needed)
```bash
cd src
python3 01_data_preparation.py
```

### 3. **Train ML Models** (if needed)
```bash
python3 earnings_mobility_rf_analysis.py
```

### 4. **Start LLM Chatbot**
```bash
cd llm
python3 college_chatbot_web.py
# Visit http://localhost:8000
```

### 5. **Start Frontend** (needs fixing)
```bash
cd fronted
rm -rf node_modules package-lock.json  # Clean install
npm install
npm run dev
# Visit http://localhost:3000
```

## 🔧 Key Configuration Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies (scikit-learn, pandas, etc.) |
| `fronted/package.json` | Node.js dependencies (Next.js, React, etc.) |
| `outputs/rf_analysis/models/model_metadata.json` | ML model specifications |
| `outputs/data/variable_lists.json` | Feature definitions |

## 📊 Available Models

Located in `/outputs/rf_analysis/models/`:

1. **R1a (Core Model)**: Full feature set with treatment interaction
2. **R1b (Baseline)**: Institution and student demographics only
3. **R1c (Interaction Model)**: With affordability × selectivity interactions
4. **R1d (Subgroup Models)**: 
   - High Pell (≥30% Pell students)
   - Low Pell (<30% Pell students)

**Performance**: ~77% R², RMSE ~$5,500 (optimized)

## 🌟 Recent Changes (Refactoring)

### What Changed:
1. ✅ Created `/llm/` directory and moved all chatbot/LLM files
2. ✅ Created `/api/` directory with Flask backend for ML model serving
3. ✅ Updated all file paths in LLM scripts to point to correct data location
4. ✅ Consolidated project structure for better organization
5. ✅ Created comprehensive documentation for all modules

### What Stayed the Same:
- All source data files remain in root
- Frontend application remains in `/fronted/`
- ML training scripts remain in `/src/`
- Outputs remain in `/outputs/`

### Why This Structure?
- **Separation of Concerns**: API, LLM tools, and ML training are separated
- **Modularity**: Each directory has a clear, single purpose
- **Maintainability**: Easier to find and update specific components
- **Scalability**: Easy to extend or modify individual components

## 📝 Notes

- **Backend API**: Flask API now available in `/api/` directory for serving ML models.
- **Frontend Permissions**: There was a WSL permissions issue with `node_modules`. See frontend README for resolution.
- **Python Version**: Developed with Python 3.11+
- **Node Version**: Tested with Node.js 25.0.0

## 🔮 Future Development

Potential additions to the structure:

```
datathon/
├── tests/             # Unit and integration tests
├── docs/              # Extended documentation
├── deployment/        # Deployment configurations (Docker, etc.)
└── notebooks/         # Jupyter notebooks for exploration
```

## 📞 Support & Contribution

- Main task list: `/tasks/tasks-affordability-mobility-causal-analysis.md`
- Analysis logs: `/outputs/logs/analysis_log.md`
- Model documentation: `/outputs/rf_analysis/models/README.md`
- API documentation: `/api/README.md`
- LLM module: `/llm/README.md`

For questions or contributions, refer to the respective README files in each directory.

