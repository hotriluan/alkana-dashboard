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
 * @returns Object with startDate and endDate
 */
export const getDefaultDateRange = () => {
  return {
    startDate: getFirstDayOfMonth(),
    endDate: getToday()
  };
};
