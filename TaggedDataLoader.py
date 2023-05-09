import os
import json

class TaggedDataLoader:
    def __init__(self, data_dir, tag=None):
        self.data_dir = data_dir
        self.tag = tag

    def load_data(self):
        file_data = []
        for root, dirs, files in os.walk(self.data_dir):
            if self.tag and self.tag not in dirs:
                continue
            for file in files:
                if file.endswith('.jpg') or file.endswith('.png') or file.endswith('.gif'):
                    file_path = os.path.join(root, file)
                    if not self.tag or self.tag in file_path:
                        file_data.append({'file_path': file_path})
        return file_data
    
'''
    loader = TaggedDataLoader('/path/to/data/dir', 'pos-pixel-art')
    file_data = loader.load_data()

    # Example usage: Print the number of tagged image files found
    print(f"Found {len(file_data)} tagged image files.")
    '''


class GeneralDataLoader:
    def __init__(self, data_dir):
        self.data_dir = data_dir 



import json
import torch
from torch.utils.data import Dataset

class ImageDataset(Dataset):
    def __init__(self, json_file):
        with open(json_file, "r") as f:
            data = json.load(f)
        self.images = []
        for item in data:
            image_path = item["path/filename"]
            image_hash = item["file_hash"]
            clip_vector = torch.tensor(item["clip_vector"])
            self.images.append((image_path, image_hash, clip_vector))

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):
        image_path, image_hash, clip_vector = self.images[index]
        return image_path, image_hash, clip_vector


