import os
import torch
from PIL import Image
import open_clip
import pandas as pd

MODEL_NAME = 'ViT-L-14'
PRETRAINED = 'laion2b_s32b_b82k'

# set the directory paths
IMAGES_DIR = 'images-sorted' # directory that contains the sorted images
# SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)) # use the dataset is in the same directory as the script
SCRIPT_DIR = os.getcwd() # use this if dataset is in the current working directory
IMAGE_DIR = os.path.join(SCRIPT_DIR, IMAGES_DIR)

INDENT = 1 # indent level for the JSON file

# read AVA.json into a dataframe
df = pd.read_json('AVA.json', orient='records')
df['ClipModel'] = MODEL_NAME
df['ClipPretrained'] = PRETRAINED
df['ClipVectorSize'] = None
df['ClipVector'] = None
# set the index to the ImageId
df.set_index('ImageId', inplace=True, drop=False)
# sort the dataframe by the index
df.sort_index(inplace=True)


model, _, preprocess = open_clip.create_model_and_transforms(model_name=MODEL_NAME, pretrained=PRETRAINED)
tokenizer = open_clip.get_tokenizer(MODEL_NAME)

if torch.cuda.is_available():
    device = 'cuda'
else:
    device = 'cpu'
    print('CUDA is not available. Using CPU instead.')

model = model.to(device)

# function to generate the embeddings
def generate_embeddings(file_name,dir_name):
    with torch.no_grad():
        # read in the image
        img = Image.open(os.path.join(IMAGE_DIR, dir_name, file_name))
        image = preprocess(img).unsqueeze(0).to(device)
        emb = model.encode_image(image).cpu().detach().numpy()
    return emb

# iterate through the directories
directories = os.listdir(IMAGES_DIR)
directories = sorted(directories)
print(f'Total number of directories: {len(directories)}')

for directory in directories:
    print(f'Processing directory: {directory}')
    # iterate through the files in the directory
    files = os.listdir(os.path.join(IMAGES_DIR, directory))
    total_files = len(files)

    # create an empty dataframe
    df_new = pd.DataFrame(columns=df.columns)

    for index, file in enumerate(files):
        # print the progress
        print(f"Processing {file} {index+1}/{total_files}", end='\r')
        # check if the file is an image
        if file.split('.')[-1] not in ['jpg', 'jpeg', 'png']:
            continue

        # try to open the image
        try:
            # check if the image is corrupt
            Image.open(os.path.join(IMAGE_DIR, directory, file)).verify()
        except:
            # write the error to a file
            with open('errors-clip.txt', 'a') as f:
                f.write(f'{file} {directory}')
        
        # generate the embeddings
        emb = generate_embeddings(file,directory)

        # get the image id
        image_id = int(file.split('.')[0])

        # insert clip vector into the dataframe
        df.at[image_id, 'ClipVectorSize'] = emb.shape
        df.at[image_id, 'ClipVector'] = emb.tolist()

        # append the row to the new dataframe
        df_new = pd.concat([df_new, df.loc[[image_id]]])

    # save the dataframe to a json file
    path = os.path.join(IMAGES_DIR, directory, directory)
    df_new.to_json(f'{path}-clip.json', orient='records', indent=INDENT)

# save the dataframe to a json file
df.to_json('AVA-clip.json', orient='records', indent=INDENT)
