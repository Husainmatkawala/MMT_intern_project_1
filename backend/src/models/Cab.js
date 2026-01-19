import mongoose from 'mongoose';

const cabSchema = new mongoose.Schema({
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
cabSchema.index({ service_name: 1, city: 1, state: 1 }, { unique: true });

const Cab = mongoose.model('Cab', cabSchema);

export default Cab;
