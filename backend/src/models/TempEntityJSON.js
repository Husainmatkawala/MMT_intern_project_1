import mongoose from 'mongoose';

const tempEntityJSONSchema = new mongoose.Schema({
  uid: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  bid: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Blog',
    required: true
  },
  name_entity_json: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  }
}, {
  timestamps: true
});

const TempEntityJSON = mongoose.model('TempEntityJSON', tempEntityJSONSchema);

export default TempEntityJSON;
