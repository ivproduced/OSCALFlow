import { ComplianceSignal } from './scanner.js';
import { deterministicUUID } from './oscal-writer.js';

export interface ImplementedRequirement {
  uuid: string;
  'control-id': string;
  description: string;
  props?: Array<{ name: string; value: string }>;
  statements?: Array<{
    'statement-id': string;
    uuid: string;
    description: string;
    'by-components': ByComponent[];
  }>;
}

interface ByComponent {
  'component-uuid': string;
  uuid: string;
  description: string;
  'implementation-status': { state: string };
  props: Array<{ name: string; value: string }>;
}

interface OSCALComponent {
  uuid: string;
  type: string;
  title: string;
  description: string;
  status: { state: string };
  props?: Array<{ name: string; value: string }>;
}

const CONTROL_FAMILY_COMPONENTS: Record<string, string> = {
  'SC-39': 'container-runtime',
  'CM-7': 'container-runtime',
  'CM-3': 'cicd',
  'CM-4': 'cicd',
  'SA-11': 'cicd',
  'SA-15': 'cicd'
};

function getOriginationForControl(controlId: string): string {
  const family = controlId.split('-')[0];
  const inheritedFamilies = ['PE', 'MP', 'CP'];
  if (inheritedFamilies.includes(family)) return 'inherited';
  return 'customer-configured';
}

function inferComponents(signals: ComplianceSignal[], systemName: string): OSCALComponent[] {
  const components: OSCALComponent[] = [];
  const files = signals.map((s) => s.file.toLowerCase());
  const controls = new Set(signals.map((s) => s.control));

  components.push({
    uuid: deterministicUUID(`component:application:${systemName}`),
    type: 'software',
    title: systemName,
    description: `The ${systemName} application. Primary system being documented in this SSP.`,
    status: { state: 'operational' }
  });

  if (controls.has('SC-39') || files.some((f) => f.includes('dockerfile'))) {
    components.push({
      uuid: deterministicUUID(`component:container-runtime:${systemName}`),
      type: 'software',
      title: 'Container Runtime',
      description: 'Docker container runtime providing process isolation and resource management.',
      status: { state: 'operational' },
      props: [{ name: 'vendor-name', value: 'Docker Inc.' }]
    });
  }

  if (files.some((f) => f.includes('.github/workflows') || f.includes('ci.yml') || f.includes('jenkinsfile') || f.includes('gitlab-ci'))) {
    components.push({
      uuid: deterministicUUID(`component:cicd:${systemName}`),
      type: 'software',
      title: 'CI/CD Pipeline',
      description: 'Automated build, test, and deployment pipeline enforcing change management controls.',
      status: { state: 'operational' }
    });
  }

  if (files.some((f) => f.includes('k8s/') || f.includes('kubernetes/') || f.includes('chart.yaml') || f.includes('helm'))) {
    components.push({
      uuid: deterministicUUID(`component:orchestration:${systemName}`),
      type: 'software',
      title: 'Container Orchestration (Kubernetes)',
      description: 'Kubernetes managing deployment, scaling, network policies, and RBAC.',
      status: { state: 'operational' },
      props: [{ name: 'vendor-name', value: 'Cloud Native Computing Foundation' }]
    });
  }

  return components;
}

function getComponentUUID(
  controlId: string,
  signal: ComplianceSignal,
  components: OSCALComponent[],
  systemName: string
): string {
  const f = signal.file.toLowerCase();

  const containerUUID = deterministicUUID(`component:container-runtime:${systemName}`);
  if (CONTROL_FAMILY_COMPONENTS[controlId] === 'container-runtime' || f.includes('dockerfile')) {
    const component = components.find((c) => c.uuid === containerUUID);
    if (component) return component.uuid;
  }

  const cicdUUID = deterministicUUID(`component:cicd:${systemName}`);
  if (CONTROL_FAMILY_COMPONENTS[controlId] === 'cicd' || f.includes('workflow') || f.includes('ci.yml')) {
    const component = components.find((c) => c.uuid === cicdUUID);
    if (component) return component.uuid;
  }

  return deterministicUUID(`component:application:${systemName}`);
}

export function mapSignalsToRequirements(signals: ComplianceSignal[]): Map<string, ImplementedRequirement> {
  const requirements = new Map<string, ImplementedRequirement>();

  for (const signal of signals) {
    if (!requirements.has(signal.control)) {
      requirements.set(signal.control, {
        uuid: deterministicUUID(`req:${signal.control}`),
        'control-id': signal.control,
        description: signal.evidence,
        statements: []
      });
    } else {
      const existing = requirements.get(signal.control)!;
      existing.description += ` | ${signal.evidence}`;
    }
  }

  return requirements;
}

export function updateSSPWithSignals(ssp: any, signals: ComplianceSignal[]): any {
  const systemName: string = ssp['system-security-plan']?.['system-characteristics']?.['system-name'] ?? 'Unknown System';

  const components = inferComponents(signals, systemName);
  ssp['system-security-plan']['system-implementation'] = {
    users: ssp['system-security-plan']['system-implementation']?.users ?? [],
    components
  };

  const signalsByControl = new Map<string, ComplianceSignal[]>();
  for (const signal of signals) {
    if (!signalsByControl.has(signal.control)) {
      signalsByControl.set(signal.control, []);
    }
    signalsByControl.get(signal.control)!.push(signal);
  }

  const implementedReqs = ssp['system-security-plan']['control-implementation']['implemented-requirements'];

  for (let i = 0; i < implementedReqs.length; i++) {
    const req = implementedReqs[i];
    const controlSignals = signalsByControl.get(req['control-id']);

    if (controlSignals && controlSignals.length > 0) {
      const origination = getOriginationForControl(req['control-id']);
      const evidenceSummary = controlSignals.map((s) => s.evidence).join(' | ');

      req.description = evidenceSummary;
      req.props = [{ name: 'implementation-status', value: 'implemented' }];

      req.statements = controlSignals.map((signal, index) => {
        const componentUUID = getComponentUUID(req['control-id'], signal, components, systemName);
        const confidenceLabel = signal.confidence === 'high' ? 'High' : signal.confidence === 'low' ? 'Low' : 'Medium';

        const byComponent: ByComponent = {
          'component-uuid': componentUUID,
          uuid: deterministicUUID(`by-component:${req['control-id']}:${signal.file}:${index}`),
          description: `${signal.evidence}. Evidence file: ${signal.file}`,
          'implementation-status': { state: 'implemented' },
          props: [
            { name: 'control-origination', value: origination },
            { name: 'detection-confidence', value: confidenceLabel.toLowerCase() }
          ]
        };

        return {
          'statement-id': `${req['control-id'].toLowerCase().replace(/[()]/g, '')}_stmt.${index + 1}`,
          uuid: deterministicUUID(`stmt:${req['control-id']}:${signal.file}:${index}`),
          description: `${signal.evidence}. Evidence found in: ${signal.file}`,
          'by-components': [byComponent]
        };
      });

      signalsByControl.delete(req['control-id']);
    }
  }

  for (const [controlId, controlSignals] of signalsByControl) {
    const origination = getOriginationForControl(controlId);
    implementedReqs.push({
      uuid: deterministicUUID(`req:${controlId}:${systemName}`),
      'control-id': controlId,
      description: controlSignals.map((s) => s.evidence).join(' | '),
      props: [{ name: 'implementation-status', value: 'implemented' }],
      statements: controlSignals.map((signal, index) => {
        const componentUUID = getComponentUUID(controlId, signal, components, systemName);
        return {
          'statement-id': `${controlId.toLowerCase().replace(/[()]/g, '')}_stmt.${index + 1}`,
          uuid: deterministicUUID(`stmt:${controlId}:${signal.file}:${index}`),
          description: `${signal.evidence}. Evidence found in: ${signal.file}`,
          'by-components': [{
            'component-uuid': componentUUID,
            uuid: deterministicUUID(`by-component:${controlId}:${signal.file}:${index}`),
            description: `${signal.evidence}. Evidence file: ${signal.file}`,
            'implementation-status': { state: 'implemented' },
            props: [
              { name: 'control-origination', value: origination },
              { name: 'detection-confidence', value: signal.confidence }
            ]
          }]
        };
      })
    });
  }

  const now = new Date().toISOString();
  const revisions = ssp['system-security-plan'].metadata['revision-history'] ?? [];
  revisions.push({
    published: now,
    version: '1.0.' + (revisions.length + 1),
    'oscal-version': '1.2.0',
    remarks: `Updated ${signalsByControl.size === 0 ? signals.length : '(partial)'} control implementations by OSCALFlow automated scan`
  });
  ssp['system-security-plan'].metadata['revision-history'] = revisions;
  ssp['system-security-plan'].metadata['last-modified'] = now;

  return ssp;
}
