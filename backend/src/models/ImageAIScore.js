import mongoose from 'mongoose';

const imageAIScoreSchema = new mongoose.Schema({
  blog_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Blog',
    required: true,
    index: true
  },
  verification_response: {
    type: mongoose.Schema.Types.Mixed,
    required: true
  },
  created_at: {
    type: Date,
    default: Date.now,
    index: true
  },
  metadata: {
    entities_processed: {
      type: Number,
      default: 0
    },
    images_analyzed: {
      type: Number,
      default: 0
    },
    timestamp: {
      type: Date
    }
  }
}, {
  timestamps: false // Using custom created_at field
});

// Compound index for efficient queries by blog_id and date
imageAIScoreSchema.index({ blog_id: 1, created_at: -1 });

const ImageAIScore = mongoose.model('ImageAIScore', imageAIScoreSchema);

export default ImageAIScore;
