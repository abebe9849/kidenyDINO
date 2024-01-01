import argparse
import os,cv2
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
import PIL.Image
import numpy
import torch
from pathlib import Path
from extractor import ViTExtractor
from tqdm import tqdm
import numpy as np
from PIL import Image
from sklearn.decomposition import PCA
from typing import List, Tuple
import pandas as pd
import pickle

def pca(image_paths, load_size: int = 224, layer: int = 11, facet: str = 'key', bin: bool = False, stride: int = 4,
        model_type: str = 'dino_vitb16', n_components: int = 4,
        all_together: bool = True,idx:int=0) -> List[Tuple[Image.Image, numpy.ndarray]]:
    """
    finding pca of a set of images.
    :param image_paths: a list of paths of all the images.
    :param load_size: size of the smaller edge of loaded images. If None, does not resize.
    :param layer: layer to extract descriptors from.
    :param facet: facet to extract descriptors from.
    :param bin: if True use a log-binning descriptor.
    :param model_type: type of model to extract descriptors from.
    :param stride: stride of the model.
    :param n_components: number of pca components to produce.
    :param all_together: if true apply pca on all images together.
    :return: a list of lists containing an image and its principal components.
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    #device = "cpu"
    w_path = "/home/abe/KidneyM/dino/pas_glomerulus_exp001/checkpoint0600.pth"
    if model_type=="dino_vitb16":
        w_path="/home/abe/KidneyM/dino/pas_glomerulus_wbf_L/checkpoint0600.pth"
    extractor = ViTExtractor(model_type, stride,w_path, device=device)
    descriptors_list = []
    image_pil_list = []
    num_patches_list = []
    load_size_list = []
    X = 200

    # extract descriptors and saliency maps for each image
    #"""
    #for image_path in tqdm(image_paths[X*idx:X*idx+X]):
    #    image_batch, image_pil = extractor.preprocess(image_path, load_size)
    #    image_pil_list.append(image_pil)
    #    descs = extractor.extract_descriptors(image_batch.to(device), layer, facet, bin, include_cls=False).cpu().numpy()
    #    curr_num_patches, curr_load_size = extractor.num_patches, extractor.load_size
    #    num_patches_list.append(curr_num_patches)
    #    load_size_list.append(curr_load_size)
    #    descriptors_list.append(descs)
    #with open(f'/home/abe/KidneyM/dino/dino-vit-features/accum_data/image_pil_list_{idx}.pickle', 'wb') as f:
    #    pickle.dump(image_pil_list, f)
    #with open(f'/home/abe/KidneyM/dino/dino-vit-features/accum_data/num_patches_list_{idx}.pickle', 'wb') as f:
    #    pickle.dump(num_patches_list, f)
    #with open(f'/home/abe/KidneyM/dino/dino-vit-features/accum_data/load_size_list_{idx}.pickle', 'wb') as f:
    #    pickle.dump(load_size_list, f)
    #with open(f'/home/abe/KidneyM/dino/dino-vit-features/accum_data/descriptors_list_{idx}.pickle', 'wb') as f:
    #    pickle.dump(descriptors_list, f)
    #"""
    #exit()
    for idx in tqdm(range(9)):
        with open(f'/home/abe/KidneyM/dino/dino-vit-features/accum_data_1024/image_pil_list_{idx}.pickle', 'rb') as f:
            image_pil_list += pickle.load(f)
        with open(f'/home/abe/KidneyM/dino/dino-vit-features/accum_data_1024/num_patches_list_{idx}.pickle', 'rb') as f:
            num_patches_list += pickle.load(f)
        with open(f'/home/abe/KidneyM/dino/dino-vit-features/accum_data_1024/load_size_list_{idx}.pickle', 'rb') as f:
            load_size_list += pickle.load(f)
        with open(f'/home/abe/KidneyM/dino/dino-vit-features/accum_data_1024/descriptors_list_{idx}.pickle', 'rb') as f:
            descriptors_list += pickle.load(f)
    all_together = True
    if all_together:
        descriptors = np.concatenate(descriptors_list[:], axis=2)[0, 0]
        print(descriptors.shape,len(descriptors_list))

        pca = PCA(n_components=n_components).fit(descriptors)#どの画像のlistを入れたのかによって結果変わる
        with open(f'/home/abe/KidneyM/dino/dino-vit-features/accum_data_1024/pca6.pickle', 'wb') as f:
            pickle.dump(pca, f)
        pca_descriptors = pca.transform(descriptors)
        print(pca_descriptors.shape)
        split_idxs = np.array([num_patches[0] * num_patches[1] for num_patches in num_patches_list])
        split_idxs = np.cumsum(split_idxs)
        pca_per_image = np.split(pca_descriptors, split_idxs[:-1], axis=0)
        np.save(f"/home/abe/KidneyM/dino/dino-vit-features/accum_data_1024/pca_per_image6.npy",pca_per_image)
    else:
        pca_per_image = []
        for descriptors in descriptors_list:
            pca = PCA(n_components=n_components).fit(descriptors[0, 0])
            pca_descriptors = pca.transform(descriptors[0, 0])
            pca_per_image.append(pca_descriptors)
    results = [(pil_image, img_pca.reshape((num_patches[0], num_patches[1], n_components))) for
               (pil_image, img_pca, num_patches) in zip(image_pil_list, pca_per_image, num_patches_list)]
    return results


def plot_pca(pil_image: Image.Image, pca_image: numpy.ndarray, save_dir_: str, last_components_rgb: bool = True,
             save_resized=True, save_prefix: str = ''):
    """
    finding pca of a set of images.
    :param pil_image: The original PIL image.
    :param pca_image: A numpy tensor containing pca components of the image. HxWxn_components
    :param save_dir: if None than show results.
    :param last_components_rgb: If true save last 3 components as RGB image in addition to each component separately.
    :param save_resized: If true save PCA components resized to original resolution.
    :param save_prefix: optional. prefix to saving
    :return: a list of lists containing an image and its principal components.
    """
    save_dir = Path(save_dir_)
    save_dir.mkdir(exist_ok=True, parents=True)
    pil_image_path = save_dir / f'{save_prefix}_orig_img.png'
    pil_image.save(pil_image_path)

    n_components = pca_image.shape[2]
    for comp_idx in range(n_components):
        comp = pca_image[:, :, comp_idx]
        comp_min = comp.min(axis=(0, 1))
        comp_max = comp.max(axis=(0, 1))
        comp_img = (comp - comp_min) / (comp_max - comp_min)
        comp_file_path = save_dir / f'{save_prefix}_{comp_idx}.png'
        pca_pil = Image.fromarray((comp_img * 255).astype(np.uint8))
        if save_resized:
            pca_pil = pca_pil.resize(pil_image.size, resample=PIL.Image.NEAREST)
        pca_pil.save(comp_file_path)

    if last_components_rgb:
        comp_idxs = f"{n_components-3}_{n_components-2}_{n_components-1}"
        comp = pca_image[:, :, -3:]
        comp_min = comp.min(axis=(0, 1))
        comp_max = comp.max(axis=(0, 1))
        comp_img = (comp - comp_min) / (comp_max - comp_min)
        comp_file_path = save_dir / f'{save_prefix}_{comp_idxs}_rgb.png'
        pca_pil = Image.fromarray((comp_img * 255).astype(np.uint8))
        if save_resized:
            pca_pil = pca_pil.resize(pil_image.size, resample=PIL.Image.NEAREST)
        pca_pil.save(comp_file_path)
        
    x = np.concatenate([cv2.imread(f'{save_dir_}/{save_prefix}_0.png'),cv2.imread(f'{save_dir_}/{save_prefix}_1.png'),cv2.imread(f'{save_dir_}/{save_prefix}_{comp_idxs}_rgb.png')],axis=1)
    y = np.concatenate([cv2.imread(f'{save_dir_}/{save_prefix}_2.png'),cv2.imread(f'{save_dir_}/{save_prefix}_3.png'),cv2.imread(f'{save_dir_}/{save_prefix}_orig_img.png')],axis=1)
    
    x = np.concatenate([x,y])
    cv2.imwrite(f"{save_dir_}/{save_prefix}_result.png",x)
    os.remove(f'{save_dir_}/{save_prefix}_0.png')
    os.remove(f'{save_dir_}/{save_prefix}_1.png')
    os.remove(f'{save_dir_}/{save_prefix}_2.png')
    os.remove(f'{save_dir_}/{save_prefix}_3.png')
    os.remove(f'{save_dir_}/{save_prefix}_{comp_idxs}_rgb.png')
    os.remove(f'{save_dir_}/{save_prefix}_orig_img.png')

    


""" taken from https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse"""
def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
df = pd.read_csv("/home/abe/KidneyM/hubmap2021/MATUI_bbxo/final_pas.csv")
df["h_w"]=df["H"]/df["W"]
df = df[df["h_w"]>0.5]
df = df[df["h_w"]<2].reset_index(drop=True)
path_l = df["path"].values
import glob
# python pca.py --idx 0
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Facilitate ViT Descriptor PCA.')
    parser.add_argument('--root_dir', type=str, required=False, help='The root dir of images.') #/home/abe/KidneyM/dino/dino-vit-features/demo
    parser.add_argument('--save_dir',default="/home/abe/KidneyM/dino/dino-vit-features/size1024_imnet", type=str, help='The root save dir for results.') #
    parser.add_argument('--load_size', default=1024, type=int, help='load size of the input image.')
    parser.add_argument('--stride', default=4, type=int, help="""stride of first convolution layer. 
                                                                    small stride -> higher resolution.""")
    parser.add_argument('--model_type', default='vit_base_patch16_224', type=str,
                        help="""type of model to extract. 
                              Choose from [dino_vits8 | dino_vitl16 | dino_vitb8 | dino_vitb16 | vit_small_patch8_224 | 
                              vit_small_patch16_224 | vit_base_patch8_224 | vit_base_patch16_224]""")
    parser.add_argument('--facet', default='key', type=str, help="""facet to create descriptors from. 
                                                                       options: ['key' | 'query' | 'value' | 'token']""")
    parser.add_argument('--layer', default=11, type=int, help="layer to create descriptors from.")
    parser.add_argument('--bin', default='False', type=str2bool, help="create a binned descriptor if True.")
    parser.add_argument('--n_components', default=4, type=int, help="number of pca components to produce.")
    parser.add_argument('--last_components_rgb', default='True', type=str2bool, help="save last components as rgb image.")
    parser.add_argument('--save_resized', default='True', type=str2bool, help="If true save pca in image resolution.")
    parser.add_argument('--all_together', default='True', type=str2bool, help="If true apply pca on all images together.")
    parser.add_argument('--idx', default=0, type=int, help="number of pca components to produce.")

    args = parser.parse_args()

    with torch.no_grad():

        # prepare directories
        #root_dir = Path(args.root_dir)

        images_paths = glob.glob("/home/abe/KidneyM/dino/dino-vit-features/forPCA/*")
        save_dir = Path(args.save_dir)
        save_dir.mkdir(exist_ok=True, parents=True)
        pca_per_image = pca(images_paths, args.load_size, args.layer, args.facet, args.bin, args.stride, args.model_type,
                            args.n_components, args.all_together,idx=args.idx)
        print("saving images")
        
        for image_path, (pil_image, pca_image) in tqdm(zip(images_paths, pca_per_image)):
            save_prefix = image_path.split("/")[-1].split(".")[0]
            plot_pca(pil_image, pca_image, str(save_dir), args.last_components_rgb, args.save_resized, save_prefix)

