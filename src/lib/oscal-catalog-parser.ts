import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export interface ControlRequirement {
  id: string;
  title: string;
  statement: string;
  guidance: string;
  requirements: string[]; // Extracted implementation requirements
}

/**
 * Load and parse the NIST 800-53 catalog
 */
export function loadNISTCatalog(): any {
  const catalogPath = path.join(__dirname, '../../data/nist/NIST_SP-800-53_rev5_catalog.json');
  
  if (!fs.existsSync(catalogPath)) {
    throw new Error('NIST 800-53 catalog not found. Expected at: data/nist/NIST_SP-800-53_rev5_catalog.json');
  }
  
  const catalogData = fs.readFileSync(catalogPath, 'utf-8');
  return JSON.parse(catalogData);
}

/**
 * Extract a specific control's requirements from the catalog
 * @param controlId - e.g., "SC-39", "AC-2"
 * @returns Control requirements object or null if not found
 */
export function getControlRequirements(controlId: string): ControlRequirement | null {
  const catalog = loadNISTCatalog();
  
  // OSCAL structure: catalog.catalog.groups[].controls[]
  const groups = catalog?.catalog?.groups || [];
  
  for (const group of groups) {
    const controls = group.controls || [];
    
    // Find the control by ID
    const control = controls.find((c: any) => c.id === controlId.toLowerCase());
    
    if (control) {
      return parseControl(control);
    }
    
    // Also check control enhancements (e.g., AC-2(1))
    for (const ctrl of controls) {
      if (ctrl.controls) {
        const enhancement = ctrl.controls.find((e: any) => e.id === controlId.toLowerCase());
        if (enhancement) {
          return parseControl(enhancement);
        }
      }
    }
  }
  
  return null;
}

/**
 * Parse an OSCAL control object into a structured requirement
 */
function parseControl(control: any): ControlRequirement {
  const id = control.id?.toUpperCase() || 'UNKNOWN';
  const title = control.title || 'No title';
  
  // Extract statement from parts
  let statement = '';
  let guidance = '';
  const requirements: string[] = [];
  
  const parts = control.parts || [];
  
  for (const part of parts) {
    if (part.name === 'statement') {
      statement = extractText(part);
    } else if (part.name === 'guidance') {
      guidance = extractText(part);
    } else if (part.name === 'item' || part.name === 'objective') {
      const req = extractText(part);
      if (req) {
        requirements.push(req);
      }
    }
  }
  
  // If no explicit requirements found, extract from statement
  if (requirements.length === 0 && statement) {
    requirements.push(statement);
  }
  
  return {
    id,
    title,
    statement,
    guidance,
    requirements
  };
}

/**
 * Extract text from an OSCAL part (handles nested prose)
 */
function extractText(part: any): string {
  if (!part) return '';
  
  let text = part.prose || '';
  
  // Handle nested parts
  if (part.parts && Array.isArray(part.parts)) {
    const nestedTexts = part.parts.map((p: any) => extractText(p)).filter(Boolean);
    if (nestedTexts.length > 0) {
      text += (text ? ' ' : '') + nestedTexts.join(' ');
    }
  }
  
  return text.trim();
}

/**
 * Get all controls from a specific family
 * @param familyId - e.g., "AC", "SC", "AU"
 */
export function getControlFamily(familyId: string): ControlRequirement[] {
  const catalog = loadNISTCatalog();
  const groups = catalog?.catalog?.groups || [];
  
  const targetGroup = groups.find((g: any) => g.id?.toUpperCase() === familyId.toUpperCase());
  
  if (!targetGroup) {
    return [];
  }
  
  const controls = targetGroup.controls || [];
  return controls.map((c: any) => parseControl(c));
}

/**
 * Get control count statistics
 */
export function getCatalogStats(): { totalControls: number; families: number } {
  const catalog = loadNISTCatalog();
  const groups = catalog?.catalog?.groups || [];
  
  let totalControls = 0;
  
  for (const group of groups) {
    totalControls += (group.controls || []).length;
  }
  
  return {
    totalControls,
    families: groups.length
  };
}
