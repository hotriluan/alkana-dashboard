// Lead Time Dashboard - MTO/MTS Lead-time Analysis
// Reference: NEXT_STEPS.md Phase 6.1.4
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Clock, AlertTriangle, CheckCircle, Package, Truck, Search } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { KPICard } from '../components/common/KPICard';
import { DataTable } from '../components/common/DataTable';
import { DateRangePicker } from '../components/common/DateRangePicker';
import api from '../services/api';


interface LeadTimeKPIs {
    avg_mto_leadtime: number;
    avg_mts_leadtime: number;
    on_time_pct: number;
    delayed_pct: number;
    critical_pct: number;
    total_orders: number;
}

interface LeadTimeBreakdown {
    order_category: string; // MTO/MTS
    avg_preparation: number | null;
    avg_production: number;
    avg_transit: number | null;
    avg_storage: number | null;
    avg_delivery: number | null;
    avg_total: number;
    order_count: number;
}

interface LeadTimeDetail {
    order_number: string;
    batch: string;
    order_category: string;
    material_description: string;
    plant_code: string;
    preparation_time: number | null;
    production_time: number | null;
    transit_time: number | null;
    storage_time: number | null;
    delivery_time: number | null;
    total_leadtime: number | null;
    leadtime_status: string;
    release_date: string;
    actual_finish_date: string;
}

interface ChannelLeadTime {
    channel: string;
    channel_name: string;
    // MTO metrics
    mto_orders: number;
    mto_avg_leadtime: number | null;
    mto_on_time_pct: number | null;
    // MTS metrics
    mts_orders: number;
    mts_avg_leadtime: number | null;
    mts_on_time_pct: number | null;
    // Total
    total_orders: number;
    avg_total_leadtime: number | null;
}

// Update Interface
interface EventDetail {
    stage: string;
    date: string;
    duration: number;
    status: string;
    details?: string;
}

interface BatchTrace {
    batch_id: string;
    product: string;
    product_description?: string;  // Added
    plant: string;
    total_lead_time: number | null;
    current_status: string;
    leadtime_status?: string; // Optional, might not be in API for trace but used in UI logic
    events: EventDetail[];
}

// ... (in component) ...



import { getFirstDayOfMonth, getToday } from '../utils/dateHelpers';

const LeadTimeDashboard = () => {
    const today = getToday();
    const firstDayOfMonth = getFirstDayOfMonth();
    const [startDate, setStartDate] = useState(firstDayOfMonth);
    const [endDate, setEndDate] = useState(today);

    const handleDateChange = (newStartDate: string, newEndDate: string) => {
        setStartDate(newStartDate);
        setEndDate(newEndDate);
    };

    const { data: kpis, isLoading: kpisLoading } = useQuery({
        queryKey: ['leadtime-kpis', startDate, endDate],
        queryFn: async () => {
            const response = await api.get<LeadTimeKPIs>(`/api/v1/leadtime/summary?start_date=${startDate}&end_date=${endDate}`);
            return response.data;
        },
    });

    const { data: breakdown, isLoading: breakdownLoading } = useQuery({
        queryKey: ['leadtime-breakdown', startDate, endDate],
        queryFn: async () => {
            const response = await api.get<LeadTimeBreakdown[]>(`/api/v1/leadtime/breakdown?start_date=${startDate}&end_date=${endDate}`);
            return response.data;
        },
    });

    const { data: orders, isLoading: ordersLoading } = useQuery({
        queryKey: ['leadtime-orders', startDate, endDate],
        queryFn: async () => {
            const response = await api.get<LeadTimeDetail[]>(`/api/v1/leadtime/orders?limit=100&start_date=${startDate}&end_date=${endDate}`);
            return response.data;
        },
    });

    // New: Channel grouping data
    const { data: channelData, isLoading: channelLoading } = useQuery({
        queryKey: ['leadtime-by-channel', startDate, endDate],
        queryFn: async () => {
            const response = await api.get<ChannelLeadTime[]>(`/api/v1/leadtime/by-channel?start_date=${startDate}&end_date=${endDate}`);
            return response.data;
        },
    });

    // New: Batch tracing
    const [batchInput, setBatchInput] = useState('');
    const [searchBatch, setSearchBatch] = useState('');

    const { data: batchTrace, isLoading: traceLoading, error: traceError } = useQuery({
        queryKey: ['batch-trace', searchBatch],
        queryFn: async () => {
            if (!searchBatch) return null;
            const response = await api.get<BatchTrace>(`/api/v1/leadtime/trace/${searchBatch}`);
            return response.data;
        },
        enabled: !!searchBatch,
        retry: false
    });

    const formatNumber = (value: number | null) => {
        if (value === null) return 'N/A';
        return value.toFixed(1);
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'ON_TIME': return 'text-green-600 bg-green-50';
            case 'DELAYED': return 'text-yellow-600 bg-yellow-50';
            case 'CRITICAL': return 'text-red-600 bg-red-50';
            default: return 'text-gray-600 bg-gray-50';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'ON_TIME': return <CheckCircle className="h-4 w-4" />;
            case 'DELAYED': return <Clock className="h-4 w-4" />;
            case 'CRITICAL': return <AlertTriangle className="h-4 w-4" />;
            default: return <Package className="h-4 w-4" />;
        }
    };

    // Transform breakdown data for stacked bar chart
    const chartData = breakdown?.map(item => ({
        category: item.order_category,
        Preparation: item.avg_preparation || 0,
        Production: item.avg_production || 0,
        Transit: item.avg_transit || 0,
        Storage: item.avg_storage || 0,
        Delivery: item.avg_delivery || 0,
    })) || [];

    const orderColumns = [
        {
            key: 'order_number' as keyof LeadTimeDetail,
            header: 'Order Number',
            sortable: true,
            width: '120px',
        },
        {
            key: 'batch' as keyof LeadTimeDetail,
            header: 'Batch',
            sortable: true,
            width: '100px',
        },
        {
            key: 'order_category' as keyof LeadTimeDetail,
            header: 'Type',
            width: '60px',
            sortable: true,
            render: (value: string) => (
                <span className={`px-2 py-1 rounded text-xs font-medium ${value === 'MTO' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                    }`}>
                    {value}
                </span>
            ),
        },
        {
            key: 'material_description' as keyof LeadTimeDetail,
            header: 'Material',
            sortable: true,
        },
        {
            key: 'total_leadtime' as keyof LeadTimeDetail,
            header: 'Total (days)',
            align: 'right' as const,
            width: '100px',
            sortable: true,
            render: (value: number | null) => (
                <span className="font-semibold">{formatNumber(value)}</span>
            ),
        },
        {
            key: 'leadtime_status' as keyof LeadTimeDetail,
            header: 'Status',
            width: '100px',
            sortable: true,
            render: (value: string) => (
                <div className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${getStatusColor(value)}`}>
                    {getStatusIcon(value)}
                    {value}
                </div>
            ),
        },
        {
            key: 'release_date' as keyof LeadTimeDetail,
            header: 'Release Date',
            width: '110px',
            sortable: true,
            render: (value: string) => value ? new Date(value).toLocaleDateString('vi-VN') : 'N/A',
        },
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Lead Time Analysis</h1>
                    <div className="text-sm text-gray-500 mt-1">
                        Last updated: {new Date().toLocaleString('vi-VN')}
                    </div>
                </div>
                <DateRangePicker startDate={startDate} endDate={endDate} onDateChange={handleDateChange} />
            </div>

            {/* KPI Cards Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
                <KPICard
                    title="Avg MTO Lead-time"
                    value={kpis ? `${formatNumber(kpis.avg_mto_leadtime)} days` : '0 days'}
                    icon={<Clock className="h-6 w-6" />}
                    loading={kpisLoading}
                    subtitle="5-stage process"
                />
                <KPICard
                    title="Avg MTS Lead-time"
                    value={kpis ? `${formatNumber(kpis.avg_mts_leadtime)} days` : '0 days'}
                    icon={<Truck className="h-6 w-6" />}
                    loading={kpisLoading}
                    subtitle="3-stage process"
                />
                <KPICard
                    title="On-Time %"
                    value={kpis ? `${formatNumber(kpis.on_time_pct)}%` : '0%'}
                    icon={<CheckCircle className="h-6 w-6" />}
                    loading={kpisLoading}
                    trend="up"
                />
                <KPICard
                    title="Delayed %"
                    value={kpis ? `${formatNumber(kpis.delayed_pct)}%` : '0%'}
                    icon={<Clock className="h-6 w-6" />}
                    loading={kpisLoading}
                    trend="neutral"
                />
                <KPICard
                    title="Critical %"
                    value={kpis ? `${formatNumber(kpis.critical_pct)}%` : '0%'}
                    icon={<AlertTriangle className="h-6 w-6" />}
                    loading={kpisLoading}
                    trend="down"
                />
                <KPICard
                    title="Total Orders"
                    value={kpis ? kpis.total_orders.toLocaleString() : '0'}
                    icon={<Package className="h-6 w-6" />}
                    loading={kpisLoading}
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Lead-time Breakdown - Stacked Bar Chart */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Lead-time Breakdown by Stage</h2>
                    <p className="text-sm text-gray-600 mb-4">
                        MTO: 4 stages (Prep → Prod → Transit → Storage)<br />
                        MTS: 3 stages (Prod → Transit → Storage)
                    </p>
                    {breakdownLoading ? (
                        <div className="h-80 flex items-center justify-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        </div>
                    ) : (
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="category" style={{ fontSize: '12px' }} />
                                <YAxis
                                    label={{ value: 'Days', angle: -90, position: 'insideLeft' }}
                                    style={{ fontSize: '12px' }}
                                />
                                <Tooltip
                                    formatter={(value) => `${Number(value).toFixed(1)} days`}
                                    contentStyle={{ fontSize: '12px' }}
                                />
                                <Legend wrapperStyle={{ fontSize: '12px' }} />
                                <Bar dataKey="Preparation" stackId="a" fill="#8b5cf6" name="Preparation" />
                                <Bar dataKey="Production" stackId="a" fill="#3b82f6" name="Production" />
                                <Bar dataKey="Transit" stackId="a" fill="#10b981" name="Transit" />
                                <Bar dataKey="Storage" stackId="a" fill="#f59e0b" name="Storage" />

                            </BarChart>
                        </ResponsiveContainer>
                    )}
                </div>

                {/* Average Lead-time Comparison */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">MTO vs MTS Comparison</h2>
                    <p className="text-sm text-gray-600 mb-4">
                        Average total lead-time by order category
                    </p>
                    {breakdownLoading ? (
                        <div className="h-80 flex items-center justify-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        </div>
                    ) : (
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={breakdown || []} layout="horizontal">
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="order_category" style={{ fontSize: '12px' }} />
                                <YAxis
                                    label={{ value: 'Days', angle: -90, position: 'insideLeft' }}
                                    style={{ fontSize: '12px' }}
                                />
                                <Tooltip
                                    formatter={(value) => `${formatNumber(Number(value))} days`}
                                    contentStyle={{ fontSize: '12px' }}
                                />
                                <Legend wrapperStyle={{ fontSize: '12px' }} />
                                <Bar dataKey="avg_total" fill="#3b82f6" name="Avg Total Lead-time" radius={[4, 4, 0, 0]}>
                                    {(breakdown || []).map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.order_category === 'MTO' ? '#3b82f6' : '#8b5cf6'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    )}
                </div>
            </div>

            {/* Order Details Table */}
            <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-900">Recent Orders (Latest 100)</h2>
                    <p className="text-sm text-gray-600 mt-1">
                        Detailed lead-time breakdown for individual production orders
                    </p>
                </div>
                <div className="p-6">
                    <DataTable
                        columns={orderColumns}
                        data={orders || []}
                        loading={ordersLoading}
                    />
                </div>
            </div>

            {/* Distribution Channel Comparison */}
            <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-900">Lead-time by Distribution Channel</h2>
                    <p className="text-sm text-gray-600 mt-1">
                        Performance comparison across channels (11: Industry, 12: Over Sea, 13: Retail, 15: Project) with MTO/MTS breakdown
                    </p>
                </div>
                <div className="p-6">
                    {channelLoading ? (
                        <div className="flex items-center justify-center h-64">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Channel</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">MTO Orders</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">MTO Avg</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">MTO On-Time</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">MTS Orders</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">MTS Avg</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">MTS On-Time</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total Orders</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Total</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {channelData?.map((row) => (
                                        <tr key={row.channel} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="text-sm font-medium text-gray-900">{row.channel_name}</div>
                                                <div className="text-xs text-gray-500">Channel {row.channel}</div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">{row.mto_orders}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                                                {row.mto_avg_leadtime ? `${row.mto_avg_leadtime} days` : '-'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                                                {row.mto_on_time_pct !== null ? (
                                                    <span className={`${row.mto_on_time_pct >= 90 ? 'text-green-600' : row.mto_on_time_pct >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
                                                        {row.mto_on_time_pct}%
                                                    </span>
                                                ) : '-'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">{row.mts_orders}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                                                {row.mts_avg_leadtime ? `${row.mts_avg_leadtime} days` : '-'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                                                {row.mts_on_time_pct !== null ? (
                                                    <span className={`${row.mts_on_time_pct >= 90 ? 'text-green-600' : row.mts_on_time_pct >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
                                                        {row.mts_on_time_pct}%
                                                    </span>
                                                ) : '-'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-gray-900">{row.total_orders}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                                                {row.avg_total_leadtime ? `${row.avg_total_leadtime} days` : '-'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>

            {/* Batch Tracing */}
            <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-900">Batch Tracing</h2>
                    <p className="text-sm text-gray-600 mt-1">
                        Track detailed timeline and lead-time breakdown for a specific batch
                    </p>
                </div>
                <div className="p-6">
                    {/* Search Input */}
                    <div className="flex gap-3 mb-6">
                        <div className="flex-1">
                            <input
                                type="text"
                                placeholder="Enter batch number (e.g., 25L2470510)"
                                value={batchInput}
                                onChange={(e) => setBatchInput(e.target.value.toUpperCase())}
                                onKeyPress={(e) => e.key === 'Enter' && setSearchBatch(batchInput)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>
                        <button
                            onClick={() => setSearchBatch(batchInput)}
                            disabled={!batchInput}
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                            <Search className="h-5 w-5" />
                            Trace
                        </button>
                    </div>

                    {/* Error Message */}
                    {traceError && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-sm text-red-600">Batch not found. Please check the batch number and try again.</p>
                        </div>
                    )}

                    {/* Loading */}
                    {traceLoading && (
                        <div className="flex items-center justify-center h-32">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        </div>
                    )}

                    {/* Batch Details */}
                    {batchTrace && (
                        <div>
                            {/* Batch Info Cards - Horizontal Layout with Gradients */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                                {/* Batch ID Card */}
                                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-5 border border-blue-200 shadow-sm hover:shadow-md transition-shadow">
                                    <div className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Batch</div>
                                    <div className="text-2xl font-bold text-blue-900">{batchTrace.batch_id}</div>
                                </div>

                                {/* Product Card */}
                                <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-5 border border-purple-200 shadow-sm hover:shadow-md transition-shadow">
                                    <div className="text-xs font-semibold text-purple-600 uppercase tracking-wide mb-2">Product</div>
                                    <div className="text-lg font-bold text-purple-900 leading-tight">
                                        {batchTrace.product_description || batchTrace.product}
                                    </div>
                                    {batchTrace.product_description && (
                                        <div className="text-xs text-purple-700 mt-1">Code: {batchTrace.product}</div>
                                    )}
                                </div>

                                {/* Lead Time Card */}
                                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-5 border border-green-200 shadow-sm hover:shadow-md transition-shadow">
                                    <div className="text-xs font-semibold text-green-600 uppercase tracking-wide mb-2">Total Lead-Time</div>
                                    <div className="flex items-baseline gap-2">
                                        <span className="text-2xl font-bold text-green-900">
                                            {batchTrace.total_lead_time || 0}
                                        </span>
                                        <span className="text-sm font-medium text-green-700">days</span>
                                        <span className={`ml-auto px-3 py-1 rounded-full text-xs font-bold ${batchTrace.current_status === 'Delivered'
                                            ? 'bg-green-600 text-white shadow-sm'
                                            : 'bg-yellow-500 text-white shadow-sm'
                                            }`}>
                                            {batchTrace.current_status}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Timeline Visualization */}
                            <div className="mb-6">
                                <h3 className="text-sm font-medium text-gray-700 mb-3">Timeline</h3>
                                <div className="relative h-20 bg-gray-100 rounded-lg overflow-hidden">
                                    {(batchTrace.events || []).map((stage: any, idx: number) => {
                                        const totalDays = batchTrace.total_lead_time || 1;
                                        const stageDays = stage.duration || 0;
                                        const widthPct = (stageDays / totalDays) * 100;

                                        // Calculate left position based on previous stages
                                        const prevStages = (batchTrace.events || []).slice(0, idx);
                                        const leftPct = prevStages.reduce((sum: number, s: any) => sum + ((s.duration || 0) / totalDays) * 100, 0);

                                        const colors: Record<string, string> = {
                                            'Preparation': '#8b5cf6',  // Violet
                                            'Production': '#3b82f6',   // Blue
                                            'Transit': '#10b981',      // Emerald
                                            'Storage': '#f59e0b',      // Amber
                                            'Delivery': '#6b7280'      // Gray
                                        };

                                        return (
                                            <div
                                                key={idx}
                                                className="absolute h-full flex items-center justify-center text-white text-xs font-medium"
                                                style={{
                                                    left: `${leftPct}%`,
                                                    width: `${widthPct}%`,
                                                    backgroundColor: colors[stage.stage] || '#6b7280'
                                                }}
                                                title={`${stage.stage}: ${stageDays} days`}
                                            >
                                                {widthPct > 10 && (
                                                    <div className="text-center px-2">
                                                        <div className="truncate">{stage.stage}</div>
                                                        <div className="text-xs opacity-90">{stageDays}d</div>
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Stage Details Table */}
                            <div>
                                <h3 className="text-sm font-medium text-gray-700 mb-3">Stage Details</h3>
                                <div className="overflow-x-auto">
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stage</th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Start Date</th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">End Date</th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Duration</th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {(batchTrace.events || []).map((event, idx) => (
                                                <tr key={idx} className="hover:bg-gray-50">
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{event.stage}</td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                                                        {event.date ? new Date(event.date).toLocaleDateString() : '-'}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium text-gray-900">
                                                        {event.duration} days
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                                                        <span className={`px-2 py-1 rounded text-xs font-medium ${event.status === 'COMPLETED' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                                            {event.status}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                                                        {event.details || '-'}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default LeadTimeDashboard;
