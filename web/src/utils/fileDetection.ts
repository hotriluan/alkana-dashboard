/**
 * File Detection Engine - Smart Upload Intelligence
 * 
 * V4: Centralized Smart Ingestion
 * Auto-detects file types based on column signatures using xlsx library
 */
import * as XLSX from 'xlsx';

export interface DetectionRule {
  type: string;
  signature: string[];
  label: string;
  requiresPeriod: boolean;
  endpoint: string;
}

export const DETECTION_RULES: DetectionRule[] = [
  {
    type: 'ZRPP062',
    signature: ['MRP controller', 'Product Group 1', 'Product Group 2', 'Process Order', 'Batch'],
    label: 'Production Yield Result',
    requiresPeriod: true,  // ⚠️ SIGNAL: Needs Month/Year Input
    endpoint: '/api/v3/yield/upload'
  },
  {
    type: 'ZRSD006',
    signature: ['Material Code', 'PH 1', 'PH 2', 'PH 3'],  // Updated: Use Material Code instead of Product hierarchy
    label: 'Product Hierarchy Master',
    requiresPeriod: false,
    endpoint: '/api/v3/yield/upload-master-data'
  },
  {
    type: 'COOISPI',
    signature: ['Plant', 'Sales Order', 'Order', 'Material Number'],  // Updated: Actual columns
    label: 'Production Orders',
    requiresPeriod: false,
    endpoint: '/api/v1/upload'
  },
  {
    type: 'MB51',
    signature: ['Posting Date', 'Movement Type', 'Material Document', 'Qty in Un. of Entry', 'Storage Location'],
    label: 'Material Movements',
    requiresPeriod: false,
    endpoint: '/api/v1/upload'
  },
  {
    type: 'ZRMM024',
    signature: ['Purch. Order', 'Item', 'Purch. Date', 'Suppl. Plant', 'Dest. Plant'],  // Updated: Use unique purchasing columns
    label: 'MRP Controller',
    requiresPeriod: false,
    endpoint: '/api/v1/upload'
  },
  {
    type: 'ZRSD002',
    signature: ['Billing Document', 'Net Value', 'Billing Date', 'Material'],  // Updated: Use actual column names
    label: 'Sales Orders',
    requiresPeriod: false,
    endpoint: '/api/v1/upload'
  },
  {
    type: 'ZRSD004',
    signature: ['Delivery Date', 'Actual GI Date', 'Delivery', 'SO Reference'],
    label: 'Delivery',
    requiresPeriod: false,
    endpoint: '/api/v1/upload'
  },
  {
    type: 'ZRFI005',
    signature: ['Company Code', 'Profit Center', 'Customer Code', 'Target 1-30 Days'],
    label: 'AR Aging Report',
    requiresPeriod: false,
    endpoint: '/api/v1/upload'
  },
  {
    type: 'TARGET',
    signature: ['Salesman Name', 'Semester', 'Year', 'Target'],  // Updated: Actual columns
    label: 'Sales Targets',
    requiresPeriod: false,
    endpoint: '/api/v1/upload'
  },
];

/**
 * Detect file type by reading Excel column headers
 * @param file Excel file to analyze
 * @returns Detected rule or null
 */
export async function detectFileType(file: File): Promise<DetectionRule | null> {
  try {
    // Read Excel file using xlsx library
    const arrayBuffer = await file.arrayBuffer();
    const workbook = XLSX.read(arrayBuffer, { type: 'array', sheetRows: 1 });
    
    // Get first sheet
    const firstSheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[firstSheetName];
    
    // Convert first row to array of column names
    const range = XLSX.utils.decode_range(worksheet['!ref'] || 'A1');
    const headers: string[] = [];
    
    for (let col = range.s.c; col <= range.e.c; col++) {
      const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col });
      const cell = worksheet[cellAddress];
      if (cell && cell.v) {
        headers.push(String(cell.v));
      }
    }
    
    console.log('🔍 Excel headers detected:', headers.slice(0, 10).join(', '));
    
    // Find matching rule
    for (const rule of DETECTION_RULES) {
      const matchCount = rule.signature.filter(sig => {
        const matches = headers.some(header => header.includes(sig));
        console.log(`  - Checking "${sig}": ${matches ? '✓' : '✗'}`);
        return matches;
      }).length;
      
      const threshold = Math.ceil(rule.signature.length * 0.6);
      console.log(`  Rule ${rule.type}: ${matchCount}/${rule.signature.length} matches (threshold: ${threshold})`);
      
      // If majority of signatures match, consider it detected
      if (matchCount >= threshold) {
        console.log(`✅ Detected as ${rule.type}`);
        return rule;
      }
    }
    
    console.warn('⚠️ No file type detected');
    return null;
  } catch (error) {
    console.error('File detection error:', error);
    return null;
  }
}

/**
 * Get file type label from filename pattern (fallback)
 */
export function guessFromFilename(filename: string): string | null {
  const lower = filename.toLowerCase();
  
  if (lower.includes('zrpp062')) return 'ZRPP062';
  if (lower.includes('zrsd006')) return 'ZRSD006';
  if (lower.includes('cooispi')) return 'COOISPI';
  if (lower.includes('mb51')) return 'MB51';
  if (lower.includes('zrmm024')) return 'ZRMM024';
  if (lower.includes('zrsd002')) return 'ZRSD002';
  if (lower.includes('zrsd004')) return 'ZRSD004';
  if (lower.includes('zrfi005')) return 'ZRFI005';
  if (lower.includes('target')) return 'TARGET';
  
  return null;
}
