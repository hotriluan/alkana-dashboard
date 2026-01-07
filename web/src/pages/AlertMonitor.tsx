/**
 * Alert Monitor Dashboard
 * 
 * Skills: frontend-development, ui-ux-pro-max
 * CLAUDE.md: DRY - Reuse KPICard and DataTable components
 * 
 * Features:
 * - 4 KPI cards (Critical, High, Medium, Total)
 * - Stuck inventory alerts table (>48h)
 * - Low yield alerts table (<85%)
 * - Resolve button for each alert
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, Clock, TrendingDown } from 'lucide-react';
import api from '../services/api';
import { KPICard } from '../components/common/KPICard';
import { DataTable } from '../components/common/DataTable';
import { DateRangePicker } from '../components/common/DateRangePicker';

interface AlertSummary {
    critical: number;
    high: number;
    medium: number;
    total: number;
}

interface AlertDetail {
    id: number;
    alert_type: string;
    severity: string;
    title: string;
    message: string;
    entity_type: string;
    entity_id: string;
    detected_at: string;
    status: string;
}

const AlertMonitor = () => {
    const queryClient = useQueryClient();
    const today = new Date().toISOString().split('T')[0];
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    const [startDate, setStartDate] = useState(thirtyDaysAgo);
    const [endDate, setEndDate] = useState(today);

    const handleDateChange = (newStartDate: string, newEndDate: string) => {
        setStartDate(newStartDate);
        setEndDate(newEndDate);
    };

    // Fetch summary (DRY - single source of truth)
    const { data: summary } = useQuery<AlertSummary>({
        queryKey: ['alert-summary', startDate, endDate],
        queryFn: async () => {
            const response = await api.get(`/api/v1/alerts/summary?start_date=${startDate}&end_date=${endDate}`);
            return response.data;
        },
        refetchInterval: 30000 // Auto-refresh every 30s
    });

    // Fetch stuck inventory alerts
    const { data: stuckAlerts, isLoading: stuckLoading } = useQuery<AlertDetail[]>({
        queryKey: ['stuck-alerts', startDate, endDate],
        queryFn: async () => {
            const response = await api.get(`/api/v1/alerts/stuck-inventory?start_date=${startDate}&end_date=${endDate}`);
            return response.data;
        },
        refetchInterval: 30000
    });

    // Fetch low yield alerts
    const { data: yieldAlerts, isLoading: yieldLoading } = useQuery<AlertDetail[]>({
        queryKey: ['yield-alerts'],
        queryFn: async () => {
            const response = await api.get('/api/v1/alerts/low-yield');
            return response.data;
        },
        refetchInterval: 30000
    });

    // Resolve alert mutation (KISS - simple POST request)
    const resolveMutation = useMutation({
        mutationFn: async (alertId: number) => {
            await api.post(`/api/v1/alerts/${alertId}/resolve`);
        },
        onSuccess: () => {
            // Invalidate all alert queries to refresh data
            queryClient.invalidateQueries({ queryKey: ['alert-summary'] });
            queryClient.invalidateQueries({ queryKey: ['stuck-alerts'] });
            queryClient.invalidateQueries({ queryKey: ['yield-alerts'] });
        }
    });

    // Severity badge component (ui-ux-pro-max - visual clarity)
    const SeverityBadge = ({ severity }: { severity: string }) => {
        const colors = {
            CRITICAL: 'bg-red-100 text-red-800 border-red-200',
            HIGH: 'bg-orange-100 text-orange-800 border-orange-200',
            MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-200'
        };

        return (
            <span className={`px-2 py-1 text-xs font-semibold rounded border ${colors[severity as keyof typeof colors] || 'bg-gray-100 text-gray-800'}`}>
                {severity}
            </span>
        );
    };

    // Table columns definition (DRY - reusable configuration)
    // FIXED: Changed from accessor/cell to key/render to match DataTable interface
    const alertColumns = [
        {
            key: 'severity' as keyof AlertDetail,
            header: 'Severity',
            render: (value: string) => <SeverityBadge severity={value} />
        },
        {
            key: 'title' as keyof AlertDetail,
            header: 'Title'
        },
        {
            key: 'message' as keyof AlertDetail,
            header: 'Message',
            render: (value: string) => (
                <div className="max-w-md truncate" title={value}>
                    {value}
                </div>
            )
        },
        {
            key: 'entity_id' as keyof AlertDetail,
            header: 'Entity',
            render: (value: string) => (
                <code className="text-xs bg-gray-100 px-2 py-1 rounded">{value}</code>
            )
        },
        {
            key: 'detected_at' as keyof AlertDetail,
            header: 'Detected',
            render: (value: string) => {
                const date = new Date(value);
                return date.toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
        },
        {
            key: 'id' as keyof AlertDetail,
            header: 'Action',
            render: (value: number) => (
                <button
                    onClick={() => resolveMutation.mutate(value)}
                    disabled={resolveMutation.isPending}
                    className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                    {resolveMutation.isPending ? 'Resolving...' : 'Resolve'}
                </button>
            )
        }
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Alert Monitor</h1>
                    <p className="text-sm text-gray-600 mt-1">
                        Real-time monitoring of stuck inventory and low production yield
                    </p>
                </div>
                <DateRangePicker startDate={startDate} endDate={endDate} onDateChange={handleDateChange} />
            </div>

            {/* KPI Cards (ui-ux-pro-max - visual hierarchy) */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <KPICard
                    title="Critical Alerts"
                    value={summary?.critical || 0}
                    icon={<AlertTriangle />}
                    trend="neutral"
                />
                <KPICard
                    title="High Priority"
                    value={summary?.high || 0}
                    icon={<AlertTriangle />}
                    trend="neutral"
                />
                <KPICard
                    title="Medium Priority"
                    value={summary?.medium || 0}
                    icon={<AlertTriangle />}
                    trend="neutral"
                />
                <KPICard
                    title="Total Active"
                    value={summary?.total || 0}
                    icon={<AlertTriangle />}
                    trend="neutral"
                />
            </div>

            {/* Stuck Inventory Alerts */}
            <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                    <div className="flex items-center gap-2">
                        <Clock className="w-5 h-5 text-orange-600" />
                        <h2 className="text-lg font-semibold text-gray-900">
                            Stuck Inventory (&gt;48h in Transit)
                        </h2>
                        {stuckAlerts && stuckAlerts.length > 0 && (
                            <span className="ml-auto px-2 py-1 bg-orange-100 text-orange-800 text-xs font-semibold rounded">
                                {stuckAlerts.length} alerts
                            </span>
                        )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                        Items received at factory but not issued to DC within 48 hours
                    </p>
                </div>
                <div className="p-6">
                    {stuckAlerts && stuckAlerts.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            <Clock className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                            <p>No stuck inventory alerts</p>
                        </div>
                    ) : (
                        <DataTable
                            columns={alertColumns}
                            data={stuckAlerts || []}
                            loading={stuckLoading}
                        />
                    )}
                </div>
            </div>

            {/* Low Yield Alerts */}
            <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                    <div className="flex items-center gap-2">
                        <TrendingDown className="w-5 h-5 text-red-600" />
                        <h2 className="text-lg font-semibold text-gray-900">
                            Low Production Yield (&lt;85%)
                        </h2>
                        {yieldAlerts && yieldAlerts.length > 0 && (
                            <span className="ml-auto px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded">
                                {yieldAlerts.length} alerts
                            </span>
                        )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                        Production chains with total yield below 85% threshold
                    </p>
                </div>
                <div className="p-6">
                    {yieldAlerts && yieldAlerts.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            <TrendingDown className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                            <p>No low yield alerts</p>
                        </div>
                    ) : (
                        <DataTable
                            columns={alertColumns}
                            data={yieldAlerts || []}
                            loading={yieldLoading}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default AlertMonitor;
