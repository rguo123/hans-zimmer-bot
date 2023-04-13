from bs4 import BeautifulSoup
import os
import json
import urllib.request, urllib.error, urllib.parse

import numpy as np
from PIL import Image
import torch
from torchvision import transforms
from torch.utils.data import Dataset
import itertools
import glob

# NOTE: In order to introduce some variety, this dataset scraper is designed 
# to have categories of multiple synonyms as one label class (ex: [sad, dark, somber, sullen]
# all represent the same category of images/music)

# TODO: depending on how many files we need, we may need to add support for extracting
# pages of a bing search. The current implementation only takes the images from page 1

class ImageDataSet(Dataset):
    def __init__(self, data_dir, transforms, label_categories=None):
        self.data_dir = data_dir
        self.transforms = transforms
        self.label_categories = label_categories
        self.labels = [i for i in range(len(self.label_categories))]

        # if the dataset has not been downloaded, initiate the scrape
        # NOTE: Repeat runs may have different images
        if not os.path.exists(self.data_dir):
            print("Making data directory...")
            os.mkdir(self.data_dir)
            self.scrape_images()
        
        image_files, labels = self.get_image_filenames_with_labels(self.data_dir)
        self.image_files = np.array(image_files)
        self.labels = np.array(labels)
        self.num_images = len(self.image_files)

    def __len__(self):
        return self.num_images

    def __getitem__(self, idx):
        try:
            image = Image.open(self.image_files[idx]).convert('RGB')
            label = self.labels[idx]
            image = self.transforms(image)
            return image, label
        except:
            return None
        
    def get_image_filenames_with_labels(self, images_dir):
        image_files = []
        labels = []
        supported_file_types = ["/*.png", "/*.jpg", "/*.jpeg"]
        
        files = os.listdir(images_dir)
        for name in files:
            if name == ".DS_Store":
                continue
            image_class_dir = os.path.join(images_dir, name)
            image_class_files = list(itertools.chain.from_iterable(
                [glob.glob(image_class_dir + file_type) for file_type in supported_file_types]))
            image_files += image_class_files
            labels += [int(name)] * len(image_class_files)
        return image_files, labels

    def scrape_images(self):
        print("Scraping images...")
        for i, category in enumerate(self.label_categories):
            seen_images = set()
            category_count = 0
            for label in category:
                print("===> Extracting '" + label + "' images...")

                # handle search queries of multiple words 
                label = label.split()
                label = '+'.join(label)

                # set up the bing query using the label name as the search query
                search_url = "http://www.bing.com/images/search?q=" + label + "&FORM=HDRSC2"
                header = {'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}
                soup = BeautifulSoup(urllib.request.urlopen(urllib.request.Request(search_url,headers=header)), 'html.parser')

                # extract the image files from the bing search results
                for a_tag in soup.find_all("a",{"class":"iusc"}): # potentially want to manually limit how many images per class
                    try:
                        m = json.loads(a_tag["m"])
                        turl = m["turl"]
                        murl = m["murl"]
                    except:
                        continue

                    image_name = urllib.parse.urlsplit(murl).path.split("/")[-1]
                    
                    # remove instances of duplicate images over two different searches within the same category
                    if image_name in seen_images:
                        continue
                    seen_images.add(image_name)

                    # create a dictionary for each label
                    label_dir = self.data_dir + str(i)
                    if not os.path.exists(label_dir):
                        os.mkdir(label_dir)

                    # attempt to extract and download the file
                    try:
                        img = urllib.request.urlopen(turl).read()
                        
                        # NOTE: line 112 sometimes fails to find an extension but this is handled in 
                        # get_image_filenames_with_labels by giving valid file extensions
                        ext = os.path.splitext(image_name)[1] 

                        # rename the image to be more generic for better data organization
                        name = label_dir + '/' + str(i) + '_' + str(category_count) + ext
                        file = open(name, 'wb')
                        file.write(img)
                        file.close()

                        category_count += 1
                    except Exception as e:
                        # if the image fails to download, skip it
                        print("Image: ", image_name, "failed to download!")
                        continue


def main():
    data_transforms = transforms.Compose([transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    
    labels = [['dark', 'somber', 'gloomy', 'shadowy', 'dark art', 'dark landscape', 'gloomy art', 'rain'], 
              ['bright', 'sparkling', 'dazzling', 'bright art', 'sunshine'],
              ['techno party', 'night club'],
              ['calm', 'peaceful']]
    
    image_data = ImageDataSet("./data/", data_transforms, label_categories=labels)
    print(len(image_data))
    print(image_data[0])


if __name__ == '__main__':
    main()