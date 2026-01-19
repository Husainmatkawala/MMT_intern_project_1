/**
 * Test script for forensic processor
 * Tests verdict normalization and overall score calculation
 */

import { processForensicResponse, extractMetadata } from './src/services/forensicProcessor.js';

// Sample JSON from user (matching the structure provided)
const sampleResponse = {
    "blog_id": "696db8d874395d31d9099aa8",
    "entities_processed": 9,
    "images_analyzed": 9,
    "message": "Verification completed successfully",
    "success": true,
    "timestamp": "2026-01-19T05:04:01.217051",
    "verification_results": {
        "activities": {
            "activity1": {
                "analysis": {
                    "message": "No images provided",
                    "reason": "no_images"
                },
                "entity_name": "ferry ride",
                "images_count": 0,
                "score": 0
            },
            "activity2": {
                "analysis": {
                    "detailed_results": [
                        {
                            "image_url": "https://res.cloudinary.com/dqfsor33p/image/upload/v1768798489/travel-entities/activities/te28plubd3ozgtwyvw9f.jpg",
                            "scores": {
                                "error_level_score": 0.8,
                                "exif_score": 0.0,
                                "frequency_score": 0.7,
                                "noise_score": 1.0
                            },
                            "status": "success",
                            "weighted_score": 0.42
                        }
                    ],
                    "images_analyzed": 1,
                    "images_failed": 0,
                    "message": "✗ Images are AI-GENERATED (confidence: 58.0%)",
                    "real_probability": 0.42,
                    "verdict": "ai_generated"
                },
                "entity_name": "art appreciation",
                "images_count": 1,
                "score": -50
            },
            "activity3": {
                "analysis": {
                    "detailed_results": [
                        {
                            "image_url": "https://res.cloudinary.com/dqfsor33p/image/upload/v1768798491/travel-entities/activities/vwskofqq8zjw0kl318tp.jpg",
                            "scores": {
                                "error_level_score": 0.8,
                                "exif_score": 0.0,
                                "frequency_score": 0.7,
                                "noise_score": 1.0
                            },
                            "status": "success",
                            "weighted_score": 0.42
                        },
                        {
                            "image_url": "https://res.cloudinary.com/dqfsor33p/image/upload/v1768798492/travel-entities/activities/diehshhwhiggxctjmeaq.jpg",
                            "scores": {
                                "error_level_score": 0.4,
                                "exif_score": 0.0,
                                "frequency_score": 0.7,
                                "noise_score": 1.0
                            },
                            "status": "success",
                            "weighted_score": 0.38
                        }
                    ],
                    "images_analyzed": 2,
                    "images_failed": 0,
                    "message": "✗ Images are AI-GENERATED (confidence: 60.0%)",
                    "real_probability": 0.4,
                    "verdict": "ai_generated"
                },
                "entity_name": "stroll",
                "images_count": 2,
                "score": -50
            }
        },
        "hotels": {
            "hotel1": {
                "analysis": {
                    "detailed_results": [
                        {
                            "image_url": "https://res.cloudinary.com/dqfsor33p/image/upload/v1768798493/travel-entities/hotels/ebxtikxbecgzrvdjahek.jpg",
                            "scores": {
                                "error_level_score": 0.4,
                                "exif_score": 0.0,
                                "frequency_score": 0.7,
                                "noise_score": 1.0
                            },
                            "status": "success",
                            "weighted_score": 0.38
                        }
                    ],
                    "images_analyzed": 1,
                    "images_failed": 0,
                    "message": "✗ Images are AI-GENERATED (confidence: 62.0%)",
                    "real_probability": 0.38,
                    "verdict": "ai_generated"
                },
                "entity_name": "Taj Mahal Palace Hotel",
                "images_count": 1,
                "score": -50
            }
        },
        "places": {
            "place1": {
                "analysis": {
                    "detailed_results": [
                        {
                            "image_url": "https://res.cloudinary.com/dqfsor33p/image/upload/v1768798494/travel-entities/places/eevdlmptsgdwl7xte4yo.jpg",
                            "scores": {
                                "error_level_score": 0.4,
                                "exif_score": 1.0,
                                "frequency_score": 0.7,
                                "noise_score": 0.7
                            },
                            "status": "success",
                            "weighted_score": 0.82
                        }
                    ],
                    "images_analyzed": 1,
                    "images_failed": 0,
                    "message": "✓ Images are REAL (confidence: 82.0%)",
                    "real_probability": 0.82,
                    "verdict": "real"
                },
                "entity_name": "Gateway of India",
                "images_count": 1,
                "score": 100
            },
            "place2": {
                "analysis": {
                    "detailed_results": [
                        {
                            "image_url": "https://res.cloudinary.com/dqfsor33p/image/upload/v1768798496/travel-entities/places/pu9ngtm9vtiuxbdnaoyg.jpg",
                            "scores": {
                                "error_level_score": 0.4,
                                "exif_score": 1.0,
                                "frequency_score": 0.7,
                                "noise_score": 0.4
                            },
                            "status": "success",
                            "weighted_score": 0.76
                        },
                        {
                            "image_url": "https://res.cloudinary.com/dqfsor33p/image/upload/v1768798499/travel-entities/places/l3k9mvzrgeq2vsey9khm.jpg",
                            "scores": {
                                "error_level_score": 0.8,
                                "exif_score": 0.0,
                                "frequency_score": 0.7,
                                "noise_score": 1.0
                            },
                            "status": "success",
                            "weighted_score": 0.42
                        }
                    ],
                    "images_analyzed": 2,
                    "images_failed": 0,
                    "message": "✓ Images are REAL (confidence: 59.0%)",
                    "real_probability": 0.59,
                    "verdict": "real"
                },
                "entity_name": "Taj Mahal Palace Hotel",
                "images_count": 2,
                "score": 100
            },
            "place3": {
                "analysis": {
                    "message": "No images provided",
                    "reason": "no_images"
                },
                "entity_name": "Elephanta Caves",
                "images_count": 0,
                "score": 0
            },
            "place4": {
                "analysis": {
                    "message": "No images provided",
                    "reason": "no_images"
                },
                "entity_name": "Jehangir Art Gallery",
                "images_count": 0,
                "score": 0
            },
            "place5": {
                "analysis": {
                    "detailed_results": [
                        {
                            "image_url": "https://res.cloudinary.com/dqfsor33p/image/upload/v1768798500/travel-entities/places/rte4ksfdrbgrzu4enayj.jpg",
                            "scores": {
                                "error_level_score": 0.8,
                                "exif_score": 1.0,
                                "frequency_score": 0.7,
                                "noise_score": 1.0
                            },
                            "status": "success",
                            "weighted_score": 0.92
                        },
                        {
                            "image_url": "https://res.cloudinary.com/dqfsor33p/image/upload/v1768798502/travel-entities/places/sdsnzthcfnl1h3eb65rv.jpg",
                            "scores": {
                                "error_level_score": 0.4,
                                "exif_score": 1.0,
                                "frequency_score": 0.7,
                                "noise_score": 0.7
                            },
                            "status": "success",
                            "weighted_score": 0.82
                        }
                    ],
                    "images_analyzed": 2,
                    "images_failed": 0,
                    "message": "✓ Images are REAL (confidence: 87.0%)",
                    "real_probability": 0.87,
                    "verdict": "real"
                },
                "entity_name": "Colaba Galleria",
                "images_count": 2,
                "score": 100
            }
        }
    }
};

console.log('🧪 Testing Forensic Processor\n');
console.log('=' .repeat(80));

try {
    // Test processForensicResponse
    console.log('\n1. Testing processForensicResponse()...\n');
    const processed = processForensicResponse(sampleResponse);
    
    // Test metadata extraction
    console.log('2. Testing extractMetadata()...\n');
    const metadata = extractMetadata(sampleResponse);
    console.log('Metadata:', JSON.stringify(metadata, null, 2));
    
    // Verify structure
    console.log('\n3. Verifying structure transformation...\n');
    
    Object.entries(processed.verification_results).forEach(([category, data]) => {
        console.log(`\n📁 Category: ${category}`);
        console.log(`   Overall Score: ${data.overall_score.toFixed(2)}`);
        console.log(`   Entries count: ${Object.keys(data.entries).length}`);
        
        // Check verdict normalization
        let normalizedCount = 0;
        Object.entries(data.entries).forEach(([entityId, entity]) => {
            if (entity.analysis && typeof entity.analysis.real_probability === 'number') {
                const expectedVerdict = entity.analysis.real_probability > 0.6 ? 'real' : 'ai_generated';
                const actualVerdict = entity.analysis.verdict;
                const matches = expectedVerdict === actualVerdict;
                
                console.log(`   - ${entityId}: real_prob=${entity.analysis.real_probability.toFixed(2)}, ` +
                           `verdict="${actualVerdict}" ${matches ? '✓' : '✗ MISMATCH!'}`);
                
                if (matches) normalizedCount++;
            }
        });
        
        console.log(`   Verdicts normalized: ${normalizedCount}/${Object.keys(data.entries).length} entities with analysis`);
    });
    
    // Verify specific cases from the requirements
    console.log('\n4. Verifying specific test cases from requirements...\n');
    
    // Test case 1: place1 with real_probability 0.82 > 0.6 should be "real"
    const place1 = processed.verification_results.places.entries.place1;
    console.log(`✓ place1: real_probability=${place1.analysis.real_probability}, verdict="${place1.analysis.verdict}"`);
    console.log(`  Expected: "real", Got: "${place1.analysis.verdict}" - ${place1.analysis.verdict === 'real' ? '✓ PASS' : '✗ FAIL'}`);
    
    // Test case 2: place2 with real_probability 0.59 <= 0.6 should be "ai_generated"
    const place2 = processed.verification_results.places.entries.place2;
    console.log(`✓ place2: real_probability=${place2.analysis.real_probability}, verdict="${place2.analysis.verdict}"`);
    console.log(`  Expected: "ai_generated", Got: "${place2.analysis.verdict}" - ${place2.analysis.verdict === 'ai_generated' ? '✓ PASS' : '✗ FAIL'}`);
    
    // Test case 3: Overall score calculation for places
    const placesOverall = processed.verification_results.places.overall_score;
    const expectedPlacesScore = (100 + 100 + 0 + 0 + 100) / 5; // 60
    console.log(`✓ places overall_score: ${placesOverall}`);
    console.log(`  Expected: ${expectedPlacesScore}, Got: ${placesOverall} - ${placesOverall === expectedPlacesScore ? '✓ PASS' : '✗ FAIL'}`);
    
    // Test case 4: Overall score calculation for activities
    const activitiesOverall = processed.verification_results.activities.overall_score;
    const expectedActivitiesScore = (0 + (-50) + (-50)) / 3; // -33.33
    console.log(`✓ activities overall_score: ${activitiesOverall.toFixed(2)}`);
    console.log(`  Expected: ${expectedActivitiesScore.toFixed(2)}, Got: ${activitiesOverall.toFixed(2)} - ${Math.abs(activitiesOverall - expectedActivitiesScore) < 0.01 ? '✓ PASS' : '✗ FAIL'}`);
    
    console.log('\n' + '='.repeat(80));
    console.log('✅ All tests completed successfully!\n');
    
    // Output sample final structure
    console.log('5. Sample output structure (places category):\n');
    console.log(JSON.stringify(processed.verification_results.places, null, 2));
    
} catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.error(error.stack);
    process.exit(1);
}
