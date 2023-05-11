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

def process_and_append_images(batch_data, file_names, model, preprocess, device, zip_file_path, tag):
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
                'clip_vector': clip_vector,
                'tag': tag  # Add the 'tag' field with the provided tag
            })

    conversion_errors = [(idx, file_names[idx], error) for idx, error in conversion_errors]

    return image_data, len(batch_data), conversion_errors


def clip_json_generator(input_directory, output_directory, batch_size):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load(model_name, device=device)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    zip_files = [file for file in os.listdir(input_directory) if file.endswith('.zip')]
    total_zip_files = len(zip_files)
    print(f"Processing {total_zip_files} zip files...")

    for file in tqdm(zip_files, desc='processing zip files'):
        zip_file_path = os.path.join(input_directory, file)
        file_data = open_zip_to_ram(zip_file_path)

    for folder_name, folder_data in file_data.items():
        folder_images = open_zip_to_ram(io.BytesIO(folder_data))

        for image_name, image_data in folder_images.items():
            image_data = []
            tag = folder_name  # Set the folder name as the tag

            for image_name, image_data in folder_data.items():
                try:
                    image = Image.open(io.BytesIO(image_data)).convert("RGB")
                    hash_value = hashlib.sha256(image_data).hexdigest()
                    image_input = preprocess(image).unsqueeze(0).to(device)
                    with torch.no_grad():
                        image_feature = model.encode_image(image_input)
                    clip_vector = image_feature.cpu().numpy().tolist()

                    image_data.append({
                        'file_archive': os.path.basename(zip_file_path),
                        'file_name': image_name,
                        'file_path': os.path.join(tag, folder_name),
                        'file_hash': hash_value,
                        'clip_model': model_name,
                        'clip_vector': clip_vector,
                        'tag': tag  # Add the 'tag' field with the folder name
                    })
                except Exception as e:
                    print(f"Error processing image '{image_name}': {e}")

            output_json_file = os.path.join(output_directory, f"{os.path.splitext(os.path.basename(file))[0]}.json")
            with open(output_json_file, 'w') as f:
                json.dump(image_data, f, indent=4)

    print("Finish process")


parser = argparse.ArgumentParser(description='Generate CLIP vectors for images in a directory of zip files.')
parser.add_argument('input_directory', type=str, help='Path to directory containing zip files')
parser.add_argument('output_directory', type=str, help='Path to directory where output JSON files will be saved')
parser.add_argument('batch_size', type=int)

args = parser.parse_args()

clip_json_generator(args.input_directory, args.output_directory, args.batch_size)
