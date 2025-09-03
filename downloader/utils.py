import os
import tempfile
import logging
from io import BytesIO
import zipfile
import magic
from django.conf import settings
from django.http import HttpResponse, Http404
from pytube import YouTube
import yt_dlp

logger = logging.getLogger('downloader')
class YouTubeDownloader:
    """Utility class for YouTube video/audio downloads"""
    
    def __init__(self, url):
        try:
            self.url = url
            self.yt = YouTube(url)
        except Exception as e:
            logger.error("YouTubeDownloader initialization error: %s", str(e))
            raise ValueError(f"Unable to process YouTube URL: {str(e)}") from e
        
    def validate_and_fetch_info(self):
        """Validate URL and fetch video information"""
        try:
            ydl_opts = {'quiet': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                video_info = {
                    'title': info.get('title'),
                    'author': info.get('uploader'),
                    'length': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                }
                self.info = info
                return video_info
        except Exception as e:
            logger.error(f"Failed to fetch video info: {str(e)}")
            raise ValueError(f"Unable to process YouTube URL: {str(e)}")
    
    def get_available_streams(self):
        """Get available video/audio streams with resolutions"""
        streams = []
        for f in self.info.get('formats', []):
            # Debug: print all formats
            logger.debug(f"Format: {f}")
            # Only include formats with a direct URL and a valid extension
            if f.get('url') and f.get('ext') in ['mp4', 'webm', 'm4a', 'mp3']:
                streams.append({
                    'itag': f.get('format_id'),
                    'resolution': f.get('resolution') or f.get('height') or 'audio',
                    'filesize': f.get('filesize', 0),
                    'mime_type': f.get('mime_type'),
                    'note': f.get('format_note'),
                    'fps': f.get('fps'),
                })
        logger.info(f"Filtered streams: {streams}")
        return streams
    def download_video(self, itag):
        """Download video stream and return file path"""
        try:
            ydl_opts = {
                'format': itag,
                'outtmpl': 'downloads/%(title)s.%(ext)s',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            raise ValueError(f"Download failed: {str(e)}")
    
    # def convert_to_mp3(self, video_path):
    #     """Convert video file to MP3 using moviepy"""
    #     try:
    #         # Create output path
    #         output_dir = os.path.dirname(video_path)
    #         base_name = os.path.splitext(os.path.basename(video_path))[0]
    #         mp3_path = os.path.join(output_dir, f"{base_name}.mp3")
            
    #         # Convert using moviepy
    #         video_clip = VideoFileClip(video_path)
    #         audio_clip = video_clip.audio
    #         audio_clip.write_audiofile(mp3_path, logger=None, verbose=False)
            
    #         # Clean up
    #         audio_clip.close()
    #         video_clip.close()
            
    #         logger.info(f"Converted to MP3: {mp3_path}")
    #         return mp3_path
            
    #     except Exception as e:
    #         logger.error(f"MP3 conversion failed: {str(e)}")
    #         raise ValueError(f"MP3 conversion failed: {str(e)}")
    
    def create_response_file(self, file_path, download_name=None):
        """Create HTTP response for file download"""
        try:
            if not os.path.exists(file_path):
                raise Http404("File not found")
            
            # Determine MIME type
            mime_type = magic.from_file(file_path, mime=True)

            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Create response
            response = HttpResponse(file_content, content_type=mime_type)
            
            # Set filename
            if not download_name:
                download_name = os.path.basename(file_path)
            
            response['Content-Disposition'] = f'attachment; filename="{download_name}"'
            response['Content-Length'] = len(file_content)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to create response: {str(e)}")
            raise ValueError(f"Failed to prepare download: {str(e)}")
    
    def create_zip_response(self, files_dict):
        """Create ZIP file response with multiple files"""
        try:
            # Create in-memory ZIP
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename, filepath in files_dict.items():
                    if os.path.exists(filepath):
                        zip_file.write(filepath, filename)
            
            zip_buffer.seek(0)
            
            # Create response
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            safe_title = "".join(c for c in self.yt.title if c.isalnum() or c in (' ', '-', '_')).strip()
            response['Content-Disposition'] = f'attachment; filename="{safe_title}_download.zip"'
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to create ZIP: {str(e)}")
            raise ValueError(f"Failed to create ZIP file: {str(e)}")

def cleanup_temp_files(*file_paths):
    """Clean up temporary files and directories"""
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    logger.info(f"Cleaned up file: {path}")
                elif os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                    logger.info(f"Cleaned up directory: {path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {path}: {str(e)}")

def format_filesize(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"