from torch.autograd import Variable
import torch
import torch.autograd
import torch.nn.functional as F
import random
import numpy as np
# from params import p
import matplotlib.pyplot as plt
from torch import nn
import torch.optim as optim
from tqdm import tqdm
import pickle as pkl
from os.path import join as oj
import numpy.random as npr
import numpy.linalg as npl
from copy import deepcopy
import pandas as pd
import seaborn as sns
import fit
from scipy.stats import random_correlation

'''
def get_data(d, N, func='x0', grid=True, shufflevar=None, seed_val=None, gt=False, eps=0.0):
    if gt:
        fit.seed(703858)
    elif not seed_val == None:
        fit.seed(seed_val)
    X = npr.randn(N, d)
    
    if grid:
        x0 = X[:, 0]
        X[:, 0] = np.linspace(np.min(x0), np.max(x0), N)
        
    if 'y=x_0' in func:    
        Y = deepcopy(X[:, 0].reshape(-1, 1))
    
    if func == 'y=x_0=2x_1':
        X[:, 1] = deepcopy(X[:, 0] / 2)
        
    if func == 'y=x_0=x_1+eps':
        X[:, 1] = deepcopy(X[:, 0]) + eps * npr.randn(N)
        
    
    if not shufflevar == None:
        X[:, shufflevar] = npr.randn(N)
    
    return X, Y.reshape(-1, 1)
'''

# generate mixture model
# means and sds should be lists of lists (sds just scale variances)
def generate_gaussian_data(N, means=[0, 1], sds=[1, 1], labs=[0, 1]):
    num_means = len(means)
    # deal with 1D
    if type(means[0]) == int or type(means[0])==float:
        means = [[m] for m in means]
        sds = [[sd] for sd in sds]
        P = 1
    else:
        P = len(means[0])
    X = np.zeros((N, P), dtype=np.float32)
    y_plot = np.zeros((N, 1), dtype=np.float32)
    y_one_hot = np.zeros((N, 2), dtype=np.float32)
    for i in range(N):
        z = np.random.randint(num_means) # select gaussian
        X[i] = np.random.multivariate_normal(means[z], np.eye(P) * np.power(sds[z], 2))
        y_plot[i] = labs[z]
        y_one_hot[i, labs[z]] = 1
    return X, y_one_hot, y_plot

# get means and covariances
def get_means_and_cov(num_vars, fix_eigs=False):
    means = np.zeros(num_vars)
    inv_sum = num_vars
    if fix_eigs == 'iid':
        eigs = [1] * num_vars    
    elif fix_eigs == True:
        if num_vars == 5:
            eigs = [2, 2, 1, 0, 0]
        elif num_vars == 10:
            eigs = [4, 3, 2, 1, 0, 0, 0, 0, 0, 0]
            print(np.sum(eigs))
    else:
        eigs = []
        while len(eigs) < num_vars - 1:
            if inv_sum <= 1e-2:
                eig = 0
            else:
                eig = np.random.uniform(0, inv_sum)
            eigs.append(eig)
            inv_sum -= eig

        eigs.append(num_vars - np.sum(eigs))
#     print('eigs', eigs, np.sum(eigs))
    covs = random_correlation.rvs(eigs)
    covs = random_correlation.rvs(eigs)
    return means, covs



def get_X(n, p, iid):
    if iid == 'iid':
        X = np.random.randn(n, p)
    else:
        print(iid, ' data not supported!')
    return X
    '''
    if iid == 'iid' or (iid == 'test_inc' and not test):
        X = np.random.randn(n, p)
    elif iid == 'test_inc' and iid == 'test_inc' and test:
        means, covs = get_means_and_cov(p, fix_eigs=False)
        covs += 5 * np.ones(covs.shape)
        covs /= 6
        X = np.random.multivariate_normal(means, covs, (n,))
    elif iid == 'rand':
        if means is None:
            means, covs = get_means_and_cov(p, fix_eigs=False)
        X = np.random.multivariate_normal(means, covs, (n,))
    '''
    


def get_data_train_test(n_train=10, n_test=100, p=10000, noise_mult=0.1, iid='iid', # parameters to be determined
                        beta_type='one_hot', beta_norm=1, seed_for_training_data=None):

    '''Get data for simulations - test should always be the same given all the parameters (except seed_for_training_data)
    Warning - this sets a random seed!
    '''
    
    np.random.seed(seed=703858704)
    
    # get beta
    if beta_type == 'one_hot':
        beta = np.zeros(p)
        beta[0] = 1
    elif beta_type == 'gaussian':
        beta = np.random.randn(p)
    beta = beta / np.linalg.norm(beta) * beta_norm
        
    
    # data
    X_test = get_X(n_test, p, iid)
    y_test = X_test @ beta + noise_mult * np.random.randn(n_test)
    
    # re-seed before getting betastar
    if not seed_for_training_data is None:
        np.random.seed(seed=seed_for_training_data)
    
    X_train = get_X(n_train, p, iid)
    y_train = X_train @ beta + noise_mult * np.random.randn(n_train)
    
    return X_train, y_train, X_test, y_test, beta