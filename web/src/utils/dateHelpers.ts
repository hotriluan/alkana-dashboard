/**
 * Date utility functions for dashboard default date ranges
 */

/**
 * Get the first day of the current month in YYYY-MM-DD format
 * @returns First day of current month
 */
export const getFirstDayOfMonth = (): string => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}-01`;
};

/**
 * Get today's date in YYYY-MM-DD format
 * @returns Today's date
 */
export const getToday = (): string => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * Get default date range for dashboards (first day of month to today)
 * DEPRECATED - Use getSmartDateRange() instead for better UX
 * @returns Object with startDate and endDate
 */
export const getDefaultDateRange = () => {
  return {
    startDate: getFirstDayOfMonth(),
    endDate: getToday()
  };
};

/**
 * Get smart date range with fallback to latest available data
 * Fetches from backend API to determine if current month has data
 * @returns Promise with startDate and endDate
 */
export const getSmartDateRange = async (): Promise<{ startDate: string; endDate: string }> => {
  try {
    const API_BASE_URL = import.meta.env.VITE_API_URL || window.location.origin;
    const response = await fetch(`${API_BASE_URL}/api/v1/dashboards/executive/latest-data-date`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch latest data date');
    }
    
    const data = await response.json();
    return {
      startDate: data.recommended_start_date,
      endDate: data.recommended_end_date
    };
  } catch (error) {
    console.warn('Failed to get smart date range, falling back to current month:', error);
    // Fallback to current month
    return {
      startDate: getFirstDayOfMonth(),
      endDate: getToday()
    };
  }};