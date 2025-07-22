# Twitter Video Downloader API

A Flask API service that downloads Twitter/X videos using yt-dlp with quality selection.

## Features

- 📱 Extract video information and available qualities from Twitter URLs
- 🎬 Download videos in selected quality
- 📊 Real-time download progress tracking
- 🌐 CORS enabled for browser extension integration
- ☁️ Railway deployment ready

## API Endpoints

- `POST /video_info` - Get video information and available qualities
- `POST /download` - Start video download
- `GET /progress/<id>` - Get download progress
- `GET /download_file/<filename>` - Download completed file

## Deployment

This app is configured for Railway deployment with:
- `Procfile` - Defines how to start the app
- `requirements.txt` - Python dependencies

## Local Development

```bash
pip install -r requirements.txt
python web_server.py
```

Server runs on port 8080 (or PORT environment variable).
