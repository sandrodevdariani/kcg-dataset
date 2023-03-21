# kcg-dataset

There are two scripts in this repository:

1 - `image_sorter.py` sorts the extracted AVA dataset images and arrange them in the directories. 

2 - `ava_json_generator.py` converts the AVA from the original txt format to JSON format. It will also read the images from the sorted image directories and add their correspoding JSON files in that directories.

3 - `convert_ava_txt.py` converts the AVA from the original txt format to JSON format. It will also read the images and stores their file name and SHA256 hash in the JSON file.

4 - `zip_generator.py` generates zip files from the extracted images in the AVA dataset. The zip files will also contain the JSON file generated for the respective images.
