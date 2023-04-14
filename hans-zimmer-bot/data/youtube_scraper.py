from bs4 import BeautifulSoup
from google.cloud import storage
from moviepy.editor import *
from pytube import YouTube
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import sys
import time



# TODO: more elegant way of setting this up
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../gcp_config.json"
client = storage.Client()

DEFAULT_CHROME_PATH = "/usr/lib/chromium-browser/chromedriver"


def upload_filename_to_bucket(source_filename, dest_filename, bucket_name, rename=None):
    """
    Given local source file, upload file to bucket and rename to specfied
    dest_filename. Use '/' to specify directories.
    """

    bucket = client.get_bucket(bucket_name)

    # Upload a file to the bucket
    blob = bucket.blob(dest_filename)

    blob.upload_from_filename(source_filename)


def download_youtube_mp3(url, filename, verbose=True):
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
    mp3_file = os.path.dirname(output_path) + "/" + filename
    mp4_file.write_audiofile(mp3_file)

    # Delete the original video file
    os.remove(output_path)

    if verbose:
        print("Download complete. MP3 file saved at: ", mp3_file)
    
    return mp3_file


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


def run_youtube_scrape_job(category, bucket_name, delete_local_mp3_file=True, limit=30):
    # TODO: execute in docker container on gcp compute instance
    # but this should work locally for now?

    query_url = build_youtube_query_url(category)
    music_urls = scrape_youtube_urls_from_query_page(query_url)

    print(f"Number of songs: {len(music_urls)}")

    idx = 0

    for url in music_urls:
    
        if idx >= limit:
            break
        
        filename = category + "_" + str(idx) + ".mp3"

        # download_youtube_mp3 will return full path
        try:
            mp3_file = download_youtube_mp3(url, filename)
            idx += 1
        except:
            # TODO: change to error logging
            print(f"Failed to download mp3... skipping for {url}")

        cloud_bucket_filename = category + "/" + filename
        upload_filename_to_bucket(mp3_file, cloud_bucket_filename, bucket_name)

        # cleanup
        if delete_local_mp3_file:
            os.remove(mp3_file)

    return music_urls



if __name__ == "__main__":
    run_youtube_scrape_job("peaceful", "music_dataset_4995")


# Test
#query_url = build_youtube_query_url("peaceful")
#print(query_url)
#music_urls = scrape_youtube_urls_from_query_page(query_url)

#print(music_urls)