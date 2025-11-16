# DATATHON: College Affordability & Mobility Analysis

A comprehensive data analysis project examining the relationship between college affordability and student economic mobility outcomes.

## 🎯 Project Overview

This project analyzes the causal relationship between college affordability (measured by the "affordability gap") and student outcomes (graduation rates and earnings 10 years post-enrollment) across U.S. 4-year institutions.

### Key Research Questions:
1. How does college affordability impact graduation rates?
2. What is the effect of affordability on post-graduation earnings?
3. Which institutional factors moderate the affordability-outcome relationship?
4. Are there differential effects for high vs. low Pell-eligible student populations?

## 📊 Quick Results

**Optimized Model Performance:**
- **R² Score**: ~77% (explains 77% of earnings variance)
- **RMSE**: ~$5,500 (prediction error)
- **Dataset**: 4,800+ U.S. 4-year institutions
- **Features**: 32 institutional, demographic, and resource variables

**Key Findings:**
- Affordability gap shows significant predictive power for earnings outcomes
- Selectivity (admit rates, test scores) is the strongest predictor
- Interaction effects between affordability and selectivity matter
- Different patterns observed for high vs. low Pell institutions

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ 
- Node.js 25+ (for frontend)
- pip and npm

### Installation

```bash
# Clone/navigate to project
cd /path/to/datathon

# Setup Python environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup frontend (if using)
cd fronted
npm install
cd ..
```

### Run the Tools

**1. LLM Chatbot (Quick Exploration)**
```bash
cd llm
python3 college_chatbot_web.py
# Visit http://localhost:8000
```

**2. Data Preparation (if starting fresh)**
```bash
cd src
python3 01_data_preparation.py
```

**3. ML Model Training (if needed)**
```bash
cd src
python3 earnings_mobility_rf_analysis.py
```

**4. Load and Use Trained Models**
```bash
cd src
python3 load_and_predict.py
```

**5. Frontend Application**
```bash
cd fronted
npm run dev
# Visit http://localhost:3000
```

## 📂 Project Structure

```
datathon/
├── api/                    # 🚀 Flask backend API for ML models
├── llm/                    # 🤖 LLM chatbot and analysis tools
├── src/                    # 🔬 Data preparation and ML training
├── outputs/                # 📈 Results, models, and figures
├── fronted/                # 🌐 Next.js web application
├── tasks/                  # 📋 Project documentation and task lists
├── requirements.txt        # Python dependencies
└── PROJECT_STRUCTURE.md    # Detailed structure documentation
```

**See [`PROJECT_STRUCTURE.md`](./PROJECT_STRUCTURE.md) for complete directory documentation.**

## 🔍 Key Components

### 1. Backend API (`/api/`)
Flask REST API for serving ML model predictions and institution data.

**Features:**
- RESTful endpoints for predictions
- Institution search and retrieval
- Model metadata and health monitoring
- CORS enabled for frontend integration

**Quick Start:**
```bash
cd api
./start.sh
# Visit http://localhost:5000
```

**Key Endpoints:**
- `GET /health` - Health check
- `GET /models` - List available models
- `POST /predict` - Make earnings predictions
- `GET /institutions?name=harvard` - Search institutions

📖 [API Documentation](./api/README.md)

---

### 2. LLM & Chatbot Module (`/llm/`)
Interactive tools for exploring college data through natural language queries.

**Features:**
- Web-based chatbot interface
- CLI chatbot
- Interactive college search and comparison
- Quick analysis scripts

**Quick Start:**
```bash
cd llm
python3 college_chatbot_web.py
```

📖 [LLM Module Documentation](./llm/README.md)

---

### 3. Data Pipeline (`/src/`)
Scripts for data cleaning, feature engineering, and model training.

**Key Scripts:**
- `01_data_preparation.py` - Data loading, cleaning, merging
- `earnings_mobility_rf_analysis.py` - Random Forest model training
- `load_and_predict.py` - Model inference

**Outputs:**
- `/outputs/data/` - Cleaned datasets
- `/outputs/rf_analysis/` - Trained models and results

---

### 4. Trained Models (`/outputs/rf_analysis/models/`)
Pre-trained Random Forest models for predicting earnings outcomes.

**Available Models:**
- **R1a**: Core model (full features + treatment)
- **R1b**: Baseline (demographics only)
- **R1c**: Interaction model (affordability × selectivity)
- **R1d**: Subgroup models (High/Low Pell)

**Model Specs:**
- Algorithm: Random Forest Regressor
- Features: 32 variables (treatment, confounders, interactions)
- Hyperparameters: 500 trees, max_depth=25, min_samples_split=5
- Performance: R²=0.77, RMSE=$5,500

📖 [Model Documentation](./outputs/rf_analysis/models/README.md)

---

### 5. Frontend Application (`/fronted/`)
Next.js web application for data visualization and exploration.

**Tech Stack:**
- Next.js 15+
- React 19+
- Tailwind CSS
- TypeScript

**Status:** Ready for development (node_modules setup resolved)

📖 [Frontend Documentation](./fronted/README.md)

---

## 📊 Data Sources

1. **Affordability Gap Data** (`Affordability_latest_02-17-25 1.csv`)
   - Net price after grants
   - Minimum wage gap calculations
   - Institution identifiers

2. **College Scorecard Data** (`College Results View 2021 Data.csv`)
   - Graduation rates
   - Earnings outcomes (10-year median)
   - Institutional characteristics
   - Student demographics
   - Selectivity metrics

**Merged Dataset:** `/outputs/data/merged_clean.csv` and `/fronted/data/merged_clean.csv`

---

## 🔬 Methodology

### Data Preparation
1. Load and standardize institution identifiers
2. Filter to 4-year institutions
3. Merge affordability and scorecard data
4. Handle missing data (listwise deletion for critical vars)
5. Create treatment variable (affordability quartiles)
6. Engineer features (selectivity, demographics, resources)
7. Median imputation for remaining missing confounders

### Modeling Approach
1. **Random Forest Regression** (non-parametric, handles non-linearity)
2. **Feature Engineering:**
   - Treatment: Affordability gap (continuous + quartiles)
   - Outcomes: Graduation rates, 10-year median earnings
   - Confounders: 32 variables across 5 categories
3. **Model Variants:**
   - Core, baseline, interaction, and subgroup models
4. **Optimization:**
   - Hyperparameter tuning (trees, depth, splits)
   - Missing data indicators (SAT/ACT flags)
   - Cross-validation

### Feature Categories
- **Selectivity**: Admit rate, SAT/ACT scores, flags for missing test scores
- **Institution**: Sector, size, state, region, control type
- **Demographics**: % Pell, % URM, % by race/ethnicity, % women
- **Resources**: Instructional expenditure, endowment (log + binary)
- **MSI Indicators**: HBCU, HSI, AANAPISI, etc.

---

## 📈 Results & Outputs

### Visualizations (`/outputs/figures/`)
- `treatment_distribution.png` - Affordability gap by quartile
- `graduation_rate_distribution.png` - 6-year grad rates
- `earnings_distribution.png` - 10-year median earnings

### Analysis Reports (`/outputs/rf_analysis/`)
- `SUMMARY_REPORT.md` - Comprehensive findings
- `PERFORMANCE_IMPROVEMENTS.md` - Optimization results
- `model_summary.csv` - Performance metrics
- `feature_importance_*.csv` - Feature rankings

### Logs (`/outputs/logs/`)
- `analysis_log.md` - Detailed decision log
- `task_2.0_stop_and_think_review.md` - Task checkpoint review

---

## 🛠️ Technical Details

### Python Dependencies
```txt
pandas>=2.0.0
numpy>=1.24.0
scikit-learn==1.6.1
matplotlib>=3.7.0
seaborn>=0.12.0
joblib>=1.2.0
```

### Environment
- **Python**: 3.11+
- **OS**: Tested on WSL2 (Ubuntu on Windows)
- **Memory**: Models require ~2GB RAM for training
- **Disk**: ~500MB for all outputs

---

## 📝 Task Management

**Main Task List:** [`tasks/tasks-affordability-mobility-causal-analysis.md`](./tasks/tasks-affordability-mobility-causal-analysis.md)

**Completed:**
- ✅ Task 0: Project Setup
- ✅ Task 1.0: Data Preparation & Cleaning
- ✅ Task 2.0: Feature Engineering & Treatment Definition

**In Progress:**
- 🔄 Task 3.0: Causal Analysis & Model Refinement
- 🔄 Frontend Integration

---

## 🚧 Known Issues & Solutions

### Issue 1: Frontend npm Permissions (WSL)
**Problem:** `EACCES: permission denied` when running `npm install`

**Solution:**
```bash
cd fronted
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

Or move project to native WSL filesystem:
```bash
cp -r /mnt/c/path/to/datathon ~/datathon
cd ~/datathon/fronted
npm install
```

### Issue 2: scikit-learn Version Mismatch
**Problem:** Models saved with scikit-learn 1.6.1, but older version installed

**Solution:**
```bash
pip install --upgrade scikit-learn==1.6.1
```

### Issue 3: Earnings Data Initially Looked Strange
**Problem:** Privacy-suppressed binned earnings data

**Solution:** Switched to granular earnings column (`Median Earnings of Dependent Students Working and Not Enrolled 10 Years After Entry`)

---

## 🔮 Future Enhancements

- [x] Create Flask backend API for model serving
- [ ] Integrate ML models into frontend application
- [ ] Add interactive visualizations (Plotly, D3.js)
- [ ] Implement causal inference methods (matching, IV)
- [ ] Add more sophisticated LLM integration (Ollama, GPT)
- [ ] Create Docker deployment configuration
- [ ] Add unit and integration tests
- [ ] Implement real-time data updates
- [ ] Build personalized recommendation system

---

## 📚 Documentation Index

| Document | Purpose |
|----------|---------|
| [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) | Complete project organization |
| [api/README.md](./api/README.md) | Backend API documentation |
| [llm/README.md](./llm/README.md) | LLM and chatbot documentation |
| [outputs/rf_analysis/models/README.md](./outputs/rf_analysis/models/README.md) | Model loading and usage |
| [outputs/rf_analysis/SUMMARY_REPORT.md](./outputs/rf_analysis/SUMMARY_REPORT.md) | Analysis findings |
| [outputs/logs/analysis_log.md](./outputs/logs/analysis_log.md) | Detailed decision log |
| [tasks/tasks-affordability-mobility-causal-analysis.md](./tasks/tasks-affordability-mobility-causal-analysis.md) | Task list |

---

## 🤝 Contributing

This is a DATATHON project. For questions or contributions:

1. Review the task list in `/tasks/`
2. Check analysis logs in `/outputs/logs/`
3. Refer to specific module READMEs
4. Follow existing code style and documentation practices

---

## 📄 License

[Add license information if applicable]

---

## 👥 Team / Authors

[Add team member information if applicable]

---

## 📧 Contact

For questions about this project, refer to:
- Task documentation in `/tasks/`
- Analysis logs in `/outputs/logs/`
- Module-specific READMEs

---

**Last Updated:** November 2025  
**Project Status:** Active Development  
**Version:** 2.0 (Post-Refactoring)

