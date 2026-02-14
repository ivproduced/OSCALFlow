import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export interface ControlDetail {
  id: string;
  title: string;
  description?: string;
  guidance?: string;
  parameters?: Array<{
    id: string;
    label?: string;
    guidelines?: string[];
  }>;
  parts?: Array<{
    id?: string;
    name?: string;
    prose?: string;
  }>;
}

/**
 * Load the NIST 800-53 Rev 5 catalog from local file
 */
export function loadCatalog(): any {
  const catalogPath = path.join(__dirname, '../../data/nist/NIST_SP-800-53_rev5_catalog.json');
  const catalogData = fs.readFileSync(catalogPath, 'utf-8');
  return JSON.parse(catalogData);
}

/**
 * Load baseline profile from local file
 */
export function loadBaselineProfile(baseline: 'low' | 'moderate' | 'high'): any {
  const baselineMap = {
    low: 'LOW',
    moderate: 'MODERATE',
    high: 'HIGH'
  };
  const profilePath = path.join(__dirname, `../../data/nist/NIST_SP-800-53_rev5_${baselineMap[baseline]}-baseline_profile.json`);
  const profileData = fs.readFileSync(profilePath, 'utf-8');
  return JSON.parse(profileData);
}

/**
 * Extract control IDs from baseline profile
 */
export function getControlsFromProfile(profile: any): string[] {
  const controlIds: string[] = [];
  
  if (profile?.profile?.imports) {
    for (const importItem of profile.profile.imports) {
      if (importItem['include-controls']) {
        for (const include of importItem['include-controls']) {
          if (include['with-ids']) {
            controlIds.push(...include['with-ids']);
          }
        }
      }
    }
  }
  
  return controlIds;
}

/**
 * Extract control details from the catalog
 */
export function extractControlDetails(catalog: any, controlId: string): ControlDetail | null {
  if (!catalog?.catalog?.groups) {
    return null;
  }
  
  // Normalize control ID to lowercase for catalog lookup
  const normalizedId = controlId.toLowerCase();
  
  // Handle control enhancements (e.g., AC-2(1) -> ac-2.1)
  const catalogId = normalizedId.replace(/\((\d+)\)/, '.$1');
  
  // Search through control groups
  for (const group of catalog.catalog.groups) {
    const control = findControlInGroup(group, catalogId);
    
    if (control) {
      return formatControl(control, controlId);
    }
  }
  
  return null;
}

/**
 * Recursively find a control within a group
 */
function findControlInGroup(group: any, controlId: string): any {
  // Check controls in this group
  if (group.controls) {
    const control = group.controls.find((c: any) => c.id === controlId);
    if (control) return control;
    
    // Check enhancements within controls
    for (const ctrl of group.controls) {
      if (ctrl.controls) {
        const enhancement = findControlInGroup(ctrl, controlId);
        if (enhancement) return enhancement;
      }
    }
  }
  
  // Check subgroups
  if (group.groups) {
    for (const subgroup of group.groups) {
      const control = findControlInGroup(subgroup, controlId);
      if (control) return control;
    }
  }
  
  return null;
}

/**
 * Format control data for SSP use
 */
function formatControl(control: any, originalId?: string): ControlDetail {
  const detail: ControlDetail = {
    id: originalId || control.id,
    title: control.title || ''
  };
  
  // Extract description/prose from parts
  if (control.parts) {
    const statementPart = control.parts.find((p: any) => p.name === 'statement');
    const guidancePart = control.parts.find((p: any) => p.name === 'guidance');
    
    if (statementPart) {
      detail.description = extractProseFromPart(statementPart);
    }
    
    if (guidancePart?.prose) {
      detail.guidance = guidancePart.prose;
    }
    
    detail.parts = control.parts;
  }
  
  // Extract parameters
  if (control.params) {
    detail.parameters = control.params.map((p: any) => ({
      id: p.id,
      label: p.label,
      guidelines: p.guidelines?.map((g: any) => g.prose).filter(Boolean)
    }));
  }
  
  return detail;
}

/**
 * Extract prose text from a part recursively
 */
function extractProseFromPart(part: any): string {
  let prose = '';
  
  if (part.prose) {
    prose += part.prose;
  }
  
  if (part.parts) {
    const childProse = part.parts
      .map((p: any) => extractProseFromPart(p))
      .filter(Boolean)
      .join(' ');
    if (childProse) {
      prose += (prose ? ' ' : '') + childProse;
    }
  }
  
  return prose;
}

/**
 * Get multiple control details
 */
export function fetchControlDetails(controlIds: string[]): Map<string, ControlDetail> {
  const catalog = loadCatalog();
  const controlMap = new Map<string, ControlDetail>();
  
  for (const controlId of controlIds) {
    const detail = extractControlDetails(catalog, controlId);
    if (detail) {
      controlMap.set(controlId, detail);
    }
  }
  
  return controlMap;
}
