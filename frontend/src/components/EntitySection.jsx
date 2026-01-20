import { useState } from 'react';
import { FiChevronDown, FiChevronUp } from 'react-icons/fi';
import ImageUpload from './ImageUpload';

const EntitySection = ({ 
  entityType, 
  entityConfig, 
  entities, 
  formData, 
  images,
  onFieldChange, 
  onImageChange 
}) => {
  const [expanded, setExpanded] = useState(true);
  const [expandedCards, setExpandedCards] = useState({});

  const toggleCard = (entityId) => {
    setExpandedCards(prev => ({
      ...prev,
      [entityId]: !prev[entityId]
    }));
  };

  // Get entity count
  const entityCount = Object.keys(entities).length;

  if (entityCount === 0) return null;

  const getFieldLabel = (field) => {
    const labels = {
      name: 'Name',
      city: 'City',
      state: 'State',
      rating: 'Rating',
      contact: 'Contact',
      type: 'Type'
    };
    return labels[field] || field;
  };

  return (
    <div className="border-b border-gray-200 dark:border-gray-700 pb-6 last:border-b-0">
      {/* Section Header */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-xl hover:from-gray-100 hover:to-gray-200 dark:hover:from-gray-700 dark:hover:to-gray-600 transition-all duration-200 mb-4"
      >
        <div className="flex items-center gap-3">
          <span className="text-3xl">{entityConfig.icon}</span>
          <div className="text-left">
            <h3 className="text-lg font-bold text-gray-800 dark:text-gray-100">
              {entityConfig.label}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {entityCount} {entityCount === 1 ? 'item' : 'items'} found
            </p>
          </div>
        </div>
        {expanded ? (
          <FiChevronUp className="w-6 h-6 text-gray-600 dark:text-gray-400" />
        ) : (
          <FiChevronDown className="w-6 h-6 text-gray-600 dark:text-gray-400" />
        )}
      </button>

      {/* Entity Cards */}
      {expanded && (
        <div className="space-y-4 pl-2">
          {Object.entries(entities).map(([entityId, entityData]) => {
            const isCardExpanded = expandedCards[entityId] !== false; // Default to expanded
            const currentFormData = formData[entityId] || {};
            const currentImages = images[entityId] || [];

            return (
              <div
                key={entityId}
                className="bg-white dark:bg-gray-800 rounded-xl border-2 border-gray-200 dark:border-gray-600 overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200"
              >
                {/* Card Header */}
                <button
                  type="button"
                  onClick={() => toggleCard(entityId)}
                  className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 hover:from-blue-100 hover:to-indigo-100 dark:hover:from-blue-900/30 dark:hover:to-indigo-900/30 transition-all duration-200"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                      <span className="text-sm font-bold text-primary-600 dark:text-primary-400">
                        {entityId.replace(/\D/g, '')}
                      </span>
                    </div>
                    <div className="text-left">
                      <h4 className="text-md font-semibold text-gray-800 dark:text-gray-100">
                        {entityData.name || `${entityConfig.label.slice(0, -1)} ${entityId.replace(/\D/g, '')}`}
                      </h4>
                      {entityData.city && (
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          {entityData.city}{entityData.state ? `, ${entityData.state}` : ''}
                        </p>
                      )}
                    </div>
                  </div>
                  {isCardExpanded ? (
                    <FiChevronUp className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  ) : (
                    <FiChevronDown className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  )}
                </button>

                {/* Card Content */}
                {isCardExpanded && (
                  <div className="p-5 space-y-4">
                    {/* Form Fields */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {entityConfig.fields.map((field) => (
                        <div key={field}>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            {getFieldLabel(field)}
                            {entityData[field] && (
                              <span className="ml-2 text-xs text-green-600 dark:text-green-400">
                                (Pre-filled)
                              </span>
                            )}
                          </label>
                          {field === 'rating' ? (
                            <input
                              type="text"
                              value={currentFormData[field] ?? entityData[field] ?? ''}
                              onChange={(e) => {
                                const value = e.target.value;
                                // Allow empty string or valid numbers between 0-5
                                if (value === '' || (!isNaN(value) && parseFloat(value) >= 0 && parseFloat(value) <= 5)) {
                                  onFieldChange(entityType, entityId, field, value);
                                }
                              }}
                              placeholder="Rating out of 5"
                              className="form-input"
                            />
                          ) : field === 'type' ? (
                            <select
                              value={currentFormData[field] ?? entityData[field] ?? ''}
                              onChange={(e) => onFieldChange(entityType, entityId, field, e.target.value)}
                              className="form-input"
                            >
                              <option value="">Select type</option>
                              <option value="sightseeing">Sightseeing</option>
                              <option value="adventure">Adventure</option>
                              <option value="cultural">Cultural</option>
                              <option value="leisure">Leisure</option>
                              <option value="sports">Sports</option>
                              <option value="entertainment">Entertainment</option>
                            </select>
                          ) : (
                            <input
                              type="text"
                              value={currentFormData[field] ?? entityData[field] ?? ''}
                              onChange={(e) => onFieldChange(entityType, entityId, field, e.target.value)}
                              placeholder={`Enter ${getFieldLabel(field).toLowerCase()}`}
                              className="form-input"
                            />
                          )}
                        </div>
                      ))}
                    </div>

                    {/* Image Upload Section */}
                    <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                      <ImageUpload
                        label={entityConfig.imageLabel}
                        images={currentImages}
                        onChange={(newImages) => onImageChange(entityType, entityId, newImages)}
                        entityKey={`${entityType}-${entityId}`}
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default EntitySection;
