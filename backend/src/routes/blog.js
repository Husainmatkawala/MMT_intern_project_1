import express from 'express';
import axios from 'axios';
import Blog from '../models/Blog.js';
import User from '../models/User.js';
import { protect } from '../middleware/auth.js';

const router = express.Router();

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

    res.json(blogs);
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

    res.json(blogs);
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: 'Server error', error: error.message });
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

    // Call NER service to extract entities (non-blocking)
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
    } catch (nerError) {
      // Log error but don't fail blog creation
      console.error('NER extraction failed:', nerError.message);
      if (nerError.response) {
        console.error('NER error details:', nerError.response.data);
      }
    }

    res.status(201).json(populatedBlog);
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

export default router;
