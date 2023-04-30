import os
import hashlib
import json
from PIL import Image
import clip
import torch

model_name = "ViT-L/14"


def clip_json_generator(input_directory, output_directory):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load(model_name, device=device)

    def get_file_hash(file):
        hasher = hashlib.sha256()
        with open(file, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def get_clip_vector(image_path):
        try:
            image = Image.open(image_path)
            image_input = preprocess(image).unsqueeze(0).to(device)
            with torch.no_grad():
                features = model.encode_image(image_input)
            normalized_features = features / features.norm(dim=-1, keepdim=True)
            clip_vector = normalized_features.cpu().numpy().tolist()
            return clip_vector
        except FileNotFoundError:
            print(f"Image file not found at {image_path}. Skipping...")
            return None

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    image_data = []

    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.lower().endswith(('.gif','.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.pgm', '.tif', '.tiff', '.webp')):
                image_file_path = os.path.join(root, file)

                # Calculate file hash
                file_hash = get_file_hash(image_file_path)

                # Generate CLIP vector
                clip_vector = get_clip_vector(image_file_path)

                # Add the data to the list (if the CLIP vector is not None)
                if clip_vector is not None:
                    image_data.append({
                        'filename': os.path.basename(image_file_path),
                        'file_hash': file_hash,
                        'clip_model': model_name,
                        'clip_vector': clip_vector
                    })
                else:
                    print(f"Skipping image {image_file_path} due to missing file.")

    # Write the image_data list to a single JSON file
    output_json_file = os.path.join(output_directory, "clip_vectors.json")
    with open(output_json_file, 'w') as f:
        json.dump(image_data, f, indent=4)


if __name__ == "__main__":
    input_directory = './input/Image-scraper-pixel-art-allimages'
    output_directory = './output/clip_json'
    clip_json_generator(input_directory, output_directory)