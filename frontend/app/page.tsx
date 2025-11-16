"use client";

export default function Page() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-slate-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-white">🔍 College Mobility Explorer</h1>
              <p className="text-slate-300 mt-1">Understanding the true impact of college affordability on economic mobility</p>
            </div>
            <div className="flex space-x-4">
              <button 
                onClick={() => document.getElementById('solution-section')?.scrollIntoView({ behavior: 'smooth' })}
                className="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                How it Works
              </button>
              <a 
                href="/demo" 
                className="bg-slate-600 hover:bg-slate-500 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                See a Demo
              </a>
              <a 
                href="/welcome" 
                className="bg-white text-slate-800 hover:bg-slate-100 px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Get Started
              </a>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <section className="text-center mb-16 py-12">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl p-12">
            <h1 className="text-6xl font-bold bg-gradient-to-r from-slate-800 to-blue-800 bg-clip-text text-transparent mb-8">
              Does College Affordability Really Drive Economic Mobility?
            </h1>
            <p className="text-xl text-gray-700 max-w-4xl mx-auto leading-relaxed">
              We're building the first comprehensive platform to understand the causal relationship between college costs, student outcomes, and long-term economic mobility.
            </p>
            <div className="mt-8 flex justify-center space-x-4">
              <a href="/welcome" className="bg-gradient-to-r from-amber-500 to-orange-500 text-white px-8 py-4 rounded-xl font-semibold hover:from-amber-600 hover:to-orange-600 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1">
                🚀 Get Started
              </a>
              <button 
                onClick={() => document.getElementById('problem-section')?.scrollIntoView({ behavior: 'smooth' })}
                className="bg-white text-slate-700 px-8 py-4 rounded-xl font-semibold border-2 border-slate-200 hover:border-slate-300 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1"
              >
                📊 Learn More
              </button>
            </div>
          </div>
        </section>

        {/* Problem Section */}
        <section id="problem-section" className="mb-16">
          <div className="bg-gradient-to-r from-red-50 to-pink-50 border border-red-100 rounded-2xl p-10 shadow-lg">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">The Problem</h2>
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Hidden Affordability Crisis</h3>
                <p className="text-gray-700 mb-4">
                  Despite billions in financial aid, many students face significant affordability gaps that impact their educational and career outcomes.
                </p>
                <ul className="text-gray-700 space-y-2">
                  <li>• Average gap of $18,450 between aid and actual costs</li>
                  <li>• Disproportionate impact on Pell Grant recipients</li>
                  <li>• Limited transparency in true institutional value</li>
                </ul>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Policy Decisions Without Evidence</h3>
                <p className="text-gray-700 mb-4">
                  Policymakers lack tools to understand which interventions actually improve student outcomes and economic mobility.
                </p>
                <ul className="text-gray-700 space-y-2">
                  <li>• Correlation vs. causation confusion</li>
                  <li>• No standardized "bang for your buck" metrics</li>
                  <li>• Equity gaps remain invisible</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Solution Section */}
        <section id="solution-section" className="mb-16">
          <div className="bg-gradient-to-r from-slate-100 to-blue-100 border border-slate-200 rounded-2xl p-10 shadow-lg">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Our Solution</h2>
            <p className="text-lg text-gray-700 mb-8">
              The College Mobility Explorer combines College Scorecard data with advanced causal inference methods to provide unprecedented insights into educational value and equity.
            </p>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-xl p-8 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 cursor-pointer border border-gray-100">
                <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-amber-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Interactive Visualizations</h3>
                <p className="text-gray-600">Explore affordability gaps, earnings outcomes, and causal effects through intuitive charts and dashboards.</p>
              </div>
              
              <div className="bg-white rounded-lg p-6 shadow hover:scale-105 transition-transform duration-200 cursor-pointer">
                <div className="w-12 h-12 bg-amber-200 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-amber-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Causal Analysis</h3>
                <p className="text-gray-600">Move beyond correlation to understand the true causal impact of affordability on student outcomes.</p>
              </div>
              
              <div className="bg-white rounded-lg p-6 shadow hover:scale-105 transition-transform duration-200 cursor-pointer">
                <div className="w-12 h-12 bg-amber-300 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-amber-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Institution Comparison Chatbot</h3>
                <p className="text-gray-600">Ask natural language questions to compare colleges and get personalized recommendations based on your criteria.</p>
              </div>
              
              <div className="bg-white rounded-lg p-6 shadow hover:scale-105 transition-transform duration-200 cursor-pointer">
                <div className="w-12 h-12 bg-purple-200 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-purple-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Predictive Modeling</h3>
                <p className="text-gray-600">Machine learning models to predict graduate earnings based on institutional factors, costs, and student demographics.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Methodology Section */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">How We Build These Solutions</h2>
          
          <div className="relative">
            <div className="absolute left-1/2 transform -translate-x-1/2 w-1 h-full bg-slate-300"></div>
            
            <div className="space-y-12">
              <div className="flex items-center">
                <div className="flex-1 pr-8 text-right">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Real Data Integration</h3>
                  <p className="text-gray-600">Comprehensive analysis of College Scorecard data, financial aid records, and long-term earnings outcomes across 6,000+ institutions.</p>
                </div>
                <div className="w-12 h-12 bg-slate-600 rounded-full flex items-center justify-center relative z-10 hover:scale-110 transition-transform duration-200 cursor-pointer">
                  <span className="text-white font-bold">1</span>
                </div>
                <div className="flex-1 pl-8"></div>
              </div>
              
              <div className="flex items-center">
                <div className="flex-1 pr-8"></div>
                <div className="w-12 h-12 bg-slate-700 rounded-full flex items-center justify-center relative z-10 hover:scale-110 transition-transform duration-200 cursor-pointer">
                  <span className="text-white font-bold">2</span>
                </div>
                <div className="flex-1 pl-8">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Advanced Statistical Modeling</h3>
                  <p className="text-gray-600">Propensity score matching, instrumental variables, and regression discontinuity to identify causal effects of affordability interventions.</p>
                </div>
              </div>
              
              <div className="flex items-center">
                <div className="flex-1 pr-8 text-right">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Equity-Focused Analysis</h3>
                  <p className="text-gray-600">Conditional Average Treatment Effects (CATE) to understand differential impacts across student populations and institutional contexts.</p>
                </div>
                <div className="w-12 h-12 bg-slate-800 rounded-full flex items-center justify-center relative z-10 hover:scale-110 transition-transform duration-200 cursor-pointer">
                  <span className="text-white font-bold">3</span>
                </div>
                <div className="flex-1 pl-8"></div>
              </div>
              
              <div className="flex items-center">
                <div className="flex-1 pr-8"></div>
                <div className="w-12 h-12 bg-slate-900 rounded-full flex items-center justify-center relative z-10 hover:scale-110 transition-transform duration-200 cursor-pointer">
                  <span className="text-white font-bold">4</span>
                </div>
                <div className="flex-1 pl-8">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Interactive Transparency Tools</h3>
                  <p className="text-gray-600">User-friendly dashboards that make complex causal inference accessible to policymakers, researchers, and institutional leaders.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Preview Section */}
        <section className="mb-16">
          <div className="bg-amber-50 border border-amber-100 rounded-lg p-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">What You'll Discover</h2>
            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-white rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Interactive Scatter Plots</h3>
                <div className="bg-gray-100 rounded h-48 flex items-center justify-center mb-4 overflow-hidden">
                  <img 
                    src="/images/image1.png" 
                    alt="Interactive scatter plot showing college affordability vs economic mobility"
                    className="max-w-full max-h-full object-contain hover:scale-110 transition-transform duration-300"
                  />
                </div>
                <p className="text-gray-600">Toggle between raw correlations and causal estimates to see the true impact of affordability on student outcomes.</p>
              </div>
              
              <div className="bg-white rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">High-Impact Institution Rankings</h3>
                <div className="bg-gray-100 rounded h-48 flex items-center justify-center mb-4 overflow-hidden">
                  <img 
                    src="/images/image2.png" 
                    alt="High-impact institution rankings showing economic mobility outcomes"
                    className="max-w-full max-h-full object-contain hover:scale-110 transition-transform duration-300"
                  />
                </div>
                <p className="text-gray-600">Discover colleges that deliver the highest economic mobility impact for students from all backgrounds.</p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="text-center">
          <div className="bg-gradient-to-r from-slate-700 to-slate-900 rounded-lg shadow-lg p-12 text-white">
            <h2 className="text-4xl font-bold mb-4">Explore the Data</h2>
            <p className="text-xl mb-8 opacity-90 max-w-2xl mx-auto">
              Ready to dive into the interactive dashboard? Discover which colleges truly deliver on the promise of economic mobility.
            </p>
            <a href="/welcome" className="inline-block bg-amber-500 text-white font-semibold py-4 px-12 rounded-lg hover:bg-amber-400 transition-colors text-lg">
              Launch Dashboard
            </a>
          </div>
        </section>
      </div>
    </main>
  );
}
