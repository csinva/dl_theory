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
import numpy as np
from copy import deepcopy
import pickle as pkl
from torch.optim.lr_scheduler import StepLR
from sklearn.decomposition import PCA
from sklearn.metrics import pairwise

import models
from dim_reduction import *

# reduce model by projecting onto pcs that explain "percent_to_explain"
def reduce_model(model, percent_to_explain=0.85):
    model_r = deepcopy(model)
    weight_dict = model_r.state_dict()
    weight_dict_new = deepcopy(model_r.state_dict())
    
    for layer_name in weight_dict.keys():
        if 'weight' in layer_name:
            w = weight_dict[layer_name]
            
            # get number of components
            pca = PCA(n_components=w.shape[1])
            pca.fit(w)
            explained_vars = pca.explained_variance_ratio_
            dim, perc_explained = 0, 0
            while perc_explained <= percent_to_explain:
                perc_explained += explained_vars[dim]
                dim += 1
            
            # actually project
            pca = PCA(n_components=dim)            
            w2 = pca.inverse_transform(pca.fit_transform(w))
            weight_dict_new[layer_name] = torch.Tensor(w2)
            
    model_r.load_state_dict(weight_dict_new)
    return model_r

def layer_norms(weight_dict):
    return {lay_name: np.linalg.norm(weight_dict[lay_name])**2 for lay_name in weight_dict.keys() if 'weight' in lay_name}

def calc_loss_acc(test_loader, batch_size, use_cuda, model, criterion):
    correct_cnt, tot_loss_test = 0, 0
    n_test = len(test_loader) * batch_size
    for batch_idx, (x, target) in enumerate(test_loader):
        if use_cuda:
            x, target = x.cuda(), target.cuda()
        x, target = Variable(x, volatile=True), Variable(target, volatile=True)
        out = model(x)
        loss = criterion(out, target)
        _, pred_label = torch.max(out.data, 1)
        correct_cnt += (pred_label == target.data).sum()
        tot_loss_test += loss.data[0]
    print('==>>> loss: {:.6f}, acc: {:.3f}'.format(tot_loss_test / n_test, correct_cnt * 1.0 / n_test))
    return tot_loss_test / n_test, correct_cnt * 1.0 / n_test
    

def fit_vision(p):
    # set random seed        
    np.random.seed(p.seed) 
    torch.manual_seed(p.seed)    
    use_cuda = torch.cuda.is_available()
    batch_size = 100
    root = oj('/scratch/users/vision/yu_dl/raaz.rsk/data', p.dset)
    if not os.path.exists(root):
        os.mkdir(root)
    
        
    ## load mnist dataset     
    if p.dset == 'mnist':
        trans = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (1.0,))])
        train_set = dset.MNIST(root=root, train=True, transform=trans, download=True)
        test_set = dset.MNIST(root=root, train=False, transform=trans, download=True)
        train_loader = torch.utils.data.DataLoader(
                         dataset=train_set,
                         batch_size=batch_size,
                         shuffle=True)
        test_loader = torch.utils.data.DataLoader(
                        dataset=test_set,
                        batch_size=batch_size,
                        shuffle=False)
        model = models.MnistNet()        
    elif p.dset == 'cifar10':
        trans = transforms.Compose(
            [transforms.ToTensor(),
             transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
        train_set = dset.CIFAR10(root=root, train=True, download=True, transform=trans)
        test_set = dset.CIFAR10(root=root, train=False, download=True, transform=trans)
        train_loader = torch.utils.data.DataLoader(train_set, 
                                                   batch_size=batch_size,
                                                   shuffle=True)
        test_loader = torch.utils.data.DataLoader(test_set, 
                                                  batch_size=batch_size,
                                                  shuffle=False)
        model = models.Cifar10Net()              
    
    criterion = nn.CrossEntropyLoss()
    if use_cuda:
        model = model.cuda()
    if p.optimizer == 'sgd':    
        optimizer = optim.SGD(model.parameters(), lr=p.lr)
    elif p.optimizer == 'adam':
        optimizer = optim.Adam(model.parameters(), lr=p.lr, betas=(p.beta1, p.beta2), eps=1e-8)
    scheduler = StepLR(optimizer, step_size=p.step_size_optimizer, gamma=p.gamma_optimizer)
    scheduler2 = StepLR(optimizer, step_size=p.step_size_optimizer_2, gamma=p.gamma_optimizer2)

        
    # things to record
    weights, weights_first10, weight_norms = {}, {}, {}
    losses_train, losses_test = np.zeros(p.num_iters), np.zeros(p.num_iters)
    accs_train, accs_test = np.zeros(p.num_iters), np.zeros(p.num_iters)
    losses_train_r, losses_test_r = np.zeros(p.num_iters), np.zeros(p.num_iters)
    accs_train_r, accs_test_r = np.zeros(p.num_iters), np.zeros(p.num_iters)    
    explained_var_dicts, explained_var_dicts_cosine, explained_var_dicts_rbf, explained_var_dicts_lap = [], [], [], []
    
    
    # save things for iter 0
    weight_dict = deepcopy({x[0]:x[1].data.cpu().numpy() for x in model.named_parameters()})
    if p.save_all_weights_mod == 0:
        weights[0] = weight_dict
        weights_first10[0] = deepcopy(model.state_dict()['fc1.weight'][:20].cpu().numpy())
    weight_norms[0] = layer_norms(model.state_dict())    
    explained_var_dicts.append(get_explained_var_from_weight_dict(weight_dict))    
    explained_var_dicts_cosine.append(get_explained_var_kernels(weight_dict, 'cosine'))
    explained_var_dicts_rbf.append(get_explained_var_kernels(weight_dict, 'rbf'))
    explained_var_dicts_lap.append(get_explained_var_kernels(weight_dict, 'laplacian'))
    ave_loss_train, acc_train = calc_loss_acc(train_loader, batch_size, use_cuda, model, criterion)
    ave_loss_test, acc_test = calc_loss_acc(test_loader, batch_size, use_cuda, model, criterion)
    losses_train[0] = ave_loss_train   
    losses_test[0] = ave_loss_test
    accs_train[0] = acc_train
    accs_test[0] = acc_test

        
    # run    
    print('training...')
    for it in range(1, p.num_iters):

        # training
        for batch_idx, (x, target) in enumerate(train_loader):
            optimizer.zero_grad()
            if use_cuda:
                x, target = x.cuda(), target.cuda()
            x, target = Variable(x), Variable(target)
            out = model(x)
            loss = criterion(out, target)
            loss.backward()
            optimizer.step()
            
            # don't go through whole dataset
            if batch_idx > len(train_loader) / p.saves_per_iter and it <= p.saves_per_iter * p.saves_per_iter_end + 1:
                break
                    
        scheduler.step()
        if it > p.num_iters_small:
            scheduler2.step()
            
        # calc stats and record
        print('it', it)
        ave_loss_train, acc_train = calc_loss_acc(train_loader, batch_size, use_cuda, model, criterion)
        ave_loss_test, acc_test = calc_loss_acc(test_loader, batch_size, use_cuda, model, criterion)
        losses_train[it], losses_test[it] = ave_loss_train, ave_loss_test
        accs_train[it], accs_test[it] = acc_train, acc_test
        
        # calculated reduced stats
        model_r = reduce_model(model)
        ave_loss_train_r, acc_train_r = calc_loss_acc(train_loader, batch_size, use_cuda, model_r, criterion)
        ave_loss_test_r, acc_test_r = calc_loss_acc(test_loader, batch_size, use_cuda, model_r, criterion)
        losses_train_r[it], losses_test_r[it] = ave_loss_train_r, ave_loss_test_r
        accs_train_r[it], accs_test_r[it] = acc_train_r, acc_test_r
        
        # record complicated things         
        weight_dict = deepcopy({x[0]:x[1].data.cpu().numpy() for x in model.named_parameters()})
        if it % p.save_all_weights_freq == p.save_all_weights_mod or it == p.num_iters - 1:
            weights[p.its[it]] = weight_dict 
        weights_first10[p.its[it]] = deepcopy(model.state_dict()['fc1.weight'][:20].cpu().numpy())            
        weight_norms[p.its[it]] = layer_norms(model.state_dict())        
        explained_var_dicts.append(get_explained_var_from_weight_dict(weight_dict))    
        explained_var_dicts_cosine.append(get_explained_var_kernels(weight_dict, 'cosine'))
        explained_var_dicts_rbf.append(get_explained_var_kernels(weight_dict, 'rbf'))
        explained_var_dicts_lap.append(get_explained_var_kernels(weight_dict, 'laplacian'))
        
        
        
    # save final
    if not os.path.exists(p.out_dir):  # delete the features if they already exist
        os.makedirs(p.out_dir)
    params = p._dict(p)
    
    results = {'losses_train': losses_train, 'losses_test': losses_test, 
               'accs_test': accs_test, 'accs_train': accs_train,
               'losses_train_r': losses_train_r, 'losses_test_r': losses_test_r, 
               'accs_test_r': accs_test_r, 'accs_train_r': accs_train_r,  
               'weight_norms': weight_norms,
               'explained_var_dicts_pca': explained_var_dicts, 
               'explained_var_dicts_cosine': explained_var_dicts_cosine, 
               'explained_var_dicts_rbf': explained_var_dicts_rbf, 
               'explained_var_dicts_lap': explained_var_dicts_lap}
    weights_results = {'weights': weights, 'weights_first10': weights_first10}    
    results_combined = {**params, **results}    
    weights_results_combined = {**params, **weights_results}
    pkl.dump(results_combined, open(oj(p.out_dir, p._str(p) + '.pkl'), 'wb'))
    pkl.dump(weights_results_combined, open(oj(p.out_dir, 'weights_' + p._str(p) + '.pkl'), 'wb'))    
    
if __name__ == '__main__':
    print('starting...')
    from params_vision import p
    
    # set params
    for i in range(1, len(sys.argv), 2):
        t = type(getattr(p, sys.argv[i]))
        setattr(p, sys.argv[i], t(sys.argv[i+1]))
        
    fit_vision(p)
    
    print('success! saved to ', p.out_dir)