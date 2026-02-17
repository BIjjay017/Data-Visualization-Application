import { motion } from 'framer-motion';
import ChartRenderer from './ChartRenderer';
import styles from '../styles/Dashboard.module.css';

export default function Dashboard({ data, onReset }) {
    const { summary, insights, recommended_charts, columns, cleaning_report, dataset_summary, chart_interpretations, conclusion } = data;

    // Extract key metrics from summary
    const getKeyMetrics = () => {
        const metrics = [];
        if (summary.total_rows) {
            metrics.push({ label: 'Total Rows', value: summary.total_rows });
        }

        // Get first few numeric summaries
        const numericKeys = Object.keys(summary).filter(k => k.includes('_sum'));
        numericKeys.slice(0, 3).forEach(key => {
            const field = key.replace('_sum', '');
            metrics.push({
                label: `Total ${field}`,
                value: summary[key].toLocaleString()
            });
        });

        return metrics;
    };

    const metrics = getKeyMetrics();

    return (
        <motion.div
            className={styles.dashboard}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
        >
            <div className={styles.header}>
                <h2>Analysis Results</h2>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                        onClick={() => window.open('http://localhost:8000/download_report', '_blank')}
                        className={styles.resetButton}
                        style={{ backgroundColor: '#10b981' }}
                    >
                        Export Report (PDF)
                    </button>
                    <button onClick={onReset} className={styles.resetButton}>
                        Upload New File
                    </button>
                </div>
            </div>

            {/* Data Cleaning Report */}
            {cleaning_report && cleaning_report.summary && (
                <motion.div
                    className={styles.cleaningReport}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                >
                    <h3>🧹 Data Cleaning Report</h3>
                    <div className={styles.cleaningSummary}>
                        <div className={styles.cleaningStat}>
                            <span className={styles.statLabel}>Original Columns:</span>
                            <span className={styles.statValue}>{cleaning_report.summary.original_columns}</span>
                        </div>
                        <div className={styles.cleaningStat}>
                            <span className={styles.statLabel}>Cleaned Columns:</span>
                            <span className={styles.statValue}>{cleaning_report.summary.cleaned_columns}</span>
                        </div>
                        <div className={styles.cleaningStat}>
                            <span className={styles.statLabel}>Columns Imputed:</span>
                            <span className={styles.statValue}>{cleaning_report.summary.columns_imputed}</span>
                        </div>
                        {cleaning_report.summary.columns_dropped > 0 && (
                            <div className={styles.cleaningStat}>
                                <span className={styles.statLabel}>Columns Dropped:</span>
                                <span className={styles.statValue} style={{ color: '#ef4444' }}>
                                    {cleaning_report.summary.columns_dropped}
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Warnings */}
                    {cleaning_report.warnings && cleaning_report.warnings.length > 0 && (
                        <div className={styles.warningsSection}>
                            <h4>⚠️ Warnings</h4>
                            <ul className={styles.warningsList}>
                                {cleaning_report.warnings.map((warning, idx) => (
                                    <li key={idx}>
                                        <strong>{warning.column}:</strong> {warning.message}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Detailed Cleaning Actions */}
                    {cleaning_report.cleaning_report && Object.keys(cleaning_report.cleaning_report).length > 0 && (
                        <details className={styles.detailsSection}>
                            <summary>View Detailed Cleaning Actions</summary>
                            <div className={styles.cleaningDetails}>
                                {Object.entries(cleaning_report.cleaning_report).map(([col, details], idx) => (
                                    <div key={idx} className={styles.columnDetail}>
                                        <div className={styles.columnName}>{col}</div>
                                        <div className={styles.columnInfo}>
                                            <span className={styles.badge}>{details.column_type}</span>
                                            <span className={styles.badge}>
                                                {details.missing_percent.toFixed(1)}% missing
                                            </span>
                                            <span className={`${styles.badge} ${styles[details.action]}`}>
                                                {details.action}
                                            </span>
                                        </div>
                                        <div className={styles.strategy}>{details.strategy}</div>
                                    </div>
                                ))}
                            </div>
                        </details>
                    )}
                </motion.div>
            )}

            {/* Dataset Summary */}
            {dataset_summary && dataset_summary.overview && (
                <motion.div
                    className={styles.datasetSummary}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <h3>📋 Dataset Summary</h3>
                    <div className={styles.summaryOverview}>
                        <div className={styles.summaryItem}>
                            <span className={styles.summaryLabel}>Total Records:</span>
                            <span className={styles.summaryValue}>{dataset_summary.overview.total_rows}</span>
                        </div>
                        <div className={styles.summaryItem}>
                            <span className={styles.summaryLabel}>Total Columns:</span>
                            <span className={styles.summaryValue}>{dataset_summary.overview.total_columns}</span>
                        </div>
                        <div className={styles.summaryItem}>
                            <span className={styles.summaryLabel}>Numeric Columns:</span>
                            <span className={styles.summaryValue}>{dataset_summary.overview.numeric_columns}</span>
                        </div>
                        <div className={styles.summaryItem}>
                            <span className={styles.summaryLabel}>Categorical Columns:</span>
                            <span className={styles.summaryValue}>{dataset_summary.overview.categorical_columns}</span>
                        </div>
                    </div>

                    <details className={styles.columnDetailsSection}>
                        <summary>View Detailed Column Information</summary>
                        <div className={styles.columnDetailsGrid}>
                            {dataset_summary.column_details && dataset_summary.column_details.map((col, idx) => (
                                <div key={idx} className={styles.columnDetailCard}>
                                    <div className={styles.columnDetailName}>{col.name}</div>
                                    <div className={styles.columnDetailType}>{col.type}</div>
                                    <div className={styles.columnDetailStats}>
                                        <span>Unique: {col.unique_values}</span>
                                        {col.type === 'numeric' && (
                                            <>
                                                <span>Range: {col.min?.toFixed(2)} - {col.max?.toFixed(2)}</span>
                                                <span>Mean: {col.mean?.toFixed(2)}</span>
                                            </>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </details>
                </motion.div>
            )}

            {/* Summary Cards */}
            <div className={styles.metricsGrid}>
                {metrics.map((metric, idx) => (
                    <motion.div
                        key={idx}
                        className={styles.metricCard}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                    >
                        <div className={styles.metricLabel}>{metric.label}</div>
                        <div className={styles.metricValue}>{metric.value}</div>
                    </motion.div>
                ))}
            </div>

            {/* Insights Panel */}
            {insights && insights.length > 0 && (
                <motion.div
                    className={styles.insightsPanel}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    <h3>🧠 Key Insights</h3>
                    <ul className={styles.insightsList}>
                        {insights.map((insight, idx) => (
                            <motion.li
                                key={idx}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.4 + idx * 0.1 }}
                            >
                                {insight}
                            </motion.li>
                        ))}
                    </ul>
                </motion.div>
            )}

            {/* Charts */}
            <div className={styles.chartsGrid}>
                {recommended_charts && recommended_charts.map((chart, idx) => (
                    <motion.div
                        key={idx}
                        className={styles.chartCard}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.5 + idx * 0.1 }}
                    >
                        <h4>{chart.title}</h4>
                        <ChartRenderer chart={chart} data={data.data} />

                        {/* Chart Interpretation */}
                        {chart_interpretations && chart_interpretations.find(ci => ci.chart_title === chart.title) && (
                            <div className={styles.chartInterpretation}>
                                <p>{chart_interpretations.find(ci => ci.chart_title === chart.title).interpretation}</p>
                            </div>
                        )}
                    </motion.div>
                ))}
            </div>

            {/* Conclusion Section */}
            {conclusion && (
                <motion.div
                    className={styles.conclusionSection}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.8 }}
                >
                    <h3>📊 {conclusion.title || 'Conclusion'}</h3>
                    <p className={styles.conclusionSummary}>{conclusion.summary}</p>

                    {conclusion.key_findings && conclusion.key_findings.length > 0 && (
                        <div className={styles.keyFindings}>
                            <h4>Key Findings:</h4>
                            <ul>
                                {conclusion.key_findings.map((finding, idx) => (
                                    <li key={idx}>{finding}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {conclusion.data_characteristics && conclusion.data_characteristics.length > 0 && (
                        <div className={styles.dataCharacteristics}>
                            <h4>Data Characteristics:</h4>
                            <ul>
                                {conclusion.data_characteristics.map((char, idx) => (
                                    <li key={idx}>{char}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </motion.div>
            )}
        </motion.div>
    );
}
