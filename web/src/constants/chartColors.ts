/**
 * Unified Semantic Color Palette for Analytics Dashboards
 * ADR Approved: January 13, 2026
 * 
 * Single source of truth for chart colors across all 4 modules.
 * Adheres to modern analytics best practices with consistent meaning.
 */

/** Semantic palette colors */
export const SEMANTIC_COLORS = {
  BLUE: '#3b82f6',      // Standard/Production/Class B/Primary data
  RED: '#ef4444',       // Alert/Late/Class A/Risk/Critical
  GREEN: '#22c55e',     // Success/On-Time/Positive
  AMBER: '#f59e0b',     // Warning/Transit/Delivery/Pending
  SLATE: '#64748b',     // Neutral/Prep/Class C/Secondary/Inactive
};

/** ABC Classification colors - Inventory Module */
export const COLORS_ABC = {
  A: SEMANTIC_COLORS.RED,     // Fast-moving (top 20%)
  B: SEMANTIC_COLORS.BLUE,    // Medium velocity (30%)
  C: SEMANTIC_COLORS.SLATE,   // Slow/Dead (50%)
};

/** Status colors - Production/Lead Time Modules */
export const COLORS_STATUS = {
  CREATED: SEMANTIC_COLORS.SLATE,    // Status: CRTD
  RELEASED: SEMANTIC_COLORS.BLUE,    // Status: REL
  IN_PROGRESS: SEMANTIC_COLORS.AMBER, // Status: CNF/Partial
  COMPLETED: SEMANTIC_COLORS.GREEN,  // Status: DLV/TECO
  DELAYED: SEMANTIC_COLORS.RED,      // Late/Overdue
};

/** Lead Time Stage colors - Strict ADR adherence */
export const COLORS_LEADTIME_STAGES = {
  PREP: SEMANTIC_COLORS.SLATE,       // Preparation time
  PRODUCTION: SEMANTIC_COLORS.BLUE,  // Production time
  DELIVERY: SEMANTIC_COLORS.AMBER,   // Delivery/Transit time
};

/** Chart color arrays for multi-series */
export const COLOR_ARRAYS = {
  // For funnel/step charts (progression from start to end)
  FUNNEL: [
    SEMANTIC_COLORS.SLATE,  // Created
    SEMANTIC_COLORS.BLUE,   // Released
    SEMANTIC_COLORS.AMBER,  // In Progress
    SEMANTIC_COLORS.GREEN,  // Completed
  ],
  
  // For generic multi-category charts
  MULTI_CATEGORY: [
    SEMANTIC_COLORS.BLUE,
    SEMANTIC_COLORS.AMBER,
    SEMANTIC_COLORS.GREEN,
    SEMANTIC_COLORS.RED,
    SEMANTIC_COLORS.SLATE,
  ],
};

/** Recharts custom tooltip styling */
export const TOOLTIP_STYLES = {
  contentStyle: {
    backgroundColor: '#ffffff',
    border: `1px solid ${SEMANTIC_COLORS.SLATE}`,
    borderRadius: '4px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
};

/** Common Recharts responsive container config */
export const RECHARTS_DEFAULTS = {
  height: 350,
  margin: { top: 5, right: 30, left: 0, bottom: 5 },
};

/** Division Names Mapping - Business Logic */
export const DIVISION_NAMES: Record<string, string> = {
  '11': 'Industry',
  '13': 'Retail',
  '15': 'Project',
};

/**
 * Get human-readable division name from code
 * @param code Division code (string or number)
 * @returns Display name or fallback format
 */
export const getDivisionName = (code: string | number): string => {
  const codeStr = String(code);
  return DIVISION_NAMES[codeStr] || `Division ${codeStr}`;
};
