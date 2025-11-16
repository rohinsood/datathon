import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

interface CollegeData {
  name: string;
  state: string;
  sector: string;
  institutionType: string;
  netPrice: number;
  graduationRate: number;
  medianEarnings: number;
  percentMinority: number;
}

function loadCollegeData(): CollegeData[] {
  try {
    const csvPath = path.join(process.cwd(), 'data', 'merged_clean.csv');
    const csvData = fs.readFileSync(csvPath, 'utf8');
    const lines = csvData.split('\n');
    const header = lines[0].split(',');
    
    const nameIdx = header.findIndex(h => h.includes('Institution Name'));
    const stateIdx = header.findIndex(h => h.includes('State Abbreviation'));
    const sectorIdx = header.findIndex(h => h.includes('Sector Name'));
    const typeIdx = header.findIndex(h => h.includes('Institution Type'));
    const netPriceIdx = header.findIndex(h => h.includes('Net Price'));
    const gradRateIdx = header.findIndex(h => h.includes('Bachelor\'s Degree Graduation Rate Within 6 Years - Total'));
    const earningsIdx = header.findIndex(h => h.includes('Median Earnings'));
    const minorityIdx = header.findIndex(h => h.includes('Percent of Latino'));
    
    return lines.slice(1).map(line => {
      const cols = line.split(',');
      if (cols.length > 10 && cols[nameIdx]) {
        return {
          name: cols[nameIdx] || 'Unknown',
          state: cols[stateIdx] || 'Unknown',
          sector: cols[sectorIdx] || 'Unknown',
          institutionType: cols[typeIdx] || 'Unknown',
          netPrice: parseFloat(cols[netPriceIdx]) || 0,
          graduationRate: parseFloat(cols[gradRateIdx]) || 0,
          medianEarnings: parseFloat(cols[earningsIdx]) || 0,
          percentMinority: parseFloat(cols[minorityIdx]) || 0
        };
      }
      return null;
    }).filter(Boolean) as CollegeData[];
  } catch (error) {
    return [];
  }
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const chartType = searchParams.get('chart');
  const filter = searchParams.get('filter');
  
  const data = loadCollegeData();
  
  switch (chartType) {
    case 'equity-gaps':
      const equityData = data
        .filter(d => filter ? d.institutionType.includes(filter) : true)
        .reduce((acc, college) => {
          const type = college.institutionType;
          if (!acc[type]) acc[type] = { total: 0, count: 0, minority: 0 };
          acc[type].total += college.graduationRate;
          acc[type].minority += college.percentMinority;
          acc[type].count++;
          return acc;
        }, {} as any);
      
      return NextResponse.json({
        labels: Object.keys(equityData),
        datasets: [{
          label: 'Avg Graduation Rate',
          data: Object.values(equityData).map((d: any) => d.total / d.count),
          backgroundColor: 'rgba(54, 162, 235, 0.6)'
        }, {
          label: 'Avg Minority %',
          data: Object.values(equityData).map((d: any) => d.minority / d.count),
          backgroundColor: 'rgba(255, 99, 132, 0.6)'
        }]
      });
      
    case 'cost-outcomes':
      const costData = data
        .filter(d => d.netPrice > 0 && d.medianEarnings > 0)
        .filter(d => filter ? d.sector.includes(filter) : true)
        .map(d => ({ x: d.netPrice, y: d.medianEarnings, label: d.name }));
      
      return NextResponse.json({
        datasets: [{
          label: 'Cost vs Earnings',
          data: costData.slice(0, 50),
          backgroundColor: 'rgba(75, 192, 192, 0.6)'
        }]
      });
      
    case 'state-comparison':
      const stateData = data
        .reduce((acc, college) => {
          if (!acc[college.state]) acc[college.state] = { total: 0, count: 0 };
          acc[college.state].total += college.graduationRate;
          acc[college.state].count++;
          return acc;
        }, {} as any);
      
      const topStates = Object.entries(stateData)
        .map(([state, data]: [string, any]) => ({ state, avg: data.total / data.count }))
        .sort((a, b) => b.avg - a.avg)
        .slice(0, 10);
      
      return NextResponse.json({
        labels: topStates.map(s => s.state),
        datasets: [{
          label: 'Graduation Rate %',
          data: topStates.map(s => s.avg),
          backgroundColor: 'rgba(153, 102, 255, 0.6)'
        }]
      });
      
    default:
      return NextResponse.json({ error: 'Invalid chart type' });
  }
}