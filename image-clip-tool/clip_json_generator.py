import os
import zipfile
import hashlib
import json
from PIL import Image
import requests
from io import BytesIO
import clip
import torch
import argparse
from tqdm import tqdm
from tqdm.auto import tqdm


model_name = "ViT-L/14"
batch_size = 16

def clip_json_generator(input_directory, output_directory):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load(model_name, device=device)

    def get_file_hash(file):
        hasher = hashlib.sha256()
        with open(file, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def process_batch(image_paths):
        images = []
        for image_path in image_paths:
            try:
                image = Image.open(image_path)
                images.append(preprocess(image))
            except FileNotFoundError:
                print(f"Image file not found at {image_path}. Skipping...")

        image_inputs = torch.stack(images).to(device)
        with torch.no_grad():
            features = model.encode_image(image_inputs)
        normalized_features = features / features.norm(dim=-1, keepdim=True)
        return normalized_features.cpu().numpy().tolist()

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    zip_files = [file for root, _, files in os.walk(input_directory) for file in files if file.endswith('.zip')]
    total_zip_files = len(zip_files)
    print("Start process")

    for file in tqdm(zip_files, desc="Processing zip files"):
        zip_file_path = os.path.join(input_directory, file)
        image_data = []

        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            image_members = [member for member in zip_ref.infolist() if member.filename.lower().endswith(('.gif','.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.pgm', '.tif', '.tiff', '.webp'))]

            for i in tqdm(range(0, len(image_members), batch_size), desc="Processing image batches"):
                batch_members = image_members[i:i + batch_size]

                # Extract images and save them
                extracted_image_paths = []
                for member in batch_members:
                    with zip_ref.open(member) as img_file:
                        img_data = img_file.read()
                        img = Image.open(BytesIO(img_data))
                        img.save(f'extracted_{os.path.basename(member.filename)}')
                        extracted_image_paths.append(f'extracted_{os.path.basename(member.filename)}')

                # Generate CLIP vectors for the batch
                clip_vectors = process_batch(extracted_image_paths)

                # Process image data
                for j, member in enumerate(batch_members):
                    file_hash = get_file_hash(extracted_image_paths[j])
                    image_data.append({
                        'zipfile': os.path.basename(zip_file_path),
                        'filename': os.path.basename(member.filename),
                        'file_hash': file_hash,
                        'clip_model': model_name,
                        'clip_vector': clip_vectors[j]
                    })

                    # Clean up the extracted image
                    os.remove(extracted_image_paths[j])

        # Write the image_data list to a separate JSON file for each zip file
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





