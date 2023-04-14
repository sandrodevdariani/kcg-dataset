# Generating CLIP vectors for images in zip files

This script generates CLIP vectors for all images in zip files found in a given input directory. The CLIP vectors are calculated using the OpenAI CLIP model, and are written to separate JSON files for each zip file.

Requirements

To run this script, you need to have the following packages installed:

* Pillow
* Torch
* OpenAI-CLIP
You can install these packages using the following command:

!pip install pillow torch openai-clip

## Usage

To run the script, execute the following command:


!python clip_json_generator.py /path/to/input/directory /path/to/output/directory



Here, /path/to/input/directory should be replaced with the path to the directory containing the zip files with images, and /path/to/output/directory should be replaced with the path to the directory where the JSON files containing the CLIP vectors will be written.