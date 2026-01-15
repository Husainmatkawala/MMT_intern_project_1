import { useState, useRef } from 'react';
import { FiUpload, FiX, FiImage } from 'react-icons/fi';

const ImageUpload = ({ label, images = [], onChange, entityKey }) => {
  const [dragActive, setDragActive] = useState(false);
  const [errors, setErrors] = useState([]);
  const fileInputRef = useRef(null);

  const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
  const ALLOWED_FORMATS = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];

  const validateFile = (file) => {
    const errors = [];
    
    if (!ALLOWED_FORMATS.includes(file.type)) {
      errors.push(`${file.name}: Invalid format. Only JPG, PNG, and WEBP are allowed.`);
    }
    
    if (file.size > MAX_FILE_SIZE) {
      errors.push(`${file.name}: File too large. Maximum size is 5MB.`);
    }
    
    return errors;
  };

  const handleFiles = (files) => {
    const fileList = Array.from(files);
    const validationErrors = [];
    const validFiles = [];

    fileList.forEach(file => {
      const fileErrors = validateFile(file);
      if (fileErrors.length > 0) {
        validationErrors.push(...fileErrors);
      } else {
        validFiles.push(file);
      }
    });

    setErrors(validationErrors);

    if (validFiles.length > 0) {
      const newImages = [...images, ...validFiles];
      onChange(newImages);
    }

    // Clear errors after 5 seconds
    if (validationErrors.length > 0) {
      setTimeout(() => setErrors([]), 5000);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  };

  const handleRemoveImage = (index) => {
    const newImages = images.filter((_, i) => i !== index);
    onChange(newImages);
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>

      {/* Upload Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleButtonClick}
        className={`
          relative border-2 border-dashed rounded-xl p-6 text-center cursor-pointer
          transition-all duration-200
          ${dragActive 
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' 
            : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 dark:hover:border-primary-500 bg-gray-50 dark:bg-gray-800/50'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/jpeg,image/jpg,image/png,image/webp"
          onChange={handleChange}
          className="hidden"
        />
        
        <div className="flex flex-col items-center gap-2">
          <div className={`
            w-12 h-12 rounded-full flex items-center justify-center
            ${dragActive 
              ? 'bg-primary-100 dark:bg-primary-800/30' 
              : 'bg-gray-100 dark:bg-gray-700'
            }
          `}>
            <FiUpload className={`
              w-6 h-6
              ${dragActive 
                ? 'text-primary-600 dark:text-primary-400' 
                : 'text-gray-500 dark:text-gray-400'
              }
            `} />
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Click to upload or drag and drop
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              JPG, PNG, WEBP (max 5MB each)
            </p>
          </div>
        </div>
      </div>

      {/* Validation Errors */}
      {errors.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
          {errors.map((error, index) => (
            <p key={index} className="text-xs text-red-600 dark:text-red-400 flex items-center gap-1">
              <FiX className="w-3 h-3" /> {error}
            </p>
          ))}
        </div>
      )}

      {/* Image Previews */}
      {images.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {images.map((image, index) => {
            const imageUrl = URL.createObjectURL(image);
            return (
              <div key={index} className="relative group">
                <div className="aspect-square rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700 border-2 border-gray-200 dark:border-gray-600">
                  <img
                    src={imageUrl}
                    alt={`Upload ${index + 1}`}
                    className="w-full h-full object-cover"
                    onLoad={() => URL.revokeObjectURL(imageUrl)}
                  />
                </div>
                
                {/* Remove Button */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveImage(index);
                  }}
                  className="
                    absolute -top-2 -right-2 w-6 h-6 
                    bg-red-500 hover:bg-red-600 
                    text-white rounded-full 
                    flex items-center justify-center
                    opacity-0 group-hover:opacity-100
                    transition-opacity duration-200
                    shadow-lg
                  "
                >
                  <FiX className="w-4 h-4" />
                </button>

                {/* Image Info */}
                <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs p-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                  <p className="truncate">{image.name}</p>
                  <p className="text-gray-300">{(image.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Image Count */}
      {images.length > 0 && (
        <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
          <FiImage className="w-3 h-3" /> {images.length} image{images.length !== 1 ? 's' : ''} selected
        </p>
      )}
    </div>
  );
};

export default ImageUpload;
