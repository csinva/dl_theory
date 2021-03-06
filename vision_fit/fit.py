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
# from torch.optim.lr_scheduler import StepLR, MultiStepLR
from sklearn.decomposition import PCA
from sklearn.metrics import pairwise
import random
import models
from dim_reduction import *
from stats import *
import stats
import data
from tqdm import tqdm
import time
import optimization
from params_save import S
import init


def seed(p):
    # set random seed        
    np.random.seed(p.seed) 
    torch.manual_seed(p.seed)    
    random.seed(p.seed)
    
def save(out_name, p, s):
    # save final
    if not os.path.exists(p.out_dir):  
        os.makedirs(p.out_dir)
    params_dict = p._dict(p)
    results_combined = {**params_dict, **s._dict_vals()}    
    weights_results_combined = {**params_dict, **s._dict_weights()}

    # dump
    pkl.dump(params_dict, open(oj(p.out_dir, 'idx_' + out_name + '.pkl'), 'wb'))
    pkl.dump(results_combined, open(oj(p.out_dir, out_name + '.pkl'), 'wb'))
    pkl.dump(weights_results_combined, open(oj(p.out_dir, 'weights_' + out_name + '.pkl'), 'wb'))     
    
def fit_vision(p):
    out_name = p._str(p) # generate random fname str before saving
    seed(p)
    use_cuda = torch.cuda.is_available()
    device = 'cuda' if use_cuda else 'cpu'
    
    # pick dataset and model
    print('loading dset...')
    train_loader, test_loader = data.get_data_loaders(p)
    X_train, Y_train_onehot = data.get_XY(train_loader)
    model = data.get_model(p, X_train, Y_train_onehot)
    init.initialize_weights(p, X_train, Y_train_onehot, model)

    # set up optimizer and freeze appropriate layers
    model, optimizer = optimization.freeze_and_set_lr(p, model, it=0)
    def reg_init(p):
        if p.lambda_reg == 0:
            return None
        
        # load the gan
        gan_dir = '/accounts/projects/vision/chandan/gan/mnist_dcgan'
        sys.path.insert(1, gan_dir)
        from dcgan import Discriminator
        D = Discriminator(ngpu=1 if torch.cuda.is_available() else 0).to(device)
        D.load_state_dict(torch.load(oj(gan_dir, 'weights/netD_epoch_99.pth'), map_location=device))
        D = D.eval()
        return D
    
    def reg(p, it, model, D, device):
        if p.lambda_reg == 0:
            return 0
            
        exs = model.exs.reshape(model.exs.shape[0], 1, 28, 28) # mnist-specific
        outputs = D(exs)

        # discriminator outputs 1 for real, 0 for fake
        loss = p.lambda_reg * torch.sum(1 - outputs)
        return loss
    
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    if 'linear' in p.dset:
        criterion = nn.MSELoss()
    reg_model = reg_init(p)

    # things to record
    s = S(p)
    s.weight_names = models.get_weight_names(model)
    if p.siamese:
        s.exs = model.exs.data.cpu().numpy()

        
    # run
    print('training...')
    for i, it in enumerate(tqdm(range(0, p.num_iters))):
        
        # calc stats and record
        s.losses_train[it], s.accs_train[it], s.confidence_unn_train[it], s.confidence_norm_train[it], s.margin_unn_train[it], s.margin_norm_train[it] = stats.calc_loss_acc_margins(train_loader, p.batch_size, use_cuda, model, criterion, p.dset)
        s.losses_test[it], s.accs_test[it], s.confidence_unn_test[it], s.confidence_norm_test[it], s.margin_unn_test[it], s.margin_norm_test[it] = stats.calc_loss_acc_margins(test_loader, p.batch_size, use_cuda, model, criterion, p.dset, print_loss=True)
        
        # record weights
        weight_dict = deepcopy({x[0]:x[1].data.cpu().numpy() for x in model.named_parameters()})
        s.weights_first10[p.its[it]] = deepcopy(model.state_dict()[s.weight_names[0]][:20].cpu().numpy())            
        s.weight_norms[p.its[it]] = stats.layer_norms(model.state_dict())
        if it % p.save_all_weights_freq == 0 or it == p.num_iters - 1 or it == 0 or (it < p.num_iters_small and it % 2 == 0): # save first, last, jumps
            s.weights[p.its[it]] = weight_dict 
            if not p.use_conv:
                s.mean_max_corrs[p.its[it]] = stats.calc_max_corr_input(X_train, Y_train_onehot, model)
            
        if p.save_singular_vals:
            # weight singular vals
            s.singular_val_dicts.append(get_singular_vals_from_weight_dict(weight_dict))   
            s.singular_val_dicts_cosine.append(get_singular_vals_kernels(weight_dict, 'cosine'))
            s.singular_val_dicts_rbf.append(get_singular_vals_kernels(weight_dict, 'rbf'))
            s.singular_val_dicts_lap.append(get_singular_vals_kernels(weight_dict, 'laplacian'))            
            
            # activations singular vals
            act_var_dicts = calc_activation_dims(use_cuda, model, train_loader.dataset, test_loader.dataset, calc_activations=p.calc_activations)
            s.act_singular_val_dicts_train.append(act_var_dicts['train']['pca'])
            s.act_singular_val_dicts_test.append(act_var_dicts['test']['pca'])
            s.act_singular_val_dicts_train_rbf.append(act_var_dicts['train']['rbf'])
            s.act_singular_val_dicts_test_rbf.append(act_var_dicts['test']['rbf'])        
        
        # reduced model
        if p.save_reduce:
            model_r = reduce_model(model)
            s.losses_train_r[it], s.accs_train_r[it] = stats.calc_loss_acc_margins(train_loader, p.batch_size, use_cuda, model_r, criterion, p.dset)[:2]
            s.losses_test_r[it], s.accs_test_r[it] = stats.calc_loss_acc_margins(test_loader, p.batch_size, use_cuda, model_r, criterion, p.dset)[:2]
        
        # training
        for batch_idx, (x, target) in enumerate(train_loader):
            optimizer.zero_grad()
            x = x.to(device)
            target = target.to(device)
            x, target = Variable(x), Variable(target)
            out = model(x)
            loss = criterion(out, target) + reg(p, it, model, reg_model, device)
            loss.backward()
            optimizer.step()
            
            # don't go through whole dataset
            if batch_idx > len(train_loader) / p.saves_per_iter and it <= p.saves_per_iter * p.saves_per_iter_end + 1:
                break
                
        # set lr / freeze
        if it - p.num_iters_small in p.lr_ticks:
            model, optimizer = optimization.freeze_and_set_lr(p, model, it)
            
        if it % p.save_all_freq == 0:
            save(out_name, p, s)
            
        # check for need to flip dset
        if 'flip' in p.dset and it == p.num_iters // 2:
            print('flipped dset')
            s.flip_iter = p.num_iters // 2 # flip_iter tells when dset flipped
            train_loader, test_loader = data.get_data_loaders(p, it=s.flip_iter)
            X_train, Y_train_onehot = data.get_XY(train_loader)
            if p.flip_freeze:
                p.freeze = 'last'
                model, optimizer = optimization.freeze_and_set_lr(p, model, it)
        elif 'permute' in p.dset and it > 0 and p.its[it] % p.change_freq == 0:
            s.permute_rng.append(int(p.its[it]))
            train_loader, test_loader = data.get_data_loaders(p, it=s.permute_rng[-1])
            X_train, Y_train_onehot = data.get_XY(train_loader)
            
            
    save(out_name, p, s)
        

if __name__ == '__main__':
    t0 = time.time()
    from params_vision import p
    
    # set params
    for i in range(1, len(sys.argv), 2):
        t = type(getattr(p, sys.argv[i]))
        if sys.argv[i+1] == 'True':
            setattr(p, sys.argv[i], t(True))            
        elif sys.argv[i+1] == 'False':
            setattr(p, sys.argv[i], t(False))
        else:
            setattr(p, sys.argv[i], t(sys.argv[i+1]))
    p.its = np.hstack((1.0 * np.arange(p.num_iters_small) / p.saves_per_iter, p.saves_per_iter_end + np.arange(p.num_iters - p.num_iters_small)))
    
    print('fname ', p._str(p))
    for key, val in p._dict(p).items():
        print('  ', key, val)
    print('starting...')
    fit_vision(p)
    
    print('success! saved to ', p.out_dir, 'in ', time.time() - t0, 'sec')