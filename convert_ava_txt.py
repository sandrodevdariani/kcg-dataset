import pandas as pd
import os
import hashlib
import json


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
for filename in os.listdir('images-extracted'):
    # if the file is not a jpg file, skip it
    if not filename.lower().endswith('.jpg') or filename.lower().endswith('.png'):
        continue
    # add the file name to the list of files
    files.append(filename)


# sort the list of files
files = sorted(files, key=lambda x: int(x.split('.')[0]))

# count the number of rows corresponding to the number of images
df_images = df.loc[df.ImageId.isin([int(file.split('.')[0]) for file in files])]
print("Number of matching rows: ", df_images.shape[0])

# sort the dataframe by ImageId
df_images = df_images.sort_values(by='ImageId')

# iterate through the list of files
for file in files:
    # read in the image
    img = open('images-extracted/' + file, 'rb').read()
    # hash the image
    hash = hashlib.sha256(img).hexdigest()
    # get the index of the image
    index = int(file.split('.')[0])
    # set the image hash in the dataframe
    df_images.loc[df_images.ImageId == index, 'FileHash'] = hash
    # set the image file name in the dataframe
    df_images.loc[df.ImageId == index, 'FileName'] = file



# save JSON file with first 1000 rows
df_images.to_json('AVA.json', orient='records', indent=4)

# find the difference between df and df_images
df_diff = df[~df.ImageId.isin(df_images.ImageId)]

# save the images that were not found in errors.txt
with open('errors.txt', 'w') as f:
    # write Index and ImageId to the file with column names
    f.write(df_diff.loc[:, ['Index', 'ImageId']].to_string(header=True, index=False))