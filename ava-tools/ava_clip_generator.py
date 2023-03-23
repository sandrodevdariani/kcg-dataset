import os
import torch
import open_clip
import pandas as pd
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

MODEL_NAME = 'ViT-L-14'
PRETRAINED = 'laion2b_s32b_b82k'
ALLOWED_EXTENSIONS = ['jpg', 'png']
DEBUG = True

# set the directory paths
IMAGES_DIR = 'images-sorted' # directory that contains the sorted images
# SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)) # use the dataset is in the same directory as the script
SCRIPT_DIR = os.getcwd() # use this if dataset is in the current working directory

IMAGE_DIR = os.path.join(SCRIPT_DIR, IMAGES_DIR)
INDENT = 1 # indent level for the JSON file

# path for ava.json
AVA_PATH = os.path.join(SCRIPT_DIR, 'AVA.json')
# read AVA.json into a dataframe
df = pd.read_json(AVA_PATH, orient='records')
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
        image = preprocess(Image.open(os.path.join(IMAGE_DIR, dir_name, file_name))).unsqueeze(0).to(device)
        emb = model.encode_image(image).cpu().detach().numpy()
    return emb

# iterate through the directories
directories = os.listdir(IMAGES_DIR)
directories = sorted(directories)
print(f'Total number of directories: {len(directories)}')
end = '\n' if DEBUG else '\r'
for directory in directories:
    print(f'Processing directory: {directory}')
    # iterate through the files in the directory
    files = os.listdir(os.path.join(IMAGES_DIR, directory))
    total_files = len(files)
    # remove json files
    files = [file for file in files if file.split('.')[-1] in ALLOWED_EXTENSIONS]
    # sort the files by name
    files = sorted(files, key=lambda x: int(x.split('.')[0]))
    # create an empty dataframe
    df_new = pd.DataFrame(columns=df.columns)

    for index, file in enumerate(files):
        # check file extension
        ext = file.split('.')[-1]
        if ext not in ALLOWED_EXTENSIONS:
            continue

        # print the progress
        print(f"Processing {file} {index+1}/{total_files}", end=end)

        # try to open the image
        try:
            # check if the image is corrupt
            img = Image.open(os.path.join(IMAGE_DIR, directory, file))
            img.verify()
        except:
            # skip the image if it is corrupt
            print(f"Error: {file} is corrupt. Skipping...")
            continue
        
        # generate the embeddings
        emb = generate_embeddings(file, directory)

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

# remove the existing clip.json file
if os.path.exists('AVA-clip.json'):
    os.remove('AVA-clip.json')

# save the dataframe to a json file
df.to_json('AVA-clip.json', orient='records', indent=INDENT)
