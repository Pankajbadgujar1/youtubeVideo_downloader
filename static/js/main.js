// YouTube Downloader JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    const urlInput = document.getElementById('youtube-url');
    const fetchBtn = document.getElementById('fetch-info-btn');
    const loadingSpinner = document.getElementById('loading-spinner');
    const videoInfo = document.getElementById('video-info');
    const downloadForm = document.getElementById('download-form');
    const qualitySelect = document.getElementById('quality-select');
    const downloadProgress = document.getElementById('download-progress');
    const selectedItagInput = document.getElementById('selected-itag');
    const selectedUrlInput = document.getElementById('selected-url');

    let availableStreams = [];

    // Fetch video info when button is clicked
    fetchBtn.addEventListener('click', function() {
        const url = urlInput.value.trim();

        if (!url) {
            showAlert('Please enter a YouTube URL', 'warning');
            return;
        }

        if (!isValidYouTubeURL(url)) {
            showAlert('Please enter a valid YouTube URL', 'danger');
            return;
        }

        fetchVideoInfo(url);
    });

    // Also fetch when Enter is pressed in URL input
    urlInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            fetchBtn.click();
        }
    });

    // Update hidden itag when quality is selected
    qualitySelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        const itag = selectedOption.dataset.itag || '';
        selectedItagInput.value = itag;
    });

    // Handle download form submission
    downloadForm.addEventListener('submit', function(e) {
        const selectedQuality = qualitySelect.value;
        const selectedItag = selectedItagInput.value;
        if (!selectedQuality || !selectedItag) {
            e.preventDefault();
            showAlert('Please select a video quality', 'warning');
            return;
        }
        downloadForm.action = '/download/';
    });

    function fetchVideoInfo(url) {
        showLoading();
        hideElements([videoInfo, downloadForm]);
        clearQualityOptions();

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        fetch('/get_streams/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ url: url })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();

            if (data.error) {
                showAlert(data.error, 'danger');
                return;
            }

            displayVideoInfo(data.video_info);
            populateQualityOptions(data.streams);
            selectedUrlInput.value = url;
            showElement(downloadForm);
            availableStreams = data.streams;
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            showAlert('An error occurred while fetching video information. Please try again.', 'danger');
        });
    }

    function displayVideoInfo(videoInfoData) {
        const thumbnail = document.getElementById('video-thumbnail');
        thumbnail.src = videoInfoData.thumbnail_url;
        thumbnail.alt = videoInfoData.title;

        document.getElementById('video-title').textContent = videoInfoData.title;
        document.getElementById('video-author').textContent = videoInfoData.author;
        document.getElementById('video-views').textContent = formatNumber(videoInfoData.views);
        document.getElementById('video-duration').textContent = formatDuration(videoInfoData.length);

        showElement(videoInfo);
        videoInfo.classList.add('fade-in-up');
    }

    function populateQualityOptions(streams) {
        clearQualityOptions();

        streams.forEach((stream, idx) => {
            const option = document.createElement('option');
            option.value = stream.resolution;
            option.dataset.itag = stream.itag;

            let optionText = `${stream.resolution}`;
            if (stream.fps) {
                optionText += ` (${stream.fps}fps)`;
            }
            optionText += ` - ${stream.filesize_formatted}`;
            if (stream.note) {
                optionText += ` - ${stream.note}`;
            }

            option.textContent = optionText;
            qualitySelect.appendChild(option);

            // Set the first itag and select the first option by default
            if (idx === 0) {
                selectedItagInput.value = stream.itag;
                qualitySelect.selectedIndex = 1; // 0 is the placeholder
            }
        });
    }

    function clearQualityOptions() {
        qualitySelect.innerHTML = '<option value="">Select video quality...</option>';
        selectedItagInput.value = '';
    }

    function showLoading() {
        showElement(loadingSpinner);
        fetchBtn.disabled = true;
        fetchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    }

    function hideLoading() {
        hideElement(loadingSpinner);
        fetchBtn.disabled = false;
        fetchBtn.innerHTML = '<i class="fas fa-search me-2"></i>Get Info';
    }

    function showDownloadProgress() {
        hideElements([downloadForm]);
        showElement(downloadProgress);
    }

    function showElement(element) {
        element.style.display = 'block';
    }

    function hideElement(element) {
        element.style.display = 'none';
    }

    function hideElements(elements) {
        elements.forEach(element => hideElement(element));
    }

    function showAlert(message, type = 'info') {
        const existingAlerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        existingAlerts.forEach(alert => alert.remove());

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            <i class="fas fa-${getIconForType(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const cardBody = document.querySelector('.card-body');
        cardBody.insertBefore(alertDiv, cardBody.firstChild);

        if (type !== 'danger') {
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    }

    function getIconForType(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    function isValidYouTubeURL(url) {
        const patterns = [
            /^(https?:\/\/)?(www\.)?youtube\.com\/watch\?v=[\w-]+/,
            /^(https?:\/\/)?(www\.)?youtu\.be\/[\w-]+/,
            /^(https?:\/\/)?(m\.)?youtube\.com\/watch\?v=[\w-]+/
        ];

        return patterns.some(pattern => pattern.test(url));
    }

    function formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    function formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;

        if (minutes >= 60) {
            const hours = Math.floor(minutes / 60);
            const remainingMinutes = minutes % 60;
            return `${hours}:${remainingMinutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
        }

        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    // Add smooth scrolling to download form when it appears
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                if (downloadForm.style.display === 'block') {
                    setTimeout(() => {
                        downloadForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 100);
                }
            }
        });
    });

    observer.observe(downloadForm, { attributes: true });
});