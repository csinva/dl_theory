class p:
    # data parameters
    N = 1000 # N is number of points
    # means = [0, 20, 40] # means of gaussian data 
    #sds = [1, 1, 1] # sds of data
    
    # small data
    # means = [[-.5], [.25], [1.]] # means of gaussian data
    #sds = [[.1], [.1], [.1]] # sds of data
    
    # centered data
    means = [[-1., -1., -1., -1, -1, -1], [0, 0, 0, 0, 0, 0], [1., 1., 1., 1., 1., 1.]] # means of gaussian data
    sds = [[.1], [.1], [.1]] # sds of data
    
    
    # big data
    
    labs = [0, 1, 0] # labels of these gaussians
    batch_size = N
    
    # model parameters
    d_in = len(means[0]) # input dim (should be 1)
    hidden1 = 10
    d_out = 2 # number of classes (should be 2)
    num_layers = 2
    
    # fitting paramters
    lr = 1e-3
    num_iters = int(2e3)
    step_size_optimizer = 500
    gamma_optimizer = 0.5
    loss_func = 'cross-entropy' # cross-entropy or mse
    init = 'data-driven' # data-driven
    
    # random seed
    seed = 2
    
    # saving
    out_dir = '/scratch/users/vision/chandan/dl_theory/sweep_init_d=3_centered' # sweep_init_large, sweep_init_small, sweep_init_centered, sweep_init_d=3_centered
    
#     out_dir = '/accounts/projects/binyu/raaz.rsk/dl/dl_theory/data/large_mean/sweep_seed_and_hidden1/large_h'
#     out_dir = '/accounts/projects/binyu/raaz.rsk/dl/dl_theory/data'
#     out_dir = '/accounts/projects/binyu/raaz.rsk/dl/dl_theory/data/small_mean/cross_entropy'
    # out_dir = '/accounts/projects/binyu/raaz.rsk/dl/dl_theory/data/large_mean/cross_entropy'
    
    def _str(self):
        s = '___'.join("%s=%s" % (attr, val) for (attr, val) in vars(p).items()
                       if not attr.startswith('_') and not attr.startswith('out'))
        return s.replace('/', '')[:251] # filenames must fit in byte 
    
    def _dict(self):
        return {attr: val for (attr, val) in vars(p).items()
                 if not attr.startswith('_')}
