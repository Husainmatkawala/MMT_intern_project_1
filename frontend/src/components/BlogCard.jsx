import { FiMapPin, FiUser, FiCalendar, FiImage } from 'react-icons/fi';

const BlogCard = ({ blog, onDelete, showDelete = false }) => {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="section-card hover:shadow-xl transition-shadow duration-300">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-2xl font-bold text-gray-900 dark:text-white flex-1">
          {blog.tittle}
        </h3>
        {showDelete && (
          <button
            onClick={() => onDelete(blog._id)}
            className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 font-semibold text-sm"
          >
            Delete
          </button>
        )}
      </div>

      {/* Meta Info */}
      <div className="flex flex-wrap items-center gap-4 mb-4 text-sm text-gray-600 dark:text-gray-400">
        <span className="flex items-center gap-1">
          <FiUser className="w-4 h-4" />
          {blog.uid?.username || 'Anonymous'}
        </span>
        <span className="flex items-center gap-1">
          <FiCalendar className="w-4 h-4" />
          {formatDate(blog.createdAt)}
        </span>
        {blog.imgs && blog.imgs.length > 0 && (
          <span className="flex items-center gap-1">
            <FiImage className="w-4 h-4" />
            {blog.imgs.length} {blog.imgs.length === 1 ? 'image' : 'images'}
          </span>
        )}
      </div>

      {/* Experience Text */}
      <div className="mb-4">
        <p className="text-gray-700 dark:text-gray-300 leading-relaxed line-clamp-4">
          {blog.travelexp}
        </p>
      </div>

      {/* Images */}
      {blog.imgs && blog.imgs.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-4">
          {blog.imgs.slice(0, 3).map((img, index) => (
            <div key={index} className="relative aspect-video rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700">
              <img
                src={img}
                alt={`Travel ${index + 1}`}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.src = 'https://via.placeholder.com/400x300?text=Image+Not+Found';
                }}
              />
              {index === 2 && blog.imgs.length > 3 && (
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center text-white font-bold text-lg">
                  +{blog.imgs.length - 3}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BlogCard;
