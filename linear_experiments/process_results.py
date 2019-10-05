import pandas as pd
import numpy as np
from os.path import join as oj
from tqdm import tqdm
import data, fit
import os
from os.path import join as oj
import sys, time
sys.path.insert(1, oj(sys.path[0], '..'))  # insert parent path
import seaborn as sns
from sklearn.model_selection import train_test_split
from regression_dsets_large_names import regression_dsets_large_names
import numpy as np
import matplotlib.pyplot as plt
from sklearn import metrics
import pmlb
from tqdm import tqdm
from copy import deepcopy
import pickle as pkl
import pandas as pd
import data
import fit


def process_results(results):
    # add keys for things which weren't recorded at the teim
    for key in ['H_trace']:
        if key not in results:
            results[key] = None
    if 'beta_norm' not in results:
        results['beta_norm'] = 1
    if 'beta_type' not in results:
        results['beta_type'] = 'one_hot'
    if 'noise_distr' not in results:
        results['noise_distr'] = 'gaussian'
    return results

def best_ridge(df):
    '''Takes in results, already aggregated over seeds and selects best ridge axes to plot
    
    Returns
    -------
    row: row of pd.Dataframe with row.df1, row.df2, row.df3
    '''
    name_best = ''
    auc_best = 1e10
    for name, curve in tqdm(df.iterrows()):
    #     print(name, curve)
        model_type = name[3]
        reg_param = name[4]
        l = str(model_type) + ' ' + str(reg_param)
        if model_type == 'ridge':
            auc = np.trapz(y=np.log(curve.mse_noiseless), x=curve.ratio)
            auc = np.trapz(y=curve.mse_noiseless) #, x=np.log(curve.ratio))
            if auc < auc_best:
                auc_best = auc
                name_best = name
    row = df.loc[name_best]
    return row


def aggregate_results(results, group_idxs, out_dir):
    '''Takes in results and makes curves when varying n_train + aggregates over seeds
    '''
    r2 = results.groupby(group_idxs)
    ind = pd.MultiIndex.from_tuples(r2.indices, names=group_idxs)
    df = pd.DataFrame(index=ind)
    keys = ['ratio', 'bias', 'var', 'wnorm', 'mse_train', 'mse_test', 'num_nonzero', 'mse_noiseless', 'df1', 'df2', 'df3']
    for key in keys:
        df[key] = None
    for name, gr in tqdm(r2):
        p = gr.iloc[0]
        dset = p.dset
        noise_mult = p.noise_mult
        dset_num = p.dset_num
        model_type = p.model_type
        reg_param = p.reg_param
        num_features = p.num_features
        curve = gr.groupby(['n_train']) #.sort_index()
        row = {k: [] for k in keys}
        row['model_type'] = model_type
        row['reg_param'] = reg_param
        row['num_features'] = num_features
        row['noise_mult'] = noise_mult
    #         print(curve.describe())
    
#         if reg_param > 9 and model_type == 'lasso':
#             print(gr.preds_test.values)

        for curve_name, gr2 in curve:
            

            if dset == 'gaussian':
                dset_name = ''
                _, _, _, y_true, betastar = \
                    data.get_data_train_test(n_test=p.n_test, p=p.num_features, 
                                             noise_mult=0, noise_distr=p.noise_distr, iid=p.iid, # parameters to be determined
                                             beta_type=p.beta_type, beta_norm=p.beta_norm)
                y_true = y_true.reshape(1, -1) # 1 x n_test
            elif dset == 'pmlb':
                dset_name = regression_dsets_large_names[dset_num]
                X, y = pmlb.fetch_data(dset_name, return_X_y=True)
                fit.seed(703858704)
                _, _, _, y_true = train_test_split(X, y) # get test set

                
            preds = gr2.preds_test.values
            preds = np.stack(preds) # num_seeds x n_test
            preds_mean = preds.mean(axis=0).reshape(1, -1) # 1 x n_test
#             print('shapes', preds.shape, y_true.shape, preds_mean.shape)
            y_true_rep = np.repeat(y_true, repeats=preds.shape[0], axis=0) # num_seeds x n_test
#             print('rep', y_true_rep.shape, y_true_rep[0, :10], y_true_rep[1, :10])
            preds_mu = np.mean(preds)
            bias = np.mean(preds_mu - y_true_rep.flatten())
            var = np.mean(np.square(preds.flatten() - preds_mu))
            mse_noiseless = metrics.mean_squared_error(preds.flatten(), y_true_rep.flatten())
#             bias = np.mean(preds_mean - y_true)
#             var = np.mean(np.square(preds - preds_mean))
            
#             print('bias', bias, 'var', var, 'mse', mse_noiseless, 'comb', bias**2 + var)

            row['ratio'].append(gr2.num_features.values[0] / gr2.n_train.values[0])
            row['bias'].append(bias)
            row['var'].append(var)
            row['wnorm'].append(gr2.wnorm.mean())
            row['mse_train'].append(gr2.train_mse.mean())
            row['mse_test'].append(gr2.test_mse.mean())
            row['mse_noiseless'].append(mse_noiseless)
            for key in ['num_nonzero', 'df1', 'df2', 'df3']:
#                 print(key, gr2[key].mean())
                row[key].append(gr2[key].mean())
#             row['mse_zero'].append(metrics.mean_squared_error(y_true, np.zeros(y_true.size).reshape(y_true.shape))) # metrics.mean_squared_error(y_true, np.zeros(y_true.size).reshape(y_true.shape))

        for k in keys:
            df.at[name, k] = np.array(row[k]) #3# ratios\
#     mse_zero = np.mean(np.square(y_true))
    df['mse_zero'] = metrics.mean_squared_error(y_true, np.zeros(y_true.size).reshape(y_true.shape))
    df.to_pickle(oj(out_dir, 'processed.pkl')) # save into out_dir
    
    
    return df


# run this to process / save some dsets
if __name__ == '__main__':
# all_linear_old
    # these all have ols, ridge, sta, lasso with appropriate hyperparams
    # beta=gaussian_noise=1e-1
    # beta=gaussian_noise=0 
    # beta=onehot_noise=0  
    # beta=onehot_noise=1e-1 
# all_linear_clustered
# all_linear_vary_noise_distr
# all_linear_pmlb




# df/basic

    out_dir = '/scratch/users/vision/yu_dl/raaz.rsk/double_descent/df'
    for folder in tqdm(sorted(os.listdir(out_dir))):
        folder_path = oj(out_dir, folder)
        if not 'processed.pkl' in os.listdir(folder_path):
            try:
                fnames = sorted([fname for fname in os.listdir(folder_path)])
                results_list = [pd.Series(pkl.load(open(oj(folder_path, fname), "rb"))) for fname in tqdm(fnames)
                                if not fname.startswith('processed')]
                results = pd.concat(results_list, axis=1).T.infer_objects()



                group_idxs = ['dset', 'dset_num',
                              'beta_type', 'model_type', 'reg_param',
                              'beta_norm',
                              'noise_mult', 'noise_distr', 'iid',  # dset
                             ] # model
                results = process_results(results)
                df = aggregate_results(results, group_idxs, folder_path)
            except Exception as e:
                print('failed', folder, e)