import { v2 as cloudinary } from 'cloudinary';
import dotenv from 'dotenv';

dotenv.config();

// Configure Cloudinary
cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET
});

/**
 * Upload image buffer to Cloudinary
 * @param {Buffer} fileBuffer - Image file buffer
 * @param {string} folder - Cloudinary folder name
 * @returns {Promise<string>} - Cloudinary URL
 */
export const uploadImage = (fileBuffer, folder = 'travel-entities') => {
  return new Promise((resolve, reject) => {
    const uploadStream = cloudinary.uploader.upload_stream(
      {
        folder: folder,
        resource_type: 'auto',
        transformation: [
          { quality: 'auto:good' },
          { fetch_format: 'auto' }
        ]
      },
      (error, result) => {
        if (error) {
          reject(error);
        } else {
          resolve(result.secure_url);
        }
      }
    );

    uploadStream.end(fileBuffer);
  });
};

/**
 * Upload multiple images to Cloudinary in parallel
 * @param {Array<Buffer>} fileBuffers - Array of image file buffers
 * @param {string} folder - Cloudinary folder name
 * @returns {Promise<Array<string>>} - Array of Cloudinary URLs
 */
export const uploadMultipleImages = async (fileBuffers, folder = 'travel-entities') => {
  try {
    const uploadPromises = fileBuffers.map(buffer => uploadImage(buffer, folder));
    const urls = await Promise.all(uploadPromises);
    return urls;
  } catch (error) {
    console.error('Error uploading multiple images:', error);
    throw error;
  }
};

export default cloudinary;
