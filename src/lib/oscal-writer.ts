import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';
import { fetchControlDetails, type ControlDetail } from './catalog-fetcher.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export interface SSPOptions {
  baseline: 'low' | 'moderate' | 'high';
  systemName: string;
  includeControlDetails?: boolean;
}

export interface ControlBaseline {
  low: string[];
  moderate: string[];
  high: string[];
}

// NIST 800-53 Rev 5 baseline controls
const BASELINE_CONTROLS: ControlBaseline = {
  low: [
    'AC-1', 'AC-2', 'AC-3', 'AC-7', 'AC-8', 'AC-14', 'AC-17', 'AC-18', 'AC-19', 'AC-20', 'AC-22',
    'AT-1', 'AT-2', 'AT-3', 'AT-4',
    'AU-1', 'AU-2', 'AU-3', 'AU-4', 'AU-5', 'AU-6', 'AU-8', 'AU-9', 'AU-11', 'AU-12',
    'CA-1', 'CA-2', 'CA-3', 'CA-5', 'CA-6', 'CA-7', 'CA-9',
    'CM-1', 'CM-2', 'CM-4', 'CM-6', 'CM-7', 'CM-8', 'CM-10', 'CM-11',
    'CP-1', 'CP-2', 'CP-3', 'CP-4', 'CP-9', 'CP-10',
    'IA-1', 'IA-2', 'IA-4', 'IA-5', 'IA-6', 'IA-7', 'IA-8',
    'IR-1', 'IR-2', 'IR-4', 'IR-5', 'IR-6', 'IR-7', 'IR-8',
    'MA-1', 'MA-2', 'MA-4', 'MA-5',
    'MP-1', 'MP-2', 'MP-6', 'MP-7',
    'PE-1', 'PE-2', 'PE-3', 'PE-6', 'PE-8', 'PE-12', 'PE-13', 'PE-14', 'PE-15', 'PE-16',
    'PL-1', 'PL-2', 'PL-4', 'PL-10', 'PL-11',
    'PS-1', 'PS-2', 'PS-3', 'PS-4', 'PS-5', 'PS-6', 'PS-7', 'PS-8',
    'RA-1', 'RA-2', 'RA-3', 'RA-5', 'RA-7',
    'SA-1', 'SA-2', 'SA-3', 'SA-4', 'SA-5', 'SA-9', 'SA-22',
    'SC-1', 'SC-5', 'SC-7', 'SC-12', 'SC-13', 'SC-15', 'SC-20', 'SC-21', 'SC-22', 'SC-39',
    'SI-1', 'SI-2', 'SI-3', 'SI-4', 'SI-5', 'SI-12'
  ],
  moderate: [],
  high: []
};

// Moderate includes all low controls plus additional ones
BASELINE_CONTROLS.moderate = [
  ...BASELINE_CONTROLS.low,
  'AC-4', 'AC-5', 'AC-6', 'AC-11', 'AC-12', 'AC-17(1)', 'AC-20(1)', 'AC-20(2)',
  'AT-2(2)', 'AT-3(3)', 'AT-3(5)',
  'AU-3(1)', 'AU-4(1)', 'AU-6(1)', 'AU-6(3)', 'AU-7', 'AU-7(1)', 'AU-9(4)', 'AU-11(1)', 'AU-12(1)', 'AU-12(3)',
  'CA-2(1)', 'CA-2(2)', 'CA-3(5)', 'CA-7(1)', 'CA-8', 'CA-8(1)',
  'CM-2(1)', 'CM-2(2)', 'CM-2(3)', 'CM-3', 'CM-3(2)', 'CM-5', 'CM-6(1)', 'CM-7(1)', 'CM-7(2)', 'CM-7(5)', 'CM-8(1)', 'CM-8(3)', 'CM-9', 'CM-11(1)',
  'CP-2(1)', 'CP-2(3)', 'CP-2(8)', 'CP-6', 'CP-7', 'CP-7(1)', 'CP-7(2)', 'CP-7(3)', 'CP-8', 'CP-8(1)', 'CP-9(1)',
  'IA-2(1)', 'IA-2(2)', 'IA-2(8)', 'IA-2(12)', 'IA-3', 'IA-5(1)', 'IA-8(1)', 'IA-8(2)', 'IA-8(4)',
  'IR-4(1)', 'IR-5(1)', 'IR-6(1)', 'IR-7(1)',
  'MA-3', 'MA-5(1)',
  'MP-3', 'MP-4', 'MP-5', 'MP-7(1)',
  'PE-4', 'PE-5', 'PE-9', 'PE-10', 'PE-11', 'PE-17', 'PE-18',
  'PL-8', 'PM-5', 'PM-9', 'PM-11',
  'PS-3(3)',
  'RA-3(1)', 'RA-5(1)', 'RA-5(2)', 'RA-5(5)',
  'SA-4(1)', 'SA-4(2)', 'SA-4(8)', 'SA-4(10)', 'SA-8', 'SA-10', 'SA-11', 'SA-15', 'SA-16',
  'SC-2', 'SC-4', 'SC-7(3)', 'SC-7(4)', 'SC-7(5)', 'SC-7(7)', 'SC-7(8)', 'SC-7(18)', 'SC-8', 'SC-8(1)', 'SC-10', 'SC-13(1)', 'SC-18', 'SC-28', 'SC-28(1)',
  'SI-2(2)', 'SI-3(1)', 'SI-3(2)', 'SI-4(2)', 'SI-4(4)', 'SI-4(5)', 'SI-7', 'SI-7(1)', 'SI-7(7)', 'SI-8', 'SI-10', 'SI-11', 'SI-16'
];

// High includes all moderate controls plus additional ones
BASELINE_CONTROLS.high = [
  ...BASELINE_CONTROLS.moderate,
  'AC-2(1)', 'AC-2(3)', 'AC-2(4)', 'AC-2(12)', 'AC-2(13)', 'AC-3(3)', 'AC-4(4)', 'AC-6(1)', 'AC-6(2)', 'AC-6(3)', 'AC-6(5)', 'AC-6(9)', 'AC-6(10)',
  'AU-2(3)', 'AU-6(5)', 'AU-6(6)', 'AU-9(2)', 'AU-9(3)', 'AU-10', 'AU-13', 'AU-14',
  'CA-2(3)', 'CA-3(3)', 'CA-5(1)', 'CA-7(3)',
  'CM-2(7)', 'CM-3(1)', 'CM-3(4)', 'CM-3(6)', 'CM-5(1)', 'CM-5(3)', 'CM-6(2)', 'CM-7(3)', 'CM-7(4)', 'CM-8(2)', 'CM-8(4)', 'CM-8(5)',
  'CP-2(2)', 'CP-2(5)', 'CP-4(2)', 'CP-6(1)', 'CP-6(3)', 'CP-7(4)', 'CP-8(2)', 'CP-8(3)', 'CP-8(4)', 'CP-9(2)', 'CP-9(3)', 'CP-9(6)',
  'IA-2(3)', 'IA-2(11)', 'IA-3(1)', 'IA-5(2)', 'IA-5(3)',
  'IR-3(2)', 'IR-4(2)', 'IR-4(3)', 'IR-6(2)', 'IR-6(3)', 'IR-7(2)', 'IR-8(1)',
  'MA-3(1)', 'MA-3(2)', 'MA-3(3)', 'MA-4(2)', 'MA-4(3)',
  'MP-5(4)', 'MP-6(1)', 'MP-6(2)', 'MP-6(3)',
  'PE-3(1)', 'PE-6(1)', 'PE-6(4)', 'PE-9(1)',
  'PL-2(3)', 'PL-8(1)',
  'PS-2(2)', 'PS-4(2)',
  'RA-2(1)', 'RA-3(2)', 'RA-3(3)', 'RA-5(3)', 'RA-5(4)', 'RA-5(6)', 'RA-5(8)',
  'SA-3(1)', 'SA-4(6)', 'SA-4(9)', 'SA-8(3)', 'SA-10(1)', 'SA-11(1)', 'SA-11(2)', 'SA-11(4)', 'SA-11(5)', 'SA-15(1)', 'SA-15(3)', 'SA-15(8)', 'SA-17',
  'SC-5(2)', 'SC-7(10)', 'SC-7(11)', 'SC-7(12)', 'SC-7(20)', 'SC-8(2)', 'SC-12(2)', 'SC-12(3)', 'SC-17', 'SC-23',
  'SI-2(3)', 'SI-3(4)', 'SI-4(11)', 'SI-4(16)', 'SI-4(20)', 'SI-6', 'SI-7(2)', 'SI-7(5)', 'SI-10(3)'
];

export function generateSSP(options: SSPOptions): any {
  const templatePath = path.join(__dirname, '../templates/ssp-skeleton.json');
  const template = JSON.parse(fs.readFileSync(templatePath, 'utf-8'));
  
  const ssp = template['system-security-plan'];
  
  // Generate UUIDs
  ssp.uuid = crypto.randomUUID();
  ssp.metadata.parties[0].uuid = crypto.randomUUID();
  
  // Set timestamps
  const now = new Date().toISOString();
  ssp.metadata['last-modified'] = now;
  
  // Set system information
  ssp['system-characteristics']['system-name'] = options.systemName;
  ssp['system-characteristics']['security-sensitivity-level'] = options.baseline.toUpperCase();
  
  // Set impact levels
  const impactLevel = options.baseline === 'low' ? 'low' : options.baseline === 'moderate' ? 'moderate' : 'high';
  ssp['system-characteristics']['security-impact-level']['security-objective-confidentiality'] = impactLevel;
  ssp['system-characteristics']['security-impact-level']['security-objective-integrity'] = impactLevel;
  ssp['system-characteristics']['security-impact-level']['security-objective-availability'] = impactLevel;
  
  // Get baseline controls
  const controls = BASELINE_CONTROLS[options.baseline];
  
  // Fetch control details if requested
  let controlDetailsMap: Map<string, ControlDetail> | null = null;
  if (options.includeControlDetails) {
    controlDetailsMap = fetchControlDetails(controls);
  }
  
  // Add baseline controls
  ssp['control-implementation']['implemented-requirements'] = controls.map(controlId => {
    const requirement: any = {
      uuid: crypto.randomUUID(),
      'control-id': controlId,
      description: `Implementation of ${controlId} control`,
      statements: []
    };
    
    // Add control details if available
    if (controlDetailsMap?.has(controlId)) {
      const detail = controlDetailsMap.get(controlId)!;
      requirement.description = detail.description || detail.title || requirement.description;
      
      // Add title as a remark
      if (detail.title) {
        requirement.remarks = `Control Title: ${detail.title}`;
        if (detail.guidance) {
          requirement.remarks += `\n\nGuidance: ${detail.guidance}`;
        }
      }
    }
    
    return requirement;
  });
  
  return { 'system-security-plan': ssp };
}
