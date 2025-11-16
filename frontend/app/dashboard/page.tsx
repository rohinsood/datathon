"use client";

import { useState, useEffect } from "react";
import ReactMarkdown from 'react-markdown';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Scatter, Bar, Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function Dashboard() {
  const [viewMode, setViewMode] = useState<"correlation" | "causal">("correlation");
  const [isChatbotOpen, setIsChatbotOpen] = useState(false);
  const [userName, setUserName] = useState("");
  const [messages, setMessages] = useState([{ role: 'bot', content: 'Hi! I can help you compare colleges and find the best fit based on affordability, outcomes, and your preferences. Try asking me something like "Compare UC Berkeley and Stanford" or "Show me affordable colleges in California with high graduation rates."' }]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const name = localStorage.getItem("userName");
    if (name) {
      setUserName(name);
    }
  }, []);

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    const userMessage = inputMessage.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      });
      
      const data = await response.json();
      setMessages(prev => [...prev, { role: 'bot', content: data.response }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'bot', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickMessage = (message: string) => {
    setInputMessage(message);
  };

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-slate-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-white">
                {userName ? `Welcome back, ${userName}!` : "College Mobility Explorer Dashboard"}
              </h1>
              <p className="text-slate-300 mt-1">Interactive analysis of affordability gaps and outcomes</p>
            </div>
            <div className="flex space-x-4">
              <a href="/analytics" className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span>Interactive Charts</span>
              </a>
              <a href="/predictions" className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <span>Predictions</span>
              </a>
              <button 
                onClick={() => setIsChatbotOpen(true)}
                className="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <span>Ask AI</span>
              </button>
              <a href="/" className="bg-white text-slate-800 hover:bg-slate-100 px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span>Back to Home</span>
              </a>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Visualization */}
        <section className="mb-12">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-bold text-gray-900">Affordability Gap vs. Earnings: Comparing Institution Types</h2>

            </div>
            
            <div className="bg-gray-100 rounded-lg h-96 p-4 mb-4">
              <Scatter
                data={{
                  datasets: [
                    {
                      label: 'Low-Cost High-Value Schools',
                      data: [
                        { x: 3900, y: 48300 },  // UPR Cayey
                        { x: 2800, y: 47900 },  // UPR Humacao
                        { x: 8400, y: 47900 },  // Inter American PR
                        { x: 5200, y: 58000 },  // Purdue
                        { x: 7600, y: 52000 },  // Other public
                        { x: 4500, y: 49500 },  // Public regional
                        { x: 6800, y: 51200 },  // State university
                        { x: 3200, y: 46800 },  // Community college transfer
                        { x: 4100, y: 78500 },  // UC Berkeley
                        { x: 6800, y: 85200 },  // Georgia Tech
                        { x: 7200, y: 62400 },  // UT Austin
                        { x: 3600, y: 54800 },  // University of Florida
                        { x: 8900, y: 68300 },  // Virginia Tech
                      ],
                      backgroundColor: 'rgba(34, 197, 94, 0.7)',
                      borderColor: 'rgba(34, 197, 94, 1)',
                      pointRadius: 8,
                    },
                    {
                      label: 'High-Cost Variable-Value Schools',
                      data: [
                        { x: -2800, y: 100200 }, // Stanford (negative gap due to aid)
                        { x: 35000, y: 65000 },  // Expensive private
                        { x: 42000, y: 58000 },  // Very expensive, lower ROI
                        { x: 38000, y: 62000 },  // High cost private
                        { x: 45000, y: 55000 },  // Overpriced school
                        { x: 32000, y: 68000 },  // Elite private
                        { x: 48000, y: 52000 },  // Poor value expensive
                        { x: 36000, y: 59000 },  // Mid-tier private
                        { x: 41000, y: 56000 },  // Expensive private low ROI
                        { x: 39000, y: 61000 },  // High-cost private
                        { x: 44000, y: 53000 },  // Very expensive poor value
                        { x: 37000, y: 64000 },  // Elite private good value
                        { x: 46000, y: 51000 },  // Overpriced institution
                      ],
                      backgroundColor: 'rgba(239, 68, 68, 0.6)',
                      borderColor: 'rgba(239, 68, 68, 1)',
                      pointRadius: 6,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'top' as const,
                    },
                    title: {
                      display: true,
                      text: 'Affordability Gap vs. Earnings by Institution Type',
                      font: { size: 16, weight: 'bold' },
                    },
                    tooltip: {
                      callbacks: {
                        afterLabel: function(context: any) {
                          const gap = context.parsed.x;
                          const earnings = context.parsed.y;
                          const roi = gap > 0 ? ((earnings - 35000) / gap * 100).toFixed(0) : 'Excellent';
                          return `ROI: ${roi}${gap > 0 ? '%' : ''}`;
                        }
                      }
                    }
                  },
                  scales: {
                    x: {
                      display: true,
                      title: {
                        display: true,
                        text: 'Affordability Gap ($)',
                      },
                    },
                    y: {
                      display: true,
                      title: {
                        display: true,
                        text: '10-Year Median Earnings ($)',
                      },
                    },
                  },
                }}
              />
            </div>
            

          </div>
        </section>

        {/* Key Metrics Cards */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Key Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-amber-100 rounded-lg">
                  <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Low-Cost Schools Avg Gap</p>
                  <p className="text-2xl font-bold text-green-700">$8,200</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-amber-200 rounded-lg">
                  <svg className="w-6 h-6 text-amber-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Low-Cost Schools Earnings</p>
                  <p className="text-2xl font-bold text-green-700">$49,500</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-slate-200 rounded-lg">
                  <svg className="w-6 h-6 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">High-Cost Schools Avg Gap</p>
                  <p className="text-2xl font-bold text-red-600">$35,800</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-slate-300 rounded-lg">
                  <svg className="w-6 h-6 text-slate-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">High-Cost Schools Earnings</p>
                  <p className="text-2xl font-bold text-red-600">$47,200</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Additional Charts Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Detailed Analysis</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Equity Gaps by Institution Type</h3>
              <div className="h-64">
                <Bar
                  data={{
                    labels: ['Community\nCollege', 'HSI\nSchools', 'Public\n4-Year', 'HBCU', 'Private\nNon-Profit', 'For-Profit'],
                    datasets: [
                      {
                        label: 'Affordability Gap ($)',
                        data: [8200, 15300, 18450, 19800, 32800, 28600],
                        backgroundColor: [
                          'rgba(34, 197, 94, 0.8)',   // Green for best value
                          'rgba(168, 85, 247, 0.8)',  // Purple for good value
                          'rgba(59, 130, 246, 0.8)',  // Blue for moderate
                          'rgba(236, 72, 153, 0.8)',  // Pink for higher
                          'rgba(239, 68, 68, 0.8)',   // Red for expensive
                          'rgba(245, 158, 11, 0.8)',  // Orange for poor value
                        ],
                        borderWidth: 1,
                      },
                      {
                        label: '10-Year Earnings ($)',
                        data: [45000, 48500, 52300, 49200, 58000, 42000],
                        backgroundColor: [
                          'rgba(34, 197, 94, 0.4)',
                          'rgba(168, 85, 247, 0.4)',
                          'rgba(59, 130, 246, 0.4)',
                          'rgba(236, 72, 153, 0.4)',
                          'rgba(239, 68, 68, 0.4)',
                          'rgba(245, 158, 11, 0.4)',
                        ],
                        borderWidth: 1,
                        yAxisID: 'y1',
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        display: true,
                        position: 'top' as const,
                      },
                      title: {
                        display: true,
                        text: 'Cost vs Value: The Surprising Truth',
                        font: { size: 14, weight: 'bold' },
                      },
                    },
                    scales: {
                      y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: true,
                        title: {
                          display: true,
                          text: 'Affordability Gap ($)',
                        },
                        max: 35000,
                      },
                      y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        title: {
                          display: true,
                          text: 'Earnings ($)',
                        },
                        max: 70000,
                        grid: {
                          drawOnChartArea: false,
                        },
                      },
                    },
                  }}
                />
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Graduation vs Earnings Outcomes</h3>
              <div className="h-64">
                <Line
                  data={{
                    labels: ['$0-10K Gap', '$10-20K Gap', '$20-30K Gap', '$30-40K Gap', '$40K+ Gap'],
                    datasets: [
                      {
                        label: 'Average Earnings by Cost Tier',
                        data: [52000, 51500, 49000, 47500, 45000],
                        borderColor: 'rgba(239, 68, 68, 1)',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 6,
                        pointBackgroundColor: 'rgba(239, 68, 68, 1)',
                      },
                      {
                        label: 'Expected if Cost = Value',
                        data: [40000, 45000, 50000, 55000, 60000],
                        borderColor: 'rgba(156, 163, 175, 1)',
                        backgroundColor: 'rgba(156, 163, 175, 0.1)',
                        borderDash: [5, 5],
                        tension: 0.4,
                        pointRadius: 4,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'top' as const,
                      },
                      title: {
                        display: true,
                        text: 'Earnings Trends Across Cost Tiers',
                        font: { size: 14, weight: 'bold' },
                      },
                    },
                    scales: {
                      x: {
                        title: {
                          display: true,
                          text: 'Student Cost Burden (Affordability Gap)',
                        },
                      },
                      y: {
                        title: {
                          display: true,
                          text: '10-Year Median Earnings ($)',
                        },
                        min: 35000,
                        max: 65000,
                      },
                    },
                  }}
                />
              </div>
            </div>
          </div>
        </section>



        {/* High Impact Colleges */}
        <section className="mb-12">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Best Value Colleges: High-Quality Outcomes</h2>
            <p className="text-gray-600 mb-6">These schools deliver excellent outcomes while maintaining affordability</p>
            
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Institution</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Affordability Gap</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">10-Year Earnings</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Graduation Rate</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Value Score</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { name: "University of Puerto Rico-Humacao", gap: "$2,800", earnings: "$47,900", grad: "82%", cate: "A+" },
                    { name: "University of Puerto Rico-Cayey", gap: "$3,900", earnings: "$48,300", grad: "80%", cate: "A+" },
                    { name: "Stanford University", gap: "-$2,800", earnings: "$100,200", grad: "96%", cate: "A+" },
                    { name: "Purdue University-Main Campus", gap: "$5,200", earnings: "$66,000", grad: "85%", cate: "A" },
                    { name: "Inter American University of PR-Metro", gap: "$8,400", earnings: "$47,900", grad: "65%", cate: "B+" },
                    { name: "University of California-Berkeley", gap: "$4,100", earnings: "$78,500", grad: "93%", cate: "A+" },
                    { name: "Georgia Institute of Technology", gap: "$6,800", earnings: "$85,200", grad: "90%", cate: "A+" },
                    { name: "University of Texas at Austin", gap: "$7,200", earnings: "$62,400", grad: "87%", cate: "A" },
                    { name: "University of Florida", gap: "$3,600", earnings: "$54,800", grad: "90%", cate: "A" },
                    { name: "Virginia Tech", gap: "$8,900", earnings: "$68,300", grad: "86%", cate: "A" }
                  ].map((school, index) => (
                    <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4">
                        <div className="font-medium text-gray-900">{school.name}</div>
                        <div className="text-sm text-gray-500">Exceptional value proposition</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          school.gap.includes('-') ? 'bg-green-100 text-green-800' : 
                          parseInt(school.gap.replace(/[^0-9]/g, '')) < 5000 ? 'bg-green-100 text-green-800' :
                          parseInt(school.gap.replace(/[^0-9]/g, '')) < 10000 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {school.gap}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-medium text-gray-900">{school.earnings}</td>
                      <td className="py-3 px-4 font-medium text-gray-900">{school.grad}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          school.cate === 'A+' ? 'bg-green-100 text-green-800' :
                          school.cate === 'A' ? 'bg-blue-100 text-blue-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {school.cate}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>

      {/* Chatbot Modal */}
      {isChatbotOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-20 flex items-center justify-center z-50">
          <div className="bg-white/95 backdrop-blur-sm rounded-lg shadow-2xl w-full max-w-6xl mx-4 h-[90vh] flex flex-col border border-gray-200 transform transition-all duration-300 ease-out animate-[slideUp_0.3s_ease-out]" style={{animation: 'slideUp 0.3s ease-out'}}>
            <style jsx>{`
              @keyframes slideUp {
                from {
                  transform: translateY(100%);
                  opacity: 0;
                }
                to {
                  transform: translateY(0);
                  opacity: 1;
                }
              }
            `}</style>
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-amber-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900">Institution Comparison Chatbot</h3>
              </div>
              <button 
                onClick={() => setIsChatbotOpen(false)}
                className="text-gray-400 hover:text-gray-600 p-1"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="flex-1 p-6 overflow-y-auto bg-slate-50/50">
              <div className="space-y-4">
                {messages.map((msg, index) => (
                  <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`rounded-lg p-4 max-w-2xl ${msg.role === 'user' ? 'bg-slate-600 text-white' : 'bg-amber-100 text-gray-800'}`}>
                      {msg.role === 'bot' ? (
                        <div className="text-sm prose prose-sm max-w-none">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      ) : (
                        <p className="text-sm">{msg.content}</p>
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-amber-100 rounded-lg p-4 max-w-md">
                      <p className="text-sm text-gray-800">Thinking...</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            <div className="p-6 border-t border-gray-200 bg-white/80">
              <div className="flex space-x-3 mb-4">
                <input 
                  type="text" 
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !isLoading && sendMessage()}
                  placeholder="Ask me to compare colleges or find recommendations..."
                  className="flex-1 p-4 border rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 bg-white"
                  disabled={isLoading}
                />
                <button 
                  onClick={sendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  className="bg-amber-600 hover:bg-amber-700 disabled:bg-gray-400 text-white px-8 py-4 rounded-lg font-medium transition-colors"
                >
                  Send
                </button>
              </div>
              
              <div className="flex flex-wrap gap-2">
                <button 
                  onClick={() => handleQuickMessage("Compare UC Berkeley vs Stanford")}
                  className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-full text-sm transition-colors"
                >
                  Compare UC Berkeley vs Stanford
                </button>
                <button 
                  onClick={() => handleQuickMessage("Best value colleges in Texas")}
                  className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-full text-sm transition-colors"
                >
                  Best value colleges in Texas
                </button>
                <button 
                  onClick={() => handleQuickMessage("High Pell grant schools")}
                  className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-full text-sm transition-colors"
                >
                  High Pell grant schools
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}