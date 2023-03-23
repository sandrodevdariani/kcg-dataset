import os
import shutil
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

IMAGE_DIR = 'images-extracted'
OUTPUT_DIR = 'images-sorted'
ACTION = 'copy' # 'copy' or 'move' the files
ALLOWED_EXTENSIONS = ['jpg', 'png']


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
    # open the file
    try:
        img = Image.open(path)
        img.verify()
    except:
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
    # read in the file
    with open(path, 'rb') as f:
        img = f.read()

    # get the size of the file
    size = len(img)
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
