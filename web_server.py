#!/usr/bin/env python3
"""
Web server for Twitter Video Downloader
Provides a web interface for downloading Twitter videos
Adapted for Railway deployment
"""

import os
import json
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
from twitter_downloader import TwitterDownloader

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

# Global variables to track download progress
download_progress = {}
download_results = {}

class WebTwitterDownloader(TwitterDownloader):
    def __init__(self, output_dir="downloads", progress_id=None):
        super().__init__(output_dir)
        self.progress_id = progress_id
        
        # Override yt-dlp options for web interface
        self.ydl_opts.update({
            'progress_hooks': [self._progress_hook],
            'quiet': True,  # Reduce console output for web interface
        })
    
    def _progress_hook(self, d):
        """Hook to track download progress"""
        if self.progress_id and d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', '0%').strip()
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                
                download_progress[self.progress_id] = {
                    'status': 'downloading',
                    'percent': percent,
                    'speed': speed,
                    'eta': eta,
                    'filename': d.get('filename', 'Unknown')
                }
            except:
                pass
        elif self.progress_id and d['status'] == 'finished':
            download_progress[self.progress_id] = {
                'status': 'finished',
                'percent': '100%',
                'filename': d.get('filename', 'Unknown')
            }
    
    def get_video_info_web(self, url):
        """Get video information and available qualities"""
        if not self.is_valid_twitter_url(url):
            return {
                'success': False,
                'error': 'Invalid Twitter URL format',
                'message': 'Please provide a valid Twitter/X URL'
            }
        
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                # Extract info without downloading
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return {
                        'success': False,
                        'error': 'No video found',
                        'message': 'No video found at this URL'
                    }
                
                # Get all formats and filter video formats
                formats = info.get('formats', [])
                video_formats = []
                
                for f in formats:
                    if f.get('vcodec') != 'none' and f.get('url'):
                        quality_info = {
                            'format_id': f.get('format_id'),
                            'ext': f.get('ext', 'mp4'),
                            'quality': f.get('format_note', 'Unknown'),
                            'resolution': f.get('resolution', 'Unknown'),
                            'width': f.get('width'),
                            'height': f.get('height'),
                            'fps': f.get('fps'),
                            'filesize': f.get('filesize'),
                            'filesize_approx': f.get('filesize_approx'),
                            'tbr': f.get('tbr'),  # Total bitrate
                            'vbr': f.get('vbr'),  # Video bitrate
                        }
                        video_formats.append(quality_info)
                
                if not video_formats:
                    return {
                        'success': False,
                        'error': 'No video content',
                        'message': 'This tweet contains no video content'
                    }
                
                # Sort by quality (height desc, then bitrate desc)
                video_formats.sort(key=lambda x: (
                    x.get('height', 0), 
                    x.get('tbr', 0)
                ), reverse=True)
                
                return {
                    'success': True,
                    'title': info.get('title', 'Unknown title'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration', 'Unknown'),
                    'thumbnail': info.get('thumbnail'),
                    'formats': video_formats
                }
                
        except yt_dlp.DownloadError as e:
            error_msg = str(e)
            if "Private" in error_msg or "protected" in error_msg.lower():
                return {
                    'success': False,
                    'error': 'Private account',
                    'message': 'This tweet is from a private account'
                }
            elif "not found" in error_msg.lower():
                return {
                    'success': False,
                    'error': 'Tweet not found',
                    'message': 'Tweet not found - it might have been deleted'
                }
            else:
                return {
                    'success': False,
                    'error': 'Download error',
                    'message': error_msg
                }
        except Exception as e:
            return {
                'success': False,
                'error': 'Unexpected error',
                'message': str(e)
            }

    def download_video_web(self, url, format_id=None):
        """Download video with web-friendly error handling and quality selection"""
        if not self.is_valid_twitter_url(url):
            return {
                'success': False,
                'error': 'Invalid Twitter URL format',
                'message': 'Please provide a valid Twitter/X URL'
            }
        
        try:
            if self.progress_id:
                download_progress[self.progress_id] = {
                    'status': 'extracting',
                    'percent': '0%',
                    'message': 'Extracting video information...'
                }
            
            # Update yt-dlp options for specific format if provided
            opts = self.ydl_opts.copy()
            if format_id:
                opts['format'] = format_id
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return {
                        'success': False,
                        'error': 'No video found',
                        'message': 'No video found at this URL'
                    }
                
                # Check for video formats
                formats = info.get('formats', [])
                video_formats = [f for f in formats if f.get('vcodec') != 'none']
                
                if not video_formats:
                    return {
                        'success': False,
                        'error': 'No video content',
                        'message': 'This tweet contains no video content'
                    }
                
                # Download the video
                ydl.download([url])
                
                # Get the downloaded filename
                filename = ydl.prepare_filename(info)
                
                # Get the selected format info
                selected_format = None
                if format_id:
                    selected_format = next((f for f in formats if f.get('format_id') == format_id), None)
                
                return {
                    'success': True,
                    'title': info.get('title', 'Unknown title'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration', 'Unknown'),
                    'filename': os.path.basename(filename),
                    'filepath': filename,
                    'format_info': {
                        'quality': selected_format.get('format_note', 'Auto') if selected_format else 'Auto',
                        'resolution': selected_format.get('resolution', 'Unknown') if selected_format else 'Best available'
                    }
                }
                
        except yt_dlp.DownloadError as e:
            error_msg = str(e)
            if "Private" in error_msg or "protected" in error_msg.lower():
                return {
                    'success': False,
                    'error': 'Private account',
                    'message': 'This tweet is from a private account'
                }
            elif "not found" in error_msg.lower():
                return {
                    'success': False,
                    'error': 'Tweet not found',
                    'message': 'Tweet not found - it might have been deleted'
                }
            else:
                return {
                    'success': False,
                    'error': 'Download error',
                    'message': error_msg
                }
        except Exception as e:
            return {
                'success': False,
                'error': 'Unexpected error',
                'message': str(e)
            }

@app.route('/')
def index():
    """Main page"""
    return jsonify({'message': 'Twitter Video Downloader API', 'status': 'running'})

@app.route('/video_info', methods=['POST'])
def get_video_info():
    """API endpoint to get video information and available qualities"""
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    downloader = WebTwitterDownloader()
    result = downloader.get_video_info_web(url)
    
    return jsonify(result)

@app.route('/download', methods=['POST'])
def download_video():
    """API endpoint to start video download"""
    data = request.get_json()
    url = data.get('url', '').strip()
    format_id = data.get('format_id')  # Optional quality selection
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    # Generate unique progress ID
    import time
    progress_id = f"download_{int(time.time())}"
    
    # Initialize progress tracking
    download_progress[progress_id] = {
        'status': 'starting',
        'percent': '0%',
        'message': 'Initializing download...'
    }
    
    def download_thread():
        """Background thread for downloading"""
        downloader = WebTwitterDownloader(progress_id=progress_id)
        result = downloader.download_video_web(url, format_id)
        download_results[progress_id] = result
        
        if result['success']:
            download_progress[progress_id] = {
                'status': 'completed',
                'percent': '100%',
                'message': 'Download completed successfully!'
            }
        else:
            download_progress[progress_id] = {
                'status': 'error',
                'percent': '0%',
                'message': result.get('message', 'Download failed')
            }
    
    # Start download in background thread
    thread = threading.Thread(target=download_thread)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'progress_id': progress_id,
        'message': 'Download started'
    })

@app.route('/progress/<progress_id>')
def get_progress(progress_id):
    """Get download progress"""
    progress = download_progress.get(progress_id, {
        'status': 'unknown',
        'percent': '0%',
        'message': 'Unknown progress ID'
    })
    
    result = download_results.get(progress_id)
    if result:
        progress['result'] = result
    
    return jsonify(progress)

@app.route('/downloads')
def list_downloads():
    """List available downloads"""
    downloads_dir = Path('downloads')
    if not downloads_dir.exists():
        return jsonify({'files': []})
    
    files = []
    for file_path in downloads_dir.glob('*'):
        if file_path.is_file():
            files.append({
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'modified': file_path.stat().st_mtime
            })
    
    return jsonify({'files': files})

@app.route('/download_file/<filename>')
def download_file(filename):
    """Download a file from the downloads directory"""
    file_path = Path('downloads') / filename
    if file_path.exists() and file_path.is_file():
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    # Create downloads directory
    Path('downloads').mkdir(exist_ok=True)
    
    # Get port from environment variable (Railway sets this automatically)
    port = int(os.environ.get('PORT', 8080))
    
    print("🚀 Starting Twitter Video Downloader Web Interface")
    print(f"📱 Server will run on port {port}")
    print("🛑 Press Ctrl+C to stop the server")
    
    app.run(debug=False, host='0.0.0.0', port=port)

@app.route('/stream_download', methods=['POST'])
def stream_download():
    """Stream video download directly to browser without saving to disk"""
    data = request.get_json()
    url = data.get('url', '').strip()
    format_id = data.get('format_id')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    downloader = WebTwitterDownloader()
    
    if not downloader.is_valid_twitter_url(url):
        return jsonify({
            'success': False, 
            'error': 'Invalid Twitter URL format',
            'message': 'Please provide a valid Twitter/X URL'
        })
    
    try:
        # Get video info first
        info_result = downloader.get_video_info_web(url)
        if not info_result['success']:
            return jsonify(info_result)
        
        # Find the requested format
        selected_format = None
        if format_id:
            for fmt in info_result['formats']:
                if fmt['format_id'] == format_id:
                    selected_format = fmt
                    break
        
        if not selected_format:
            selected_format = info_result['formats'][0]  # Use best quality
        
        # Generate filename
        import re
        clean_title = re.sub(r'[<>:"/\\|?*]', '_', (info_result['title'] or 'twitter_video'))[:100]
        filename = f"{clean_title}_{selected_format['resolution']}.{selected_format['ext']}"
        
        # Stream the download using yt-dlp
        import subprocess
        import io
        
        cmd = [
            'yt-dlp',
            '--format', selected_format['format_id'],
            '--output', '-',  # Output to stdout
            url
        ]
        
        def generate():
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                while True:
                    chunk = process.stdout.read(8192)
                    if not chunk:
                        break
                    yield chunk
            finally:
                process.terminate()
                process.wait()
        
        from flask import Response
        return Response(
            generate(),
            mimetype='video/mp4',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'video/mp4'
            }
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Download error', 
            'message': str(e)
        })
