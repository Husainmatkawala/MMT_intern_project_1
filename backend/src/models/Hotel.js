import mongoose from 'mongoose';

const hotelSchema = new mongoose.Schema({
  hotel_name: {
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

// Compound unique index for deduplication based on (hotel_name, city, state)
hotelSchema.index({ hotel_name: 1, city: 1, state: 1 }, { unique: true });

const Hotel = mongoose.model('Hotel', hotelSchema);

export default Hotel;
