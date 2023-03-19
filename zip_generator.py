import pandas as pd
import os
import hashlib
import zipfile
import json


# directory for the zip files
ZIP_DIR = 'zip_files'
# directory for the images
IMAGE_DIR = 'images-extracted'
# indent for the json file
INDENT = 4

# Read in the data
df = pd.read_csv('AVA.txt', sep=' ',header=None)

# list of column names
COL_NAMES = ['Index', 'ImageId', '1', '2', '3', '4', '5', '6', '7','8','9','10','SemanticTag_1','SemanticTag_2','ChallengeId']

# set the column names
df.columns = COL_NAMES


# add an empty column for the image hash
df['FileHash'] = ''
# add an empty column for the image file name
df['FileName'] = ''
# add ScoreCount column
df['ScoreCount'] = df.loc[:, '1':'10'].sum(axis=1)
# add a dictionary column for the for image ratings
df['ScoreDictionary'] = df.loc[:, '1':'10'].to_dict(orient='records')
# drop the columns for the image ratings
df.drop(df.loc[:, '1':'10'], axis=1, inplace=True)
# drop the columns for the semantic tags and challenge id
df.drop(df.loc[:, 'SemanticTag_1':'ChallengeId'], axis=1, inplace=True)


# iterate through the list of images in the images-extracted folder
files = []
indexes = []
for filename in os.listdir(IMAGE_DIR):
    # if the file is not a jpg file, skip it
    if not filename.lower().endswith('.jpg') or filename.lower().endswith('.png'):
        continue
    # add the file name to the list of files
    files.append(filename)
    # add the index to the list of indexes
    indexes.append(int(filename.split('.')[0]))

# sort the list of indexes
indexes = sorted(indexes)
# sort the list of files
files = sorted(files, key=lambda x: int(x.split('.')[0]))

# count the number of rows corresponding to the number of images
df_images = df.loc[df.ImageId.isin(indexes)]
print("Number of matching rows: ", df_images.shape[0])

# sort the dataframe by ImageId
df_images = df_images.sort_values(by='ImageId')
# set the index values to the ImageId
df_images.set_index('ImageId', inplace=True, drop=False)
df.set_index('ImageId', inplace=True, drop=False)

zip_file_name = '0'
total_bytes = 0
start_index = df_images.index[0]


# create directory for the zip files
if not os.path.exists(ZIP_DIR):
    os.mkdir(ZIP_DIR)

# function to generate the zip files
def generate_zip_file(output_file_name,dataframe,next_index):
    # save the JSON file
    dataframe.to_json(f'{output_file_name}.json', orient='records', indent=INDENT)
    # create a zip file that contains the images and the JSON file
    path = os.path.join(ZIP_DIR, output_file_name)
    with zipfile.ZipFile(f'{path}.zip', 'w') as zip_file:
        # add the JSON file to the zip file
        zip_file.write(f'{output_file_name}.json')
        # iterate through the ImageId column
        for image_id in dataframe.index:
            if image_id >= next_index:
                break
            # read in the image
            with open(os.path.join(IMAGE_DIR, dataframe.at[image_id, 'FileName']), 'rb') as f:
                img = f.read()
            # add the image to the zip file
            zip_file.writestr(f'{dataframe.at[image_id, "FileName"]}',img)
        # remove the JSON file
        os.remove(f'{output_file_name}.json')

# iterate through the list of files
for file in files:
    # read in the image
    path = os.path.join(IMAGE_DIR, file)
    with open(path, 'rb') as f:
        img = f.read()
    # find the total number of bytes in the image
    size = len(img)
    # add the number of bytes to the total
    total_bytes += size
    # hash the image
    hash = hashlib.sha256(img).hexdigest()
    # get the index of the image
    index = int(file.split('.')[0])
    # set the image hash in the dataframe
    df_images.at[index, 'FileHash'] = hash
    # set the image file name in the dataframe
    df_images.at[index, 'FileName'] = file
    # check if the total number of bytes is greater than or equal to 500 MB
    if total_bytes >= 500000000:
        # save JSON file that has the image hashes and file names up to the current index
        temp = df_images.loc[(df_images.index >= start_index) & (df_images.index <= index)]
        # generate the zip file
        generate_zip_file(f'dataset-ava-{zip_file_name.zfill(3)}',temp,index+1)
        # increment the zip file name
        zip_file_name = str(int(zip_file_name) + 1)
        # reset the total number of bytes
        total_bytes = 0
        # set the start index
        start_index = index + 1

# check if there are any images left
if total_bytes > 0:
    # save the JSON file for the last zip file
    temp = df_images.loc[(df_images.index >= start_index) & (df_images.index <= index)]
    generate_zip_file(f'dataset-ava-{zip_file_name.zfill(3)}',temp,index+1)

# save JSON file
df_images.to_json('AVA.json', orient='records', indent=1)

# find the rows that were not found in the images-extracted folder
df = df.loc[~df.ImageId.isin(df_images.ImageId)]

# save the images that were not found in errors.txt
with open('errors.txt', 'w') as f:
    # write Index and ImageId to the file with column names
    f.write(df.loc[:, ['Index', 'ImageId']].to_string(header=True, index=False))