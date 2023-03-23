import os
import shutil
import filetype
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

IMAGE_DIR = 'images-extracted'
OUTPUT_DIR = 'images-sorted'
ACTION = 'copy' # 'copy' or 'move' the files
ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png']


# SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)) # use the dataset is in the same directory as the script
SCRIPT_DIR = os.getcwd() # use this if dataset is in the current working directory

# get the full path of the image and output directory
OUTPUT_DIR = os.path.join(SCRIPT_DIR, OUTPUT_DIR)
IMAGE_DIR = os.path.join(SCRIPT_DIR, IMAGE_DIR)

# create output directory
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
else:
    # remove the directory
    shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

# create a list of all the files in the directory
files_all = os.listdir(IMAGE_DIR)
files_images = []

# iterate through the files
for file in files_all:
    # get the extension of the file
    ext = file.split('.')[-1]
    # check if the extension is allowed
    if ext not in ALLOWED_EXTENSIONS:
        print(f'Invalid extension: {file}')
        continue

    # get the full path of the file
    path = os.path.join(IMAGE_DIR, file)
    try:
        im = Image.open(path)
        # get image format
        format = im.format
        if format.lower() not in ALLOWED_EXTENSIONS:
            print(f'Invalid extension: {file}')
            continue
        im.verify()     
    except Exception as e:
        print(e)
        print(f'Invalid image: {file}')
        continue

    if not filetype.is_image(path):
        print(f'Invalid image: {file}')
        continue

    # check file size
    size = os.path.getsize(path)
    if size == 0:
        print(f'Invalid image: {file}')
        continue
    
    # add the file to the list
    files_images.append(file)

# sort the files by name
files = sorted(files_images, key=lambda x: int(x.split('.')[0]))

total_bytes = 0
start_index = 0
directory_index = 0
naming_convention = 'dataset-ava-'
total_images = len(files)
action = shutil.copy if ACTION == 'copy' else shutil.move
print(f'Total number of images: {total_images}')

# iterate through the files
for index,file in enumerate(files):
    # print the progress
    print(f"Processing {file} {index+1}/{total_images}", end='\r')
    path = os.path.join(IMAGE_DIR, file)
    # get the size of the file
    size = os.path.getsize(path)
    total_bytes += size

    # if the total size is greater than 500 MB
    if total_bytes > 500000000:
        dir_name = f'{naming_convention}{str(directory_index).zfill(3)}'
        # create a new directory
        if not os.path.exists(os.path.join(SCRIPT_DIR, OUTPUT_DIR, dir_name)):
            os.makedirs(os.path.join(SCRIPT_DIR, OUTPUT_DIR, dir_name))

        for i in range(start_index, index+1):
            src_path = os.path.join(SCRIPT_DIR, IMAGE_DIR, files[i])
            dst_path = os.path.join(SCRIPT_DIR, OUTPUT_DIR, dir_name, files[i])
            action(src_path, dst_path)

        # reset the total size
        total_bytes = 0
        # reset the start index
        start_index = index+1
        # increment the directory index
        directory_index += 1
            
# check if there are any files left
if total_bytes > 0:
    # create a new directory
    dir_name = f'{naming_convention}{str(directory_index).zfill(3)}'
    # create a new directory
    if not os.path.exists(os.path.join(SCRIPT_DIR, OUTPUT_DIR, dir_name)):
        os.makedirs(os.path.join(SCRIPT_DIR, OUTPUT_DIR, dir_name))

    for i in range(start_index, len(files)):
        src_path = os.path.join(SCRIPT_DIR, IMAGE_DIR, files[i])
        dst_path = os.path.join(SCRIPT_DIR, OUTPUT_DIR, dir_name, files[i])
        action(src_path, dst_path)
