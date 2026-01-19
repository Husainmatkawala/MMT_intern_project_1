import mongoose from 'mongoose';

const busSchema = new mongoose.Schema({
  service_name: {
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
  rating: {
    type: [String],
    default: []
  },
  contact: {
    type: [String],
    default: []
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

// Compound unique index for deduplication based on (service_name, city, state)
busSchema.index({ service_name: 1, city: 1, state: 1 }, { unique: true });

const Bus = mongoose.model('Bus', busSchema);

export default Bus;
