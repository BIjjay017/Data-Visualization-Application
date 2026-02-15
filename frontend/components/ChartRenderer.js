import { LineChart, Line, BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

const COLORS = ['#8b5cf6', '#ec4899', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

export default function ChartRenderer({ chart, data }) {
    const { type, x, y, title, columns } = chart;

    // Prepare data based on chart type
    const prepareData = () => {
        if (type === 'line' || type === 'scatter') {
            return data;
        }

        if (type === 'bar') {
            // Aggregate data by x column
            const aggregated = {};
            data.forEach(row => {
                const key = row[x];
                if (!aggregated[key]) {
                    aggregated[key] = 0;
                }
                aggregated[key] += parseFloat(row[y]) || 0;
            });

            return Object.entries(aggregated).map(([key, value]) => ({
                [x]: key,
                [y]: value
            }));
        }

        if (type === 'heatmap') {
            // For heatmap, we'd need correlation matrix data
            // This is a placeholder - backend should send correlation matrix
            return [];
        }

        return data;
    };

    const chartData = prepareData();

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
                            <Line type="monotone" dataKey={y} stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6' }} />
                        </LineChart>
                    </ResponsiveContainer>
                );

            case 'bar':
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
                                    borderRadius: '8px'
                                }}
                            />
                            <Legend />
                            <Bar dataKey={y} fill="#8b5cf6">
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                );

            case 'scatter':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <ScatterChart>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey={x} stroke="#9ca3af" />
                            <YAxis dataKey={y} stroke="#9ca3af" />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px'
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
                return <div>Unsupported chart type</div>;
        }
    };

    return <div>{renderChart()}</div>;
}
