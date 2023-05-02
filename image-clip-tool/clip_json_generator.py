import os
import zipfile
import hashlib
import json
from PIL import Image
import clip
import torch
import argparse
from tqdm import tqdm


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


def clip_json_generator(input_directory, output_directory):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load(model_name, device=device)

    def process_image(image_data):
        try:
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            image_input = preprocess(image).unsqueeze(0).to(device)
            with torch.no_grad():
                image_features = model.encode_image(image_input)
            image_hash = hashlib.sha256(image_data).hexdigest()
            return {
                'hash': image_hash,
                'vector': image_features.cpu().numpy().tolist()
            }
        except Exception as e:
            print(f"Error processing image data: {e}")
            return None

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    zip_files = [os.path.join(root, file) for root, _, files in os.walk(input_directory) for file in files if file.endswith('.zip')]
    total_zip_files = len(zip_files)
    print(f"Processing {total_zip_files} zip files...")

    for file in tqdm(zip_files, desc="Processing zip files"):
        zip_file_path = os.path.join(input_directory, file)
        file_data = open_zip_to_ram(zip_file_path)

        image_data = []
        for file_name, binary_data in file_data.items():
            if file_name.lower().endswith(('.gif','.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.pgm', '.tif', '.tiff', '.webp')):
                clip_data = process_image(binary_data)
                if clip_data:
                    image_data.append({
                        'zipfile': os.path.basename(zip_file_path),
                        'filename': file_name,
                        'file_hash': clip_data['hash'],
                        'clip_model': model_name,
                        'clip_vector': clip_data['vector']
                    })

        output_json_file = os.path.join(output_directory, f"{os.path.splitext(file)[0]}_clip_vectors.json")
        with open(output_json_file, 'w') as f:
            json.dump(image_data, f, indent=4)

    print("Finish process")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate CLIP vectors for images in a directory.")
    parser.add_argument("input_directory", help="Path to the input directory containing the images.")
    parser.add_argument("output_directory", help="Path to the output directory where the JSON file will be saved.")
    args = parser.parse_args()

    clip_json_generator(args.input_directory, args.output_directory)
