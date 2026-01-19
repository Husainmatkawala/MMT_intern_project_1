import mongoose from 'mongoose';

const activitySchema = new mongoose.Schema({
  activity_name: {
    type: String,
    required: true,
    default: ""
  },
  type: {
    type: String,
    required: true,
    default: ""
  },
  city: {
    type: String,
    required: true,
    default: ""
  },
  state: {
    type: String,
    required: true,
    default: ""
  },
  description: {
    type: [String],
    default: []
  },
  image_urls: {
    type: [String],
    default: []
  }
}, {
  timestamps: true
});

// Compound unique index for deduplication based on (activity_name, city, state)
activitySchema.index({ activity_name: 1, city: 1, state: 1 }, { unique: true });

const Activity = mongoose.model('Activity', activitySchema);

export default Activity;
