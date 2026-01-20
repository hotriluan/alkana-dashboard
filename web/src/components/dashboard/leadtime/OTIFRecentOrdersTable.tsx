// OTIF Recent Orders Table - Logistics-Only Delivery Status
// Displays recent deliveries with on-time delivery analysis
// Data source: fact_delivery (ZRSD004) only, no cross-module linking

import { useQuery } from '@tanstack/react-query';
import { Clock, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { DataTable } from '../../common/DataTable';
import api from '../../../services/api';

interface RecentOrderRecord {
    delivery: string;
    so_reference?: string;
    target_date?: string;  // Planned delivery date
    actual_date?: string;  // Actual goods issue date
    status: string;  // "Pending", "On Time", "Late"
    material_code?: string;
    material_description?: string;
    delivery_qty?: number;
}

export const OTIFRecentOrdersTable = () => {
    const { data: orders, isLoading, error } = useQuery({
        queryKey: ['leadtime-recent-orders'],
        queryFn: async () => {
            const response = await api.get<RecentOrderRecord[]>('/api/v1/leadtime/recent-orders?limit=50');
            return response.data;
        },
        refetchInterval: 30000, // Refresh every 30 seconds
    });

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'On Time':
                return 'bg-green-50 text-green-700 border-green-200';
            case 'Late':
                return 'bg-red-50 text-red-700 border-red-200';
            case 'Pending':
            default:
                return 'bg-gray-50 text-gray-700 border-gray-200';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'On Time':
                return <CheckCircle className="w-4 h-4 inline mr-1" />;
            case 'Late':
                return <AlertCircle className="w-4 h-4 inline mr-1" />;
            case 'Pending':
            default:
                return <Clock className="w-4 h-4 inline mr-1" />;
        }
    };

    const columns: Array<{
        key: keyof RecentOrderRecord;
        header: string;
        sortable?: boolean;
        render?: (value: any, row: RecentOrderRecord) => React.ReactNode;
    }> = [
        {
            key: 'delivery' as keyof RecentOrderRecord,
            header: 'Delivery #',
            sortable: true,
            render: (_, row: RecentOrderRecord) => (
                <span className="font-mono text-sm">{row.delivery}</span>
            ),
        },
        {
            key: 'so_reference' as keyof RecentOrderRecord,
            header: 'Sales Order',
            sortable: true,
            render: (_, row: RecentOrderRecord) => (
                <span className="text-sm text-gray-700">{row.so_reference || '-'}</span>
            ),
        },
        {
            key: 'material_description' as keyof RecentOrderRecord,
            header: 'Material',
            sortable: true,
            render: (_, row: RecentOrderRecord) => (
                <div className="text-sm">
                    <div className="font-medium text-gray-900">{row.material_description || row.material_code || '-'}</div>
                    <div className="text-xs text-gray-500">{row.material_code}</div>
                </div>
            ),
        },
        {
            key: 'target_date' as keyof RecentOrderRecord,
            header: 'Planned Delivery Date',
            sortable: true,
            render: (_, row: RecentOrderRecord) => (
                <span className="text-sm text-gray-700">
                    {row.target_date ? new Date(row.target_date).toLocaleDateString() : '-'}
                </span>
            ),
        },
        {
            key: 'actual_date' as keyof RecentOrderRecord,
            header: 'Actual GI Date',
            sortable: true,
            render: (_, row: RecentOrderRecord) => (
                <span className="text-sm text-gray-700">
                    {row.actual_date ? new Date(row.actual_date).toLocaleDateString() : '-'}
                </span>
            ),
        },
        {
            key: 'delivery_qty' as keyof RecentOrderRecord,
            header: 'Qty',
            sortable: true,
            render: (_, row: RecentOrderRecord) => (
                <span className="text-sm text-gray-700">
                    {row.delivery_qty ? row.delivery_qty.toLocaleString('en-US', { maximumFractionDigits: 2 }) : '-'}
                </span>
            ),
        },
        {
            key: 'status' as keyof RecentOrderRecord,
            header: 'OTIF Status',
            sortable: true,
            render: (_, row: RecentOrderRecord) => (
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(row.status)}`}>
                    {getStatusIcon(row.status)}
                    {row.status}
                </div>
            ),
        },
    ];

    if (error) {
        return (
            <div className="bg-white rounded-lg shadow">
                <div className="p-6">
                    <div className="text-red-600 text-sm">
                        Error loading recent orders: {error instanceof Error ? error.message : 'Unknown error'}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Recent Deliveries (OTIF Analysis)</h2>
                <p className="text-sm text-gray-600 mt-1">
                    On-Time In-Full (OTIF) status based on planned delivery date vs actual goods issue date
                </p>
            </div>
            <div className="p-6">
                {isLoading ? (
                    <div className="flex items-center justify-center h-64">
                        <Loader className="w-6 h-6 animate-spin text-blue-600" />
                    </div>
                ) : (
                    <DataTable
                        columns={columns as any}
                        data={orders || []}
                        loading={false}
                    />
                )}
            </div>
        </div>
    );
};
