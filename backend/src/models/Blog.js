import mongoose from 'mongoose';

const blogSchema = new mongoose.Schema({
  uid: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  tittle: {
    type: String,
    required: true,
    trim: true
  },
  travelexp: {
    type: String,
    required: true
  },
  imgs: {
    type: [String],
    default: []
  }
}, {
  timestamps: true
});

// Create blog_id as alias for _id
blogSchema.virtual('blog_id').get(function() {
  return this._id.toHexString();
});

blogSchema.set('toJSON', { virtuals: true });
blogSchema.set('toObject', { virtuals: true });

const Blog = mongoose.model('Blog', blogSchema);

export default Blog;
