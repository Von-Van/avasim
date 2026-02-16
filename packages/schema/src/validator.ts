import Ajv, { ValidateFunction } from 'ajv';
import addFormats from 'ajv-formats';
import runRequestSchema from '../json-schema/run-request.schema.json';
import runSummarySchema from '../json-schema/run-summary.schema.json';
import { RunRequest, RunSummary, RunEvent, ValidationError, RunErrorResponse } from './types';

/**
 * Schema validator for AvaSim contracts
 */
export class SchemaValidator {
  private ajv: Ajv;
  private runRequestValidator: ValidateFunction;
  private runSummaryValidator: ValidateFunction;

  constructor() {
    this.ajv = new Ajv({
      allErrors: true,
      strict: false
    });
    addFormats(this.ajv);

    // Compile validators
    this.runRequestValidator = this.ajv.compile(runRequestSchema);
    this.runSummaryValidator = this.ajv.compile(runSummarySchema);
  }

  /**
   * Validate a RunRequest payload
   */
  validateRunRequest(data: unknown): { valid: boolean; errors?: ValidationError[] } {
    const valid = this.runRequestValidator(data);

    if (!valid && this.runRequestValidator.errors) {
      const errors: ValidationError[] = this.runRequestValidator.errors.map(err => ({
        field: err.instancePath || err.params?.missingProperty || 'unknown',
        message: err.message || 'Validation failed',
        value: err.data
      }));
      return { valid: false, errors };
    }

    return { valid: true };
  }

  /**
   * Validate a RunSummary payload
   */
  validateRunSummary(data: unknown): { valid: boolean; errors?: ValidationError[] } {
    const valid = this.runSummaryValidator(data);

    if (!valid && this.runSummaryValidator.errors) {
      const errors: ValidationError[] = this.runSummaryValidator.errors.map(err => ({
        field: err.instancePath || err.params?.missingProperty || 'unknown',
        message: err.message || 'Validation failed',
        value: err.data
      }));
      return { valid: false, errors };
    }

    return { valid: true };
  }

  /**
   * Validate a RunEvent (basic structure check)
   */
  validateRunEvent(event: unknown): { valid: boolean; error?: string } {
    if (typeof event !== 'object' || event === null) {
      return { valid: false, error: 'Event must be an object' };
    }

    const e = event as any;

    if (!e.event_id || typeof e.event_id !== 'string') {
      return { valid: false, error: 'Missing or invalid event_id' };
    }

    if (!e.type || typeof e.type !== 'string') {
      return { valid: false, error: 'Missing or invalid event type' };
    }

    if (!e.timestamp || typeof e.timestamp !== 'string') {
      return { valid: false, error: 'Missing or invalid timestamp' };
    }

    if (typeof e.round !== 'number') {
      return { valid: false, error: 'Missing or invalid round' };
    }

    if (!e.message || typeof e.message !== 'string') {
      return { valid: false, error: 'Missing or invalid message' };
    }

    return { valid: true };
  }

  /**
   * Create a standardized error response
   */
  createErrorResponse(
    error: string,
    code: string,
    message: string,
    validationErrors?: ValidationError[]
  ): RunErrorResponse {
    return {
      error,
      error_code: code,
      message,
      validation_errors: validationErrors,
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * Singleton validator instance
 */
export const validator = new SchemaValidator();
