import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiX, FiCheck, FiInfo, FiAward } from 'react-icons/fi';
import { blogAPI } from '../utils/api';
import Header from '../components/Header';

const CreateBlog = () => {
  const [formData, setFormData] = useState({
    tittle: '',
    travelexp: '',
  });

  const [errors, setErrors] = useState({});
  const [validationError, setValidationError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
    // Clear validation error when user starts typing
    if (validationError) {
      setValidationError(null);
    }
  };


  const validateForm = () => {
    const newErrors = {};

    if (!formData.tittle.trim()) newErrors.tittle = 'Title is required';
    if (!formData.travelexp.trim()) newErrors.travelexp = 'Travel experience is required';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setValidationError(null);

    try {
      const response = await blogAPI.createBlog({
        tittle: formData.tittle,
        travelexp: formData.travelexp,
        imgs: [],
      });

      // Directly navigate to entity details page
      const blogId = response.data._id;
      const entities = response.data.entities;
      
      if (blogId && entities) {
        // Navigate with entities in state
        navigate(`/entity-details/${blogId}`, { 
          state: { 
            entities: entities,
            blogTitle: response.data.tittle 
          } 
        });
      } else {
        // No entities extracted, skip to my-blogs
        navigate('/my-blogs');
      }
    } catch (error) {
      console.error(error);
      
      // Check if it's a validation error
      if (error.response?.data?.type === 'validation_error') {
        setValidationError({
          message: error.response.data.message,
          reason: error.response.data.reason,
          suggestions: error.response.data.suggestions || [],
          confidence: error.response.data.confidence
        });
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        alert(error.response?.data?.message || 'Failed to create blog. Please try again.');
      }
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <Header />
      
      <div className="max-w-4xl mx-auto px-4 py-8 animate-fade-in">
        {/* Header */}
        <div className="text-center mb-10 animate-slide-up">
          <h1 className="text-4xl md:text-5xl font-extrabold mb-4 bg-gradient-to-r from-primary-600 via-purple-600 to-pink-600 dark:from-primary-400 dark:via-purple-400 dark:to-pink-400 bg-clip-text text-transparent">
            Share Your Travel Experience
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Tell the world about your amazing journey
          </p>
        </div>

        {/* Validation Error Message */}
        {validationError && (
          <div className="mb-6 animate-slide-up">
            <div className="bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500 rounded-lg p-6 shadow-lg">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-amber-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div className="ml-4 flex-1">
                  <h3 className="text-lg font-semibold text-amber-900 dark:text-amber-200 mb-2">
                    Content Not Travel-Related
                  </h3>
                  <p className="text-amber-800 dark:text-amber-300 mb-4 leading-relaxed">
                    {validationError.message}
                  </p>
                  {validationError.suggestions && validationError.suggestions.length > 0 && (
                    <div className="mt-4">
                      <p className="text-sm font-medium text-amber-900 dark:text-amber-200 mb-2">
                        What you can include:
                      </p>
                      <ul className="space-y-1">
                        {validationError.suggestions.map((suggestion, index) => (
                          <li key={index} className="text-sm text-amber-800 dark:text-amber-300 flex items-center">
                            <span className="mr-2">•</span>
                            {suggestion}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <button
                    onClick={() => setValidationError(null)}
                    className="mt-4 text-sm font-medium text-amber-700 dark:text-amber-400 hover:text-amber-900 dark:hover:text-amber-200 flex items-center gap-1"
                  >
                    <FiX className="w-4 h-4" /> Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Form */}
        <form onSubmit={handleSubmit} className="section-card space-y-8 animate-slide-up">
          {/* Title */}
          <section>
            <h2 className="section-header">
              <span className="text-2xl">📋</span>
              Blog Information
            </h2>
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                  Blog Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.tittle}
                  onChange={(e) => handleInputChange('tittle', e.target.value)}
                  placeholder="e.g., Amazing 5-day trip to Goa"
                  className={`form-input ${errors.tittle ? 'border-red-500 dark:border-red-500 ring-red-500' : ''}`}
                />
                {errors.tittle && <p className="text-red-500 dark:text-red-400 text-sm mt-2 flex items-center gap-1">
                  <FiX className="w-4 h-4" /> {errors.tittle}
                </p>}
              </div>
            </div>
          </section>

          {/* Travel Experience */}
          <section>
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                Travel Experience <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.travelexp}
                onChange={(e) => handleInputChange('travelexp', e.target.value)}
                placeholder="Share your complete travel experience - hotels, attractions, food, local commute, costs, safety tips, and anything else that would help fellow travelers..."
                rows="12"
                className={`form-textarea ${errors.travelexp ? 'border-red-500 dark:border-red-500 ring-red-500' : ''}`}
              />
              {errors.travelexp && <p className="text-red-500 dark:text-red-400 text-sm mt-2 flex items-center gap-1">
                <FiX className="w-4 h-4" /> {errors.travelexp}
              </p>}
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 flex items-center gap-1">
                <FiInfo className="w-3 h-3" /> The more detailed your experience, the more helpful it is!
              </p>
            </div>
          </section>

          {/* Submit Button */}
          <div className="flex flex-col sm:flex-row gap-4 pt-6">
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary flex-1 text-lg"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Validating & Creating...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <FiCheck className="w-5 h-5" /> Create Blog
                </span>
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate('/all-blogs')}
              className="btn-secondary text-lg"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateBlog;
