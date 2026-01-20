/**
 * Production Dashboard - Efficiency Hub (V3)
 * 
 * Single view: Efficiency Hub with historical trends and operational insights
 * 
 * Reference: Deep Clean 2026-01-12 - Removed V2 Variance Analysis
 */
import YieldV3Dashboard from '../components/dashboard/production/YieldV3Dashboard';

const ProductionDashboard = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <YieldV3Dashboard />
    </div>
  );
};

export default ProductionDashboard;
