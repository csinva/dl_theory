import itertools
from slurmpy import Slurm

partition = 'high'

# sweep maxpool reps and reset freq
# conclusion resetting more isn't a big deal if you keep the norm the same
# problems when you don't maintain the norm
params_to_vary = {
    'reps': [1], # 1, 3
    'train_prototypes': [False, True],
    'similarity': ['cosine'],
    'use_conv': [True], # True, False,
    'siamese_init': ['points', 'unif'],
    'out_dir': ['/scratch/users/vision/yu_dl/raaz.rsk/kernel_init/sweep_reps_conv'],  
    'seed': range(0, 1),
    'dset': ['mnist', 'cifar10'], # mnist, cifar10  
    'lr': [0.01, 0.1, 0.5],
    'optimizer': ['adam'],
    'num_layers': [4], # add in 2, 7
    'batch_size': [100], # 10, 100, 1000
    'shuffle_labels': [False], # loop
    'hidden_size': [128], # 128, 512
    'freeze': [False],
    'num_iters': [40],
    'first_layer_lr_mult': [1],
    'save_all_freq': [20],
    'save_acts_and_reduce': [False],
    'saves_per_iter': [2],
}


# run
s = Slurm("sweep_full", {"partition": partition, "time": "3-0"})
ks = sorted(params_to_vary.keys())
vals = [params_to_vary[k] for k in ks]
param_combinations = list(itertools.product(*vals)) # list of tuples
print(param_combinations)
# for param_delete in params_to_delete:
#     param_combinations.remove(param_delete)

# iterate
for i in range(len(param_combinations)):
    param_str = 'module unload python/3.7; module load python/3.5; module load pytorch; python ../vision_fit/fit.py '
    for j, key in enumerate(ks):
        param_str += key + ' ' + str(param_combinations[i][j]) + ' '
    s.run(param_str)
