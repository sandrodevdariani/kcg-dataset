import os
import zipfile
import hashlib
import json
from PIL import Image
import clip
import torch
import argparse
from tqdm import tqdm
import io
import time
import argparse



model_name = "ViT-L/14"
batch_size = 16


def open_zip_to_ram(zip_path):
    """
    Open a zip file to RAM.

    :param zip_path: Path of the zip file
    :return: Dictionary containing file names as keys and file contents as values
    """
    file_data = {}

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                with zip_ref.open(file_info) as file:
                    file_data[file_info.filename] = file.read()
        print(f"Zip file '{zip_path}' has been loaded into RAM.")
    except Exception as e:
        print(f"Error: {e}")

    return file_data


def clip_json_generator(input_directory, output_directory, batch_size):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load(model_name, device=device)

    def process_images(image_data_list):
        try:
            images = [Image.open(io.BytesIO(image_data)).convert("RGB") for image_data in image_data_list]
            image_inputs = torch.stack([preprocess(image) for image in images]).to(device)
            with torch.no_grad():
                image_features = model.encode_image(image_inputs)
            image_hashes = [hashlib.sha256(image_data).hexdigest() for image_data in image_data_list]
            return [{'hash': h, 'vector': v.cpu().numpy().tolist()} for h, v in zip(image_hashes, image_features)]
        except Exception as e:
            print(f"Error processing image data: {e}")
            return [None] * len(image_data_list)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    zip_files = [os.path.join(root, file) for root, _, files in os.walk(input_directory) for file in files if file.endswith('.zip')]
    total_zip_files = len(zip_files)
    print(f"Processing {total_zip_files} zip files...")

    for file in tqdm(zip_files, desc="Processing zip files"):
        zip_file_path = os.path.join(input_directory, file)
        file_data = open_zip_to_ram(zip_file_path)


        image_data = []
        total_images = len(file_data)
        processed_images = 0
        start_time = time.time()

        batch_data = []
        for file_name, binary_data in tqdm(file_data.items(), desc="Processing images", total=total_images):
            if file_name.lower().endswith(('.gif','.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.pgm', '.tif', '.tiff', '.webp')):
                batch_data.append(binary_data)

                if len(batch_data) == batch_size:
                    clip_data_list = process_images(batch_data)
                    for clip_data, binary_data in zip(clip_data_list, batch_data):
                        if clip_data:
                            image_data.append({
                                'zipfile': os.path.basename(zip_file_path),
                                'filename': file_name,
                                'file_hash': clip_data['hash'],
                                'clip_model': model_name,
                                'clip_vector': clip_data['vector']
                            })
                    processed_images += len(batch_data)
                    batch_data = []

        if batch_data:
            clip_data_list = process_images(batch_data)
            for clip_data, binary_data in zip(clip_data_list, batch_data):
                if clip_data:
                    image_data.append({
                        'zipfile': os.path.basename(zip_file_path),
                        'filename': file_name,
                        'file_hash': clip_data['hash'],
                        'clip_model': model_name,
                        'clip_vector': clip_data['vector']
                    })
            processed_images += len(batch_data)




        end_time = time.time()
        total_time = end_time - start_time
        mb_s = sum(len(binary_data) for binary_data in file_data.values()) / (total_time * 1024 * 1024)
        print(f"Processed {processed_images} images in {total_time:.2f} seconds. ({mb_s:.2f} MB/s)")

        output_json_file = os.path.join(output_directory, f"{os.path.splitext(os.path.basename(file))[0]}_clip_vectors.json")
        with open(output_json_file, 'w') as f:
            json.dump(image_data, f, indent=4)

    print("Finish process")

 




parser = argparse.ArgumentParser(description='Generate CLIP vectors for images in a directory of zip files.')
parser.add_argument('input_directory', type=str, help='Path to directory containing zip files')
parser.add_argument('output_directory', type=str, help='Path to directory where output JSON files will be saved')
parser.add_argument('batch_size', type=int)

args = parser.parse_args()
  
clip_json_generator(args.input_directory, args.output_directory, args.batch_size)


