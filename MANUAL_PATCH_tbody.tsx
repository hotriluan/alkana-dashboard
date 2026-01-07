/* 
 * MANUAL PATCH FOR LeadTimeDashboard.tsx
 * Replace the entire <tbody> section (lines 405-431) with this code:
 */

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
