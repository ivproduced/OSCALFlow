import { ComplianceSignal } from './scanner.js';
import crypto from 'node:crypto';

export interface ImplementedRequirement {
  uuid: string;
  'control-id': string;
  description: string;
  statements?: Array<{
    'statement-id': string;
    uuid: string;
    description: string;
  }>;
}

export function mapSignalsToRequirements(signals: ComplianceSignal[]): Map<string, ImplementedRequirement> {
  const requirements = new Map<string, ImplementedRequirement>();
  
  for (const signal of signals) {
    if (!requirements.has(signal.control)) {
      requirements.set(signal.control, {
        uuid: crypto.randomUUID(),
        'control-id': signal.control,
        description: signal.evidence,
        statements: []
      });
    } else {
      // Enhance existing requirement with additional evidence
      const existing = requirements.get(signal.control)!;
      existing.description += ` | ${signal.evidence}`;
    }
  }
  
  return requirements;
}

export function updateSSPWithSignals(ssp: any, signals: ComplianceSignal[]): any {
  // Group signals by control ID
  const signalsByControl = new Map<string, ComplianceSignal[]>();
  
  for (const signal of signals) {
    if (!signalsByControl.has(signal.control)) {
      signalsByControl.set(signal.control, []);
    }
    signalsByControl.get(signal.control)!.push(signal);
  }
  
  // Update existing implemented requirements
  const implementedReqs = ssp['system-security-plan']['control-implementation']['implemented-requirements'];
  
  for (let i = 0; i < implementedReqs.length; i++) {
    const req = implementedReqs[i];
    const controlSignals = signalsByControl.get(req['control-id']);
    
    if (controlSignals && controlSignals.length > 0) {
      // Update description with summary
      const evidenceSummary = controlSignals.map(s => s.evidence).join(' | ');
      req.description = evidenceSummary;
      
      // Add implementation statements
      req.statements = controlSignals.map((signal, index) => ({
        'statement-id': `${req['control-id'].toLowerCase()}_stmt.${index + 1}`,
        uuid: crypto.randomUUID(),
        description: `${signal.evidence}. Evidence found in: ${signal.file}`
      }));
      
      signalsByControl.delete(req['control-id']);
    }
  }
  
  // Add any remaining controls that weren't in the baseline
  for (const [controlId, controlSignals] of signalsByControl) {
    implementedReqs.push({
      uuid: crypto.randomUUID(),
      'control-id': controlId,
      description: controlSignals.map(s => s.evidence).join(' | '),
      statements: controlSignals.map((signal, index) => ({
        'statement-id': `${controlId.toLowerCase()}_stmt.${index + 1}`,
        uuid: crypto.randomUUID(),
        description: `${signal.evidence}. Evidence found in: ${signal.file}`
      }))
    });
  }
  
  // Update last-modified timestamp
  ssp['system-security-plan'].metadata['last-modified'] = new Date().toISOString();
  
  return ssp;
}
