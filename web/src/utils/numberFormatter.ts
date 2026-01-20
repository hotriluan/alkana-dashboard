/**
 * Number formatting utilities for charts and displays (legacy names)
 * Delegates to standardized helpers in `utils/formatters.ts`.
 */
import { formatCurrencyCompact, formatCurrencyFull, formatInteger } from './formatters';

/**
 * Format large numbers to readable format (1B, 500M, 100K, etc)
 * Used for chart axes and displays with large values
 */
// Deprecated: use `formatCurrencyCompact` directly
export const formatLargeNumber = (value: number): string => formatCurrencyCompact(value);

/**
 * Format number as Vietnamese currency (VND)
 * Displays full value with locale formatting
 */
// Deprecated: use `formatCurrencyFull` directly
export const formatCurrency = (value: number): string => formatCurrencyFull(value);

/**
 * Format number with locale-specific thousands separator
 */
// Deprecated: use `formatInteger` for counts
export const formatNumber = (value: number): string => formatInteger(value);
