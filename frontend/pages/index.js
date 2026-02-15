import { useState } from 'react';
import Head from 'next/head';
import Upload from '../components/Upload';
import Dashboard from '../components/Dashboard';
import ThemeToggle from '../components/ThemeToggle';
import styles from '../styles/Home.module.css';

export default function Home() {
  const [analysisData, setAnalysisData] = useState(null);

  return (
    <div className={styles.container}>
      <Head>
        <title>Data Visualization App</title>
        <meta name="description" content="Smart Data Visualization Application" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <ThemeToggle />

      <main className={styles.main}>
        <h1 className={styles.title}>
          📊 Smart Data Visualization
        </h1>

        <p className={styles.description}>
          Upload your CSV file and get instant insights
        </p>

        {!analysisData ? (
          <Upload onAnalysisComplete={setAnalysisData} />
        ) : (
          <Dashboard data={analysisData} onReset={() => setAnalysisData(null)} />
        )}
      </main>
    </div>
  );
}
