import numpy as np
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
import models

def freeze_and_set_lr(p, model, it):
    # optimization
    if p.freeze == 'first':
#             print('freezing all but first...')
        for name, param in model.named_parameters():
            if ('fc1' in name or 'fc.0' in name or 'conv1' in name):
                param.requires_grad = True 
            else:
                param.requires_grad = False
            print(name, param.requires_grad)
    elif p.freeze == 'last':
#             print('freezing all but last...')
        for name, param in model.named_parameters():
            if 'fc.' + str(p.num_layers - 1) in name:
                param.requires_grad = True 
            else:
                param.requires_grad = False
            print(name, param.requires_grad)   
    elif p.freeze == 'progress_first' or p.freeze == 'progress_last':
#             print('it', it, p.num_iters_small, p.lr_step)
        num = max(0, (it - p.num_iters_small) // p.lr_step) # number of ticks so far (at least 0)
        num = min(num, p.num_layers - 1) # (max is num layers - 1)
        if p.freeze == 'progress_first':
            s = 'fc.' + str(num) 
        elif p.freeze == 'progress_last':
            s = 'fc.' + str(p.num_layers - 1 - num)

#             print('progress', 'num', num, 'training only', s)                
        for name, param in model.named_parameters():
            if s in name:
                param.requires_grad = True
            else:
                param.requires_grad = False

    # needs to work on the newly frozen params
#         print('it', it, 'lr', p.lr * p.lr_ticks[max(0, it - p.num_iters_small)])
    if p.optimizer == 'sgd':    
        optimizer = optim.SGD(filter(lambda p: p.requires_grad, model.parameters()), lr=p.lr * p.lr_ticks[max(0, it - p.num_iters_small)])
    elif p.optimizer == 'adam':
        optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=p.lr * p.lr_ticks[max(0, it - p.num_iters_small)])    

    return model, optimizer