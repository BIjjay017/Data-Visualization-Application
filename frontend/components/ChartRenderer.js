import { LineChart, Line, BarChart, Bar, ScatterChart, Scatter, PieChart, Pie, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell, AreaChart, Area, ComposedChart, ReferenceLine } from 'recharts';

const COLORS = ['#8b5cf6', '#ec4899', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#6366f1', '#14b8a6', '#f97316', '#06b6d4'];

// Color scale for heatmap
const getHeatmapColor = (value) => {
    // value ranges from -1 to 1 for correlation
    if (value >= 0.7) return '#22c55e';
    if (value >= 0.4) return '#84cc16';
    if (value >= 0.1) return '#fbbf24';
    if (value >= -0.1) return '#f3f4f6';
    if (value >= -0.4) return '#fb923c';
    if (value >= -0.7) return '#f87171';
    return '#ef4444';
};

export default function ChartRenderer({ chart, data }) {
    const { type, x, y, title, data: customData, statistics, correlation, stackCategories } = chart;

    // Use custom data (pre-aggregated/binned from backend) if available
    const chartData = customData || ((() => {
        if (type === 'bar' && !customData) {
            const aggregated = {};
            data.forEach(row => {
                const key = row[x];
                if (!aggregated[key]) {
                    aggregated[key] = 0;
                }
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
        return data;
    })());

    const renderChart = () => {
        switch (type) {
            case 'line':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey={x} stroke="#9ca3af" fontSize={12} tickFormatter={(val) => val?.toString().substring(0, 10)} />
                            <YAxis stroke="#9ca3af" fontSize={12} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px',
                                    color: '#fff'
                                }}
                            />
                            <Legend />
                            <Line type="monotone" dataKey={y} stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6', r: 2 }} activeDot={{ r: 5 }} />
                        </LineChart>
                    </ResponsiveContainer>
                );

            case 'area':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={chartData}>
                            <defs>
                                <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey={x} stroke="#9ca3af" fontSize={12} tickFormatter={(val) => val?.toString().substring(0, 10)} />
                            <YAxis stroke="#9ca3af" fontSize={12} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px',
                                    color: '#fff'
                                }}
                            />
                            <Legend />
                            <Area type="monotone" dataKey={y} stroke="#8b5cf6" fillOpacity={1} fill="url(#colorGradient)" />
                        </AreaChart>
                    </ResponsiveContainer>
                );

            case 'bar':
            case 'histogram':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey={x} stroke="#9ca3af" fontSize={11} angle={-45} textAnchor="end" height={80} interval={0} />
                            <YAxis stroke="#9ca3af" fontSize={12} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px',
                                    color: '#fff'
                                }}
                            />
                            <Legend />
                            <Bar dataKey={y} fill="#8b5cf6" name={y === 'count' ? 'Count' : y} radius={[4, 4, 0, 0]}>
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Bar>
                            {statistics && (
                                <ReferenceLine y={statistics.mean} stroke="#f59e0b" strokeDasharray="5 5" label={{ value: `Mean: ${statistics.mean}`, fill: '#f59e0b', fontSize: 10 }} />
                            )}
                        </BarChart>
                    </ResponsiveContainer>
                );

            case 'horizontalBar':
                return (
                    <ResponsiveContainer width="100%" height={Math.max(300, chartData.length * 35)}>
                        <BarChart data={chartData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis type="number" stroke="#9ca3af" fontSize={12} />
                            <YAxis dataKey={y} type="category" stroke="#9ca3af" fontSize={11} width={120} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px',
                                    color: '#fff'
                                }}
                            />
                            <Legend />
                            <Bar dataKey={x} fill="#8b5cf6" name="Count" radius={[0, 4, 4, 0]}>
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                );

            case 'stackedBar':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey={x} stroke="#9ca3af" fontSize={11} />
                            <YAxis stroke="#9ca3af" fontSize={12} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px',
                                    color: '#fff'
                                }}
                            />
                            <Legend />
                            {stackCategories && stackCategories.map((cat, idx) => (
                                <Bar key={cat} dataKey={cat} stackId="a" fill={COLORS[idx % COLORS.length]} />
                            ))}
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
                                dataKey={y}
                                nameKey={x}
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

            case 'donut':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={chartData}
                                cx="50%"
                                cy="50%"
                                labelLine={true}
                                label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                                innerRadius={60}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey={y}
                                nameKey={x}
                                paddingAngle={2}
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
                            <XAxis type="number" dataKey={x} name={x} stroke="#9ca3af" fontSize={12} />
                            <YAxis type="number" dataKey={y} name={y} stroke="#9ca3af" fontSize={12} />
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
                const columns = chart.columns || [];
                const cellSize = Math.min(50, 300 / columns.length);
                return (
                    <div style={{ padding: '20px', overflowX: 'auto' }}>
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: `80px repeat(${columns.length}, ${cellSize}px)`,
                            gap: '2px',
                            fontSize: '10px'
                        }}>
                            {/* Header row */}
                            <div></div>
                            {columns.map((col, idx) => (
                                <div key={`header-${idx}`} style={{
                                    transform: 'rotate(-45deg)',
                                    transformOrigin: 'left bottom',
                                    whiteSpace: 'nowrap',
                                    color: '#9ca3af',
                                    height: '60px',
                                    display: 'flex',
                                    alignItems: 'flex-end'
                                }}>
                                    {col.substring(0, 10)}
                                </div>
                            ))}
                            {/* Data rows */}
                            {columns.map((rowCol, rowIdx) => (
                                <>
                                    <div key={`row-${rowIdx}`} style={{
                                        color: '#9ca3af',
                                        display: 'flex',
                                        alignItems: 'center',
                                        paddingRight: '5px',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis'
                                    }}>
                                        {rowCol.substring(0, 10)}
                                    </div>
                                    {columns.map((colCol, colIdx) => {
                                        const cellData = chartData.find(d => d.x === colCol && d.y === rowCol);
                                        const value = cellData?.value || 0;
                                        return (
                                            <div
                                                key={`cell-${rowIdx}-${colIdx}`}
                                                style={{
                                                    width: cellSize,
                                                    height: cellSize,
                                                    backgroundColor: getHeatmapColor(value),
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    color: Math.abs(value) > 0.5 ? '#fff' : '#374151',
                                                    fontWeight: '600',
                                                    borderRadius: '2px',
                                                    cursor: 'pointer'
                                                }}
                                                title={`${rowCol} vs ${colCol}: ${value}`}
                                            >
                                                {value.toFixed(2)}
                                            </div>
                                        );
                                    })}
                                </>
                            ))}
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginTop: '15px', fontSize: '11px', color: '#9ca3af' }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <span style={{ width: 12, height: 12, backgroundColor: '#ef4444', borderRadius: 2 }}></span> -1
                            </span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <span style={{ width: 12, height: 12, backgroundColor: '#f3f4f6', borderRadius: 2 }}></span> 0
                            </span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <span style={{ width: 12, height: 12, backgroundColor: '#22c55e', borderRadius: 2 }}></span> +1
                            </span>
                        </div>
                    </div>
                );

            case 'boxPlot':
                const boxData = chartData[0];
                if (!boxData) return <div>No data available</div>;

                // Prepare data for Recharts - we'll use a Bar for the IQR (Q1 to Q3)
                // and ReferenceLines for whiskers and median.
                const boxPlotData = [{
                    name: boxData.name || 'Dataset',
                    q1: boxData.q1,
                    q3: boxData.q3,
                    median: boxData.median,
                    min: boxData.min,
                    max: boxData.max,
                    iqr: [boxData.q1, boxData.q3], // Recharts Bar can takes [start, end]
                    lowerWhisker: [boxData.min, boxData.q1],
                    upperWhisker: [boxData.q3, boxData.max]
                }];

                return (
                    <div style={{ padding: '20px' }}>
                        <ResponsiveContainer width="100%" height={300}>
                            <ComposedChart data={boxPlotData} layout="vertical" margin={{ top: 20, right: 30, left: 40, bottom: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                                <XAxis type="number" stroke="#9ca3af" domain={['auto', 'auto']} />
                                <YAxis dataKey="name" type="category" stroke="#9ca3af" />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#1f2937',
                                        border: '1px solid #374151',
                                        borderRadius: '8px',
                                        color: '#fff'
                                    }}
                                />
                                {/* Bottom Whisker */}
                                <Bar dataKey="lowerWhisker" fill="none" stroke="#9ca3af" strokeWidth={2} stackId="a" isAnimationActive={false} />
                                {/* Box (IQR) */}
                                <Bar dataKey="iqr" fill="#8b5cf6" radius={[4, 4, 4, 4]} opacity={0.8} />
                                {/* Top Whisker */}
                                <Bar dataKey="upperWhisker" fill="none" stroke="#9ca3af" strokeWidth={2} stackId="a" isAnimationActive={false} />

                                {/* Median Line */}
                                <ReferenceLine x={boxData.median} stroke="#10b981" strokeWidth={3} label={{ position: 'top', value: 'Median', fill: '#10b981', fontSize: 10 }} />

                                {/* Outliers as dots */}
                                {boxData.outliers && boxData.outliers.map((val, idx) => (
                                    <ReferenceLine key={idx} x={val} stroke="#f59e0b" strokeWidth={1} strokeDasharray="3 3" />
                                ))}
                            </ComposedChart>
                        </ResponsiveContainer>
                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-around',
                            padding: '15px',
                            backgroundColor: 'rgba(31, 41, 55, 0.5)',
                            borderRadius: '12px',
                            border: '1px solid #374151',
                            marginTop: '20px',
                            flexWrap: 'wrap',
                            gap: '10px'
                        }}>
                            <div style={{ textAlign: 'center', minWidth: '60px' }}>
                                <div style={{ color: '#9ca3af', fontSize: '11px', textTransform: 'uppercase' }}>Min</div>
                                <div style={{ color: '#fff', fontWeight: '700', fontSize: '1.1rem' }}>{boxData.min.toFixed(2)}</div>
                            </div>
                            <div style={{ textAlign: 'center', minWidth: '60px' }}>
                                <div style={{ color: '#9ca3af', fontSize: '11px', textTransform: 'uppercase' }}>Q1</div>
                                <div style={{ color: '#fff', fontWeight: '700', fontSize: '1.1rem' }}>{boxData.q1.toFixed(2)}</div>
                            </div>
                            <div style={{ textAlign: 'center', minWidth: '60px' }}>
                                <div style={{ color: '#10b981', fontSize: '11px', textTransform: 'uppercase' }}>Median</div>
                                <div style={{ color: '#10b981', fontWeight: '800', fontSize: '1.2rem' }}>{boxData.median.toFixed(2)}</div>
                            </div>
                            <div style={{ textAlign: 'center', minWidth: '60px' }}>
                                <div style={{ color: '#9ca3af', fontSize: '11px', textTransform: 'uppercase' }}>Q3</div>
                                <div style={{ color: '#fff', fontWeight: '700', fontSize: '1.1rem' }}>{boxData.q3.toFixed(2)}</div>
                            </div>
                            <div style={{ textAlign: 'center', minWidth: '60px' }}>
                                <div style={{ color: '#9ca3af', fontSize: '11px', textTransform: 'uppercase' }}>Max</div>
                                <div style={{ color: '#fff', fontWeight: '700', fontSize: '1.1rem' }}>{boxData.max.toFixed(2)}</div>
                            </div>
                            {boxData.outliers && boxData.outliers.length > 0 && (
                                <div style={{ textAlign: 'center', minWidth: '60px' }}>
                                    <div style={{ color: '#f59e0b', fontSize: '11px', textTransform: 'uppercase' }}>Outliers</div>
                                    <div style={{ color: '#f59e0b', fontWeight: '700', fontSize: '1.1rem' }}>{boxData.outliers.length}</div>
                                </div>
                            )}
                        </div>
                    </div>
                );

            default:
                return <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>Unsupported chart type: {type}</div>;
        }
    };

    return <div>{renderChart()}</div>;
}
