import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiUser, FiCalendar, FiImage, FiChevronLeft, FiChevronRight, FiMapPin } from 'react-icons/fi';
import { blogAPI } from '../utils/api';
import Header from '../components/Header';

const BlogDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [blog, setBlog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  useEffect(() => {
    fetchBlog();
  }, [id]);

  const fetchBlog = async () => {
    try {
      setLoading(true);
      const response = await blogAPI.getBlog(id);
      setBlog(response.data);
    } catch (err) {
      console.error('Error fetching blog:', err);
      setError(err.response?.data?.message || 'Failed to load blog');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const handlePrevImage = () => {
    setCurrentImageIndex((prev) => (prev === 0 ? allImages.length - 1 : prev - 1));
  };

  const handleNextImage = () => {
    setCurrentImageIndex((prev) => (prev === allImages.length - 1 ? 0 : prev + 1));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <Header />
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (error || !blog) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <Header />
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
            <p className="text-red-800 dark:text-red-300 mb-4">{error || 'Blog not found'}</p>
            <button onClick={() => navigate(-1)} className="btn-primary">
              Go Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  const entityImages = blog.entityImages || [];
  const blogImages = blog.imgs || [];
  const allImages = [...entityImages, ...blogImages];
  const hasImages = allImages.length > 0;
  const hasMultipleImages = allImages.length > 1;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <Header />
      
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Back Button */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 mb-6 transition-colors"
        >
          <FiArrowLeft className="w-5 h-5" />
          <span className="font-semibold">Back to Blogs</span>
        </button>

        {/* Hero Image Carousel */}
        {hasImages && (
          <div className="relative h-96 md:h-[500px] rounded-2xl overflow-hidden mb-8 bg-gradient-to-br from-primary-100 to-purple-100 dark:from-gray-700 dark:to-gray-600">
            <img
              src={allImages[currentImageIndex]}
              alt={`${blog.tittle} - Image ${currentImageIndex + 1}`}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.src = 'https://via.placeholder.com/1200x600?text=Image+Not+Available';
              }}
            />
            
            {hasMultipleImages && (
              <>
                {/* Navigation Buttons */}
                <button
                  onClick={handlePrevImage}
                  className="absolute left-4 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white rounded-full p-4 backdrop-blur-sm transition-all duration-200 hover:scale-110"
                >
                  <FiChevronLeft className="w-6 h-6" />
                </button>
                <button
                  onClick={handleNextImage}
                  className="absolute right-4 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white rounded-full p-4 backdrop-blur-sm transition-all duration-200 hover:scale-110"
                >
                  <FiChevronRight className="w-6 h-6" />
                </button>

                {/* Image Indicators */}
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
                  {allImages.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentImageIndex(index)}
                      className={`w-2.5 h-2.5 rounded-full transition-all duration-200 ${
                        index === currentImageIndex
                          ? 'bg-white w-10'
                          : 'bg-white/50 hover:bg-white/75'
                      }`}
                    />
                  ))}
                </div>

                {/* Image Counter */}
                <div className="absolute top-4 right-4 bg-black/50 backdrop-blur-sm text-white px-4 py-2 rounded-full font-semibold">
                  {currentImageIndex + 1} / {allImages.length}
                </div>
              </>
            )}
          </div>
        )}

        {/* Main Content Card */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 md:p-10 mb-8">
          {/* Title */}
          <h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 dark:text-white mb-6 leading-tight">
            {blog.tittle}
          </h1>

          {/* Meta Information */}
          <div className="flex flex-wrap items-center gap-6 pb-6 mb-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
              <FiUser className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              <span className="font-medium">{blog.uid?.username || 'Anonymous'}</span>
            </div>
            <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
              <FiCalendar className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              <span className="font-medium">{formatDate(blog.createdAt)}</span>
            </div>
            {hasImages && (
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                <FiImage className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                <span className="font-medium">{allImages.length} {allImages.length === 1 ? 'Photo' : 'Photos'}</span>
              </div>
            )}
          </div>

          {/* Travel Experience */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <FiMapPin className="text-primary-600 dark:text-primary-400" />
              Travel Experience
            </h2>
            <div className="prose prose-lg dark:prose-invert max-w-none">
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                {blog.travelexp}
              </p>
            </div>
          </div>

          {/* All Photos Gallery */}
          {allImages.length > 1 && (
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                All Photos
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                {allImages.map((img, index) => (
                  <div
                    key={index}
                    onClick={() => setCurrentImageIndex(index)}
                    className="relative aspect-square rounded-xl overflow-hidden bg-gray-200 dark:bg-gray-700 cursor-pointer group hover:ring-4 hover:ring-primary-500 transition-all"
                  >
                    <img
                      src={img}
                      alt={`Photo ${index + 1}`}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                      onError={(e) => {
                        e.target.src = 'https://via.placeholder.com/400x400?text=Image';
                      }}
                    />
                    {index === currentImageIndex && (
                      <div className="absolute inset-0 bg-primary-500/30 flex items-center justify-center">
                        <div className="bg-white dark:bg-gray-800 rounded-full p-2">
                          <FiImage className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Entity Details */}
          {blog.entityDetails && (
            <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                Travel Details
              </h2>
              <div className="space-y-6">
                {Object.entries(blog.entityDetails).map(([entityType, entities]) => (
                  <div key={entityType} className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-6">
                    <h3 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-4 capitalize">
                      {entityType}
                    </h3>
                    <div className="grid gap-4">
                      {Object.entries(entities).map(([entityId, entity]) => (
                        <div key={entityId} className="bg-white dark:bg-gray-800 rounded-lg p-4">
                          {entity.name && (
                            <p className="font-semibold text-gray-900 dark:text-white mb-2">
                              {entity.name}
                            </p>
                          )}
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {entity.city && (
                              <p className="text-gray-600 dark:text-gray-400">
                                <span className="font-medium">City:</span> {entity.city}
                              </p>
                            )}
                            {entity.state && (
                              <p className="text-gray-600 dark:text-gray-400">
                                <span className="font-medium">State:</span> {entity.state}
                              </p>
                            )}
                            {entity.rating && (
                              <p className="text-gray-600 dark:text-gray-400">
                                <span className="font-medium">Rating:</span> ⭐ {entity.rating}
                              </p>
                            )}
                            {entity.contact && (
                              <p className="text-gray-600 dark:text-gray-400">
                                <span className="font-medium">Contact:</span> {entity.contact}
                              </p>
                            )}
                            {entity.type && (
                              <p className="text-gray-600 dark:text-gray-400">
                                <span className="font-medium">Type:</span> {entity.type}
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BlogDetail;
