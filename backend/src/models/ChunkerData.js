import mongoose from 'mongoose';

const chunkerDataSchema = new mongoose.Schema({
  user_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  blog_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Blog',
    required: true,
    index: true
  },
  updated_entities: {
    type: mongoose.Schema.Types.Mixed,
    required: true,
    default: {}
  }
}, {
  timestamps: true
});

// Compound index for efficient queries
chunkerDataSchema.index({ user_id: 1, blog_id: 1 });

const ChunkerData = mongoose.model('ChunkerData', chunkerDataSchema);

export default ChunkerData;
