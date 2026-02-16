/**
 * @avasim/schema - Shared type definitions and validation
 *
 * This package provides:
 * - TypeScript types for all AvaSim service contracts
 * - JSON Schema definitions for runtime validation
 * - Validation utilities using AJV
 * - Example payloads for testing
 */

export * from './types';
export * from './validator';

/**
 * Current schema version
 */
export const SCHEMA_VERSION = '0.1.0';

/**
 * Engine version (will be updated by build system)
 */
export const ENGINE_VERSION = '0.1.0';
