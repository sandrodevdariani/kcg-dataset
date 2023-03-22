import os
import zipfile
import shutil

IMAGES_DIR = 'images-sorted' # directory that contains the images
OUTPUT_DIR = 'images-zipped' # directory that will contain the zipped images

#SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)) # use this if the dataset is in the same directory as the script
SCRIPT_DIR = os.getcwd() # use this if the dataset is in the current working directory

IMAGES_DIR = os.path.join(SCRIPT_DIR, IMAGES_DIR)
OUTPUT_DIR = os.path.join(SCRIPT_DIR, OUTPUT_DIR)
print(f'Images directory: {IMAGES_DIR}')
print(f'Output directory: {OUTPUT_DIR}')

# if the output directory does not exist, create it
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
else:
    # remove the directory
    shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

# create a list of all the files in the directory
directories = os.listdir(IMAGES_DIR)
# sort directories
directories = sorted(directories)
print(f'Total number of directories: {len(directories)}')

for directory in directories:
    print(f'Processing directory: {directory}')
    # construct the path to the output file
    path = os.path.join(OUTPUT_DIR, directory)
    with zipfile.ZipFile(f'{path}.zip', 'w') as zip_file:
        # iterate through the files in the directory
        files = os.listdir(os.path.join(IMAGES_DIR, directory))
        total_files = len(files)
        for index, file in enumerate(files):
            print(f'Processing file {index+1}/{total_files}', end='\r')
            # read in the image
            path = os.path.join(IMAGES_DIR, directory, file)
            with open(os.path.join(IMAGES_DIR, directory, file), 'rb') as f:
                img = f.read()
            # add the image to the zip file
            zip_file.writestr(f'{file}',img)


