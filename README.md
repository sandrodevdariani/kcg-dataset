# kcg-dataset
There are two scripts in this repository:
1 - `convert_ava_txt.py` converts the AVA from the original txt format to JSON format. It will also read the images and stores their file name and SHA256 hash in the JSON file.

2 - `zip_generator.py` generates zip files from the extracted images in the AVA dataset. The zip files will also contain the JSON file generated for the respective images.
