export interface WaterQualityRange {
  min: number;
  max: number;
  unit: string;
}

export const WATER_QUALITY_SAFE_RANGES: Record<string, WaterQualityRange> = {
  temperature: { min: 24.0, max: 29.0, unit: '°C' },
  ph: { min: 6.8, max: 7.8, unit: 'pH' },
  dissolved_oxygen: { min: 6.0, max: 9.0, unit: 'mg/L' },
  ammonia: { min: 0.0, max: 0.05, unit: 'ppm' },
  nitrite: { min: 0.0, max: 0.1, unit: 'ppm' },
  nitrate: { min: 0.0, max: 40.0, unit: 'ppm' },
  salinity: { min: 0.0, max: 2.0, unit: 'ppt' },
  hardness: { min: 50.0, max: 200.0, unit: 'ppm' },
  alkalinity: { min: 50.0, max: 150.0, unit: 'ppm' },
};

export interface ReadingEvaluation {
  parameter: string;
  value: number;
  isSafe: boolean;
  severity: 'normal' | 'warning' | 'critical';
  message: string;
}

export function evaluateWaterQualityReading(parameter: string, value: number): ReadingEvaluation {
  const range = WATER_QUALITY_SAFE_RANGES[parameter.toLowerCase()];
  if (!range) {
    return {
      parameter,
      value,
      isSafe: true,
      severity: 'normal',
      message: 'No safe range configured.',
    };
  }

  if (value >= range.min && value <= range.max) {
    return {
      parameter,
      value,
      isSafe: true,
      severity: 'normal',
      message: `In safe range (${range.min}–${range.max} ${range.unit})`,
    };
  }

  const deviation = value < range.min ? range.min - value : value - range.max;
  const isCritical = deviation > (range.max - range.min) * 0.5;

  return {
    parameter,
    value,
    isSafe: false,
    severity: isCritical ? 'critical' : 'warning',
    message: `Out of safe range (${range.min}–${range.max} ${range.unit})`,
  };
}

export interface FormSubmissionAnswer {
  field_id: string; // Must be immutable UUID string
  value: any;
}

export interface FormSubmissionPayload {
  form_version_id: string;
  answers: Record<string, FormSubmissionAnswer>;
}

export function validateFormAnswers(payload: FormSubmissionPayload): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  if (!payload.form_version_id) {
    errors.push('Missing form_version_id');
  }

  for (const [key, answer] of Object.entries(payload.answers || {})) {
    if (!answer.field_id) {
      errors.push(`Answer key '${key}' missing field_id UUID`);
    }
  }

  return { valid: errors.length === 0, errors };
}
