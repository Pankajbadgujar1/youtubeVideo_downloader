from django import forms
import re

class YouTubeURLForm(forms.Form):
    """Form for YouTube URL input validation"""
    
    url = forms.URLField(
        max_length=500,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Paste YouTube URL here...',
            'id': 'youtube-url'
        }),
        help_text='Enter a valid YouTube video URL'
    )
    
    def clean_url(self):
        """Validate that the URL is a YouTube URL"""
        url = self.cleaned_data['url']
        
        # YouTube URL patterns
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
            r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=[\w-]+',
        ]
        
        if not any(re.match(pattern, url) for pattern in youtube_patterns):
            raise forms.ValidationError('Please enter a valid YouTube URL.')
        
        return url

class DownloadForm(forms.Form):
    """Form for download options"""
    
    DOWNLOAD_TYPES = [
        ('mp4', 'MP4 Video'),
        ('mp3', 'MP3 Audio'),
        ('both', 'Both MP4 & MP3'),
    ]
    
    url = forms.CharField(widget=forms.HiddenInput())
    itag = forms.CharField(max_length=10, required=False, widget=forms.HiddenInput())
    resolution = forms.CharField(max_length=20, required=False)
    download_type = forms.ChoiceField(
        choices=DOWNLOAD_TYPES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='mp4'
    ) 