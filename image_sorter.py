import os
import shutil

IMAGE_DIR = 'images-extracted'
OUTPUT_DIR = 'images-sorted'
ACTION = 'move' # 'copy' or 'move' the files
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

# create output directory
if not os.path.exists(OUTPUT_DIR):
    path = os.path.join(SCRIPT_DIR, OUTPUT_DIR)
    os.makedirs(path)

# create a list of all the files in the directory
files = os.listdir(IMAGE_DIR)

# remove the files that are not images
files = [file for file in files if file.endswith('.jpg') or file.endswith('.png')]

# sort the files by name
files = sorted(files, key=lambda x: int(x.split('.')[0]))

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
    print(f"Processing file {index+1}/{total_images}", end='\r')
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