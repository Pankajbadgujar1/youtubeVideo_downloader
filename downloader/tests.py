from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json

class YouTubeDownloaderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.valid_youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.invalid_url = "https://example.com"
    
    def test_index_page_loads(self):
        """Test that the main page loads successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'YouTube Video/Audio Downloader')
    
    @patch('downloader.utils.YouTube')
    def test_get_streams_valid_url(self, mock_youtube):
        """Test get_streams with valid YouTube URL"""
        # Mock YouTube object
        mock_yt = MagicMock()
        mock_yt.title = "Test Video"
        mock_yt.length = 240
        mock_yt.views = 1000
        mock_yt.author = "Test Author"
        mock_yt.thumbnail_url = "http://example.com/thumb.jpg"
        
        # Mock stream
        mock_stream = MagicMock()
        mock_stream.itag = 18
        mock_stream.resolution = "360p"
        mock_stream.fps = 30
        mock_stream.filesize = 1000000
        mock_stream.mime_type = "video/mp4"
        
        mock_yt.streams.filter.return_value.order_by.return_value = [mock_stream]
        mock_youtube.return_value = mock_yt
        
        response = self.client.post(
            '/get_streams/',
            data=json.dumps({'url': self.valid_youtube_url}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('video_info', data)
        self.assertIn('streams', data)
    
    def test_get_streams_invalid_url(self):
        """Test get_streams with invalid URL"""
        response = self.client.post(
            '/get_streams/',
            data=json.dumps({'url': self.invalid_url}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_get_streams_missing_url(self):
        """Test get_streams without URL"""
        response = self.client.post(
            '/get_streams/',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)