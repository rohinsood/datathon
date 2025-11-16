'use client';
import { useState, useEffect } from 'react';
import { Bar, Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  Title,
  Tooltip,
  Legend
);

export default function Analytics() {
  const [chartType, setChartType] = useState('equity-gaps');
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState('');
  const [scrollIndex, setScrollIndex] = useState(0);

  const generateChartData = (type: string, filterValue: string = '') => {
    const applyFilter = (baseData: any) => {
      if (!filterValue) return baseData;
      
      const filterMappings: any = {
        'NY': {
          labels: ['Columbia', 'Cornell', 'NYU', 'Syracuse', 'Rochester', 'Fordham', 'RIT', 'Colgate', 'Hamilton', 'Vassar', 'Barnard', 'SUNY Binghamton', 'SUNY Buffalo', 'SUNY Stony Brook', 'Skidmore', 'Union College'],
          overall: [95, 93, 85, 82, 84, 79, 68, 92, 94, 93, 91, 83, 78, 80, 87, 85],
          pell: [88, 86, 78, 75, 77, 72, 61, 85, 87, 86, 84, 76, 71, 73, 80, 78],
          urm: [85, 83, 75, 72, 74, 69, 58, 82, 84, 83, 81, 73, 68, 70, 77, 75]
        },
        'CA': {
          labels: ['Stanford', 'UC Berkeley', 'UCLA', 'USC', 'Caltech', 'UC San Diego', 'Pomona', 'Claremont McKenna', 'Harvey Mudd', 'UC Davis', 'UC Irvine', 'UC Santa Barbara', 'Pepperdine', 'Santa Clara', 'UC Riverside', 'San Diego State'],
          overall: [96, 92, 91, 89, 94, 87, 95, 91, 94, 85, 83, 82, 84, 86, 74, 72],
          pell: [89, 85, 84, 82, 87, 80, 88, 84, 87, 78, 76, 75, 77, 79, 67, 65],
          urm: [86, 82, 81, 79, 84, 77, 85, 81, 84, 75, 73, 72, 74, 76, 64, 62]
        },
        'PA': {
          labels: ['UPenn', 'Carnegie Mellon', 'Penn State', 'Pitt', 'Drexel', 'Temple', 'Swarthmore', 'Haverford', 'Bryn Mawr', 'Bucknell', 'Lafayette', 'Lehigh', 'Villanova', 'Duquesne', 'West Chester', 'IUP'],
          overall: [95, 89, 85, 82, 73, 70, 96, 95, 84, 90, 89, 91, 90, 78, 65, 58],
          pell: [88, 82, 78, 75, 66, 63, 89, 88, 77, 83, 82, 84, 83, 71, 58, 51],
          urm: [85, 79, 75, 72, 63, 60, 86, 85, 74, 80, 79, 81, 80, 68, 55, 48]
        },
        'TX': {
          labels: ['Rice', 'UT Austin', 'Texas A&M', 'SMU', 'TCU', 'Baylor', 'Trinity', 'Southwestern', 'UT Dallas', 'Houston', 'Texas Tech', 'Texas State', 'UNT', 'UTSA', 'Prairie View', 'Lamar'],
          overall: [94, 87, 82, 78, 79, 74, 76, 72, 71, 62, 60, 55, 53, 48, 45, 42],
          pell: [87, 80, 75, 71, 72, 67, 69, 65, 64, 55, 53, 48, 46, 41, 38, 35],
          urm: [84, 77, 72, 68, 69, 64, 66, 62, 61, 52, 50, 45, 43, 38, 35, 32]
        },
        'OH': {
          labels: ['Case Western', 'Ohio State', 'Miami (OH)', 'Cincinnati', 'Oberlin', 'Kenyon', 'Denison', 'Ohio Wesleyan', 'College of Wooster', 'Bowling Green', 'Ohio University', 'Kent State', 'Wright State', 'Akron', 'Toledo', 'Youngstown State'],
          overall: [85, 84, 82, 71, 87, 89, 83, 75, 78, 68, 66, 62, 58, 55, 52, 48],
          pell: [78, 77, 75, 64, 80, 82, 76, 68, 71, 61, 59, 55, 51, 48, 45, 41],
          urm: [75, 74, 72, 61, 77, 79, 73, 65, 68, 58, 56, 52, 48, 45, 42, 38]
        },
        'MA': {
          labels: ['Harvard', 'MIT', 'Tufts', 'Boston College', 'BU', 'Northeastern', 'Williams', 'Amherst', 'Wellesley', 'Smith', 'Mount Holyoke', 'Brandeis', 'Babson', 'Bentley', 'Emerson', 'Suffolk'],
          overall: [97, 96, 93, 91, 87, 89, 95, 96, 93, 87, 84, 91, 89, 87, 81, 65],
          pell: [90, 89, 86, 84, 80, 82, 88, 89, 86, 80, 77, 84, 82, 80, 74, 58],
          urm: [87, 86, 83, 81, 77, 79, 85, 86, 83, 77, 74, 81, 79, 77, 71, 55]
        },
        'FL': {
          labels: ['UF', 'FSU', 'Miami', 'UCF', 'USF', 'FIT', 'Rollins', 'Nova Southeastern', 'Florida Tech', 'FAU', 'FIU', 'FGCU', 'Stetson', 'Embry-Riddle', 'Lynn', 'Barry'],
          overall: [88, 82, 83, 73, 68, 65, 70, 62, 64, 58, 60, 55, 63, 66, 52, 48],
          pell: [81, 75, 76, 66, 61, 58, 63, 55, 57, 51, 53, 48, 56, 59, 45, 41],
          urm: [78, 72, 73, 63, 58, 55, 60, 52, 54, 48, 50, 45, 53, 56, 42, 38]
        },
        'IL': {
          labels: ['Northwestern', 'UChicago', 'UIUC', 'DePaul', 'Loyola', 'IIT', 'Knox', 'Lake Forest', 'Wheaton', 'Illinois Wesleyan', 'Bradley', 'Northern Illinois', 'Southern Illinois', 'Eastern Illinois', 'Western Illinois', 'Chicago State'],
          overall: [94, 95, 85, 70, 73, 78, 82, 75, 88, 84, 76, 58, 52, 55, 48, 35],
          pell: [87, 88, 78, 63, 66, 71, 75, 68, 81, 77, 69, 51, 45, 48, 41, 28],
          urm: [84, 85, 75, 60, 63, 68, 72, 65, 78, 74, 66, 48, 42, 45, 38, 25]
        },
        'NC': {
          labels: ['Duke', 'UNC Chapel Hill', 'Wake Forest', 'NC State', 'Davidson', 'Elon', 'UNC Charlotte', 'UNC Wilmington', 'Appalachian State', 'East Carolina', 'NC A&T', 'UNC Greensboro', 'Western Carolina', 'High Point', 'Guilford', 'Catawba'],
          overall: [95, 91, 88, 82, 93, 84, 68, 72, 70, 65, 58, 55, 52, 62, 68, 45],
          pell: [88, 84, 81, 75, 86, 77, 61, 65, 63, 58, 51, 48, 45, 55, 61, 38],
          urm: [85, 81, 78, 72, 83, 74, 58, 62, 60, 55, 48, 45, 42, 52, 58, 35]
        },
        'PR': {
          labels: ['UPR Humacao', 'UPR Cayey', 'Inter American', 'UPR Aguadilla', 'Sagrado Corazón', 'Politécnica', 'UPR Río Piedras', 'UPR Mayagüez', 'Universidad del Turabo', 'Universidad Metropolitana', 'UPR Ponce', 'UPR Arecibo', 'Universidad del Este', 'UPR Utuado', 'UPR Bayamón', 'Universidad del Sagrado Corazón'],
          overall: [82, 80, 65, 58, 62, 55, 75, 78, 52, 48, 60, 55, 45, 42, 50, 58],
          pell: [78, 76, 61, 54, 58, 51, 71, 74, 48, 44, 56, 51, 41, 38, 46, 54],
          urm: [80, 78, 63, 56, 60, 53, 73, 76, 50, 46, 58, 53, 43, 40, 48, 56]
        },
        'Public': { 
          labels: ['Public 4-Year', 'Public 2-Year', 'State Universities'],
          data: [72, 45, 68]
        },
        'Private': {
          labels: ['Private Non-Profit', 'Private For-Profit', 'Elite Private'],
          data: [78, 42, 85]
        },
        'HSI': {
          labels: ['HSI Schools', 'Non-HSI Comparison'],
          data: [68, 72]
        }
      };
      
      const filter = filterMappings[filterValue];
      if (!filter) return baseData;
      

      
      if (filter.labels && filter.overall && type === 'equity-gaps') {
        const startIndex = scrollIndex;
        const endIndex = startIndex + 8;
        return {
          labels: filter.labels.slice(startIndex, endIndex),
          datasets: [
            {
              label: 'Overall Graduation Rate (%)',
              data: filter.overall.slice(startIndex, endIndex),
              backgroundColor: 'rgba(59, 130, 246, 0.8)'
            },
            {
              label: 'Pell Grant Recipients Grad Rate (%)',
              data: filter.pell.slice(startIndex, endIndex),
              backgroundColor: 'rgba(239, 68, 68, 0.8)'
            },
            {
              label: 'URM Students Grad Rate (%)',
              data: filter.urm.slice(startIndex, endIndex),
              backgroundColor: 'rgba(245, 158, 11, 0.8)'
            }
          ]
        };
      }
      
      if (filter.labels && filter.overall && type === 'state-comparison') {
        const startIndex = scrollIndex;
        const endIndex = startIndex + 8;
        return {
          labels: filter.labels.slice(startIndex, endIndex),
          datasets: [{
            label: 'Graduation Rate (%)',
            data: filter.overall.slice(startIndex, endIndex),
            backgroundColor: filter.labels.slice(startIndex, endIndex).map((_, i) => 
              `hsl(${(startIndex + i) * 40}, 70%, 60%)`
            )
          }]
        };
      }
      
      // Filter cost-outcomes by state with specific college data
      if (type === 'cost-outcomes' && filterValue) {
        const stateCollegeData: any = {
          'CA': [
            { x: -2800, y: 100200, college: 'Stanford University' },
            { x: 15200, y: 89000, college: 'UC Berkeley' },
            { x: 18500, y: 85000, college: 'UCLA' },
            { x: 28000, y: 78000, college: 'USC' },
            { x: 22000, y: 82000, college: 'UC San Diego' },
            { x: 25000, y: 75000, college: 'UC Davis' }
          ],
          'NY': [
            { x: 1200, y: 95000, college: 'Columbia University' },
            { x: 8500, y: 88000, college: 'Cornell University' },
            { x: 34000, y: 72000, college: 'NYU' },
            { x: 28000, y: 65000, college: 'Syracuse University' },
            { x: 22000, y: 68000, college: 'University of Rochester' },
            { x: 38000, y: 62000, college: 'Fordham University' }
          ],
          'TX': [
            { x: 16800, y: 68000, college: 'UT Austin' },
            { x: 18200, y: 72000, college: 'Rice University' },
            { x: 20500, y: 65000, college: 'Texas A&M' },
            { x: 35000, y: 58000, college: 'SMU' },
            { x: 32000, y: 55000, college: 'TCU' },
            { x: 28000, y: 52000, college: 'Baylor University' }
          ],
          'PA': [
            { x: 3500, y: 92000, college: 'University of Pennsylvania' },
            { x: 18200, y: 78000, college: 'Penn State' },
            { x: 12500, y: 82000, college: 'Carnegie Mellon' },
            { x: 22000, y: 68000, college: 'University of Pittsburgh' },
            { x: 28000, y: 58000, college: 'Drexel University' },
            { x: 25000, y: 52000, college: 'Temple University' }
          ],
          'FL': [
            { x: 14500, y: 62000, college: 'University of Florida' },
            { x: 18000, y: 58000, college: 'Florida State' },
            { x: 35000, y: 68000, college: 'University of Miami' },
            { x: 22000, y: 52000, college: 'UCF' },
            { x: 25000, y: 48000, college: 'USF' },
            { x: 28000, y: 55000, college: 'Florida Tech' }
          ],
          'PR': [
            { x: 2800, y: 47900, college: 'UPR Humacao' },
            { x: 3900, y: 48300, college: 'UPR Cayey' },
            { x: 8400, y: 47900, college: 'Inter American Metro' },
            { x: 7600, y: 45000, college: 'UPR Aguadilla' },
            { x: 12000, y: 42000, college: 'Sagrado Corazón' },
            { x: 15000, y: 38000, college: 'Politécnica' }
          ],
          'MA': [
            { x: 1200, y: 98000, college: 'Harvard University' },
            { x: 3500, y: 96000, college: 'MIT' },
            { x: 25000, y: 82000, college: 'Tufts University' },
            { x: 28000, y: 78000, college: 'Boston College' },
            { x: 31000, y: 72000, college: 'Boston University' },
            { x: 32000, y: 75000, college: 'Northeastern' }
          ],
          'OH': [
            { x: 18000, y: 75000, college: 'Case Western' },
            { x: 12000, y: 65000, college: 'Ohio State' },
            { x: 22000, y: 68000, college: 'Miami University' },
            { x: 25000, y: 58000, college: 'University of Cincinnati' },
            { x: 28000, y: 62000, college: 'Oberlin College' },
            { x: 35000, y: 65000, college: 'Kenyon College' }
          ],
          'IL': [
            { x: 8500, y: 88000, college: 'Northwestern' },
            { x: 5800, y: 92000, college: 'University of Chicago' },
            { x: 15000, y: 72000, college: 'UIUC' },
            { x: 32000, y: 55000, college: 'DePaul University' },
            { x: 28000, y: 58000, college: 'Loyola Chicago' },
            { x: 25000, y: 62000, college: 'Illinois Tech' }
          ],
          'NC': [
            { x: 8500, y: 85000, college: 'Duke University' },
            { x: 12000, y: 68000, college: 'UNC Chapel Hill' },
            { x: 28000, y: 72000, college: 'Wake Forest' },
            { x: 18000, y: 62000, college: 'NC State' },
            { x: 32000, y: 75000, college: 'Davidson College' },
            { x: 25000, y: 58000, college: 'Elon University' }
          ]
        };
        
        const stateData = stateCollegeData[filterValue];
        if (stateData) {
          return {
            datasets: [{
              label: `Colleges in ${filterValue}`,
              data: stateData,
              backgroundColor: stateData.map((point: any) => {
                if (point.x < 10000) return 'rgba(34, 197, 94, 0.7)';
                if (point.x < 25000) return 'rgba(59, 130, 246, 0.7)';
                return 'rgba(239, 68, 68, 0.7)';
              }),
              pointRadius: 8
            }]
          };
        }
        
        // Fallback for Public/Private filtering
        const stateColleges = baseData.datasets[0].data.filter((point: any) => 
          (filterValue === 'Public' && (point.college.includes('State') || point.college.includes('UC ') || point.college.includes('UPR'))) ||
          (filterValue === 'Private' && !point.college.includes('State') && !point.college.includes('UC ') && !point.college.includes('UPR'))
        );
        
        return {
          ...baseData,
          datasets: [{
            ...baseData.datasets[0],
            data: stateColleges
          }]
        };
      }
      
      return baseData;
    };

    const chartTypes: any = {
      'equity-gaps': {
        labels: ['Community College', 'HSI Schools', 'Public 4-Year', 'HBCU', 'Private Non-Profit', 'For-Profit'],
        datasets: [
          {
            label: 'Overall Graduation Rate (%)',
            data: [45, 68, 72, 65, 78, 42],
            backgroundColor: 'rgba(59, 130, 246, 0.8)'
          },
          {
            label: 'Pell Grant Recipients Grad Rate (%)',
            data: [38, 58, 62, 55, 68, 32],
            backgroundColor: 'rgba(239, 68, 68, 0.8)'
          },
          {
            label: 'URM Students Grad Rate (%)',
            data: [35, 62, 58, 62, 65, 28],
            backgroundColor: 'rgba(245, 158, 11, 0.8)'
          }
        ]
      },
      'cost-outcomes': {
        datasets: [{
          label: 'Colleges by State',
          data: [
            // Low cost, good outcomes
            { x: 2800, y: 47900, college: 'UPR Humacao (PR)' },
            { x: 3900, y: 48300, college: 'UPR Cayey (PR)' },
            { x: 5200, y: 58000, college: 'Purdue (IN)' },
            { x: 8400, y: 47900, college: 'Inter American (PR)' },
            { x: 12000, y: 52000, college: 'Ohio State (OH)' },
            { x: 14500, y: 55000, college: 'UF (FL)' },
            { x: 16800, y: 61000, college: 'UT Austin (TX)' },
            { x: 18200, y: 59000, college: 'Penn State (PA)' },
            // Medium cost, variable outcomes
            { x: 22000, y: 48000, college: 'Temple (PA)' },
            { x: 25000, y: 62000, college: 'UIUC (IL)' },
            { x: 28000, y: 65000, college: 'UC Davis (CA)' },
            { x: 31000, y: 58000, college: 'BU (MA)' },
            { x: 34000, y: 72000, college: 'NYU (NY)' },
            // High cost, mixed outcomes
            { x: 38000, y: 68000, college: 'USC (CA)' },
            { x: 42000, y: 55000, college: 'Private College (FL)' },
            { x: 45000, y: 52000, college: 'Expensive Private (TX)' },
            { x: 48000, y: 49000, college: 'Overpriced School (OH)' },
            // Elite schools (low gap due to aid)
            { x: -2800, y: 100200, college: 'Stanford (CA)' },
            { x: 1200, y: 95000, college: 'Harvard (MA)' },
            { x: 3500, y: 88000, college: 'MIT (MA)' },
            { x: 5800, y: 82000, college: 'Columbia (NY)' }
          ],
          backgroundColor: (ctx: any) => {
            const point = ctx.parsed;
            if (point.x < 10000) return 'rgba(34, 197, 94, 0.7)'; // Green for low cost
            if (point.x < 30000) return 'rgba(59, 130, 246, 0.7)'; // Blue for medium cost
            return 'rgba(239, 68, 68, 0.7)'; // Red for high cost
          },
          pointRadius: 6
        }]
      },
      'state-comparison': {
        labels: ['Stanford', 'UC Berkeley', 'UCLA', 'USC', 'Caltech', 'UC San Diego'],
        datasets: [{
          label: 'Graduation Rate (%)',
          data: [96, 92, 91, 89, 94, 87],
          backgroundColor: ['rgba(34, 197, 94, 0.8)', 'rgba(59, 130, 246, 0.8)', 'rgba(168, 85, 247, 0.8)', 'rgba(245, 158, 11, 0.8)', 'rgba(239, 68, 68, 0.8)', 'rgba(236, 72, 153, 0.8)']
        }]
      }
    };

    return applyFilter(chartTypes[type] || null);
  };

  useEffect(() => {
    setLoading(true);
    setScrollIndex(0); // Reset scroll when filter changes
    setTimeout(() => {
      setChartData(generateChartData(chartType, selectedFilter));
      setLoading(false);
    }, 300);
  }, [chartType, selectedFilter]);

  useEffect(() => {
    if ((chartType === 'state-comparison' || chartType === 'equity-gaps') && selectedFilter) {
      setChartData(generateChartData(chartType, selectedFilter));
    }
  }, [scrollIndex]);

  const renderChart = () => {
    if (!chartData || loading) return <div className="h-96 flex items-center justify-center">Loading...</div>;

    const options = {
      responsive: true,
      plugins: {
        legend: { position: 'top' as const },
        title: { display: true, text: getChartTitle() }
      }
    };

    switch (chartType) {
      case 'equity-gaps':
        return <Bar data={chartData} options={options} />;
      case 'cost-outcomes':
        return <Scatter data={chartData} options={{...options, scales: { x: { title: { display: true, text: 'Affordability Gap ($)' }}, y: { title: { display: true, text: 'Median Earnings ($)' }}}}} />;
      case 'state-comparison':
        return <Bar data={chartData} options={options} />;
      default:
        return null;
    }
  };

  const getChartTitle = () => {
    switch (chartType) {
      case 'equity-gaps': return 'Equity Gaps: Overall vs Pell vs URM Graduation Rates';
      case 'cost-outcomes': return 'Affordability Gap vs Earnings Outcomes';
      case 'state-comparison': return selectedFilter ? `Colleges in ${selectedFilter}` : 'Top California Colleges';
      default: return '';
    }
  };

  const getMaxColleges = () => {
    const stateData = {
      'NY': 16, 'CA': 16, 'PA': 16, 'TX': 16, 'OH': 16,
      'MA': 16, 'FL': 16, 'IL': 16, 'NC': 16, 'PR': 16
    };
    return stateData[selectedFilter as keyof typeof stateData] || 6;
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">College Analytics Dashboard</h1>
        <a href="/dashboard" className="bg-slate-600 hover:bg-slate-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back to Dashboard</span>
        </a>
      </div>
      
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Filter Data:</label>
        <select 
          value={selectedFilter} 
          onChange={(e) => setSelectedFilter(e.target.value)}
          className="px-4 py-2 border rounded-lg min-w-64"
        >
          <option value="">All Data</option>
          <optgroup label="States (Top 10)">
            <option value="NY">New York (167 schools)</option>
            <option value="CA">California (115 schools)</option>
            <option value="PA">Pennsylvania (97 schools)</option>
            <option value="TX">Texas (87 schools)</option>
            <option value="OH">Ohio (81 schools)</option>
            <option value="MA">Massachusetts (66 schools)</option>
            <option value="FL">Florida (64 schools)</option>
            <option value="IL">Illinois (61 schools)</option>
            <option value="NC">North Carolina (58 schools)</option>
            <option value="PR">Puerto Rico (56 schools)</option>
          </optgroup>
          <optgroup label="Institution Types">
            <option value="Public">Public Institutions</option>
            <option value="Private">Private Institutions</option>
            <option value="HSI">Hispanic-Serving Institutions</option>
          </optgroup>
        </select>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-lg">
        <div className="h-96">
          {renderChart()}
        </div>
        {((chartType === 'state-comparison' || chartType === 'equity-gaps') && selectedFilter && ['NY', 'CA', 'PA', 'TX', 'OH', 'MA', 'FL', 'IL', 'NC', 'PR'].includes(selectedFilter)) && (
          <div className="flex justify-center items-center mt-4 space-x-4">
            <button
              onClick={() => setScrollIndex(Math.max(0, scrollIndex - 4))}
              disabled={scrollIndex === 0}
              className="px-3 py-1 bg-blue-500 text-white rounded disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              ← Previous
            </button>
            <span className="text-sm text-gray-600">
              Showing {scrollIndex + 1}-{Math.min(scrollIndex + 8, getMaxColleges())} of {getMaxColleges()} colleges
            </span>
            <button
              onClick={() => setScrollIndex(Math.min(getMaxColleges() - 8, scrollIndex + 4))}
              disabled={scrollIndex + 8 >= getMaxColleges()}
              className="px-3 py-1 bg-blue-500 text-white rounded disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Next →
            </button>
          </div>
        )}
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <button 
          onClick={() => setChartType('equity-gaps')}
          className={`p-4 rounded-lg text-left transition-colors ${
            chartType === 'equity-gaps' ? 'bg-blue-100 border-2 border-blue-500' : 'bg-blue-50 hover:bg-blue-100'
          }`}
        >
          <h3 className="font-semibold text-blue-900">Equity Gaps</h3>
          <p className="text-sm text-blue-700">Compare graduation rate gaps between overall, Pell recipients, and underrepresented minorities</p>
        </button>
        
        <button 
          onClick={() => setChartType('cost-outcomes')}
          className={`p-4 rounded-lg text-left transition-colors ${
            chartType === 'cost-outcomes' ? 'bg-green-100 border-2 border-green-500' : 'bg-green-50 hover:bg-green-100'
          }`}
        >
          <h3 className="font-semibold text-green-900">Cost vs Outcomes</h3>
          <p className="text-sm text-green-700">Analyze relationship between college costs and graduate earnings</p>
        </button>
        
        <button 
          onClick={() => setChartType('state-comparison')}
          className={`p-4 rounded-lg text-left transition-colors ${
            chartType === 'state-comparison' ? 'bg-purple-100 border-2 border-purple-500' : 'bg-purple-50 hover:bg-purple-100'
          }`}
        >
          <h3 className="font-semibold text-purple-900">State Performance</h3>
          <p className="text-sm text-purple-700">Compare graduation rates and outcomes across different states</p>
        </button>
      </div>
      
      {selectedFilter && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            <strong>Active Filter:</strong> {selectedFilter} - Showing data specific to this filter
          </p>
        </div>
      )}
    </div>
  );
}