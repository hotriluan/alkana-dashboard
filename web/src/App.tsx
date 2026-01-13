import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Login from './pages/Login';
import ExecutiveDashboard from './pages/ExecutiveDashboard';
import ArAging from './pages/ArAging';
import Inventory from './pages/Inventory';
import MTOOrders from './pages/MTOOrders';
import SalesPerformance from './pages/SalesPerformance';
import LeadTimeDashboard from './pages/LeadTimeDashboard';
import AlertMonitor from './pages/AlertMonitor';
import DataUpload from './pages/DataUpload';
import ProductionDashboard from './pages/ProductionDashboard';
import { ProtectedRoute } from './components/ProtectedRoute';
import { DashboardLayout } from './components/DashboardLayout';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <ExecutiveDashboard />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/ar-aging"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <ArAging />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/inventory"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <Inventory />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/mto-orders"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <MTOOrders />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/sales"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <SalesPerformance />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/leadtime"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <LeadTimeDashboard />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/alerts"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <AlertMonitor />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/production"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <ProductionDashboard />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <DataUpload />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
