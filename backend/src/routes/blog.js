import express from 'express';
import axios from 'axios';
import mongoose from 'mongoose';
import multer from 'multer';
import Blog from '../models/Blog.js';
import User from '../models/User.js';
import TempEntityJSON from '../models/TempEntityJSON.js';
import TempEntityJSON2 from '../models/TempEntityJSON2.js';
import { protect } from '../middleware/auth.js';
import { uploadImage } from '../config/cloudinary.js';

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

// @route   GET /api/blogs
// @desc    Get all blogs from all users
// @access  Private
router.get('/', protect, async (req, res) => {
  try {
    const blogs = await Blog.find()
      .populate('uid', 'username')
      .sort({ createdAt: -1 });
    
    // Fetch entity images for each blog
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

    // Fetch entity images for each blog
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

    res.json(blog);
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
    
    // Process uploaded images
    const uploadedImages = {};
    
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
            // Upload to Cloudinary
            const imageUrl = await uploadImage(file.buffer, `travel-entities/${entityType}`);
            
            // Store the URL
            if (!uploadedImages[entityType]) {
              uploadedImages[entityType] = {};
            }
            if (!uploadedImages[entityType][entityId]) {
              uploadedImages[entityType][entityId] = [];
            }
            uploadedImages[entityType][entityId].push(imageUrl);
            
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
        
        // Add image URLs
        if (uploadedImages[entityType] && uploadedImages[entityType][entityId]) {
          mergedEntity.images = uploadedImages[entityType][entityId];
        } else {
          mergedEntity.images = [];
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
    }
    
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
