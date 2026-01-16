import { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { FiCheck, FiAward, FiAlertCircle, FiSkipForward, FiSave } from 'react-icons/fi';
import { blogAPI } from '../utils/api';
import Header from '../components/Header';
import EntitySection from '../components/EntitySection';

const EntityDetailsForm = () => {
  const { blogId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [nerData, setNerData] = useState(null);
  const [blogTitle, setBlogTitle] = useState('');
  const [formData, setFormData] = useState({});
  const [images, setImages] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Entity configurations
  const entityConfigs = {
    hotels: {
      icon: '🏨',
      label: 'Hotels',
      fields: ['name', 'city', 'state', 'rating', 'contact'],
      imageLabel: 'Upload photos',
      imageTypes: ['bill', 'photo']
    },
    restaurants: {
      icon: '🍽️',
      label: 'Restaurants',
      fields: ['name', 'city', 'state', 'rating'],
      imageLabel: 'Upload photos',
      imageTypes: ['bill', 'food_photo']
    },
    places: {
      icon: '📍',
      label: 'Places',
      fields: ['name', 'city', 'state', 'rating'],
      imageLabel: 'Upload photos',
      imageTypes: ['photo']
    },
    activities: {
      icon: '🎯',
      label: 'Activities',
      fields: ['name', 'city', 'state', 'rating', 'type'],
      imageLabel: 'Upload photos',
      imageTypes: ['photo']
    },
    Bus: {
      icon: '🚌',
      label: 'Bus',
      fields: ['name', 'city', 'state', 'rating', 'contact'],
      imageLabel: 'Upload bill photo',
      imageTypes: ['bill']
    },
    Cab: {
      icon: '🚕',
      label: 'Cab',
      fields: ['name', 'city', 'state', 'rating', 'contact'],
      imageLabel: 'Upload bill photo',
      imageTypes: ['bill']
    }
  };

  useEffect(() => {
    // Check if entities were passed via navigation state
    if (location.state?.entities) {
      console.log('Using entities from navigation state');
      setNerData(location.state.entities);
      setBlogTitle(location.state.blogTitle || 'Your Travel Blog');
      
      // Initialize form data structure
      const initialFormData = {};
      const initialImages = {};
      
      Object.keys(location.state.entities).forEach(entityType => {
        initialFormData[entityType] = {};
        initialImages[entityType] = {};
        
        Object.keys(location.state.entities[entityType]).forEach(entityId => {
          initialFormData[entityType][entityId] = {};
          initialImages[entityType][entityId] = [];
        });
      });
      
      setFormData(initialFormData);
      setImages(initialImages);
      setLoading(false);
    } else {
      // Fallback: fetch from API (if user refreshes page or navigates directly)
      console.log('Fetching entities from API');
      fetchEntityData();
    }
  }, [blogId, location.state]);

  const fetchEntityData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch entity details from backend
      const response = await blogAPI.getEntityDetails(blogId);
      
      if (response.data.success) {
        setNerData(response.data.entities);
        setBlogTitle(response.data.blog_title || 'Your Travel Blog');
        
        // Initialize form data structure
        const initialFormData = {};
        const initialImages = {};
        
        Object.keys(response.data.entities).forEach(entityType => {
          initialFormData[entityType] = {};
          initialImages[entityType] = {};
          
          Object.keys(response.data.entities[entityType]).forEach(entityId => {
            initialFormData[entityType][entityId] = {};
            initialImages[entityType][entityId] = [];
          });
        });
        
        setFormData(initialFormData);
        setImages(initialImages);
      } else {
        setError('Failed to load entity data');
      }
    } catch (err) {
      console.error('Error fetching entity data:', err);
      setError(err.response?.data?.message || 'Failed to load entity details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (entityType, entityId, field, value) => {
    setFormData(prev => ({
      ...prev,
      [entityType]: {
        ...prev[entityType],
        [entityId]: {
          ...prev[entityType][entityId],
          [field]: value
        }
      }
    }));
  };

  const handleImageChange = (entityType, entityId, newImages) => {
    setImages(prev => ({
      ...prev,
      [entityType]: {
        ...prev[entityType],
        [entityId]: newImages
      }
    }));
  };

  const handleSkip = () => {
    navigate('/my-blogs');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      // Prepare FormData for multipart upload
      const formDataToSend = new FormData();
      
      // Add entity data as JSON string
      formDataToSend.append('entityData', JSON.stringify(formData));
      
      // Add all images with proper field names
      Object.entries(images).forEach(([entityType, entities]) => {
        Object.entries(entities).forEach(([entityId, imageFiles]) => {
          imageFiles.forEach((imageFile) => {
            // Field name format: images_entityType_entityId
            formDataToSend.append(`images_${entityType}_${entityId}`, imageFile);
          });
        });
      });

      console.log('Submitting entity details for blog:', blogId);
      
      // Call the API
      const response = await blogAPI.saveEntityDetails(blogId, formDataToSend);
      
      if (response.data.success) {
        console.log('Entity details saved successfully:', response.data);
        setIsSubmitting(false);
        setSubmitSuccess(true);
        
        // Redirect after 2 seconds
        setTimeout(() => {
          navigate('/my-blogs');
        }, 2000);
      } else {
        throw new Error(response.data.message || 'Failed to save entity details');
      }
      
    } catch (err) {
      console.error('Error submitting entity details:', err);
      setIsSubmitting(false);
      setError(err.response?.data?.message || err.message || 'Failed to save entity details. Please try again.');
    }
  };

  // Calculate total entities count
  const getTotalEntitiesCount = () => {
    if (!nerData) return 0;
    return Object.values(nerData).reduce((total, entities) => {
      return total + Object.keys(entities).length;
    }, 0);
  };

  // Calculate completion percentage
  const getCompletionPercentage = () => {
    if (!nerData) return 0;
    
    let totalFields = 0;
    let filledFields = 0;
    
    Object.entries(nerData).forEach(([entityType, entities]) => {
      Object.entries(entities).forEach(([entityId, entityData]) => {
        const config = entityConfigs[entityType];
        if (!config) return;
        
        config.fields.forEach(field => {
          totalFields++;
          const value = formData[entityType]?.[entityId]?.[field] || entityData[field];
          if (value && value !== '') {
            filledFields++;
          }
        });
      });
    });
    
    return totalFields > 0 ? Math.round((filledFields / totalFields) * 100) : 0;
  };

  if (submitSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <Header />
        <div className="flex items-center justify-center p-4 py-20 animate-fade-in">
          <div className="section-card max-w-md w-full text-center animate-slide-up">
            <div className="relative w-20 h-20 mx-auto mb-6">
              <div className="absolute inset-0 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full animate-pulse-slow"></div>
              <div className="absolute inset-2 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
                <FiCheck className="w-10 h-10 text-green-600 dark:text-green-400" />
              </div>
            </div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 dark:from-primary-400 dark:to-purple-400 bg-clip-text text-transparent mb-3">
              Blog Created Successfully!
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-6 leading-relaxed">
              Your travel blog has been created with all the details. Thank you for sharing your experience with fellow travelers!
            </p>
            <div className="flex items-center justify-center gap-2 text-primary-600 dark:text-primary-400 font-semibold">
              <FiAward className="w-5 h-5" />
              <span>Keep sharing detailed experiences!</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <Header />
        <div className="flex items-center justify-center p-4 py-20">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary-600 mx-auto mb-4"></div>
            <p className="text-lg font-semibold text-gray-700 dark:text-gray-300">
              Loading entity details...
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              Analyzing your travel experience
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <Header />
        <div className="flex items-center justify-center p-4 py-20">
          <div className="section-card max-w-md w-full text-center">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <FiAlertCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-3">
              Unable to Load Details
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              {error}
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={fetchEntityData}
                className="btn-primary"
              >
                Try Again
              </button>
              <button
                onClick={() => navigate('/my-blogs')}
                className="btn-secondary"
              >
                Go to My Blogs
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const totalEntities = getTotalEntitiesCount();
  const completionPercentage = getCompletionPercentage();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <Header />
      
      <div className="max-w-6xl mx-auto px-4 py-8 animate-fade-in">
        {/* Header Section */}
        <div className="mb-8 animate-slide-up">
          <div className="section-card">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h1 className="text-3xl md:text-4xl font-extrabold mb-2 bg-gradient-to-r from-primary-600 via-purple-600 to-pink-600 dark:from-primary-400 dark:via-purple-400 dark:to-pink-400 bg-clip-text text-transparent">
                  Complete Your Travel Details
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-300">
                  {blogTitle}
                </p>
              </div>
            </div>

            {/* Incentive Banner */}
            <div className="bg-gradient-to-r from-amber-50 to-yellow-50 dark:from-amber-900/20 dark:to-yellow-900/20 border-2 border-amber-200 dark:border-amber-800 rounded-xl p-4 mb-4">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-amber-100 dark:bg-amber-800/30 rounded-full flex items-center justify-center">
                    <FiAward className="w-6 h-6 text-amber-600 dark:text-amber-400" />
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="text-md font-bold text-amber-900 dark:text-amber-200 mb-1">
                    Earn Rewards for Accurate Information!
                  </h3>
                  <p className="text-sm text-amber-800 dark:text-amber-300">
                    Providing genuine and detailed information helps fellow travelers and earns you points, vouchers, and exclusive badges. All fields are optional!
                  </p>
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-sm">
                <span className="font-medium text-gray-700 dark:text-gray-300">
                  Completion Progress
                </span>
                <span className="font-bold text-primary-600 dark:text-primary-400">
                  {completionPercentage}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-primary-500 to-purple-500 h-full rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${completionPercentage}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {totalEntities} {totalEntities === 1 ? 'entity' : 'entities'} found in your blog
              </p>
            </div>
          </div>
        </div>

        {/* Main Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Entity Sections */}
          <div className="section-card space-y-6">
            {nerData && Object.entries(nerData).map(([entityType, entities]) => {
              const config = entityConfigs[entityType];
              if (!config) return null;

              return (
                <EntitySection
                  key={entityType}
                  entityType={entityType}
                  entityConfig={config}
                  entities={entities}
                  formData={formData[entityType] || {}}
                  images={images[entityType] || {}}
                  onFieldChange={handleFieldChange}
                  onImageChange={handleImageChange}
                />
              );
            })}

            {(!nerData || Object.keys(nerData).length === 0) && (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                  <FiAlertCircle className="w-8 h-8 text-gray-400 dark:text-gray-500" />
                </div>
                <h3 className="text-xl font-bold text-gray-700 dark:text-gray-300 mb-2">
                  No Entities Found
                </h3>
                <p className="text-gray-500 dark:text-gray-400">
                  No travel entities were extracted from your blog. You can skip this step.
                </p>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="section-card">
            <div className="flex flex-col sm:flex-row gap-4">
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
                    Saving Details...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <FiSave className="w-5 h-5" /> Save & Continue
                  </span>
                )}
              </button>
              <button
                type="button"
                onClick={handleSkip}
                disabled={isSubmitting}
                className="btn-secondary flex-1 text-lg"
              >
                <span className="flex items-center justify-center gap-2">
                  <FiSkipForward className="w-5 h-5" /> Skip for Now
                </span>
              </button>
            </div>
            <p className="text-xs text-center text-gray-500 dark:text-gray-400 mt-4">
              All fields are optional. You can come back later to complete this information.
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EntityDetailsForm;
