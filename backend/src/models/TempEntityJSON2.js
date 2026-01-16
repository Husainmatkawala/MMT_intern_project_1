import mongoose from 'mongoose';

const tempEntityJSON2Schema = new mongoose.Schema({
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
tempEntityJSON2Schema.index({ user_id: 1, blog_id: 1 });

const TempEntityJSON2 = mongoose.model('TempEntityJSON2', tempEntityJSON2Schema);

export default TempEntityJSON2;
