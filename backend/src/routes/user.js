import express from 'express';
import User from '../models/User.js';
import Blog from '../models/Blog.js';
import { protect } from '../middleware/auth.js';

const router = express.Router();

// @route   GET /api/users/profile
// @desc    Get user profile with stats
// @access  Private
router.get('/profile', protect, async (req, res) => {
  try {
    const user = await User.findById(req.user._id).select('-password');
    const blogCount = await Blog.countDocuments({ uid: req.user._id });

    res.json({
      _id: user._id,
      uid: user.uid,
      username: user.username,
      score: user.score,
      blogCount
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

export default router;
