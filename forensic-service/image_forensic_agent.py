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
    Clean AI image detection using forensic analysis.
    
    Key principle: Real camera photos have distinct characteristics that AI images lack.
    """
    
    def __init__(self, download_timeout=30, max_image_size_mb=10):
        """Initialize the forensic agent."""
        self.download_timeout = download_timeout
        self.max_image_size_bytes = max_image_size_mb * 1024 * 1024
        
        if not HAS_PIL:
            logger.warning("PIL (Pillow) not available. Image analysis will be limited.")
        if not HAS_IMAGEHASH:
            logger.warning("imagehash not available. Hash analysis will be skipped.")
    
    def download_image(self, image_url: str) -> str:
        """Download image from URL to temporary file."""
        try:
            logger.info(f"Downloading image: {image_url}")
            
            # Check size first
            head_response = requests.head(image_url, timeout=5, allow_redirects=True)
            content_length = head_response.headers.get('content-length')
            
            if content_length and int(content_length) > self.max_image_size_bytes:
                raise ValueError(f"Image too large: {int(content_length)} bytes")
            
            # Download
            response = requests.get(
                image_url, 
                timeout=self.download_timeout,
                stream=True,
                headers={'User-Agent': 'Mozilla/5.0 ForensicAgent/1.0'}
            )
            response.raise_for_status()
            
            # Save to temp file
            parsed_url = urlparse(image_url)
            ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            
            temp_file.close()
            logger.info(f"Downloaded to: {temp_file.name}")
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise
    
    def _analyze_image(self, image_path: str, preserved_exif: Dict = None) -> Dict[str, float]:
        """
        Analyze image authenticity using forensic techniques.
        
        Returns scores 0.0-1.0 where 1.0 = definitely real, 0.0 = definitely AI.
        """
        scores = {
            "exif_score": 0.0,
            "frequency_score": 0.0,
            "error_level_score": 0.0,
            "noise_score": 0.0
        }
        
        if not HAS_PIL or not os.path.exists(image_path):
            return scores
        
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # ===== 1. EXIF ANALYSIS - MOST RELIABLE SIGNAL =====
                # Real camera photos ALWAYS have EXIF with camera make/model
                # AI images almost NEVER have camera EXIF
                
                if preserved_exif:
                    tag_count = preserved_exif.get('tagCount', 0)
                    make = preserved_exif.get('make', '')
                    model = preserved_exif.get('model', '')
                    
                    if make or model:
                        # HAS CAMERA INFO = DEFINITELY REAL (cameras don't lie)
                        scores["exif_score"] = 1.0
                        logger.info(f"✓ EXIF: Camera detected ({make} {model}) → REAL")
                    elif tag_count > 5:
                        # Has some EXIF but no camera = edited photo or screenshot
                        scores["exif_score"] = 0.4
                        logger.info(f"⚠ EXIF: {tag_count} tags but no camera → Edited/Screenshot")
                    else:
                        # NO EXIF = HIGHLY SUSPICIOUS
                        scores["exif_score"] = 0.0
                        logger.info(f"✗ EXIF: No data → SUSPICIOUS (likely AI)")
                else:
                    # No preserved EXIF (shouldn't happen with our backend)
                    exif_data = img._getexif()
                    if exif_data and len(exif_data) > 5:
                        scores["exif_score"] = 0.5
                        logger.info(f"⚠ EXIF: Found {len(exif_data)} tags from image")
                    else:
                        scores["exif_score"] = 0.0
                        logger.info(f"✗ EXIF: No data")
                
                # ===== 2. FREQUENCY ANALYSIS - AI = TOO SMOOTH =====
                # Real photos have natural high-frequency content (edges, texture, noise)
                # AI images are unnaturally smooth
                
                try:
                    img_array = np.array(img)
                    gray = np.mean(img_array, axis=2).astype(np.uint8) if len(img_array.shape) == 3 else img_array
                    
                    # FFT to analyze frequency distribution
                    fft = np.fft.fft2(gray)
                    fft_shift = np.fft.fftshift(fft)
                    magnitude = np.abs(fft_shift)
                    
                    # Calculate high-frequency content
                    high_freq_threshold = np.percentile(magnitude, 85)
                    high_freq_ratio = np.sum(magnitude > high_freq_threshold) / magnitude.size
                    
                    # Real photos: high_freq_ratio typically 0.10-0.20
                    # AI images: high_freq_ratio typically < 0.08 (too smooth)
                    
                    if high_freq_ratio < 0.06:
                        scores["frequency_score"] = 0.1  # Too smooth = AI
                        logger.info(f"✗ Frequency: Too smooth ({high_freq_ratio:.4f}) → AI-like")
                    elif high_freq_ratio < 0.10:
                        scores["frequency_score"] = 0.4  # Somewhat smooth
                        logger.info(f"⚠ Frequency: Smooth ({high_freq_ratio:.4f})")
                    elif high_freq_ratio > 0.18:
                        scores["frequency_score"] = 1.0  # Natural texture
                        logger.info(f"✓ Frequency: Natural texture ({high_freq_ratio:.4f}) → REAL")
                    else:
                        scores["frequency_score"] = 0.7  # Normal range
                        logger.info(f"✓ Frequency: Normal ({high_freq_ratio:.4f})")
                        
                except Exception as e:
                    logger.debug(f"Frequency analysis error: {e}")
                    scores["frequency_score"] = 0.5
                
                # ===== 3. ERROR LEVEL ANALYSIS =====
                # Real photos have natural compression artifacts
                
                try:
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        img.save(tmp.name, 'JPEG', quality=95)
                        reloaded = Image.open(tmp.name)
                        diff = np.abs(np.array(img.convert('L')) - np.array(reloaded.convert('L')))
                        error_level = np.mean(diff)
                        
                        # Real photos: error_level typically 10-25
                        # AI images: often lower (too perfect) or higher (generated artifacts)
                        
                        if 8 < error_level < 30:
                            scores["error_level_score"] = 0.8
                            logger.info(f"✓ ELA: Natural compression ({error_level:.1f})")
                        else:
                            scores["error_level_score"] = 0.4
                            logger.info(f"⚠ ELA: Unusual compression ({error_level:.1f})")
                        
                        os.unlink(tmp.name)
                except Exception as e:
                    logger.debug(f"ELA error: {e}")
                    scores["error_level_score"] = 0.5
                
                # ===== 4. NOISE ANALYSIS - AI = TOO PERFECT =====
                # Real photos have natural sensor noise and texture variation
                # AI images are unnaturally uniform
                
                try:
                    img_array = np.array(img.convert('L'))
                    
                    # Edge detection to find natural texture
                    kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
                    edges = np.convolve(img_array.flatten(), kernel.flatten(), mode='same')
                    noise_level = np.std(edges)
                    
                    # Calculate local variance (texture consistency)
                    h, w = img_array.shape
                    patch_size = 16
                    variances = []
                    for i in range(0, h - patch_size, patch_size):
                        for j in range(0, w - patch_size, patch_size):
                            patch = img_array[i:i+patch_size, j:j+patch_size]
                            variances.append(np.var(patch))
                    
                    variance_mean = np.mean(variances) if variances else 0
                    
                    # Real photos: noise_level > 40, variance_mean > 200
                    # AI images: noise_level < 30, variance_mean < 150 (too uniform)
                    
                    if noise_level < 25 and variance_mean < 100:
                        scores["noise_score"] = 0.1  # Too smooth = AI
                        logger.info(f"✗ Noise: Too uniform (noise={noise_level:.1f}, var={variance_mean:.1f}) → AI-like")
                    elif noise_level < 35 and variance_mean < 180:
                        scores["noise_score"] = 0.4  # Somewhat smooth
                        logger.info(f"⚠ Noise: Smooth (noise={noise_level:.1f}, var={variance_mean:.1f})")
                    elif noise_level > 50 and variance_mean > 250:
                        scores["noise_score"] = 1.0  # Natural texture
                        logger.info(f"✓ Noise: Natural texture (noise={noise_level:.1f}, var={variance_mean:.1f}) → REAL")
                    else:
                        scores["noise_score"] = 0.7  # Normal range
                        logger.info(f"✓ Noise: Normal (noise={noise_level:.1f}, var={variance_mean:.1f})")
                        
                except Exception as e:
                    logger.debug(f"Noise analysis error: {e}")
                    scores["noise_score"] = 0.5
                    
        except Exception as e:
            logger.error(f"Analysis error: {e}")
        
        return scores
    
    def detect_ai_image(self, image_urls: List[str], images_exif: List[Dict] = None) -> Tuple[float, List[Dict]]:
        """
        Detect if images are AI-generated.
        
        Returns:
            (real_probability, detailed_results)
            real_probability: 0.0 = definitely AI, 1.0 = definitely real
        """
        if not image_urls:
            logger.info("No images provided")
            return 0.5, []
        
        logger.info(f"Analyzing {len(image_urls)} images")
        
        # Create EXIF lookup
        exif_by_url = {}
        if images_exif:
            for exif_data in images_exif:
                if isinstance(exif_data, dict) and 'url' in exif_data:
                    exif_by_url[exif_data['url']] = exif_data.get('exif')
        
        valid_images = 0
        total_scores = []
        detailed_results = []
        
        for idx, image_url in enumerate(image_urls):
            logger.info(f"\n{'='*60}")
            logger.info(f"IMAGE {idx + 1}/{len(image_urls)}: {image_url}")
            logger.info(f"{'='*60}")
            
            image_path = None
            try:
                image_path = self.download_image(image_url)
                preserved_exif = exif_by_url.get(image_url)
                
                # Analyze image
                scores = self._analyze_image(image_path, preserved_exif)
                
                # ===== WEIGHTED SCORING =====
                # EXIF is the most reliable signal (50% weight)
                # Other forensic techniques support the decision (50% combined)
                
                weights = {
                    "exif_score": 0.50,      # CRITICAL - camera EXIF is proof
                    "frequency_score": 0.20,  # AI = too smooth
                    "noise_score": 0.20,      # AI = too uniform
                    "error_level_score": 0.10 # Compression artifacts
                }
                
                image_score = sum(scores[key] * weights[key] for key in weights.keys())
                total_scores.append(image_score)
                valid_images += 1
                
                logger.info(f"\n--- FINAL SCORE ---")
                logger.info(f"Image score: {image_score:.3f}")
                logger.info(f"Breakdown: EXIF={scores['exif_score']:.2f} (50%), "
                          f"Freq={scores['frequency_score']:.2f} (20%), "
                          f"Noise={scores['noise_score']:.2f} (20%), "
                          f"ELA={scores['error_level_score']:.2f} (10%)")
                
                detailed_results.append({
                    "image_url": image_url,
                    "scores": scores,
                    "weighted_score": round(image_score, 3),
                    "status": "success"
                })
                
            except Exception as e:
                logger.error(f"Failed to analyze image: {e}")
                detailed_results.append({
                    "image_url": image_url,
                    "error": str(e),
                    "status": "failed"
                })
            finally:
                if image_path and os.path.exists(image_path):
                    try:
                        os.unlink(image_path)
                    except:
                        pass
        
        if valid_images == 0:
            logger.warning("No valid images")
            return 0.5, detailed_results
        
        # Average across all images
        final_score = np.mean(total_scores)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"FINAL ANALYSIS: {valid_images} images → score={final_score:.3f}")
        logger.info(f"{'='*60}\n")
        
        return round(final_score, 3), detailed_results
    
    def compute_entity_score(self, image_urls: List[str], images_exif: List[Dict] = None) -> Tuple[int, Dict]:
        """
        Compute entity score based on image analysis.
        
        Rules:
        - No images: score = 0
        - AI images (score < 0.50): score = -50
        - Real images (score >= 0.50): score = 100
        """
        if not image_urls:
            logger.info("No images → score = 0")
            return 0, {
                "reason": "no_images",
                "message": "No images provided"
            }
        
        # Analyze images
        real_probability, detailed_results = self.detect_ai_image(image_urls, images_exif)
        
        # ===== DECISION THRESHOLD =====
        # >= 0.50 = REAL (has camera EXIF or natural characteristics)
        # < 0.50 = AI (no EXIF + synthetic patterns)
        
        THRESHOLD = 0.50
        AI_SCORE = -50
        REAL_SCORE = 100
        
        if real_probability >= THRESHOLD:
            entity_score = REAL_SCORE
            verdict = "real"
            message = f"✓ Images are REAL (confidence: {real_probability*100:.1f}%)"
            logger.info(f"→ Entity score: {REAL_SCORE} (REAL)")
        else:
            entity_score = AI_SCORE
            verdict = "ai_generated"
            message = f"✗ Images are AI-GENERATED (confidence: {(1-real_probability)*100:.1f}%)"
            logger.info(f"→ Entity score: {AI_SCORE} (AI)")
        
        return entity_score, {
            "real_probability": real_probability,
            "verdict": verdict,
            "message": message,
            "images_analyzed": len([r for r in detailed_results if r.get("status") == "success"]),
            "images_failed": len([r for r in detailed_results if r.get("status") == "failed"]),
            "detailed_results": detailed_results
        }
