import { FiUser, FiCalendar, FiImage, FiTrash2 } from 'react-icons/fi';
import { useState } from 'react';

const BlogCard = ({ blog, onDelete, showDelete = false }) => {
  const [imageError, setImageError] = useState(false);
  
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // Get all available images from entity images (uploaded by user)
  const entityImages = blog.entityImages && Array.isArray(blog.entityImages) ? blog.entityImages : [];
  const blogImages = blog.imgs && Array.isArray(blog.imgs) ? blog.imgs : [];
  const allImages = [...entityImages, ...blogImages];
  const hasImages = allImages.length > 0;
  const heroImage = hasImages ? allImages[0] : null;
  const galleryImages = allImages.slice(1);

  return (
    <article className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden border border-gray-200 dark:border-gray-700 group">
      {/* Hero Image Section - Only show if images exist */}
      {heroImage && !imageError && (
        <div className="relative h-80 md:h-96 overflow-hidden bg-gradient-to-br from-primary-100 to-purple-100 dark:from-gray-700 dark:to-gray-600">
          <img
            src={heroImage}
            alt={blog.tittle}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            onError={() => setImageError(true)}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent"></div>
          
          {/* Floating Author Badge */}
          <div className="absolute top-4 left-4 bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm rounded-full px-4 py-2 shadow-lg">
            <span className="flex items-center gap-2 text-sm font-semibold text-gray-800 dark:text-gray-200">
              <FiUser className="w-4 h-4 text-primary-600 dark:text-primary-400" />
              {blog.uid?.username || 'Anonymous'}
            </span>
          </div>

          {/* Delete Button (if applicable) */}
          {showDelete && (
            <button
              onClick={() => onDelete(blog._id)}
              className="absolute top-4 right-4 bg-red-500 hover:bg-red-600 text-white rounded-full p-3 shadow-lg transition-all duration-200 hover:scale-110"
              title="Delete blog"
            >
              <FiTrash2 className="w-5 h-5" />
            </button>
          )}
        </div>
      )}

      {/* Content Section */}
      <div className="p-6 md:p-8">
        {/* Title */}
        <h2 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white mb-4 leading-tight">
          {blog.tittle}
        </h2>

        {/* Meta Information */}
        <div className="flex flex-wrap items-center gap-4 mb-6 pb-6 border-b border-gray-200 dark:border-gray-700">
          {/* Author - only show if no hero image */}
          {!heroImage && (
            <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
              <FiUser className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              <span className="text-sm font-medium">{blog.uid?.username || 'Anonymous'}</span>
            </div>
          )}
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
            <FiCalendar className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            <span className="text-sm font-medium">{formatDate(blog.createdAt)}</span>
          </div>
          {hasImages && (
            <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
              <FiImage className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              <span className="text-sm font-medium">
                {allImages.length} {allImages.length === 1 ? 'Photo' : 'Photos'}
              </span>
            </div>
          )}
          
          {/* Delete Button for cards without hero image */}
          {showDelete && !heroImage && (
            <button
              onClick={() => onDelete(blog._id)}
              className="ml-auto bg-red-500 hover:bg-red-600 text-white rounded-full px-4 py-2 shadow-lg transition-all duration-200 hover:scale-105 flex items-center gap-2"
              title="Delete blog"
            >
              <FiTrash2 className="w-4 h-4" />
              <span className="text-sm font-semibold">Delete</span>
            </button>
          )}
        </div>

        {/* Travel Experience */}
        <div className="mb-6">
          <h3 className="text-sm font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
            Travel Experience
          </h3>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed text-lg line-clamp-6">
            {blog.travelexp}
          </p>
        </div>

        {/* Image Gallery */}
        {galleryImages.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
              More Photos
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {galleryImages.slice(0, 7).map((img, index) => (
                <div 
                  key={index} 
                  className="relative aspect-square rounded-xl overflow-hidden bg-gray-200 dark:bg-gray-700 group/img"
                >
                  <img
                    src={img}
                    alt={`Travel photo ${index + 2}`}
                    className="w-full h-full object-cover group-hover/img:scale-110 transition-transform duration-300"
                    onError={(e) => {
                      e.target.src = 'https://via.placeholder.com/300x300?text=Image';
                    }}
                  />
                  {index === 6 && galleryImages.length > 7 && (
                    <div className="absolute inset-0 bg-black/70 flex items-center justify-center text-white font-bold text-xl">
                      +{galleryImages.length - 7}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Read More Indicator */}
        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between text-primary-600 dark:text-primary-400 font-semibold">
            <span className="text-sm">Click to read full experience</span>
            <svg className="w-5 h-5 group-hover:translate-x-2 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </div>
    </article>
  );
};

export default BlogCard;
