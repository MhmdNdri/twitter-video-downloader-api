#!/usr/bin/env python3
"""
Twitter Video Downloader
A simple tool to download videos from Twitter/X using tweet URLs
"""

import os
import sys
import re
import argparse
from pathlib import Path
import yt_dlp
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class TwitterDownloader:
    def __init__(self, output_dir="downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configure yt-dlp options
        self.ydl_opts = {
            'outtmpl': str(self.output_dir / '%(uploader)s_%(title)s_%(id)s.%(ext)s'),
            'format': 'best[ext=mp4]/best',  # Prefer mp4 format
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': True,
        }
    
    def is_valid_twitter_url(self, url):
        """Check if the URL is a valid Twitter/X URL"""
        twitter_patterns = [
            r'https?://(?:www\.)?twitter\.com/\w+/status/\d+',
            r'https?://(?:www\.)?x\.com/\w+/status/\d+',
            r'https?://t\.co/\w+',  # Shortened Twitter URLs
        ]
        
        return any(re.match(pattern, url) for pattern in twitter_patterns)
    
    def download_video(self, url):
        """Download video from Twitter URL"""
        if not self.is_valid_twitter_url(url):
            print(f"{Fore.RED}❌ Invalid Twitter URL format")
            print(f"{Fore.YELLOW}Please provide a valid Twitter/X URL like:")
            print(f"  https://twitter.com/username/status/1234567890")
            print(f"  https://x.com/username/status/1234567890")
            return False
        
        print(f"{Fore.CYAN}🐦 Processing Twitter URL: {url}")
        print(f"{Fore.YELLOW}📁 Output directory: {self.output_dir.absolute()}")
        
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract info first to check if video exists
                print(f"{Fore.BLUE}ℹ️  Extracting video information...")
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    print(f"{Fore.RED}❌ No video found at this URL")
                    return False
                
                # Check if there are video formats available
                formats = info.get('formats', [])
                video_formats = [f for f in formats if f.get('vcodec') != 'none']
                
                if not video_formats:
                    print(f"{Fore.RED}❌ No video content found in this tweet")
                    print(f"{Fore.YELLOW}💡 This tweet might contain only images or text")
                    return False
                
                print(f"{Fore.GREEN}✅ Video found: {info.get('title', 'Unknown title')}")
                print(f"{Fore.BLUE}👤 Author: {info.get('uploader', 'Unknown')}")
                print(f"{Fore.BLUE}⏱️  Duration: {info.get('duration', 'Unknown')} seconds")
                
                # Download the video
                print(f"{Fore.CYAN}⬇️  Starting download...")
                ydl.download([url])
                
                print(f"{Fore.GREEN}🎉 Download completed successfully!")
                return True
                
        except yt_dlp.DownloadError as e:
            print(f"{Fore.RED}❌ Download error: {str(e)}")
            if "Private" in str(e) or "protected" in str(e).lower():
                print(f"{Fore.YELLOW}💡 This tweet might be from a private account")
            elif "not found" in str(e).lower():
                print(f"{Fore.YELLOW}💡 Tweet not found - it might have been deleted")
            return False
        except Exception as e:
            print(f"{Fore.RED}❌ Unexpected error: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(
        description="Download videos from Twitter/X tweets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python twitter_downloader.py https://twitter.com/username/status/1234567890
  python twitter_downloader.py https://x.com/username/status/1234567890 -o my_videos
        """
    )
    
    parser.add_argument(
        'url',
        help='Twitter/X tweet URL containing the video'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='downloads',
        help='Output directory for downloaded videos (default: downloads)'
    )
    
    args = parser.parse_args()
    
    print(f"{Fore.MAGENTA}🚀 Twitter Video Downloader")
    print(f"{Fore.MAGENTA}{'=' * 30}")
    
    downloader = TwitterDownloader(args.output)
    success = downloader.download_video(args.url)
    
    if success:
        print(f"\n{Fore.GREEN}✨ All done! Check the '{args.output}' folder for your video.")
    else:
        print(f"\n{Fore.RED}💥 Download failed. Please check the URL and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
