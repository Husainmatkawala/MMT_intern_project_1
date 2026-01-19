import os
import logging
import tempfile
import requests
from typing import Dict, List, Tuple
from urllib.parse import urlparse
import numpy as np

# Try importing optional dependencies
HAS_PIL = False
HAS_IMAGEHASH = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    pass

try:
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    pass

logger = logging.getLogger(__name__)


class ImageForensicAgent:
    """
    Forensic agent for detecting AI-generated images using multiple analysis techniques.
    
    Implements:
    - EXIF metadata analysis
    - Frequency domain analysis (FFT)
    - Error Level Analysis (ELA)
    - Perceptual hash consistency
    - Noise pattern analysis
    """
    
    def __init__(self, download_timeout=30, max_image_size_mb=10):
        """
        Initialize the forensic agent.
        
        Args:
            download_timeout: Timeout for downloading images (seconds)
            max_image_size_mb: Maximum image size to download (MB)
        """
        self.download_timeout = download_timeout
        self.max_image_size_bytes = max_image_size_mb * 1024 * 1024
        
        if not HAS_PIL:
            logger.warning("PIL (Pillow) not available. Image analysis will be limited.")
        if not HAS_IMAGEHASH:
            logger.warning("imagehash not available. Hash analysis will be skipped.")
    
    def download_image(self, image_url: str) -> str:
        """
        Download image from URL to temporary file.
        
        Args:
            image_url: URL of the image to download
            
        Returns:
            Path to downloaded image file
            
        Raises:
            Exception if download fails
        """
        try:
            logger.info(f"Downloading image from: {image_url}")
            
            # Send HEAD request first to check size
            head_response = requests.head(image_url, timeout=5, allow_redirects=True)
            content_length = head_response.headers.get('content-length')
            
            if content_length and int(content_length) > self.max_image_size_bytes:
                raise ValueError(f"Image too large: {int(content_length)} bytes")
            
            # Download the image
            response = requests.get(
                image_url, 
                timeout=self.download_timeout,
                stream=True,
                headers={'User-Agent': 'Mozilla/5.0 ForensicAgent/1.0'}
            )
            response.raise_for_status()
            
            # Get file extension from URL
            parsed_url = urlparse(image_url)
            ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            
            # Write content to temp file
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            
            temp_file.close()
            logger.info(f"Image downloaded successfully to: {temp_file.name}")
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            raise
    
    def _analyze_image_authenticity(self, image_path: str, preserved_exif: Dict = None) -> Dict[str, float]:
        """
        Perform real AI image detection analysis using multiple techniques.
        
        Args:
            image_path: Path to image file
            preserved_exif: Pre-extracted EXIF data (before Cloudinary upload)
            
        Returns:
            Dictionary with analysis scores (0-1 range, higher = more likely real)
        """
        scores = {
            "exif_score": 0.0,
            "frequency_score": 0.0,
            "error_level_score": 0.0,
            "hash_consistency_score": 0.0,
            "noise_pattern_score": 0.0
        }
        
        if not HAS_PIL or not os.path.exists(image_path):
            logger.warning(f"Cannot analyze image: PIL not available or file not found: {image_path}")
            return scores
        
        try:
            with Image.open(image_path) as img:
                logger.debug(f"Analyzing image: {image_path} (mode={img.mode}, size={img.size})")
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 1. EXIF Analysis (using preserved EXIF from before Cloudinary upload)
                # CRITICAL: No EXIF is a strong indicator of AI-generated images
                try:
                    if preserved_exif:
                        # Use pre-extracted EXIF data
                        tag_count = preserved_exif.get('tagCount', 0)
                        has_camera_info = bool(preserved_exif.get('make') or preserved_exif.get('model'))
                        has_datetime = bool(preserved_exif.get('dateTime'))
                        
                        if tag_count >= 10 and has_camera_info:
                            # Rich EXIF with camera info = definitely real photo from camera
                            scores["exif_score"] = 1.0
                            logger.debug(f"EXIF analysis (preserved): {tag_count} tags, camera={preserved_exif.get('make')} {preserved_exif.get('model')}, score=1.00 [REAL CAMERA]")
                        elif tag_count >= 5 and has_camera_info:
                            # Some EXIF with camera info = likely real
                            scores["exif_score"] = 0.8
                            logger.debug(f"EXIF analysis (preserved): {tag_count} tags, camera={preserved_exif.get('make')} {preserved_exif.get('model')}, score=0.80")
                        elif tag_count > 0:
                            # Some EXIF but no camera info = edited/processed
                            scores["exif_score"] = 0.5
                            logger.debug(f"EXIF analysis (preserved): {tag_count} tags but no camera info, score=0.50")
                        else:
                            # No EXIF = HIGHLY SUSPICIOUS (likely AI, screenshot, or heavily edited)
                            scores["exif_score"] = 0.0
                            logger.debug("EXIF analysis (preserved): No EXIF data, score=0.00 [HIGHLY SUSPICIOUS - likely AI]")
                    else:
                        # No preserved EXIF provided - try from image (will likely fail for Cloudinary)
                        exif_data = img._getexif()
                        if exif_data:
                            exif_tags = len([k for k in exif_data.keys() if exif_data[k] is not None])
                            scores["exif_score"] = min(exif_tags / 10.0, 1.0)
                            logger.debug(f"EXIF analysis (from image): {exif_tags} tags, score={scores['exif_score']:.2f}")
                        else:
                            # No EXIF and no preserved data = VERY SUSPICIOUS
                            scores["exif_score"] = 0.1
                            logger.debug("EXIF analysis: No preserved or embedded EXIF, score=0.10 [SUSPICIOUS]")
                except Exception as e:
                    logger.debug(f"EXIF analysis error: {e}")
                    scores["exif_score"] = 0.1
                
                # 2. Enhanced Frequency Domain Analysis (AI images have unnatural smoothness)
                try:
                    img_array = np.array(img)
                    # Convert to grayscale for analysis
                    if len(img_array.shape) == 3:
                        gray = np.mean(img_array, axis=2).astype(np.uint8)
                    else:
                        gray = img_array
                    
                    # FFT analysis - STRICTER for AI detection
                    fft = np.fft.fft2(gray)
                    fft_shift = np.fft.fftshift(fft)
                    magnitude = np.abs(fft_shift)
                    
                    # Real photos: natural high-frequency content (edges, textures, noise)
                    # AI images: too smooth OR unnaturally perfect distribution
                    high_freq_ratio = np.sum(magnitude > np.percentile(magnitude, 80)) / magnitude.size
                    mid_freq_ratio = np.sum((magnitude > np.percentile(magnitude, 40)) & 
                                           (magnitude < np.percentile(magnitude, 80))) / magnitude.size
                    
                    # Calculate frequency distribution smoothness (AI = too uniform)
                    freq_std = np.std(magnitude)
                    
                    # Real photos: good high+mid freq balance + variation
                    # AI photos: low high-freq (smooth) OR very uniform distribution
                    if high_freq_ratio < 0.08:
                        # Very low high-frequency = too smooth = AI
                        scores["frequency_score"] = 0.2
                        logger.debug(f"Frequency analysis: TOO SMOOTH [AI], high_freq={high_freq_ratio:.4f}, score=0.20")
                    elif high_freq_ratio > 0.25:
                        # Very high = likely real photo with natural texture
                        scores["frequency_score"] = 0.9
                        logger.debug(f"Frequency analysis: Natural texture [REAL], high_freq={high_freq_ratio:.4f}, score=0.90")
                    else:
                        # Middle range - check mid-frequency and smoothness
                        freq_balance = (high_freq_ratio * 0.5 + mid_freq_ratio * 0.3 + min(freq_std/10000, 0.2))
                        scores["frequency_score"] = min(freq_balance * 4, 1.0)
                        logger.debug(f"Frequency analysis: high_freq={high_freq_ratio:.4f}, mid_freq={mid_freq_ratio:.4f}, std={freq_std:.1f}, score={scores['frequency_score']:.2f}")
                except Exception as e:
                    logger.debug(f"Frequency analysis error: {e}")
                    scores["frequency_score"] = 0.5
                
                # 3. Error Level Analysis (ELA) - detects compression artifacts
                try:
                    # Save and reload to detect compression
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        img.save(tmp.name, 'JPEG', quality=95)
                        reloaded = Image.open(tmp.name)
                        diff = np.abs(np.array(img.convert('L')) - np.array(reloaded.convert('L')))
                        error_level = np.mean(diff)
                        # Higher error level = more compression artifacts = more likely real
                        scores["error_level_score"] = min(error_level / 30.0, 1.0)
                        logger.debug(f"ELA analysis: error_level={error_level:.2f}, score={scores['error_level_score']:.2f}")
                        os.unlink(tmp.name)
                except Exception as e:
                    logger.debug(f"ELA analysis error: {e}")
                    scores["error_level_score"] = 0.5
                
                # 4. Image Hash Consistency (check for signs of AI generation)
                if HAS_IMAGEHASH:
                    try:
                        # Calculate perceptual hash
                        phash = imagehash.phash(img)
                        # Real photos typically have more variation
                        hash_variance = len(str(phash)) - str(phash).count('0')
                        scores["hash_consistency_score"] = min(hash_variance / 64.0, 1.0)
                        logger.debug(f"Hash analysis: variance={hash_variance}, score={scores['hash_consistency_score']:.2f}")
                    except Exception as e:
                        logger.debug(f"Hash analysis error: {e}")
                        scores["hash_consistency_score"] = 0.5
                else:
                    scores["hash_consistency_score"] = 0.5
                    logger.debug("Hash analysis: imagehash not available, using default score=0.50")
                
                # 5. STRICT Noise Pattern Analysis (AI images are unnaturally smooth)
                try:
                    img_array = np.array(img.convert('L'))
                    
                    # Method 1: Edge detection (real photos have natural edges + noise)
                    kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
                    filtered = np.abs(np.convolve(img_array.flatten(), kernel.flatten(), mode='same'))
                    noise_level = np.std(filtered)
                    
                    # Method 2: Local variance (AI images are too uniform/perfect)
                    patch_size = 8
                    h, w = img_array.shape
                    variances = []
                    for i in range(0, h - patch_size, patch_size):
                        for j in range(0, w - patch_size, patch_size):
                            patch = img_array[i:i+patch_size, j:j+patch_size]
                            variances.append(np.var(patch))
                    
                    variance_std = np.std(variances) if variances else 0
                    
                    # Method 3: Check for unnatural smoothness in flat regions
                    # AI images have suspiciously smooth gradients
                    mean_var = np.mean(variances) if variances else 0
                    
                    # STRICTER THRESHOLDS for AI detection
                    # Real photos: noise_level > 25, variance_std > 100
                    # AI photos: noise_level < 20, variance_std < 80
                    
                    if noise_level < 15 and variance_std < 60:
                        # Extremely smooth = definitely AI
                        scores["noise_pattern_score"] = 0.1
                        logger.debug(f"Noise analysis: EXTREMELY SMOOTH [AI], noise={noise_level:.2f}, var_std={variance_std:.2f}, score=0.10")
                    elif noise_level < 20 and variance_std < 100:
                        # Very smooth = likely AI
                        scores["noise_pattern_score"] = 0.3
                        logger.debug(f"Noise analysis: TOO SMOOTH [Suspicious], noise={noise_level:.2f}, var_std={variance_std:.2f}, score=0.30")
                    else:
                        # Has natural noise and texture variation = likely real
                        noise_score = min(noise_level / 35.0, 1.0) if noise_level > 0 else 0.1
                        variance_score = min(variance_std / 150.0, 1.0) if variance_std > 0 else 0.1
                        scores["noise_pattern_score"] = (noise_score * 0.6 + variance_score * 0.4)
                        logger.debug(f"Noise analysis: Natural texture, noise={noise_level:.2f}, var_std={variance_std:.2f}, score={scores['noise_pattern_score']:.2f}")
                except Exception as e:
                    logger.debug(f"Noise analysis error: {e}")
                    scores["noise_pattern_score"] = 0.5
                    
        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}")
        
        return scores
    
    def detect_ai_image(self, image_urls: List[str], images_exif: List[Dict] = None) -> Tuple[float, List[Dict]]:
        """
        Detect AI-generated images using real analysis techniques.
        
        Uses multiple forensic techniques:
        - EXIF metadata analysis
        - Frequency domain analysis (FFT)
        - Error Level Analysis (ELA)
        - Perceptual hash consistency
        - Noise pattern analysis
        
        Args:
            image_urls: List of image URLs to analyze
            images_exif: List of dicts with pre-extracted EXIF data
            
        Returns:
            Tuple of (probability that images are real (0-1), list of detailed results per image)
        """
        if not image_urls or len(image_urls) == 0:
            logger.info("No images provided, returning neutral score (0.5)")
            return 0.5, []
        
        logger.info(f"Starting AI detection for {len(image_urls)} images")
        
        valid_images = 0
        total_scores = []
        detailed_results = []
        
        # Create EXIF lookup by URL
        exif_by_url = {}
        if images_exif:
            for exif_data in images_exif:
                if isinstance(exif_data, dict) and 'url' in exif_data:
                    exif_by_url[exif_data['url']] = exif_data.get('exif')
        
        for idx, image_url in enumerate(image_urls):
            logger.info(f"Processing image {idx + 1}/{len(image_urls)}: {image_url}")
            
            image_path = None
            try:
                # Download the image
                image_path = self.download_image(image_url)
                
                # Get pre-extracted EXIF for this image URL
                preserved_exif = exif_by_url.get(image_url)
                
                # Perform real AI detection analysis (with preserved EXIF if available)
                analysis = self._analyze_image_authenticity(image_path, preserved_exif)
                
                # Weighted combination of analysis scores
                # STRICT weighting - EXIF is critical, combined with texture analysis
                weights = {
                    "exif_score": 0.35,  # CRITICAL - no EXIF is huge red flag
                    "frequency_score": 0.25,  # AI = too smooth
                    "noise_pattern_score": 0.25,  # AI = unnaturally perfect
                    "error_level_score": 0.10,
                    "hash_consistency_score": 0.05
                }
                
                image_score = sum(analysis[key] * weights[key] for key in weights.keys())
                total_scores.append(image_score)
                valid_images += 1
                
                result = {
                    "image_url": image_url,
                    "analysis": analysis,
                    "weighted_score": round(image_score, 3),
                    "status": "success"
                }
                detailed_results.append(result)
                
                logger.info(f"Image {idx + 1} analysis complete: score={image_score:.3f}")
                logger.debug(f"  Detailed scores: {analysis}")
                
            except Exception as e:
                logger.error(f"Failed to analyze image {idx + 1} ({image_url}): {e}")
                detailed_results.append({
                    "image_url": image_url,
                    "error": str(e),
                    "status": "failed"
                })
            finally:
                # Clean up downloaded image
                if image_path and os.path.exists(image_path):
                    try:
                        os.unlink(image_path)
                        logger.debug(f"Cleaned up temporary file: {image_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up temp file {image_path}: {e}")
        
        if valid_images == 0:
            logger.warning("No valid images analyzed, returning neutral score (0.5)")
            return 0.5, detailed_results
        
        # Average score across all images
        avg_score = np.mean(total_scores) if total_scores else 0.5
        
        # Bonus for multiple images (consistency check)
        if len(total_scores) > 1:
            score_variance = np.var(total_scores)
            # Lower variance = more consistent = more likely all real
            consistency_bonus = max(0, 0.1 - score_variance * 0.5)
            avg_score = min(avg_score + consistency_bonus, 1.0)
            logger.debug(f"Consistency bonus applied: variance={score_variance:.4f}, bonus={consistency_bonus:.4f}")
        
        final_score = max(0.0, min(1.0, avg_score))
        
        logger.info(f"AI detection complete: {valid_images}/{len(image_urls)} images analyzed, final_score={final_score:.3f}")
        
        return round(final_score, 3), detailed_results
    
    def compute_entity_score(self, image_urls: List[str], images_exif: List[Dict] = None) -> Tuple[int, Dict]:
        """
        Compute credibility score for an entity based on its images.
        
        Scoring rules:
        - No images: score = 0
        - AI-generated images (very low confidence): score = -50
        - Real images: score = 100
        - Multiple images: average the individual scores
        
        Args:
            image_urls: List of image URLs for the entity
            images_exif: List of dicts with EXIF data (extracted before Cloudinary upload)
            
        Returns:
            Tuple of (entity_score, analysis_details)
        """
        logger.info(f"Computing entity score for {len(image_urls)} images")
        
        # No images case
        if not image_urls or len(image_urls) == 0:
            logger.info("No images provided, entity score = 0")
            return 0, {
                "reason": "no_images",
                "message": "No images provided for this entity"
            }
        
        # Detect AI-generated images (pass EXIF data if available)
        real_probability, detailed_results = self.detect_ai_image(image_urls, images_exif)
        
        # STRICT threshold for AI detection
        # real_probability: 0 = definitely AI, 1 = definitely real
        # With EXIF + forensic analysis, we can be more confident
        
        # STRICTER thresholds
        AI_THRESHOLD = 0.45  # Below this = AI-generated
        REAL_THRESHOLD = 0.60  # Above this = confidently real
        # Between 0.45-0.60 = uncertain, needs careful analysis
        
        AI_SCORE = -50
        REAL_SCORE = 100
        
        if real_probability < AI_THRESHOLD:
            # AI-generated (no EXIF + smooth/perfect patterns)
            entity_score = AI_SCORE
            verdict = "ai_generated"
            message = f"Images flagged as AI-generated (real score: {real_probability * 100:.1f}%). Likely created by AI tool."
            logger.info(f"Entity score = {AI_SCORE} (AI-generated, real_prob={real_probability:.3f})")
        elif real_probability >= REAL_THRESHOLD:
            # Confidently real (has EXIF or very natural patterns)
            entity_score = REAL_SCORE
            verdict = "real"
            message = f"Images verified as real (confidence: {real_probability * 100:.1f}%)"
            logger.info(f"Entity score = {REAL_SCORE} (Real, real_prob={real_probability:.3f})")
        else:
            # Uncertain zone (0.45-0.60) - could be edited real photo or lower-quality AI
            # Flag as AI to be safe (better false positive than false negative)
            entity_score = AI_SCORE
            verdict = "uncertain_ai"
            message = f"Images uncertain (score: {real_probability * 100:.1f}%). Flagged as suspicious - may be AI or heavily edited."
            logger.info(f"Entity score = {AI_SCORE} (Uncertain/Flagged, real_prob={real_probability:.3f})")
        
        analysis_details = {
            "real_probability": real_probability,
            "verdict": verdict,
            "message": message,
            "images_analyzed": len([r for r in detailed_results if r.get("status") == "success"]),
            "images_failed": len([r for r in detailed_results if r.get("status") == "failed"]),
            "detailed_results": detailed_results
        }
        
        return entity_score, analysis_details
