import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'path';
import { getControlRequirements, type ControlRequirement } from './oscal-catalog-parser.js';

export interface ValidationResult {
  controlId: string;
  validated: boolean;
  confidence: 'high' | 'medium' | 'low';
  evidence: string;
  aiAnalysis: string;
}

/**
 * Validate a file's implementation against a NIST control using Copilot CLI
 * @param controlId - e.g., "SC-39"
 * @param filePath - Path to the file to validate
 * @param repoPath - Repository root path (for context)
 * @param model - AI model to use (default: gpt-5-mini for cost efficiency)
 * @returns Validation result with AI analysis
 */
export async function validateControlImplementation(
  controlId: string,
  filePath: string,
  repoPath: string,
  model: string = 'gpt-5-mini'
): Promise<ValidationResult> {
  // Get the control requirements from OSCAL catalog
  const control = getControlRequirements(controlId);
  
  if (!control) {
    return {
      controlId,
      validated: false,
      confidence: 'low',
      evidence: 'Control not found in OSCAL catalog',
      aiAnalysis: 'Unable to validate - control definition not available'
    };
  }
  
  // Read the file content — skip symlinks and cap at 1 MB to prevent DoS
  const absolutePath = path.isAbsolute(filePath) ? filePath : path.join(repoPath, filePath);
  
  if (!fs.existsSync(absolutePath)) {
    return {
      controlId,
      validated: false,
      confidence: 'low',
      evidence: 'File not found',
      aiAnalysis: `File ${filePath} does not exist`
    };
  }

  const stat = fs.lstatSync(absolutePath);
  if (stat.isSymbolicLink()) {
    return {
      controlId,
      validated: false,
      confidence: 'low',
      evidence: 'Skipped symbolic link',
      aiAnalysis: `${filePath} is a symbolic link and was not read`
    };
  }
  if (stat.size > 1024 * 1024) {
    return {
      controlId,
      validated: false,
      confidence: 'low',
      evidence: 'File too large to validate',
      aiAnalysis: `${filePath} exceeds 1 MB and was skipped`
    };
  }

  const fileContent = fs.readFileSync(absolutePath, 'utf-8');
  
  // Build the validation prompt for Copilot CLI
  const prompt = buildValidationPrompt(control, filePath, fileContent);
  
  try {
    // Call Copilot CLI for validation
    const result = await callCopilotForValidation(prompt, repoPath, model);
    
    // Parse the response
    return parseValidationResponse(controlId, result);
  } catch (error) {
    return {
      controlId,
      validated: false,
      confidence: 'low',
      evidence: 'AI validation failed',
      aiAnalysis: `Error: ${error instanceof Error ? error.message : String(error)}`
    };
  }
}

/**
 * Build a validation prompt for Copilot CLI
 */
function buildValidationPrompt(
  control: ControlRequirement,
  filePath: string,
  fileContent: string
): string {
  // Truncate file content if too large (keep first 500 lines)
  const lines = fileContent.split('\n');
  const truncatedContent = lines.slice(0, 500).join('\n');
  const wasTruncated = lines.length > 500;
  
  return `You are a cybersecurity compliance validator. Analyze if this file implements NIST 800-53 control ${control.id}.

CONTROL: ${control.id} - ${control.title}

REQUIREMENTS:
${control.requirements.map((req, i) => `${i + 1}. ${req}`).join('\n')}

GUIDANCE:
${control.guidance || 'No additional guidance'}

FILE TO VALIDATE: ${filePath}
${wasTruncated ? '(Showing first 500 lines)' : ''}

FILE CONTENT:
\`\`\`
${truncatedContent}
\`\`\`

VALIDATION TASK:
Analyze if this file implements the control requirements above.

OUTPUT FORMAT (respond EXACTLY in this format):
VALIDATION: [YES/NO]
CONFIDENCE: [HIGH/MEDIUM/LOW]
EVIDENCE: [Specific code/configuration that implements the control]
ANALYSIS: [1-2 sentence explanation]

Be strict: Only return YES if there is clear evidence of implementation.`;
}

/** Allowlist of models that may be passed to gh copilot */
const ALLOWED_MODELS = new Set([
  'gpt-4o', 'gpt-4o-mini', 'gpt-5-mini', 'gpt-5.4-mini',
  'claude-sonnet-4.6', 'claude-haiku-4.5', 'claude-opus-4.8',
  'o1', 'o3-mini',
]);

/**
 * Call GitHub Copilot CLI for validation
 */
async function callCopilotForValidation(prompt: string, cwd: string, model: string = 'gpt-5-mini'): Promise<string> {
  // Validate model against allowlist to prevent argument injection
  const safeModel = ALLOWED_MODELS.has(model) ? model : 'gpt-5-mini';

  // Pass prompt as a discrete argument — no shell interpolation
  const args = ['copilot', '--', '-p', prompt, '--model', safeModel, '--allow-all-tools'];

  try {
    const output = execFileSync('gh', args, {
      cwd,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
      maxBuffer: 10 * 1024 * 1024, // 10 MB buffer
      timeout: 30000 // 30 s timeout
    });
    
    return output;
  } catch (error: any) {
    if (error.stderr) {
      throw new Error(`Copilot CLI error: ${error.stderr}`);
    }
    throw error;
  }
}

/**
 * Parse Copilot's validation response
 */
function parseValidationResponse(controlId: string, response: string): ValidationResult {
  // Extract structured fields from response
  const validationMatch = response.match(/VALIDATION:\s*(YES|NO)/i);
  const confidenceMatch = response.match(/CONFIDENCE:\s*(HIGH|MEDIUM|LOW)/i);
  const evidenceMatch = response.match(/EVIDENCE:\s*(.+?)(?=ANALYSIS:|$)/is);
  const analysisMatch = response.match(/ANALYSIS:\s*(.+?)$/is);
  
  const validated = validationMatch?.[1]?.toUpperCase() === 'YES';
  const confidence = (confidenceMatch?.[1]?.toLowerCase() || 'low') as 'high' | 'medium' | 'low';
  const evidence = evidenceMatch?.[1]?.trim() || 'No specific evidence provided';
  const aiAnalysis = analysisMatch?.[1]?.trim() || response.substring(0, 200);
  
  return {
    controlId,
    validated,
    confidence,
    evidence,
    aiAnalysis
  };
}

/**
 * Batch validate multiple controls
 */
export async function validateMultipleControls(
  validations: Array<{ controlId: string; filePath: string }>,
  repoPath: string
): Promise<ValidationResult[]> {
  const results: ValidationResult[] = [];
  
  // Validate each control sequentially to avoid overwhelming Copilot CLI
  for (const { controlId, filePath } of validations) {
    const result = await validateControlImplementation(controlId, filePath, repoPath);
    results.push(result);
  }
  
  return results;
}
