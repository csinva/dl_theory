import os
import torch
import torch.nn as nn
from torch.autograd import Variable
import torchvision.datasets as dset
import torchvision.transforms as transforms
import torch.nn.functional as F
import torch.optim as optim
import torchvision
from os.path import join as oj
import sys
sys.path.append('../vision_fit')
sys.path.append('../vision_analyze')
import viz_weights
import numpy as np
from copy import deepcopy
import pickle as pkl
from torch.optim.lr_scheduler import StepLR
from sklearn.decomposition import PCA
from sklearn.metrics import pairwise
import matplotlib.pyplot as plt
import models
from dim_reduction import *
from sklearn.decomposition import MiniBatchDictionaryLearning
from tqdm import tqdm

from params import p

# set params
for i in range(1, len(sys.argv), 2):
    t = type(getattr(p, sys.argv[i]))
    if sys.argv[i+1] == 'True':
        setattr(p, sys.argv[i], t(True))            
    elif sys.argv[i+1] == 'False':
        setattr(p, sys.argv[i], t(False))
    elif sys.argv[i+1] == 'None':
        setattr(p, sys.argv[i], None)
    else:
        setattr(p, sys.argv[i], t(sys.argv[i+1]))

print(vars(p))
        
np.random.seed(p.seed) 
torch.manual_seed(p.seed)

# load dset
root = oj('/scratch/users/vision/yu_dl/raaz.rsk/data', 'cifar10')
trans = transforms.Compose([transforms.ToTensor()])
test_set = dset.CIFAR10(root=root, train=False, download=True)
X_test = test_set.test_data
Y_test = np.array(test_set.test_labels)
lab_dict = {0: 'airplane', 1: 'automobile', 2: 'bird', 3: 'cat', 4: 'deer', 5: 'dog', 6: 'frog', 7: 'horse', 8: 'ship', 9: 'truck'}

# filter by a class
if p.class_num is None:
    X = X_test
    Y = Y_test
else:
    idxs = Y_test==p.class_num
    X = X_test[idxs]
    Y = Y_test[idxs]

X_d = X.reshape(X.shape[0], -1)
print(X_d.shape)

n_iter = int(1000 / p.batch_size)
dico = MiniBatchDictionaryLearning(n_components=p.num_bases, alpha=p.alpha, n_iter=n_iter, n_jobs=1, batch_size=p.batch_size) 
save_freq = 100
for i in tqdm(range(50000)):
    V = dico.fit(X_d)
    if i % save_freq == 0:
        s = '_alpha=' + str(p.alpha) + '_ncomps=' + str(p.num_bases) + '_class=' + str(p.class_num)
        fname1 = 'bases/bases_iters=' + str(i) + s + '.npy' 
        np.save(fname1, V.components_)        
        fname2 = 'bases/bases_iters=' + str(i - save_freq) + s + '.npy'
        viz_weights.plot_weights(V.components_, dset='rgb')
        fname3 = 'bases_figs/bases_iters=' + str(i - save_freq) + s + '.png'
        plt.savefig('bases_figs/bases_iters=' + str(i) + s + '.png', dpi=200, bbox_inches = 'tight', pad_inches = 0)
        
        if os.path.exists(fname2):
            os.remove(fname2)
            
        if os.path.exists(fname3):
            os.remove(fname3)
            
        plt.clf()
        plt.cla()
        plt.close()