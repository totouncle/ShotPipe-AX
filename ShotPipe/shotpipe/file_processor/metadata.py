"""
Metadata extraction module for ShotPipe.
Provides functionality for extracting and managing metadata from media files.
"""
import os
import json
import logging
import subprocess
import shutil
from pathlib import Path
import traceback

# Try to import exiftool
EXIFTOOL_AVAILABLE = False
EXIFTOOL_PATH = None
try:
    import exiftool
    EXIFTOOL_AVAILABLE = True
    # Try to find ExifTool executable path in the system
    EXIFTOOL_PATH = shutil.which('exiftool')
except ImportError:
    pass

# Try to import ffmpeg-python for video metadata
FFMPEG_AVAILABLE = False
try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    pass

logger = logging.getLogger(__name__)

class MetadataExtractor:
    """Extracts and manages metadata from media files."""
    
    def __init__(self):
        """Initialize the metadata extractor."""
        self.exiftool = None
        self._initialize_exiftool()
    
    def _initialize_exiftool(self):
        """Initialize the ExifTool instance if available."""
        global EXIFTOOL_AVAILABLE, EXIFTOOL_PATH
        
        if not EXIFTOOL_AVAILABLE:
            logger.warning("ExifTool Python library not available. Some metadata functionality will be limited.")
            return False
        
        if not EXIFTOOL_PATH:
            # Try to find exiftool on the system path
            logger.debug("Searching for ExifTool executable")
            EXIFTOOL_PATH = shutil.which('exiftool')
            
            if not EXIFTOOL_PATH:
                logger.warning("ExifTool executable not found in system path. Trying alternative methods.")
                # Try common install locations
                for path in ['/usr/bin/exiftool', '/usr/local/bin/exiftool', '/opt/homebrew/bin/exiftool']:
                    if os.path.exists(path) and os.access(path, os.X_OK):
                        EXIFTOOL_PATH = path
                        logger.info(f"Found ExifTool at: {EXIFTOOL_PATH}")
                        break
        
        if EXIFTOOL_PATH:
            logger.info(f"Using ExifTool from: {EXIFTOOL_PATH}")
        
        try:
            # Initialize exiftool properly based on the version of PyExifTool that's installed
            try:
                # Try the newer ExifToolHelper interface first
                if hasattr(exiftool, 'ExifToolHelper'):
                    options = []
                    if EXIFTOOL_PATH:
                        options = ['-executable', EXIFTOOL_PATH]
                    self.exiftool = exiftool.ExifToolHelper(executable=EXIFTOOL_PATH)
                    logger.info("ExifTool initialized successfully using ExifToolHelper")
                    # Test run to verify it's working
                    version = self.exiftool.get_version()
                    logger.info(f"ExifTool version: {version}")
                    return True
            except (AttributeError, TypeError) as e:
                logger.warning(f"Could not initialize ExifToolHelper: {e}")
                
            # Fall back to the older ExifTool interface if necessary
            if not self.exiftool and hasattr(exiftool, 'ExifTool'):
                self.exiftool = exiftool.ExifTool()
                try:
                    if hasattr(self.exiftool, 'start'):
                        self.exiftool.start()
                        logger.info("ExifTool initialized successfully using legacy ExifTool interface")
                        # Test getting version to verify it's working
                        try:
                            if hasattr(self.exiftool, 'execute'):
                                version = self.exiftool.execute('-ver')
                                logger.info(f"ExifTool legacy version: {version.strip()}")
                            else:
                                logger.warning("Legacy ExifTool missing 'execute' method")
                        except Exception as test_e:
                            logger.warning(f"Error testing legacy ExifTool: {test_e}")
                        return True
                    else:
                        logger.warning("ExifTool object has no 'start' method")
                except Exception as e:
                    logger.warning(f"Failed to start ExifTool: {e}")
                    if self.exiftool and hasattr(self.exiftool, 'terminate'):
                        try:
                            self.exiftool.terminate()
                        except:
                            pass
                    self.exiftool = None
            
            # If we couldn't initialize with either method, try a direct subprocess approach
            if not self.exiftool and EXIFTOOL_PATH:
                try:
                    # Check if the executable works by getting its version
                    result = subprocess.run([EXIFTOOL_PATH, '-ver'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        # Save the path and mark as available for direct subprocess calls
                        self.exiftool = {'path': EXIFTOOL_PATH, 'direct': True}
                        logger.info(f"Will use direct ExifTool subprocess calls (version: {result.stdout.strip()})")
                        return True
                except Exception as e:
                    logger.warning(f"Error executing ExifTool directly: {e}")
            
            # If we got here, we couldn't initialize ExifTool
            logger.warning("Could not initialize any ExifTool interface")
            EXIFTOOL_AVAILABLE = False
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize ExifTool: {str(e)}")
            EXIFTOOL_AVAILABLE = False
            return False
    
    def extract_metadata(self, file_path):
        """
        Extract metadata from a file.
        
        Args:
            file_path (str): Path to the file
        
        Returns:
            dict: Extracted metadata
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {}
        
        logger.debug(f"Extracting metadata from: {file_path}")
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Always include basic file information
        metadata = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "file_extension": file_extension,
            "file_size": os.path.getsize(file_path),
            "modified_time": os.path.getmtime(file_path),
            "creation_time": os.path.getctime(file_path)
        }
        
        # Determine file type based on extension
        if file_extension in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.gif', '.bmp', '.webp', '.exr', '.dpx']:
            metadata["file_type"] = "image"
        elif file_extension in ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.mxf', '.m4v', '.webm']:
            metadata["file_type"] = "video"
        else:
            metadata["file_type"] = "unknown"
        
        try:
            # Try to extract metadata using ExifTool first
            exiftool_success = False
            if EXIFTOOL_AVAILABLE and self.exiftool:
                try:
                    exif_data = None
                    
                    # Check which type of exiftool interface we're using
                    if isinstance(self.exiftool, dict) and self.exiftool.get('direct'):
                        # Using direct subprocess calls
                        try:
                            exiftool_path = self.exiftool['path']
                            result = subprocess.run(
                                [exiftool_path, '-json', '-a', '-u', '-g1', file_path], 
                                capture_output=True, 
                                text=True, 
                                timeout=10
                            )
                            if result.returncode == 0:
                                try:
                                    exif_data = json.loads(result.stdout)
                                    logger.debug(f"ExifTool direct subprocess metadata extracted for {file_path}")
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse ExifTool JSON output: {e}")
                        except Exception as e:
                            logger.warning(f"Error extracting metadata with direct ExifTool call: {e}")
                    elif hasattr(self.exiftool, 'get_metadata'):
                        # Using ExifToolHelper interface
                        exif_data = self.exiftool.get_metadata(file_path)
                        logger.debug(f"ExifToolHelper metadata extracted for {file_path}")
                    elif hasattr(self.exiftool, 'get_tags'):
                        # Using legacy ExifTool interface
                        exif_data = self.exiftool.get_tags(file_path)
                        logger.debug(f"Legacy ExifTool metadata extracted for {file_path}")
                    
                    if exif_data:
                        # ExifTool can return a list or dict depending on the version
                        if isinstance(exif_data, list):
                            if len(exif_data) > 0:
                                cleaned_exif = self._make_json_serializable(exif_data[0])
                                metadata["exif"] = cleaned_exif
                                exiftool_success = True
                        else:
                            # Assuming it's a dictionary
                            cleaned_exif = self._make_json_serializable(exif_data)
                            metadata["exif"] = cleaned_exif
                            exiftool_success = True
                        
                        # Extract common metadata fields if available
                        if "exif" in metadata:
                            self._extract_common_metadata(metadata, metadata["exif"])
                except Exception as e:
                    logger.error(f"Error extracting metadata with ExifTool: {e}")
            
            # Try PIL for images if ExifTool failed or for all images as backup
            if metadata["file_type"] == "image":
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        metadata["width"] = img.width
                        metadata["height"] = img.height
                        metadata["format"] = img.format
                        metadata["mode"] = img.mode
                        
                        # Try to get exif from PIL
                        if hasattr(img, '_getexif') and img._getexif():
                            metadata["pil_exif"] = self._make_json_serializable(img._getexif())
                        
                        logger.debug(f"PIL metadata extracted for {file_path}")
                except Exception as e:
                    logger.error(f"Error extracting image metadata with PIL: {e}")
            
            # For video files, try ffmpeg if available
            if metadata["file_type"] == "video" and FFMPEG_AVAILABLE:
                try:
                    video_info = ffmpeg.probe(file_path)
                    if video_info:
                        logger.debug(f"FFMPEG metadata extracted for {file_path}")
                        metadata["ffmpeg"] = video_info
                        
                        # Extract common video metadata
                        if "streams" in video_info:
                            for stream in video_info["streams"]:
                                if stream.get("codec_type") == "video":
                                    metadata["width"] = stream.get("width")
                                    metadata["height"] = stream.get("height")
                                    metadata["codec"] = stream.get("codec_name")
                                    metadata["frame_rate"] = self._parse_frame_rate(stream.get("r_frame_rate", ""))
                                    metadata["duration"] = stream.get("duration")
                                    metadata["video_stream"] = stream
                                    break
                except Exception as e:
                    logger.error(f"Error extracting video metadata with FFMPEG: {e}")
            
            return metadata
        
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Error extracting metadata for {file_path}: {e}\n{error_trace}")
            return metadata  # Return basic metadata even if extraction fails
    
    def _parse_frame_rate(self, frame_rate_str):
        """Parse frame rate string (e.g. '24000/1001') to a float."""
        try:
            if '/' in frame_rate_str:
                num, den = frame_rate_str.split('/')
                return float(num) / float(den)
            else:
                return float(frame_rate_str)
        except:
            return None
    
    def _extract_common_metadata(self, metadata, exif_data):
        """
        Extract common metadata fields from ExifTool data.
        
        Args:
            metadata (dict): Metadata dictionary to update
            exif_data (dict): ExifTool metadata
        """
        # Map common ExifTool fields to our metadata structure
        field_mapping = {
            "EXIF:Make": "camera_make",
            "EXIF:Model": "camera_model",
            "EXIF:DateTimeOriginal": "capture_date",
            "EXIF:CreateDate": "create_date",
            "EXIF:ImageWidth": "width",
            "EXIF:ImageHeight": "height",
            "Composite:ImageSize": "image_size",
            "File:FileType": "file_type",
            "File:MIMEType": "mime_type"
        }
        
        # Alternative field names that might be present
        alt_fields = {
            "SourceFile": None,  # Skip this field
            "File:FileName": "file_name",
            "File:Directory": "directory",
            "File:FileSize": "file_size",
            "PNG:ImageWidth": "width",
            "PNG:ImageHeight": "height",
            "JPEG:ImageWidth": "width",
            "JPEG:ImageHeight": "height",
            "QuickTime:ImageWidth": "width",
            "QuickTime:ImageHeight": "height",
            "XMP:CreateDate": "create_date",
            "XMP:ModifyDate": "modify_date"
        }
        
        # Add primary field mappings
        for exif_field, meta_field in field_mapping.items():
            if exif_field in exif_data:
                metadata[meta_field] = exif_data[exif_field]
        
        # Try alternative field names if primary ones aren't present
        for exif_field, meta_field in alt_fields.items():
            if meta_field and exif_field in exif_data and meta_field not in metadata:
                metadata[meta_field] = exif_data[exif_field]
    
    def save_metadata(self, metadata, output_path):
        """
        Save metadata to a JSON file.
        
        Args:
            metadata (dict): Metadata to save
            output_path (str): Path to save the metadata file
        
        Returns:
            bool: Success status
        """
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Prepare metadata for serialization (ensure it's JSON serializable)
            serializable_metadata = self._make_json_serializable(metadata)
            
            # Write the metadata to the file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_metadata, f, indent=4, ensure_ascii=False)
            
            logger.debug(f"Metadata saved to: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving metadata to {output_path}: {e}")
            return False
    
    def _make_json_serializable(self, obj):
        """
        Make an object JSON serializable by converting problematic types.
        
        Args:
            obj: The object to make serializable
        
        Returns:
            object: JSON serializable version of the object
        """
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (bytes, bytearray)):
            return str(obj)
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    def __del__(self):
        """Clean up the ExifTool instance."""
        if EXIFTOOL_AVAILABLE and hasattr(self, 'exiftool') and self.exiftool is not None:
            try:
                # Clean up based on the interface being used
                if hasattr(self.exiftool, 'terminate'):
                    self.exiftool.terminate()
                    logger.debug("ExifTool instance terminated")
                # ExifToolHelper doesn't need explicit termination
                logger.debug("ExifTool instance cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up ExifTool: {e}")