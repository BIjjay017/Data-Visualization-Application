import { LineChart, Line, BarChart, Bar, ScatterChart, Scatter, PieChart, Pie, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

const COLORS = ['#8b5cf6', '#ec4899', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#6366f1', '#14b8a6'];

export default function ChartRenderer({ chart, data }) {
    const { type, x, y, title, data: customData } = chart;

    // Use custom data (pre-aggregated/binned from backend) if available, otherwise use raw data
    // For histograms and pre-aggregated bars, customData is essential.
    const chartData = customData || ((() => {
        // Fallback: Client-side aggregation (only if no customData provided)
        if (type === 'bar' && !customData) {
            const aggregated = {};
            data.forEach(row => {
                const key = row[x];
                if (!aggregated[key]) {
                    aggregated[key] = 0;
                }
                // If y is "count", just count occurences
                if (y === 'count') {
                    aggregated[key] += 1;
                } else {
                    aggregated[key] += parseFloat(row[y]) || 0;
                }
            });

            return Object.entries(aggregated).map(([key, value]) => ({
                [x]: key,
                [y]: value
            }));
        }
        return data; // For scatter/line with raw data
    })());

    const renderChart = () => {
        switch (type) {
            case 'line':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey={x} stroke="#9ca3af" />
                            <YAxis stroke="#9ca3af" />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px'
                                }}
                            />
                            <Legend />
                            <Line type="monotone" dataKey={y} stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6', r: 2 }} activeDot={{ r: 5 }} />
                        </LineChart>
                    </ResponsiveContainer>
                );

            case 'bar':
            case 'histogram': // Histograms are just bar charts with pre-binned data
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey={x} stroke="#9ca3af" />
                            <YAxis stroke="#9ca3af" />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px',
                                    color: '#fff'
                                }}
                            />
                            <Legend />
                            <Bar dataKey={y} fill="#8b5cf6" name={y === 'count' ? 'Count' : y}>
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                );

            case 'pie':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={chartData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey={y} // Should be 'count' usually
                                nameKey={x} // The category column
                            >
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px',
                                    color: '#fff'
                                }}
                            />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                );

            case 'scatter':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <ScatterChart>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis type="number" dataKey={x} name={x} stroke="#9ca3af" />
                            <YAxis type="number" dataKey={y} name={y} stroke="#9ca3af" />
                            <Tooltip
                                cursor={{ strokeDasharray: '3 3' }}
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px',
                                    color: '#fff'
                                }}
                            />
                            <Legend />
                            <Scatter name={`${x} vs ${y}`} data={chartData} fill="#8b5cf6" />
                        </ScatterChart>
                    </ResponsiveContainer>
                );

            case 'heatmap':
                return (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>
                        Heatmap visualization coming soon
                    </div>
                );

            default:
                return <div>Unsupported chart type: {type}</div>;
        }
    };

    return <div>{renderChart()}</div>;
}
