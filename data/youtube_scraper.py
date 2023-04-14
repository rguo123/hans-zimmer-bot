from bs4 import BeautifulSoup
from moviepy.editor import *
from pytube import YouTube
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import sys
import time

from storage import upload_file_to_bucket

DEFAULT_CHROME_PATH = "/usr/lib/chromium-browser/chromedriver"


def download_youtube_mp3(url):
    """
    Downloads a YouTube video as an MP3 file.
    
    Args:
    url: the YouTube video URL
    
    Returns:
    None
    """
    # Download the YouTube video
    yt = YouTube(url)
    video = yt.streams.filter(only_audio=True).first()
    output_path = video.download()

    # Convert the video to an MP3 file
    mp4_file = AudioFileClip(output_path)
    mp3_file = os.path.splitext(output_path)[0] + ".mp3"
    mp4_file.write_audiofile(mp3_file)

    # Delete the original video file
    os.remove(output_path)

    print("Download complete. MP3 file saved at: ", mp3_file)



def build_youtube_query_url(category):
    """
    Build a youtube search query based on category keyword.
    All videos from URL will be filtered to be between 4-20 minutes long.
    """

    return f"https://www.youtube.com/results?search_query={category}+instrumental+song&sp=EgIYAw%253D%253D"


def scrape_youtube_urls_from_query_page(youtube_query_url, scroll_pause_time=3, scroll_amount = 5000, chrome_path = None):
    # Launch the Chrome browser using Selenium WebDriver

    if chrome_path is None:
        chrome_path = DEFAULT_CHROME_PATH
    
    sys.path.insert(0, chrome_path)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome('chromedriver', options=chrome_options)
    # Load the YouTube url
    driver.get(youtube_query_url)

    # Wait for the page to load completely
    driver.implicitly_wait(10)
    
    # scroll
    driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
    # Wait to load page
    time.sleep(scroll_pause_time)
    
    # Find all the links on the page
    links = driver.find_elements(By.TAG_NAME, "a")

    youtube_links = set()

    # Print the href attribute of each link
    for link in links:
        href = link.get_attribute("href")
        if href and "watch?v=" in href:
            # remove time stamps
            href = href.split("&t=")[0]
            youtube_links.add(href)

    # Close the browser
    driver.quit()
    return youtube_links


query_url = build_youtube_query_url("peaceful")
print(query_url)
music_urls = scrape_youtube_urls_from_query_page(query_url)

print(music_urls)