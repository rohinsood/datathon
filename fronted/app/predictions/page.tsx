"use client";

import { useState } from "react";

export default function Predictions() {
  const [selectedModel, setSelectedModel] = useState("all-factors");
  const [formData, setFormData] = useState({
    tuition: "",
    room_board: "",
    books_supplies: "",
    other_expenses: "",
    pell_percentage: "",
    admission_rate: "",
    sat_avg: "",
    faculty_salary: "",
    student_faculty_ratio: "",
    completion_rate: "",
    retention_rate: "",
    debt_median: "",
    family_income: "",
    independent_students: "",
    first_generation: "",
    women_only: "",
    men_only: "",
    religious: "",
    historically_black: "",
    tribal: "",
    hispanic_serving: "",
    nanti: ""
  });
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  const modelConfigs = {
    "all-factors": {
      name: "All Factors Model",
      description: "Comprehensive model using all available institutional factors",
      fields: ["tuition", "room_board", "books_supplies", "other_expenses", "pell_percentage", "admission_rate", "sat_avg", "faculty_salary", "student_faculty_ratio", "completion_rate", "retention_rate", "debt_median", "family_income", "independent_students", "first_generation", "women_only", "men_only", "religious", "historically_black", "tribal", "hispanic_serving", "nanti"]
    },
    "cost": {
      name: "Cost-Focused Model",
      description: "Model focusing primarily on cost-related factors",
      fields: ["tuition", "room_board", "books_supplies", "other_expenses", "debt_median", "family_income"]
    },
    "no-cost": {
      name: "No Cost Consideration Model",
      description: "Model excluding all cost-related factors",
      fields: ["pell_percentage", "admission_rate", "sat_avg", "faculty_salary", "student_faculty_ratio", "completion_rate", "retention_rate", "independent_students", "first_generation", "women_only", "men_only", "religious", "historically_black", "tribal", "hispanic_serving", "nanti"]
    },
    "pell-grant": {
      name: "Pell Grant Consideration Model",
      description: "Model specifically focused on Pell Grant recipients and related factors",
      fields: ["pell_percentage", "tuition", "family_income", "first_generation", "completion_rate", "retention_rate", "debt_median"]
    }
  };

  const fieldLabels = {
    tuition: "Tuition ($)",
    room_board: "Room & Board ($)",
    books_supplies: "Books & Supplies ($)",
    other_expenses: "Other Expenses ($)",
    pell_percentage: "Pell Grant Recipients (%)",
    admission_rate: "Admission Rate (%)",
    sat_avg: "Average SAT Score",
    faculty_salary: "Faculty Salary ($)",
    student_faculty_ratio: "Student-Faculty Ratio",
    completion_rate: "Completion Rate (%)",
    retention_rate: "Retention Rate (%)",
    debt_median: "Median Debt ($)",
    family_income: "Family Income ($)",
    independent_students: "Independent Students (%)",
    first_generation: "First Generation (%)",
    women_only: "Women Only (0/1)",
    men_only: "Men Only (0/1)",
    religious: "Religious Affiliation (0/1)",
    historically_black: "HBCU (0/1)",
    tribal: "Tribal College (0/1)",
    hispanic_serving: "HSI (0/1)",
    nanti: "NANTI (0/1)"
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handlePredict = async () => {
    setLoading(true);
    
    // Simulate API call with mock prediction
    setTimeout(() => {
      const mockPrediction = {
        earnings: Math.floor(Math.random() * 30000) + 40000,
        confidence: Math.floor(Math.random() * 20) + 80,
        factors: [
          { name: "Completion Rate", impact: "High", value: "+$8,500" },
          { name: "Faculty Salary", impact: "Medium", value: "+$3,200" },
          { name: "Student-Faculty Ratio", impact: "Low", value: "-$1,100" }
        ]
      };
      setPrediction(mockPrediction);
      setLoading(false);
    }, 1500);
  };

  const currentModel = modelConfigs[selectedModel as keyof typeof modelConfigs];

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-slate-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-white">Earnings Predictions</h1>
              <p className="text-slate-300 mt-1">Predict graduate earnings using machine learning models</p>
            </div>
            <a href="/dashboard" className="bg-white text-slate-800 hover:bg-slate-100 px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span>Back to Dashboard</span>
            </a>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Model Selection */}
        <section className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Select Prediction Model</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(modelConfigs).map(([key, config]) => (
              <button
                key={key}
                onClick={() => setSelectedModel(key)}
                className={`p-4 rounded-lg text-left transition-colors ${
                  selectedModel === key 
                    ? 'bg-purple-100 border-2 border-purple-500' 
                    : 'bg-white hover:bg-purple-50 border border-gray-200'
                }`}
              >
                <h3 className="font-semibold text-gray-900 mb-2">{config.name}</h3>
                <p className="text-sm text-gray-600">{config.description}</p>
              </button>
            ))}
          </div>
        </section>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Form */}
          <section className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              {currentModel.name} - Input Parameters
            </h3>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {currentModel.fields.map((field) => (
                <div key={field}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {fieldLabels[field as keyof typeof fieldLabels]}
                  </label>
                  <input
                    type="number"
                    value={formData[field as keyof typeof formData]}
                    onChange={(e) => handleInputChange(field, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    placeholder="Enter value"
                  />
                </div>
              ))}
            </div>
            <button
              onClick={handlePredict}
              disabled={loading}
              className="w-full mt-6 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white py-3 px-4 rounded-lg font-medium transition-colors"
            >
              {loading ? "Predicting..." : "Generate Prediction"}
            </button>
          </section>

          {/* Results */}
          <section className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Prediction Results</h3>
            {prediction ? (
              <div className="space-y-6">
                <div className="text-center">
                  <div className="text-4xl font-bold text-purple-600 mb-2">
                    ${prediction.earnings.toLocaleString()}
                  </div>
                  <p className="text-gray-600">Predicted 10-Year Median Earnings</p>
                  <div className="mt-2">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                      {prediction.confidence}% Confidence
                    </span>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-semibold text-gray-900 mb-3">Key Contributing Factors</h4>
                  <div className="space-y-2">
                    {prediction.factors.map((factor, index) => (
                      <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <span className="font-medium">{factor.name}</span>
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            factor.impact === 'High' ? 'bg-red-100 text-red-800' :
                            factor.impact === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {factor.impact}
                          </span>
                          <span className="font-semibold">{factor.value}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <p className="text-gray-500">Fill in the parameters and click "Generate Prediction" to see results</p>
              </div>
            )}
          </section>
        </div>

        {/* Model Information */}
        <section className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">About This Model</h3>
          <p className="text-blue-800 mb-4">{currentModel.description}</p>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-medium text-blue-900 mb-2">Input Features ({currentModel.fields.length})</h4>
              <ul className="text-blue-700 space-y-1">
                {currentModel.fields.slice(0, Math.ceil(currentModel.fields.length / 2)).map((field) => (
                  <li key={field}>• {fieldLabels[field as keyof typeof fieldLabels]}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-blue-900 mb-2">&nbsp;</h4>
              <ul className="text-blue-700 space-y-1">
                {currentModel.fields.slice(Math.ceil(currentModel.fields.length / 2)).map((field) => (
                  <li key={field}>• {fieldLabels[field as keyof typeof fieldLabels]}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}