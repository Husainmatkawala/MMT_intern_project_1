import mongoose from 'mongoose';

const blogScoreSchema = new mongoose.Schema({
  blog_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Blog',
    required: true,
    unique: true,
    index: true
  },
  content_depth_score: {
    type: Number,
    default: 0,
    min: 0,
    max: 20
  },
  entity_richness_score: {
    type: Number,
    default: 0,
    min: 0,
    max: 20
  },
  proof_support_score: {
    type: Number,
    default: 0,
    min: 0,
    max: 20
  },
  authenticity_score: {
    type: Number,
    default: 0,
    min: 0,
    max: 15
  },
  language_quality_score: {
    type: Number,
    default: 0,
    min: 0,
    max: 15
  },
  ai_risk_score: {
    type: Number,
    default: 0,
    min: 0,
    max: 10
  },
  final_score: {
    type: Number,
    default: 0,
    min: 0,
    max: 100
  },
  meaning: {
    type: String,
    enum: ['exceptional', 'very good', 'average', 'weak', 'low quality'],
    default: 'low quality'
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
}, {
  collection: 'blogscores',
  timestamps: false // Using custom createdAt and updatedAt fields
});

// Index for efficient lookups by blog_id
blogScoreSchema.index({ blog_id: 1 });

// Index for sorting by score
blogScoreSchema.index({ final_score: -1 });

const BlogScore = mongoose.model('BlogScore', blogScoreSchema);

export default BlogScore;
