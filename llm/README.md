# LLM / Chatbot Module

This directory contains the LLM-powered chatbot and college analysis tools for the DATATHON project.

## 📁 Directory Structure

```
llm/
├── college_chatbot_web.py       # Web-based chatbot with HTTP server
├── college_chatbot.py           # CLI chatbot interface
├── college_search.py            # Interactive college search tool
├── college_comparison.py        # College comparison utilities
├── analyze_colleges.py          # Basic college data analysis
├── simple_college_analysis.py   # Comprehensive analysis script
├── setup-ollama.sh              # Setup script for Ollama LLM
└── README.md                    # This file
```

## 🚀 Quick Start

### Web Chatbot

Start the web-based chatbot server:

```bash
cd llm
python3 college_chatbot_web.py
```

Then open your browser to: `http://localhost:8000`

### CLI Chatbot

Run the command-line chatbot:

```bash
cd llm
python3 college_chatbot.py
```

### Interactive Search

Run the interactive college search:

```bash
cd llm
python3 college_search.py
```

## 📊 Available Tools

### 1. **Web Chatbot** (`college_chatbot_web.py`)
- HTTP server on port 8000
- Simple web interface for college queries
- Ask about colleges, graduation rates, earnings, affordability

**Example Questions:**
- "Tell me about Harvard"
- "What are the best colleges by graduation rate?"
- "Which colleges have the highest earnings?"
- "What are the most affordable colleges?"

### 2. **CLI Chatbot** (`college_chatbot.py`)
- Command-line interface
- Same query capabilities as web version
- Interactive prompt-based

### 3. **College Search** (`college_search.py`)
- Search colleges by name
- Filter by state, graduation rate, price
- Compare multiple colleges
- Interactive menu system

### 4. **Analysis Tools**
- `analyze_colleges.py`: Basic dataset exploration
- `simple_college_analysis.py`: Comprehensive analysis with statistics
- `college_comparison.py`: Detailed comparison utilities

## 📋 Dependencies

Python packages required:
- `pandas` (data manipulation)
- `csv` (built-in)
- `json` (built-in)
- `re` (built-in)
- `http.server` (built-in)

Install dependencies:
```bash
pip install pandas
```

## 🔧 Configuration

### Data Source
All tools read from: `../fronted/data/merged_clean.csv`

To change the data source, update the CSV path in each script.

### Port Configuration
Web chatbot runs on port 8000 by default. To change:

Edit `college_chatbot_web.py`:
```python
server = HTTPServer(('localhost', 8080), ChatHandler)  # Change 8000 to 8080
```

## 🎯 Features

### Data Fields Available:
- Institution Name
- State
- Graduation Rate (6-year)
- Net Price (average after grants)
- Median Earnings (10 years after entry)
- Affordability Gap

### Query Types:
1. **Single College Info**: "Tell me about [college name]"
2. **Top Rankings**: "Best colleges by [metric]"
3. **Filters**: "Cheapest colleges", "Highest earnings"
4. **Comparisons**: Compare multiple institutions

## 🔮 Future Enhancements

- [ ] Integration with Ollama for enhanced LLM capabilities
- [ ] More sophisticated natural language understanding
- [ ] Personalized recommendations based on student profile
- [ ] Integration with ML models from `/outputs/rf_analysis/`
- [ ] Real-time data updates
- [ ] Multi-modal queries (voice, text)

## 📝 Notes

- Data is loaded from the merged and cleaned dataset
- Missing values are handled gracefully
- All financial figures are in USD
- Graduation rates are 6-year bachelor's degree rates

## 🔗 Related Directories

- `/src/` - Data preparation and ML model training
- `/outputs/` - Analysis results and trained models
- `/fronted/` - Next.js frontend application
- `/fronted/data/` - Source data files

## 🛠️ Troubleshooting

**Issue**: "File not found" error
- **Solution**: Make sure you're running from the `llm/` directory
- Check that `../fronted/data/merged_clean.csv` exists

**Issue**: Web server won't start
- **Solution**: Port 8000 might be in use. Change the port or stop conflicting services

**Issue**: No colleges found in search
- **Solution**: Check spelling and try partial names (e.g., "Harvard" instead of full name)

## 📧 Support

For issues or questions about the LLM module, refer to the main project README or task documentation.

