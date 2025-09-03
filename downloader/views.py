import json
import logging
import tempfile
import os
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from .forms import YouTubeURLForm, DownloadForm
from .utils import YouTubeDownloader, cleanup_temp_files, format_filesize

logger = logging.getLogger('downloader')

def index(request):
    """Main page with download form"""
    url_form = YouTubeURLForm()
    download_form = DownloadForm()
    
    context = {
        'url_form': url_form,
        'download_form': download_form,
        'max_file_size': settings.MAX_FILE_SIZE_MB
    }
    
    return render(request, 'index.html', context)

@require_POST
def get_streams(request):
    try:
        data = json.loads(request.body)
        url = data.get('url')
        print("Received URL:", url)
        if not url:
            return HttpResponseBadRequest('Missing URL')
        url_form = YouTubeURLForm({'url': url})
        if not url_form.is_valid():
            return HttpResponseBadRequest('Invalid YouTube URL')
        downloader = YouTubeDownloader(url)
        print("Downloader initialized")
        video_info = downloader.validate_and_fetch_info()
        print("Video info fetched:", video_info)
        streams = downloader.get_available_streams()
        print("Streams:", streams)
        if not streams:
            return HttpResponseBadRequest('No compatible streams found for this video')
        response_data = {
            'video_info': video_info,
            'streams': []
        }
        for stream in streams:
            response_data['streams'].append({
                'itag': stream['itag'],
                'resolution': stream['resolution'],
                'fps': stream.get('fps'),
                'filesize': stream.get('filesize', 0),
                'filesize_formatted': format_filesize(stream.get('filesize', 0)),
                'mime_type': stream.get('mime_type'),
                'note': stream.get('note', '')
            })
        return JsonResponse(response_data)
    except Exception as e:
        import traceback
        print("Error in get_streams:", str(e))
        traceback.print_exc()
        return HttpResponseBadRequest(str(e))

@require_POST
def download_video(request):
    """Handle video/audio download requests"""
    temp_files = []  # Track temp files for cleanup
    
    try:
        # Get form data
        url = request.POST.get('url')
        itag = request.POST.get('itag')
        download_type = request.POST.get('download_type', 'mp4')
        
        if not url or not itag:
            messages.error(request, 'Missing required parameters')
            return render(request, 'index.html', {
                'url_form': YouTubeURLForm(),
                'download_form': DownloadForm()
            })
        
        # Initialize downloader
        downloader = YouTubeDownloader(url)
        downloader.validate_and_fetch_info()
        
        # Download video file
        video_path = downloader.download_video(itag)
        temp_files.append(video_path)
        temp_files.append(os.path.dirname(video_path))  # Add temp directory for cleanup
        
        if download_type == 'mp4':
            # Return video file
            response = downloader.create_response_file(video_path)
            
        elif download_type == 'mp3':
            # Convert to MP3 and return audio file
            mp3_path = downloader.convert_to_mp3(video_path)
            temp_files.append(mp3_path)
            response = downloader.create_response_file(mp3_path)
            
        elif download_type == 'both':
            # Convert to MP3 and create ZIP with both files
            mp3_path = downloader.convert_to_mp3(video_path)
            temp_files.append(mp3_path)
            
            files_dict = {
                os.path.basename(video_path): video_path,
                os.path.basename(mp3_path): mp3_path
            }
            response = downloader.create_zip_response(files_dict)
            
        else:
            raise ValueError('Invalid download type')
        
        # Cleanup temp files after response
        import threading, time
        def delayed_cleanup():
            time.sleep(getattr(settings, 'TEMP_FILE_CLEANUP_TIMEOUT', 60))
            cleanup_temp_files(*temp_files)
        threading.Thread(target=delayed_cleanup, daemon=True).start()

        return response

    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        messages.error(request, str(e))
        cleanup_temp_files(*temp_files)
        return render(request, 'index.html', {
            'url_form': YouTubeURLForm(),
            'download_form': DownloadForm()
        })

def get_available_streams(self):
    print("Raw formats:", self.info.get('formats', []))
    streams = []
    for f in self.info.get('formats', []):
        # Only require 'url', not 'filesize'
        if f.get('url'):
            streams.append({
                'itag': f.get('format_id'),
                'resolution': f.get('resolution') or f.get('height'),
                'filesize': f.get('filesize', 0),
                'mime_type': f.get('mime_type'),
                'note': f.get('format_note'),
                'fps': f.get('fps'),
            })
    print("Filtered streams:", streams)
    return streams
