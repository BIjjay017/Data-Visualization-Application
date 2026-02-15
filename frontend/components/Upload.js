import { useState } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import styles from '../styles/Upload.module.css';

export default function Upload({ onAnalysisComplete }) {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isDragging, setIsDragging] = useState(false);

    const ACCEPTED_FILE_TYPES = {
        'text/csv': ['.csv'],
        'application/vnd.ms-excel': ['.xls'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
        'application/pdf': ['.pdf'],
        'application/msword': ['.doc'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    };

    const validateFile = (selectedFile) => {
        if (!selectedFile) return false;

        const fileExtension = '.' + selectedFile.name.split('.').pop().toLowerCase();
        const validExtensions = Object.values(ACCEPTED_FILE_TYPES).flat();

        if (!validExtensions.includes(fileExtension)) {
            setError(`Invalid file type. Please upload: ${validExtensions.join(', ')}`);
            return false;
        }

        // Check file size (max 50MB)
        const maxSize = 50 * 1024 * 1024; // 50MB
        if (selectedFile.size > maxSize) {
            setError('File size exceeds 50MB limit');
            return false;
        }

        return true;
    };

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile && validateFile(selectedFile)) {
            setFile(selectedFile);
            setError(null);
        } else if (selectedFile) {
            setFile(null);
        }
    };

    const handleDragEnter = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile && validateFile(droppedFile)) {
            setFile(droppedFile);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setError('Please select a file first');
            return;
        }

        setLoading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post('http://localhost:8000/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            onAnalysisComplete(response.data);
        } catch (err) {
            setError('Failed to analyze file. Please ensure the backend is running and supports this file type.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    const getFileIcon = (fileName) => {
        const extension = fileName.split('.').pop().toLowerCase();
        const icons = {
            csv: '📊',
            xls: '📗',
            xlsx: '📗',
            pdf: '📄',
            doc: '📝',
            docx: '📝'
        };
        return icons[extension] || '📎';
    };

    return (
        <motion.div
            className={styles.uploadContainer}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
        >
            <div
                className={`${styles.uploadBox} ${isDragging ? styles.dragging : ''}`}
                onDragEnter={handleDragEnter}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                <div className={styles.uploadContent}>
                    <div className={styles.iconWrapper}>
                        <svg className={styles.uploadIcon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                    </div>

                    <h2 className={styles.uploadTitle}>Upload Your Data File</h2>
                    <p className={styles.uploadSubtext}>
                        Drag and drop your file here, or click to browse
                    </p>

                    <div className={styles.supportedFormats}>
                        <span className={styles.formatLabel}>Supported formats:</span>
                        <div className={styles.formatBadges}>
                            <span className={styles.formatBadge}>CSV</span>
                            <span className={styles.formatBadge}>XLSX</span>
                            <span className={styles.formatBadge}>XLS</span>
                            <span className={styles.formatBadge}>PDF</span>
                            <span className={styles.formatBadge}>DOC</span>
                            <span className={styles.formatBadge}>DOCX</span>
                        </div>
                    </div>

                    <input
                        type="file"
                        accept=".csv,.xls,.xlsx,.pdf,.doc,.docx"
                        onChange={handleFileChange}
                        className={styles.fileInput}
                        id="file-upload"
                    />

                    <label htmlFor="file-upload" className={styles.browseButton}>
                        Browse Files
                    </label>

                    <AnimatePresence>
                        {file && (
                            <motion.div
                                className={styles.fileInfo}
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                            >
                                <div className={styles.fileDetails}>
                                    <span className={styles.fileIcon}>{getFileIcon(file.name)}</span>
                                    <div className={styles.fileText}>
                                        <span className={styles.fileName}>{file.name}</span>
                                        <span className={styles.fileSize}>{formatFileSize(file.size)}</span>
                                    </div>
                                    <button
                                        className={styles.removeButton}
                                        onClick={(e) => {
                                            e.preventDefault();
                                            setFile(null);
                                            setError(null);
                                        }}
                                    >
                                        ✕
                                    </button>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <button
                        onClick={handleUpload}
                        disabled={!file || loading}
                        className={styles.uploadButton}
                    >
                        {loading ? 'Analyzing...' : 'Analyze Data'}
                    </button>
                </div>

                {loading && (
                    <div className={styles.loadingContainer}>
                        <video
                            className={styles.loadingVideo}
                            autoPlay
                            loop
                            muted
                        >
                            <source src="/loading.webm" type="video/webm" />
                        </video>
                        <p className={styles.loadingText}>Processing your data...</p>
                    </div>
                )}

                {error && (
                    <motion.div
                        className={styles.error}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                    >
                        {error}
                    </motion.div>
                )}
            </div>
        </motion.div>
    );
}
