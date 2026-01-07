// Layout component with sidebar navigation
import type { ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  Package,
  DollarSign,
  ClipboardList,
  TrendingUp,
  BarChart3,
  LogOut,
  Menu,
  X,
  LayoutDashboard,
  Clock,
  AlertTriangle,
  Upload
} from 'lucide-react';
import { useState } from 'react';

interface DashboardLayoutProps {
  children: ReactNode;
}

export const DashboardLayout = ({ children }: DashboardLayoutProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const menuItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Executive' },
    { path: '/ar-aging', icon: DollarSign, label: 'AR Collection' },
    { path: '/inventory', icon: Package, label: 'Inventory' },
    { path: '/mto-orders', icon: ClipboardList, label: 'MTO Orders' },
    { path: '/yield', icon: TrendingUp, label: 'Production Yield' },
    { path: '/sales', icon: BarChart3, label: 'Sales Performance' },
    { path: '/leadtime', icon: Clock, label: 'Lead Time Analysis' },
    { path: '/alerts', icon: AlertTriangle, label: 'Alert Monitor' },
    { path: '/upload', icon: Upload, label: 'Data Upload' },
  ];

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <div
        className={`${sidebarOpen ? 'w-64' : 'w-20'
          } bg-slate-900 text-white transition-all duration-300 flex flex-col`}
      >
        {/* Header */}
        <div className="p-4 flex items-center justify-between border-b border-slate-700">
          {sidebarOpen && (
            <h1 className="text-xl font-bold">Alkana Dashboard</h1>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-slate-800 rounded"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* User Info & Logout */}
        <div className="p-4 border-t border-slate-700">
          {sidebarOpen && user && (
            <div className="mb-3">
              <p className="text-sm font-medium text-white">{user.full_name}</p>
              <p className="text-xs text-slate-400">{user.username}</p>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-2 w-full text-slate-300 hover:bg-slate-800 hover:text-white rounded-lg transition-colors"
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span>Logout</span>}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {children}
      </div>
    </div>
  );
};
