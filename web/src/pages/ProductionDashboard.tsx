/**
 * Production Dashboard - Production Yield and Variance Analysis
 * 
 * Features two tabs:
 * 1. Variance Analysis (V2) - Snapshot analysis from ZRPP062
 * 2. Efficiency Hub (V3) - Historical trends and operational insights
 * 
 * Reference: ARCHITECTURAL DIRECTIVE Production Yield V2.1, ADR-2026-01-12 V3, Deep Clean 2026-01-12
 */
import { useState } from 'react';
import VarianceAnalysisTable from '../components/dashboard/production/VarianceAnalysisTable';
import YieldV3Dashboard from '../components/dashboard/production/YieldV3Dashboard';

type TabType = 'variance' | 'efficiency';

const ProductionDashboard = () => {
  const [activeTab, setActiveTab] = useState<TabType>('efficiency');

  const tabs = [
    { id: 'variance' as TabType, label: 'Variance Analysis', version: 'V2' },
    { id: 'efficiency' as TabType, label: 'Efficiency Hub', version: 'V3', highlight: true },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                {tab.label}
                {tab.version && (
                  <span className={`ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                    tab.highlight 
                      ? 'bg-blue-100 text-blue-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {tab.version}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto">
        {activeTab === 'variance' && (
          <VarianceAnalysisTable />
        )}

        {activeTab === 'efficiency' && (
          <YieldV3Dashboard />
        )}
      </div>
    </div>
  );
};

export default ProductionDashboard;
