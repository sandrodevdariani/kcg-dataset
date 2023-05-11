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
import threading


model_name = "ViT-L/14"

def open_zip_to_ram(zip_path):
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

def convert_images(image_data_list):
    converted_images = []
    errors = []

    for idx, image_data in enumerate(image_data_list):
        try:
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            converted_images.append(image)
        except Exception as e:
            errors.append((idx, str(e)))

    return converted_images, errors

def compute_sha256(image_data_list):
    return [hashlib.sha256(image_data).hexdigest() for image_data in image_data_list]

def process_images(images, model, preprocess, device):
    image_inputs = torch.stack([preprocess(image) for image in images]).to(device)
    with torch.no_grad():
        image_features = model.encode_image(image_inputs)
    return image_features.cpu().numpy().tolist()

def process_and_append_images(batch_data, file_names, model, preprocess, device, zip_file_path):
    image_data = []
    converted_images, conversion_errors = convert_images(batch_data)
    image_hashes = compute_sha256(batch_data)
    clip_vectors = process_images(converted_images, model, preprocess, device)

    for idx, (file_name, hash_value, clip_vector) in enumerate(zip(file_names, image_hashes, clip_vectors)):
        if idx not in [error[0] for error in conversion_errors]:
            file_path = os.path.join(zip_file_path, file_name)
            dir_path = os.path.dirname(file_path)
            image_data.append({
                'file_archive': os.path.basename(zip_file_path),
                'file_name': file_name,
                'file_path': dir_path,
                'file_hash': hash_value,
                'clip_model': model_name,
                'clip_vector': clip_vector
            })

    conversion_errors = [(idx, file_names[idx], error) for idx, error in conversion_errors]

    return image_data, len(batch_data), conversion_errors


def load_zip_to_ram_threaded(zip_file_path, file_data_dict):
    file_data_dict[zip_file_path] = open_zip_to_ram(zip_file_path)

def clip_json_generator(input_directory, output_directory, batch_size):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load(model_name, device=device)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    zip_files = [os.path.join(root, file) for root, _, files in os.walk(input_directory) for file in files if file.endswith('.zip')]
    total_zip_files = len(zip_files)
    print(f"Processing {total_zip_files} zip files...")

    threads = {}
    file_data_dict = {}

    for i, file in enumerate(tqdm(zip_files, desc="Processing zip files")):
        unzip_start_time = time.time()

        zip_file_path = os.path.join(input_directory, file)

        if i > 0:
            # Wait for the previous zip file to be loaded into memory
            threads[previous_zip_file_path].join()
            file_data = file_data_dict[previous_zip_file_path]

            unzip_end_time = time.time()
            unzip_time = unzip_end_time - unzip_start_time

            # calculate zip file size in MB
            zip_file_size = os.path.getsize(previous_zip_file_path) / (1024 * 1024)

            image_data = []
            total_images = len(file_data)
            processed_images = 0
            start_time = time.time()

            batch_data = []
            batch_file_names = []
            errors = []

            def process_batch(batch_data, batch_file_names):
                nonlocal processed_images
                batch_image_data, processed, conversion_errors = process_and_append_images(batch_data, batch_file_names, model, preprocess, device, zip_file_path)
                image_data.extend(batch_image_data)
                errors.extend(conversion_errors)
                processed_images += processed
                batch_data.clear()
                batch_file_names.clear()

            for file_name, binary_data in tqdm(file_data.items(), desc="Processing images", total=total_images):
                if file_name.lower().endswith(('.gif','.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.tif', '.tiff', '.webp')):
                    batch_data.append(binary_data)
                    batch_file_names.append(file_name)

                    if len(batch_data) == batch_size:
                        process_batch(batch_data, batch_file_names)

            if batch_data:
                process_batch(batch_data, batch_file_names)

            end_time = time.time()
            total_time = end_time - start_time
            clip_time = total_time - unzip_time

            mb_s = sum(len(binary_data) for binary_data in file_data.values()) / (clip_time * 1024 * 1024)
            img_s = processed_images / clip_time

            total_mb = sum(len(binary_data) for binary_data in file_data.values()) / (1024 * 1024)
            total_gb = total_mb / 1024

            # calculate M/S
            ms = zip_file_size / unzip_time

            print(f"Reading/uncompressing zip files took {unzip_time:.2f} seconds.")
            print(f"Processed {processed_images} images in {clip_time:.2f} seconds. ({img_s:.2f} images/s, {mb_s:.2f} MB/s)")
            print(f"Total GB processed: {total_gb:.2f} GB")
            print(f"Zip file processed at {ms:.2f} MB/s")


            output_json_file = os.path.join(output_directory, f"{os.path.splitext(os.path.basename(file))[0]}.json")
            with open(output_json_file, 'w') as f:
                json.dump(image_data, f, indent=4)
            if errors:
                error_file = os.path.join(output_directory, f"{os.path.splitext(os.path.basename(file))[0]}_errors.txt")
                with open(error_file, 'w') as f:
                    for error in errors:
                        f.write(f"{error[1]}: {error[2]}\n")

        # Start loading the next zip file into memory
        thread = threading.Thread(target=load_zip_to_ram_threaded, args=(zip_file_path, file_data_dict))
        thread.start()
        threads[zip_file_path] = thread
        previous_zip_file_path = zip_file_path

    # Make sure the last zip file is loaded into memory
    threads[previous_zip_file_path].join()

    print("Finish process")



parser = argparse.ArgumentParser(description='Generate CLIP vectors for images in a directory of zip files.')
parser.add_argument('input_directory', type=str, help='Path to directory containing zip files')
parser.add_argument('output_directory', type=str, help='Path to directory where output JSON files will be saved')
parser.add_argument('batch_size', type=int)

args = parser.parse_args()

clip_json_generator(args.input_directory, args.output_directory, args.batch_size)
