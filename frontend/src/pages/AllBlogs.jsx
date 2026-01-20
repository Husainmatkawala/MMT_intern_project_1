import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { blogAPI } from '../utils/api';
import Header from '../components/Header';
import BlogCard from '../components/BlogCard';
import { FiGlobe, FiAlertCircle } from 'react-icons/fi';

const AllBlogs = () => {
  const [blogs, setBlogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchBlogs();
  }, []);

  const fetchBlogs = async () => {
    try {
      setLoading(true);
      const response = await blogAPI.getAllBlogs();
      setBlogs(response.data);
      setError('');
    } catch (err) {
      setError('Failed to load blogs. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <Header />
      
      {/* Hero Background Section */}
      <div 
        className="h-[50vh] w-full bg-cover bg-center relative"
        style={{ backgroundImage: "url('/hero-background.jpg')" }}
      >
        <div className="absolute inset-0 bg-black/30" />
        <div className="relative h-full flex items-center justify-center">
          <div className="text-center text-white px-4">
            <h1 className="text-5xl md:text-6xl font-bold mb-4 drop-shadow-lg">
              Explore Travel Stories
            </h1>
            <p className="text-xl md:text-2xl drop-shadow-md">
              Discover authentic experiences from travelers worldwide
            </p>
          </div>
        </div>
      </div>

      {/* Content Section */}
      <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 dark:from-primary-400 dark:to-purple-400 bg-clip-text text-transparent mb-2 flex items-center gap-3">
            <FiGlobe className="text-primary-600 dark:text-primary-400" />
            All Travel Blogs
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Explore travel experiences from our community
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-2 text-red-800 dark:text-red-300">
            <FiAlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && blogs.length === 0 && (
          <div className="text-center py-20">
            <div className="inline-block p-6 bg-gray-100 dark:bg-gray-800 rounded-full mb-4">
              <FiGlobe className="w-16 h-16 text-gray-400" />
            </div>
            <h3 className="text-2xl font-bold text-gray-700 dark:text-gray-300 mb-2">
              No blogs yet
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Be the first to share your travel experience!
            </p>
          </div>
        )}

        {/* Blogs List - Vertical Single Column */}
        {!loading && !error && blogs.length > 0 && (
          <div className="space-y-8">
            {blogs.map((blog) => (
              <BlogCard 
                key={blog._id} 
                blog={blog}
                onClick={(blogId) => navigate(`/blog/${blogId}`)}
              />
            ))}
          </div>
        )}

        {/* Blog Count */}
        {!loading && blogs.length > 0 && (
          <div className="mt-8 text-center text-gray-600 dark:text-gray-400">
            Showing {blogs.length} {blogs.length === 1 ? 'blog' : 'blogs'}
          </div>
        )}
        </div>
      </div>
    </div>
  );
};

export default AllBlogs;
