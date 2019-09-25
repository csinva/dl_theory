import itertools
from slurmpy import Slurm
import numpy as np

partition = 'low'

# run w/ shifted test
params_to_vary = {
    'out_dir': ['/scratch/users/vision/yu_dl/raaz.rsk/double_descent/all_linear'],
    'seed': range(0, 5),    
    'num_features': [500],    
    'n_train_over_num_features': [1e-2, 5e-2, 1e-1, 0.5, 0.75, 0.9, 1, 1.2, 1.5, 2, 5, 7.5, 1e1, 2e1, 4e1, 1e2],    
    'dset': ['gaussian'],
    'n_test': [5000],
    'noise_mult': [1e-1], #0.001],
    'model_type': ['linear_sta', 'ridge', 'ols', 'lasso'],     
    'iid': ['iid'],
    
    
    'reg_param': [0, 1e-2, 1e-1, 1, 1e1], # make sure to always have reg_param 0!
    'dset_num': [0]
    
}


# run
s = Slurm("double descent", {"partition": partition, "time": "3-0"})
ks = sorted(params_to_vary.keys())
vals = [params_to_vary[k] for k in ks]
param_combinations = list(itertools.product(*vals)) # list of tuples
print(len(param_combinations))
ks = np.array(ks)
i_model_type = np.where(ks == 'model_type')[0][0]
i_reg_param = np.where(ks == 'reg_param')[0][0]
i_dset = np.where(ks == 'dset')[0][0]
i_dset_num = np.where(ks == 'dset_num')[0][0]

for t in param_combinations:
    # remove reg_param for non-ridge and non-lasso
    if t[i_reg_param] > 0 and not t[i_model_type] in ['ridge', 'lasso']:
        param_combinations.remove(t)
        
    # remove reg_param = 0 for ridge and lasso
    if t[i_reg_param] == 0 and t[i_model_type] in ['ridge', 'lasso']:
        param_combinations.remove(t)
    
    # remove dset_num for non-pmlb
    if t[i_dset] is not 'pmlb' and t[i_dset_num] > 0:
        param_combinations.remove(t)

print(len(param_combinations))
#             print(t[i])
#     print(t)
# print(param_combinations)
# for param_delete in params_to_delete:
#     param_combinations.remove(param_delete)

# iterate
for i in range(len(param_combinations)):
    param_str = 'module load python; python3 ../linear_experiments/fit.py '
    for j, key in enumerate(ks):
        param_str += key + ' ' + str(param_combinations[i][j]) + ' '
    s.run(param_str)
    
    
    
# sweep different ways to initialize weights
'''
params_to_vary = {
    'out_dir': ['/scratch/users/vision/yu_dl/raaz.rsk/double_descent/linear_strange_gaussian'],
    'seed': range(0, 6),    
    'num_features': [1000],
    'n_train_over_num_features': [1e-2, 5e-2, 1e-1, 0.5, 0.75, 0.9, 1, 1.2, 1.5, 2, 5, 7.5, 1e1, 2e1, 4e1, 1e2],    

    'dset': ['gaussian'],
#     'dset': ['pmlb'], # pblm, gaussian
#     'dset_num': range(0, 12), # only if using pmlb, 12 of these seem distinct
    
    'n_test': [5000],
    'noise_mult': [0.1], #0.001],
    'model_type': ['linear', 'linear_sta', 'linear_univariate'],     
#     'ridge_param': [0, 1e-2, 1e-1, 1],
}
'''

# sweep different things for linear sta
'''
params_to_vary = {
    'out_dir': ['/scratch/users/vision/yu_dl/raaz.rsk/double_descent/linear_sta'],
    'seed': range(0, 6),    
    'num_features': [1000],
    'n_train_over_num_features': [1e-2, 5e-2, 1e-1, 0.5, 0.75, 0.9, 1, 1.2, 1.5, 2, 5, 7.5, 1e1, 2e1, 4e1, 1e2],    

#     'dset': ['gaussian'],
    'dset': ['pmlb'], # pblm, gaussian
    'dset_num': range(0, 2), # only if using pmlb, 12 of these seem distinct
    
    'n_test': [5000],
    'noise_mult': [0, 1e-2, 1e-1], #0.001],
    'model_type': ['linear_sta'],     
#     'ridge_param': [0, 1e-2, 1e-1, 1],
}
'''

'''
# run w/ diffeent covariances
params_to_vary = {
    'out_dir': ['/scratch/users/vision/yu_dl/raaz.rsk/double_descent/cov_vary'],
    'seed': range(0, 6),    
    'num_features': [1000],
    'n_train_over_num_features': [1e-2, 5e-2, 1e-1, 0.5, 0.75, 0.9, 1, 1.2, 1.5, 2, 5, 7.5, 1e1, 2e1, 4e1, 1e2],    

#     'dset': ['gaussian'],
    'dset': ['gaussian'], # pblm, gaussian
    
    'n_test': [5000],
    'noise_mult': [1e-1], #0.001],
    'model_type': ['linear'],     
    'iid': [False],
#     'ridge_param': [0, 1e-2, 1e-1, 1],
}
'''

# run w/ shifted test
'''
params_to_vary = {
    'out_dir': ['/scratch/users/vision/yu_dl/raaz.rsk/double_descent/shifted_test5'],
    'seed': range(0, 6),    
    'num_features': [1000],
    'n_train_over_num_features': [1e-2, 5e-2, 1e-1, 0.5, 0.75, 0.9, 1, 1.2, 1.5, 2, 5, 7.5, 1e1, 2e1, 4e1, 1e2],    

#     'dset': ['gaussian'],
    'dset': ['gaussian'], # pblm, gaussian
    
    'n_test': [5000],
    'noise_mult': [1e-1], #0.001],
    'model_type': ['linear'],     
    'iid': ['test_inc'],
#     'ridge_param': [0, 1e-2, 1e-1, 1],
}
'''

# for rf
'''
params_to_vary = {
    'out_dir': ['/scratch/users/vision/yu_dl/raaz.rsk/double_descent/rf_pmlb_sweep'],
    'seed': range(0, 7),    

    'num_features': [1000],
    'n_train_over_num_features': [5], # [1e-2, 5e-2, 1e-1, 0.5, 0.75, 0.9, 1, 1.2, 1.5, 2, 5, 7.5, 1e1, 2e1, 4e1, 1e2],    

    
    'dset': ['pmlb'], # pmlb, gaussian
    'dset_num': range(0, 12), # only if using pmlb, 12 of these seem distinct
    
    'n_test': [5000],
    'noise_mult': [0.1], #0.001],
    'model_type': ['rf'],    
    'num_trees': [1, 2, 4, 8, 10, 16, 32, 64],
    'max_depth': [1, 2, 3, 4, 8, 10, 12]
}
'''