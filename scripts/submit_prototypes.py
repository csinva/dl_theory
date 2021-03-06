import itertools
from slurmpy import Slurm

partition = 'high'

# sweep lambda_reg
params_to_vary = {
    'siamese': ['True'],
    'reps': [1], # 1, 3
    'train_prototypes': ['True'],
    'prototype_dim': [0], # 0, 14
    'similarity': ['dot', 'cosine'], # 'cosine'
    'use_conv': ['False'], # True, False,
    'siamese_init': ['unif'],
    'out_dir': ['/scratch/users/vision/yu_dl/raaz.rsk/kernel_init/mnist_gan'],  
    'lr': [0.01], # 0.01 is what works for LeNet
    'optimizer': ['adam'],
    'lambda_reg': [0, 1e0, 1e1, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e10],
    
    # keep these fixed
    'num_iters': [40],    
    'seed': range(0, 1),
    'dset': ['mnist'], # mnist, cifar10  
    'num_layers': [4], # add in 2, 7
    'batch_size': [100], # 10, 100, 1000
    'shuffle_labels': ['False'], # loop
    'hidden_size': [128], # 128, 512
    'freeze': ['False'],
    'first_layer_lr_mult': [1],
    'save_all_freq': [20],
    'save_reduce': ['False'],
    'saves_per_iter': [2],
}


# sweep maxpool reps and reset freq
# conclusion resetting more isn't a big deal if you keep the norm the same
# problems when you don't maintain the norm
'''
params_to_vary = {
    'siamese': [True],
    'reps': [1, 2], # 1, 3
    'train_prototypes': [True],
    'prototype_dim': [14, 20], # 0, 14
    'similarity': ['dot'], # 'cosine'
    'use_conv': [True], # True, False,
    'siamese_init': ['unif'],
    'out_dir': ['/scratch/users/vision/yu_dl/raaz.rsk/kernel_init/conv'],  
    'lr': [0.01], # 0.01 is what works for LeNet
    'optimizer': ['adam'],
    
    # keep these fixed
    'num_iters': [40],    
    'seed': range(0, 1),
    'dset': ['mnist', 'cifar10'], # mnist, cifar10  
    'num_layers': [4], # add in 2, 7
    'batch_size': [100], # 10, 100, 1000
    'shuffle_labels': [False], # loop
    'hidden_size': [128], # 128, 512
    'freeze': ['False'],
    'first_layer_lr_mult': [1],
    'save_all_freq': [20],
    'save_reduce': [False],
    'saves_per_iter': [2],
}
'''

# run
s = Slurm("proto", {"partition": partition, "time": "3-0"})
ks = sorted(params_to_vary.keys())
vals = [params_to_vary[k] for k in ks]
param_combinations = list(itertools.product(*vals)) # list of tuples
print(param_combinations)
# for param_delete in params_to_delete:
#     param_combinations.remove(param_delete)

# iterate
for i in range(len(param_combinations)):
    param_str = 'module load python; module load pytorch; python ../vision_fit/fit.py '
    for j, key in enumerate(ks):
        param_str += key + ' ' + str(param_combinations[i][j]) + ' '
    s.run(param_str)
