%% Setup
do_followup_viz = false;
% To run this demo, you will need a stack of movie frames stored as a 4D 
% (X x Y x Color x Time) array.
% If you have your own stimuli, you will need to modify this variable:
% fname = 'nishimoto_2011_val_1min_uint8.mat';
fname = '/scratch/users/vision/data/gallant/vim_2_crcns/Stimuli.mat'

% add relevant paths
if ~exist('preprocColorSpace_GetMetaParams','file')
    addpath('../');
    addpath('../utils/');
end

%% Load images
try
    d = load(fname);
catch err_msg
    fprintf(['You may need to modify the "fname" variable in ComputeMotionEnergy.m\nto point to a .mat file with movie frames in it!\n' ...
        'A sample file can be downloaded at https://www.dropbox.com/s/1531dr5u7767wat/nishimoto_2011_val_1min_uint8.mat?dl=0\n'])
    throw(err_msg);
end
% the field d.S is an array that is (96 x 96 x 3 x 900); (X x Y x Color x
% Images).  The images are stored as 8-bit integer arrays (no decimal
% places, with pixel values from 0-255). These should be converted to
% floating point decimals from 0-1:
S  = single(d.st)/255;
% print S.size

%% Preprocessing
% Conver to grayscale (luminance only)
% The argument 1 here indicates a pre-specified set of parameters to feed
% to the preprocColorSpace function to convert from RGB images to 
% luminance values by converting from RGB to L*A*B colorspace and then
% keeping only the luminance channel. (You could also use matlab's
% rgb2gray.m function, but this is more principled.) Inspect cparams to see
% what those parameters are.
cparams = preprocColorSpace_GetMetaParams(1);
[S_lum, cparams] = preprocColorSpace(S, cparams);

%% Gabor wavelet processing
% Process with Gabor wavelets
% The numerical argument here specifies a set of parameters for the
% preprocWavelets_grid function, that dictate the locations, spatial
% frequencies, phases, and orientations of Gabors to use. 2 specifies Gabor
% wavelets with three different temporal frequencies (0, 2, and 4 hz),
% suitable for computing motion energy in movies.  
gparams = preprocWavelets_grid_GetMetaParams(2);
[S_gab, gparams] = preprocWavelets_grid(S_lum, gparams);

%% Optional additions
% Compute log of each channel to scale down very large values
nlparams = preprocNonLinearOut_GetMetaParams(1);
[S_nl, nlparams] = preprocNonLinearOut(S_gab, nlparams);

% Downsample data to the sampling rate of your fMRI data (the TR)
dsparams = preprocDownsample_GetMetaParams(1); % for TR=1; use (2) for TR=2
[S_ds, dsparams] = preprocDownsample(S_nl, dsparams);

% Z-score each channel
nrmparams = preprocNormalize_GetMetaParams(1);
[S_fin, nrmparams] = preprocNormalize(S_ds, nrmparams);

save mot_energy_feats_st.mat S_fin nrmparams

%% Display output
if do_followup_viz
    % Simple feature size
    disp('Final matrix size (images x features):')
    disp(size(S_fin));
    % show image of feature matrix
    figure(1);clf;
    imagesc(S_fin);
    ylabel('Time (TR)')
    xlabel('Gabor wavelet feature')
    caxis([-3,3]);
    colorbar();
    % Create examples of Gabor wavelets used for each feature
    gparams.show_or_preprocess = 0;
    [gab, pp] = preprocWavelets_grid(zeros(96,96), gparams);
    fig = figure();
    % 150th Gabor wavelet (corresponds to 150th column on x axis in plot above)
    subplot(121);
    imagesc(gab(:,:,1,150));
    caxis([-1,1])
    axis image off
    title('150th Gabor filter')
    % 1219th Gabor wavelet
    subplot(122);
    imagesc(gab(:,:,1,1219));
    caxis([-1,1])
    axis image off
    title('1219th Gabor filter')
    colormap(gray)
end
