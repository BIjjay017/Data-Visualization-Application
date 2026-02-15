import { useTheme } from '../context/ThemeContext';
import styles from '../styles/ThemeToggle.module.css';

export default function ThemeToggle() {
    const { isDark, toggleTheme } = useTheme();

    return (
        <button
            onClick={toggleTheme}
            className={styles.toggleButton}
            aria-label="Toggle theme"
        >
            {isDark ? (
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M10 2V4M10 16V18M4 10H2M18 10H16M15.657 15.657L14.243 14.243M15.657 4.343L14.243 5.757M4.343 15.657L5.757 14.243M4.343 4.343L5.757 5.757" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    <circle cx="10" cy="10" r="3" stroke="currentColor" strokeWidth="2" />
                </svg>
            ) : (
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
            )}
        </button>
    );
}
