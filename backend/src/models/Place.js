import mongoose from 'mongoose';

const placeSchema = new mongoose.Schema({
  place_name: {
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

// Compound unique index for deduplication based on (place_name, city, state)
placeSchema.index({ place_name: 1, city: 1, state: 1 }, { unique: true });

const Place = mongoose.model('Place', placeSchema);

export default Place;
