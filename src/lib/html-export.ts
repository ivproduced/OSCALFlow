import fs from 'node:fs';
import path from 'node:path';

export interface SSPData {
  systemName: string;
  baseline: string;
  totalControls: number;
  implementedControls: number;
  coverage: number;
  controls: ControlData[];
}

export interface ControlData {
  id: string;
  title: string;
  family: string;
  description: string;
  implemented: boolean;
  statements: any[];
  remarks?: string;
}

export function generateHTMLReport(sspPath: string, outputPath: string): void {
  // Read SSP
  const ssp = JSON.parse(fs.readFileSync(sspPath, 'utf-8'));
  const sspData = ssp['system-security-plan'];
  
  // Extract data
  const systemName = sspData.metadata.title || 'System Security Plan';
  const requirements = sspData['control-implementation']['implemented-requirements'] || [];
  
  const totalControls = requirements.length;
  const implementedControls = requirements.filter((req: any) => req.statements && req.statements.length > 0).length;
  const coverage = totalControls > 0 ? ((implementedControls / totalControls) * 100).toFixed(1) : '0.0';
  
  // Group by family
  const controlsByFamily: Record<string, ControlData[]> = {};
  
  for (const req of requirements) {
    const controlId = req['control-id'];
    const family = controlId.split('-')[0];
    const implemented = req.statements && req.statements.length > 0;
    
    const control: ControlData = {
      id: controlId,
      title: extractTitle(req.remarks),
      family: family,
      description: req.description || 'No description available',
      implemented: implemented,
      statements: req.statements || [],
      remarks: req.remarks
    };
    
    if (!controlsByFamily[family]) {
      controlsByFamily[family] = [];
    }
    controlsByFamily[family].push(control);
  }
  
  // Generate HTML
  const html = generateHTML({
    systemName,
    baseline: 'MODERATE', // Could extract from metadata
    totalControls,
    implementedControls,
    coverage: parseFloat(coverage),
    controls: requirements.map((req: any) => ({
      id: req['control-id'],
      title: extractTitle(req.remarks),
      family: req['control-id'].split('-')[0],
      description: req.description || '',
      implemented: req.statements && req.statements.length > 0,
      statements: req.statements || [],
      remarks: req.remarks
    }))
  }, controlsByFamily);
  
  fs.writeFileSync(outputPath, html);
}

function extractTitle(remarks?: string): string {
  if (!remarks) return 'Untitled Control';
  const match = remarks.match(/Control Title:\s*([^\n]+)/);
  return match ? match[1].trim() : 'Untitled Control';
}

function generateHTML(data: SSPData, controlsByFamily: Record<string, ControlData[]>): string {
  const familyNames: Record<string, string> = {
    'AC': 'Access Control',
    'AU': 'Audit and Accountability',
    'AT': 'Awareness and Training',
    'CM': 'Configuration Management',
    'CP': 'Contingency Planning',
    'IA': 'Identification and Authentication',
    'IR': 'Incident Response',
    'MA': 'Maintenance',
    'MP': 'Media Protection',
    'PS': 'Personnel Security',
    'PE': 'Physical and Environmental Protection',
    'PL': 'Planning',
    'PM': 'Program Management',
    'RA': 'Risk Assessment',
    'CA': 'Assessment, Authorization, and Monitoring',
    'SC': 'System and Communications Protection',
    'SI': 'System and Information Integrity',
    'SA': 'System and Services Acquisition',
    'AP': 'Authority and Purpose',
    'AR': 'Accountability, Audit, and Risk Management',
    'DI': 'Data Quality and Integrity',
    'DM': 'Data Minimization and Retention',
    'IP': 'Individual Participation and Redress',
    'SE': 'Security',
    'TR': 'Transparency',
    'UL': 'Use Limitation'
  };
  
  const sortedFamilies = Object.keys(controlsByFamily).sort();
  
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${data.systemName} - OSCAL SSP Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9rem;
        }
        
        .progress-bar {
            background: #e0e0e0;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin: 1rem 0;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.9rem;
            transition: width 0.3s ease;
        }
        
        .family-section {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
        }
        
        .family-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1rem;
            border-bottom: 2px solid #667eea;
            margin-bottom: 1rem;
        }
        
        .family-title {
            font-size: 1.3rem;
            color: #667eea;
            font-weight: 600;
        }
        
        .family-badge {
            background: #667eea;
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .control {
            padding: 1rem;
            margin-bottom: 0.75rem;
            border-left: 4px solid #e0e0e0;
            background: #f9f9f9;
            border-radius: 4px;
        }
        
        .control.implemented {
            border-left-color: #4caf50;
            background: #f1f8f4;
        }
        
        .control-header {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .control-id {
            font-weight: bold;
            color: #667eea;
            margin-right: 0.75rem;
            font-size: 1.1rem;
        }
        
        .control-title {
            color: #555;
            flex: 1;
        }
        
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .status-implemented {
            background: #4caf50;
            color: white;
        }
        
        .status-pending {
            background: #ff9800;
            color: white;
        }
        
        .control-description {
            color: #666;
            font-size: 0.9rem;
            margin-top: 0.5rem;
            padding-left: 0.5rem;
        }
        
        .statements {
            margin-top: 0.75rem;
            padding-left: 1rem;
        }
        
        .statement {
            background: white;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 4px;
            border-left: 3px solid #4caf50;
            font-size: 0.9rem;
        }
        
        .footer {
            text-align: center;
            padding: 2rem;
            color: #666;
            font-size: 0.9rem;
        }
        
        .legend {
            display: flex;
            gap: 1.5rem;
            justify-content: center;
            margin: 2rem 0;
            padding: 1rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }
        
        @media print {
            .header {
                background: #667eea;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
            .progress-fill {
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>${data.systemName}</h1>
        <p>OSCAL System Security Plan - Generated ${new Date().toLocaleDateString()}</p>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">${data.totalControls}</div>
                <div class="stat-label">Total Controls</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.implementedControls}</div>
                <div class="stat-label">Implemented</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.coverage}%</div>
                <div class="stat-label">Coverage</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">~${(data.implementedControls * 0.5).toFixed(1)}h</div>
                <div class="stat-label">Time Saved</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${data.coverage}%">
                ${data.implementedControls}/${data.totalControls} Controls
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #4caf50;"></div>
                <span>Implemented (${data.implementedControls})</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ff9800;"></div>
                <span>Pending (${data.totalControls - data.implementedControls})</span>
            </div>
        </div>
        
        ${sortedFamilies.map(family => {
          const controls = controlsByFamily[family];
          const implementedCount = controls.filter(c => c.implemented).length;
          
          return `
        <div class="family-section">
            <div class="family-header">
                <h2 class="family-title">${family} - ${familyNames[family] || family}</h2>
                <span class="family-badge">${implementedCount}/${controls.length} Implemented</span>
            </div>
            ${controls.map(control => `
            <div class="control ${control.implemented ? 'implemented' : ''}">
                <div class="control-header">
                    <span class="control-id">${control.id}</span>
                    <span class="control-title">${control.title}</span>
                    <span class="status-badge ${control.implemented ? 'status-implemented' : 'status-pending'}">
                        ${control.implemented ? '✓ Implemented' : '○ Pending'}
                    </span>
                </div>
                ${control.implemented && control.statements.length > 0 ? `
                <div class="statements">
                    ${control.statements.map((stmt: any) => `
                    <div class="statement">
                        ${stmt.description}
                    </div>
                    `).join('')}
                </div>
                ` : `
                <div class="control-description">
                    ${control.description.substring(0, 200)}${control.description.length > 200 ? '...' : ''}
                </div>
                `}
            </div>
            `).join('')}
        </div>
          `;
        }).join('')}
    </div>
    
    <div class="footer">
        <p>Generated by gh-oscal CLI | OSCAL 1.2.0 Compliant</p>
    </div>
</body>
</html>`;
}
