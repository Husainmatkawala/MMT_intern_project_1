import express from 'express';
import axios from 'axios';
import mongoose from 'mongoose';
import multer from 'multer';
import exifParser from 'exif-parser';
import Blog from '../models/Blog.js';
import User from '../models/User.js';
import TempEntityJSON from '../models/TempEntityJSON.js';
import TempEntityJSON2 from '../models/TempEntityJSON2.js';
import ImageAIScore from '../models/ImageAIScore.js';
import BlogScore from '../models/BlogScore.js';
import { protect } from '../middleware/auth.js';
import { uploadImage } from '../config/cloudinary.js';
import { processForensicResponse, extractMetadata } from '../services/forensicProcessor.js';

const router = express.Router();

// Configure multer for memory storage
const storage = multer.memoryStorage();
const upload = multer({
  storage: storage,
  limits: {
    fileSize: 5 * 1024 * 1024 // 5MB limit per file
  },
  fileFilter: (req, file, cb) => {
    // Accept images only
    if (!file.mimetype.startsWith('image/')) {
      return cb(new Error('Only image files are allowed'), false);
    }
    cb(null, true);
  }
});

// NER Service URL from environment or default
const NER_SERVICE_URL = process.env.NER_SERVICE_URL || 'http://localhost:5001';

// Forensic Service URL from environment or default
const FORENSIC_SERVICE_URL = process.env.FORENSIC_SERVICE_URL || 'http://localhost:5002';

// Blog Score Service URL from environment or default
const BLOG_SCORE_SERVICE_URL = process.env.BLOG_SCORE_SERVICE_URL || 'http://localhost:5003';

// @route   GET /api/blogs
// @desc    Get all blogs from all users
// @access  Private
router.get('/', protect, async (req, res) => {
  try {
    const blogs = await Blog.find()
      .populate('uid', 'username')
      .sort({ createdAt: -1 });
    
    // Fetch entity images and scores for each blog
    const blogsWithImages = await Promise.all(blogs.map(async (blog) => {
      const blogObj = blog.toObject();
      
      // Get entity images from TempEntityJSON2
      const entityData = await TempEntityJSON2.findOne({ blog_id: blog._id });
      
      if (entityData && entityData.updated_entities) {
        // Extract all images from entities
        const allImages = [];
        Object.values(entityData.updated_entities).forEach(entityType => {
          Object.values(entityType).forEach(entity => {
            if (entity.images && Array.isArray(entity.images)) {
              allImages.push(...entity.images);
            }
          });
        });
        
        // Add entity images to blog
        blogObj.entityImages = allImages;
      } else {
        blogObj.entityImages = [];
      }
      
      // Get blog quality score
      const blogScore = await BlogScore.findOne({ blog_id: blog._id });
      if (blogScore) {
        blogObj.qualityScore = {
          final_score: blogScore.final_score,
          meaning: blogScore.meaning,
          scores: {
            content_depth: blogScore.content_depth_score,
            entity_richness: blogScore.entity_richness_score,
            proof_support: blogScore.proof_support_score,
            authenticity: blogScore.authenticity_score,
            language_quality: blogScore.language_quality_score,
            ai_risk: blogScore.ai_risk_score
          }
        };
      }
      
      return blogObj;
    }));
      
    res.json(blogsWithImages);
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// @route   GET /api/blogs/my
// @desc    Get logged-in user's blogs
// @access  Private
router.get('/my', protect, async (req, res) => {
  try {
    const blogs = await Blog.find({ uid: req.user._id })
      .populate('uid', 'username')
      .sort({ createdAt: -1 });

    // Fetch entity images and scores for each blog
    const blogsWithImages = await Promise.all(blogs.map(async (blog) => {
      const blogObj = blog.toObject();
      
      // Get entity images from TempEntityJSON2
      const entityData = await TempEntityJSON2.findOne({ blog_id: blog._id });
      
      if (entityData && entityData.updated_entities) {
        // Extract all images from entities
        const allImages = [];
        Object.values(entityData.updated_entities).forEach(entityType => {
          Object.values(entityType).forEach(entity => {
            if (entity.images && Array.isArray(entity.images)) {
              allImages.push(...entity.images);
            }
          });
        });
        
        // Add entity images to blog
        blogObj.entityImages = allImages;
      } else {
        blogObj.entityImages = [];
      }
      
      // Get blog quality score
      const blogScore = await BlogScore.findOne({ blog_id: blog._id });
      if (blogScore) {
        blogObj.qualityScore = {
          final_score: blogScore.final_score,
          meaning: blogScore.meaning,
          scores: {
            content_depth: blogScore.content_depth_score,
            entity_richness: blogScore.entity_richness_score,
            proof_support: blogScore.proof_support_score,
            authenticity: blogScore.authenticity_score,
            language_quality: blogScore.language_quality_score,
            ai_risk: blogScore.ai_risk_score
          }
        };
      }
      
      return blogObj;
    }));

    res.json(blogsWithImages);
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// @route   GET /api/blogs/:id/entities
// @desc    Get extracted entities for a blog
// @access  Private
router.get('/:id/entities', protect, async (req, res) => {
  try {
    const blogId = req.params.id;
    
    // Validate ObjectId format
    if (!mongoose.Types.ObjectId.isValid(blogId)) {
      return res.status(400).json({ 
        success: false,
        message: 'Invalid blog ID format' 
      });
    }
    
    // Find the blog
    const blog = await Blog.findById(blogId);
    
    if (!blog) {
      return res.status(404).json({ 
        success: false,
        message: 'Blog not found' 
      });
    }
    
    // Find the entity extraction data
    const entityData = await TempEntityJSON.findOne({ bid: blogId });
    
    if (!entityData || !entityData.name_entity_json) {
      // No entities extracted yet or extraction failed
      return res.json({
        success: true,
        blog_id: blogId,
        blog_title: blog.tittle,
        entities: {},
        message: 'No entities have been extracted for this blog yet'
      });
    }
    
    // Return the entities with blog info
    res.json({
      success: true,
      blog_id: blogId,
      blog_title: blog.tittle,
      entities: entityData.name_entity_json
    });
    
  } catch (error) {
    console.error('Error fetching entity details:', error);
    res.status(500).json({ 
      success: false,
      message: 'Server error while fetching entity details', 
      error: error.message 
    });
  }
});

// @route   GET /api/blogs/:id
// @desc    Get single blog by ID
// @access  Private
router.get('/:id', protect, async (req, res) => {
  try {
    const blog = await Blog.findById(req.params.id).populate('uid', 'username');

    if (!blog) {
      return res.status(404).json({ message: 'Blog not found' });
    }

    const blogObj = blog.toObject();
    
    // Get entity images from TempEntityJSON2
    const entityData = await TempEntityJSON2.findOne({ blog_id: blog._id });
    
    if (entityData && entityData.updated_entities) {
      // Extract all images from entities
      const allImages = [];
      Object.values(entityData.updated_entities).forEach(entityType => {
        Object.values(entityType).forEach(entity => {
          if (entity.images && Array.isArray(entity.images)) {
            allImages.push(...entity.images);
          }
        });
      });
      
      // Add entity images and full entity data to blog
      blogObj.entityImages = allImages;
      blogObj.entityDetails = entityData.updated_entities;
    } else {
      blogObj.entityImages = [];
      blogObj.entityDetails = null;
    }

    // Get blog quality score
    const blogScore = await BlogScore.findOne({ blog_id: blog._id });
    if (blogScore) {
      blogObj.qualityScore = {
        final_score: blogScore.final_score,
        meaning: blogScore.meaning,
        scores: {
          content_depth: blogScore.content_depth_score,
          entity_richness: blogScore.entity_richness_score,
          proof_support: blogScore.proof_support_score,
          authenticity: blogScore.authenticity_score,
          language_quality: blogScore.language_quality_score,
          ai_risk: blogScore.ai_risk_score
        }
      };
    }

    res.json(blogObj);
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// @route   POST /api/blogs
// @desc    Create a new blog
// @access  Private
router.post('/', protect, async (req, res) => {
  try {
    const { tittle, travelexp, imgs } = req.body;

    // Validation
    if (!tittle || !travelexp) {
      return res.status(400).json({ message: 'Please provide title and travel experience' });
    }

    // Validate if content is travel-related
    try {
      console.log('Validating travel content...');
      const validationResponse = await axios.post(
        `${NER_SERVICE_URL}/validate-content`,
        {
          title: tittle,
          travel_experience: travelexp
        },
        { timeout: 10000 } // 10 second timeout
      );

      const validationResult = validationResponse.data;
      console.log(`Validation result: is_valid=${validationResult.is_valid}, confidence=${validationResult.confidence}`);

      // Block blog creation if not travel-related
      if (!validationResult.is_valid) {
        return res.status(400).json({
          message: validationResult.message,
          type: 'validation_error',
          reason: validationResult.reason,
          suggestions: validationResult.suggestions,
          confidence: validationResult.confidence
        });
      }
    } catch (validationError) {
      // Log error but allow blog creation (fail open)
      console.error('Content validation service error:', validationError.message);
      // Proceed with blog creation even if validation fails
    }

    const blog = await Blog.create({
      uid: req.user._id,
      tittle,
      travelexp,
      imgs: imgs || []
    });

    const populatedBlog = await Blog.findById(blog._id).populate('uid', 'username');

    // Call NER service to extract entities
    let extractedEntities = null;
    try {
      console.log('Calling NER service for entity extraction...');
      const nerResponse = await axios.post(`${NER_SERVICE_URL}/extract-entities`, {
        user_id: req.user._id.toString(),
        blog_id: blog._id.toString(),
        title: tittle,
        travel_experience: travelexp
      }, {
        timeout: 30000 // 30 second timeout
      });
      console.log('NER extraction successful:', nerResponse.data.message);
      
      // Store entities from NER response
      if (nerResponse.data.success && nerResponse.data.entities) {
        extractedEntities = nerResponse.data.entities;
      }
    } catch (nerError) {
      // Log error but don't fail blog creation
      console.error('NER extraction failed:', nerError.message);
      if (nerError.response) {
        console.error('NER error details:', nerError.response.data);
      }
    }

    // Return blog with entities
    res.status(201).json({
      ...populatedBlog.toObject(),
      entities: extractedEntities
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// @route   DELETE /api/blogs/:id
// @desc    Delete user's own blog
// @access  Private
router.delete('/:id', protect, async (req, res) => {
  try {
    const blog = await Blog.findById(req.params.id);

    if (!blog) {
      return res.status(404).json({ message: 'Blog not found' });
    }

    // Check if user owns the blog
    if (blog.uid.toString() !== req.user._id.toString()) {
      return res.status(403).json({ message: 'Not authorized to delete this blog' });
    }

    await Blog.findByIdAndDelete(req.params.id);

    res.json({ message: 'Blog deleted successfully' });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// @route   POST /api/blogs/:id/entity-details
// @desc    Save entity details with images
// @access  Private
router.post('/:id/entity-details', protect, upload.any(), async (req, res) => {
  try {
    const blogId = req.params.id;
    
    // Validate ObjectId format
    if (!mongoose.Types.ObjectId.isValid(blogId)) {
      return res.status(400).json({ 
        success: false,
        message: 'Invalid blog ID format' 
      });
    }
    
    // Find the blog to verify it exists and user owns it
    const blog = await Blog.findById(blogId);
    
    if (!blog) {
      return res.status(404).json({ 
        success: false,
        message: 'Blog not found' 
      });
    }
    
    // Check if user owns the blog
    if (blog.uid.toString() !== req.user._id.toString()) {
      return res.status(403).json({ 
        success: false,
        message: 'Not authorized to update this blog' 
      });
    }
    
    // Parse the entity data from form data
    const entityData = JSON.parse(req.body.entityData || '{}');
    
    // Get the original NER entities
    const originalEntityData = await TempEntityJSON.findOne({ bid: blogId });
    const originalEntities = originalEntityData?.name_entity_json || {};
    
    // Process uploaded images and extract EXIF data
    const uploadedImages = {};
    const imageExifData = {}; // Store EXIF data before Cloudinary strips it
    
    if (req.files && req.files.length > 0) {
      console.log(`Processing ${req.files.length} uploaded images...`);
      
      // Group files by their field names (entityType-entityId)
      for (const file of req.files) {
        const fieldName = file.fieldname; // Format: "images_hotels_hotel1"
        const parts = fieldName.split('_');
        
        if (parts.length >= 3 && parts[0] === 'images') {
          const entityType = parts[1];
          const entityId = parts.slice(2).join('_');
          
          try {
            // Extract EXIF data BEFORE uploading to Cloudinary
            let exifInfo = null;
            try {
              const parser = exifParser.create(file.buffer);
              const result = parser.parse();
              if (result && result.tags) {
                exifInfo = {
                  make: result.tags.Make || null,
                  model: result.tags.Model || null,
                  dateTime: result.tags.DateTime || result.tags.DateTimeOriginal || null,
                  software: result.tags.Software || null,
                  gps: result.tags.GPSLatitude && result.tags.GPSLongitude ? {
                    latitude: result.tags.GPSLatitude,
                    longitude: result.tags.GPSLongitude
                  } : null,
                  tagCount: Object.keys(result.tags).length
                };
                console.log(`  Extracted EXIF: ${exifInfo.tagCount} tags, Make: ${exifInfo.make || 'N/A'}, Model: ${exifInfo.model || 'N/A'}`);
              }
            } catch (exifError) {
              console.log(`  No EXIF data found (may be screenshot or edited image)`);
            }
            
            // Upload to Cloudinary (EXIF will be stripped)
            const imageUrl = await uploadImage(file.buffer, `travel-entities/${entityType}`);
            
            // Store the URL
            if (!uploadedImages[entityType]) {
              uploadedImages[entityType] = {};
            }
            if (!uploadedImages[entityType][entityId]) {
              uploadedImages[entityType][entityId] = [];
            }
            uploadedImages[entityType][entityId].push(imageUrl);
            
            // Store EXIF data mapped to image URL
            if (!imageExifData[entityType]) {
              imageExifData[entityType] = {};
            }
            if (!imageExifData[entityType][entityId]) {
              imageExifData[entityType][entityId] = [];
            }
            imageExifData[entityType][entityId].push({
              url: imageUrl,
              exif: exifInfo
            });
            
            console.log(`Uploaded image for ${entityType}/${entityId}: ${imageUrl}`);
          } catch (uploadError) {
            console.error(`Failed to upload image for ${entityType}/${entityId}:`, uploadError);
            // Continue with other images even if one fails
          }
        }
      }
    }
    
    // Merge original entities with user updates and image URLs
    const updatedEntities = {};
    
    Object.keys(originalEntities).forEach(entityType => {
      updatedEntities[entityType] = {};
      
      Object.keys(originalEntities[entityType]).forEach(entityId => {
        // Start with original entity data
        const mergedEntity = { ...originalEntities[entityType][entityId] };
        
        // Apply user updates from form data
        if (entityData[entityType] && entityData[entityType][entityId]) {
          Object.keys(entityData[entityType][entityId]).forEach(field => {
            const value = entityData[entityType][entityId][field];
            if (value !== undefined && value !== null && value !== '') {
              mergedEntity[field] = value;
            }
          });
        }
        
        // Add image URLs and EXIF data
        if (uploadedImages[entityType] && uploadedImages[entityType][entityId]) {
          mergedEntity.images = uploadedImages[entityType][entityId];
          // Also store EXIF data for forensic analysis
          mergedEntity.images_exif = imageExifData[entityType]?.[entityId] || [];
        } else {
          mergedEntity.images = [];
          mergedEntity.images_exif = [];
        }
        
        updatedEntities[entityType][entityId] = mergedEntity;
      });
    });
    
    // Check if a record already exists for this user and blog
    let entityRecord = await TempEntityJSON2.findOne({
      user_id: req.user._id,
      blog_id: blogId
    });
    
    if (entityRecord) {
      // Update existing record
      entityRecord.updated_entities = updatedEntities;
      await entityRecord.save();
      console.log(`Updated existing entity details for blog ${blogId}`);
    } else {
      // Create new record
      entityRecord = await TempEntityJSON2.create({
        user_id: req.user._id,
        blog_id: blogId,
        updated_entities: updatedEntities
      });
      console.log(`Created new entity details for blog ${blogId}`);
      console.log(`  Document _id: ${entityRecord._id}`);
    }
    
    // Verify the document was created and log its structure
    const verifyDoc = await TempEntityJSON2.findOne({ blog_id: blogId });
    if (!verifyDoc) {
      console.error(`⚠ Warning: Document not found immediately after creation for blog ${blogId}`);
    } else {
      console.log(`✓ Verified document exists in database`);
      console.log(`  Document ID: ${verifyDoc._id}`);
      console.log(`  Entity types: ${Object.keys(verifyDoc.updated_entities).join(', ')}`);
      
      // Log image and EXIF counts per entity type
      let totalImages = 0;
      let totalWithExif = 0;
      
      Object.keys(verifyDoc.updated_entities).forEach(entityType => {
        const entities = verifyDoc.updated_entities[entityType];
        Object.keys(entities).forEach(entityId => {
          const entity = entities[entityId];
          const imageCount = entity.images?.length || 0;
          const exifCount = entity.images_exif?.filter(e => e.exif).length || 0;
          totalImages += imageCount;
          totalWithExif += exifCount;
        });
      });
      
      console.log(`  Total images: ${totalImages}, with EXIF: ${totalWithExif}`);
    }
    
    // Trigger image verification asynchronously (don't block response)
    // This will analyze all images and update scores in TempEntityJSON2
    const triggerVerification = async () => {
      try {
        console.log(`Triggering image verification for blog ${blogId}...`);
        const verificationResponse = await axios.post(
          `${FORENSIC_SERVICE_URL}/verify-blog`,
          { blog_id: blogId },
          { timeout: 120000 } // 2 minute timeout
        );
        console.log(`✓ Image verification completed for blog ${blogId}`);
        console.log(`  - Entities processed: ${verificationResponse.data.entities_processed}`);
        console.log(`  - Images analyzed: ${verificationResponse.data.images_analyzed}`);
        
        // Process the forensic response (normalize verdicts and calculate overall scores)
        try {
          console.log(`\n📊 Processing forensic response for blog ${blogId}...`);
          const processedResponse = processForensicResponse(verificationResponse.data);
          const metadata = extractMetadata(verificationResponse.data);
          
          // Store processed response in image_ai_score collection
          const aiScoreRecord = await ImageAIScore.create({
            blog_id: blogId,
            verification_response: processedResponse,
            metadata: metadata
          });
          
          console.log(`✓ Stored AI score record in database:`);
          console.log(`  - Record ID: ${aiScoreRecord._id}`);
          console.log(`  - Blog ID: ${aiScoreRecord.blog_id}`);
          console.log(`  - Entities processed: ${metadata.entities_processed}`);
          console.log(`  - Images analyzed: ${metadata.images_analyzed}`);
          
          // Log overall scores by category
          if (processedResponse.verification_results) {
            console.log(`\n  Overall Scores by Category:`);
            Object.entries(processedResponse.verification_results).forEach(([category, data]) => {
              console.log(`    - ${category}: ${data.overall_score.toFixed(2)}`);
            });
          }
        } catch (processingError) {
          console.error(`⚠ Failed to process and store AI score for blog ${blogId}:`, processingError.message);
        }
        
        // Fetch and log the updated document with scores
        const updatedDoc = await TempEntityJSON2.findOne({ blog_id: blogId });
        if (updatedDoc) {
          console.log(`\n✓ FINAL CHECK: Document with scores in MongoDB`);
          console.log(`  Document ID: ${updatedDoc._id}`);
          console.log(`  Scores by entity:`);
          
          Object.keys(updatedDoc.updated_entities).forEach(entityType => {
            const entities = updatedDoc.updated_entities[entityType];
            Object.keys(entities).forEach(entityId => {
              const entity = entities[entityId];
              if (entity.images && entity.images.length > 0) {
                console.log(`    - ${entityType}/${entityId} (${entity.name}): score=${entity.score}, images=${entity.images.length}`);
              }
            });
          });
        }
      } catch (verificationError) {
        // Log error but don't fail the main request
        console.error(`⚠ Image verification failed for blog ${blogId}:`, verificationError.message);
        if (verificationError.response) {
          console.error('  Error details:', verificationError.response.data);
        }
      }
    };
    
    // Trigger verification in background (non-blocking)
    triggerVerification().catch(err => {
      console.error('Verification trigger error:', err);
    });
    
    // Trigger blog scoring asynchronously (don't block response)
    const triggerBlogScoring = async () => {
      try {
        console.log(`Triggering blog scoring for blog ${blogId}...`);
        const scoreResponse = await axios.post(
          `${BLOG_SCORE_SERVICE_URL}/score-blog`,
          { blog_id: blogId },
          { timeout: 60000 } // 60 second timeout
        );
        console.log(`✓ Blog scoring completed for blog ${blogId}`);
        console.log(`  - Final score: ${scoreResponse.data.final_score}/100`);
        console.log(`  - Meaning: ${scoreResponse.data.meaning}`);
        console.log(`  - Score breakdown:`);
        console.log(`    - Content depth: ${scoreResponse.data.scores.content_depth_score}`);
        console.log(`    - Entity richness: ${scoreResponse.data.scores.entity_richness_score}`);
        console.log(`    - Proof support: ${scoreResponse.data.scores.proof_support_score}`);
        console.log(`    - Authenticity: ${scoreResponse.data.scores.authenticity_score}`);
        console.log(`    - Language quality: ${scoreResponse.data.scores.language_quality_score}`);
        console.log(`    - AI risk: ${scoreResponse.data.scores.ai_risk_score}`);
      } catch (scoringError) {
        console.error(`⚠ Blog scoring failed for blog ${blogId}:`, scoringError.message);
        if (scoringError.response) {
          console.error('  Error details:', scoringError.response.data);
        }
      }
    };
    
    // Trigger in background (non-blocking)
    triggerBlogScoring().catch(err => {
      console.error('Blog scoring trigger error:', err);
    });
    
    res.json({
      success: true,
      message: 'Entity details saved successfully',
      data: {
        blog_id: blogId,
        entities: updatedEntities,
        images_uploaded: Object.values(uploadedImages).reduce(
          (total, entityType) => total + Object.values(entityType).reduce(
            (sum, images) => sum + images.length, 0
          ), 0
        )
      }
    });
    
  } catch (error) {
    console.error('Error saving entity details:', error);
    
    if (error instanceof multer.MulterError) {
      if (error.code === 'LIMIT_FILE_SIZE') {
        return res.status(400).json({ 
          success: false,
          message: 'File size too large. Maximum size is 5MB per file.' 
        });
      }
      return res.status(400).json({ 
        success: false,
        message: `Upload error: ${error.message}` 
      });
    }
    
    res.status(500).json({ 
      success: false,
      message: 'Server error while saving entity details', 
      error: error.message 
    });
  }
});

export default router;
