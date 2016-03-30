from PySparseConvNet import SparseNetwork
from PySparseConvNet import Off3DPicture
from PySparseConvNet import SparseDataset

import os

def create_DeepC2Network(dimension, l, k, fn, nInputFeatures, nClasses, p):
    sparse_net = SparseNetwork(dimension, nInputFeatures, nClasses)
    for i in range(l + 1):
        sparse_net.addLeNetLayerMP(
            (i + 1) * k, 2, 1, 3 if (i < l) else 1, 2 if (i < l) else 1, fn,
            p * i * 1.0 / l)
    sparse_net.addSoftmaxLayer()
    return sparse_net


def create_dC2():
    nFeatures = 1
    nClasses = 40
    return create_DeepC2Network(3, 5, 32, 'VLEAKYRELU', nFeatures, nClasses, 0.0)

def load_and_get_weights(deepC2):
    baseName = "SparseConvNet/weights/ModelNet"
    epoch = 20
    deepC2.loadWeights(baseName, epoch)
    return deepC2.get_weights()


def load_3d_off():
    path = "SparseConvNet/Data/ModelNet/airplane/train/airplane_0511.off"
    print("Creating Off3DPicture object")
    picture = Off3DPicture(path, 40)
    print("Codifying...")
    pairs, features = picture.codifyInputData(126)
    print ("done")
    return pairs

def generate_modelnet_dataset():
    number_of_features = 1
    renderSize = 40
    data_folder = "SparseConvNet/Data/ModelNet/"
    class_folders = os.listdir(data_folder)
    class_folders.sort()
    number_of_classes = len(class_folders)
    sparse_dataset = SparseDataset("ModelNet (Train subset)", 'TRAINBATCH',
                                   number_of_features, number_of_classes)
    for class_id, folder in enumerate(class_folders):
        dirpath = os.path.join(data_folder, folder, 'train')
        for filename in os.listdir(dirpath):
            sparse_dataset.add_picture(Off3DPicture(
                os.path.join(dirpath, filename), renderSize, label=class_id))
    # sparse_dataset.repeatSamples(10)
    return sparse_dataset