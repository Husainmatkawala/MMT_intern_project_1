/**
 * Forensic Response Processor
 * 
 * Processes forensic service responses by:
 * 1. Normalizing verdicts based on real_probability threshold (>0.6)
 * 2. Calculating overall scores per category
 * 3. Restructuring categories to include overall_score and entries
 */

/**
 * Normalize verdict based on real_probability
 * Rule: If real_probability > 0.6 → verdict = "real", else → verdict = "ai_generated"
 * 
 * @param {Object} analysis - The analysis object containing real_probability and verdict
 * @returns {Object} - The analysis object with normalized verdict
 */
function normalizeVerdict(analysis) {
  if (!analysis || typeof analysis !== 'object') {
    return analysis;
  }

  // Clone the analysis object to avoid mutation
  const normalizedAnalysis = { ...analysis };

  // Only normalize if real_probability exists
  if (typeof normalizedAnalysis.real_probability === 'number') {
    normalizedAnalysis.verdict = normalizedAnalysis.real_probability > 0.6 ? 'real' : 'ai_generated';
  }

  return normalizedAnalysis;
}

/**
 * Calculate overall score for a category
 * 
 * @param {Object} categoryEntries - Object containing all entities in a category
 * @returns {number} - Average score across all entities
 */
function calculateOverallScore(categoryEntries) {
  if (!categoryEntries || typeof categoryEntries !== 'object') {
    return 0;
  }

  const entities = Object.values(categoryEntries);
  
  if (entities.length === 0) {
    return 0;
  }

  const totalScore = entities.reduce((sum, entity) => {
    const score = typeof entity.score === 'number' ? entity.score : 0;
    return sum + score;
  }, 0);

  return totalScore / entities.length;
}

/**
 * Process a single category (activities, hotels, places)
 * - Normalizes verdicts for all entities
 * - Calculates overall_score
 * - Restructures to { overall_score, entries: {...} }
 * 
 * @param {Object} categoryData - The category object with entities
 * @returns {Object} - Processed category with overall_score and entries
 */
function processCategory(categoryData) {
  if (!categoryData || typeof categoryData !== 'object') {
    return {
      overall_score: 0,
      entries: {}
    };
  }

  // Process each entity to normalize verdicts
  const processedEntries = {};
  
  for (const [entityId, entityData] of Object.entries(categoryData)) {
    processedEntries[entityId] = {
      ...entityData,
      analysis: normalizeVerdict(entityData.analysis)
    };
  }

  // Calculate overall score
  const overallScore = calculateOverallScore(processedEntries);

  return {
    overall_score: overallScore,
    entries: processedEntries
  };
}

/**
 * Process the complete forensic response
 * 
 * @param {Object} forensicResponse - The raw response from forensic service
 * @returns {Object} - Processed response with normalized verdicts and overall scores
 */
export function processForensicResponse(forensicResponse) {
  if (!forensicResponse || typeof forensicResponse !== 'object') {
    throw new Error('Invalid forensic response: must be an object');
  }

  // Clone the response to avoid mutation
  const processedResponse = { ...forensicResponse };

  // Process verification_results if it exists
  if (processedResponse.verification_results && typeof processedResponse.verification_results === 'object') {
    const verificationResults = processedResponse.verification_results;
    const processedResults = {};

    // Process each category (activities, hotels, places, etc.)
    for (const [categoryName, categoryData] of Object.entries(verificationResults)) {
      processedResults[categoryName] = processCategory(categoryData);
    }

    processedResponse.verification_results = processedResults;
  }

  return processedResponse;
}

/**
 * Extract metadata from forensic response
 * 
 * @param {Object} forensicResponse - The response from forensic service
 * @returns {Object} - Metadata object with entities_processed, images_analyzed, timestamp
 */
export function extractMetadata(forensicResponse) {
  return {
    entities_processed: forensicResponse.entities_processed || 0,
    images_analyzed: forensicResponse.images_analyzed || 0,
    timestamp: forensicResponse.timestamp ? new Date(forensicResponse.timestamp) : new Date()
  };
}
