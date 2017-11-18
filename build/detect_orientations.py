#!/usr/bin/python2 -utt
# -*- coding: utf-8 -*-
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import torch.backends.cudnn as cudnn
import time
import os
sys.path.insert(0, '/home/ubuntu/dev/opencv-3.1/build/lib')
import cv2
import math
import numpy as np
from architectures import OriNetFast, YiNet
from HandCraftedModules import OrientationDetector

PSS = 32
coef = -1.
USE_CUDA = True

model = OriNetFast(PS = PSS)
#weightd_fname = 'tanh_plain_9.pth'
#weightd_fname = 'pixels_only_checkpoint_9.pth'
#weightd_fname = 'HardNetLoss_1.pth'
#weightd_fname = 'newrot.pth'
#weightd_fname = '/home/old-ufo/dev/mods/wxbs-journal/build/!!!!!!/orinet_hn_9.pth'
#weightd_fname = '/home/old-ufo/dev/mods/wxbs-journal/build/!!!!!!/orinet_pos_9.pth'
weightd_fname = '/home/old-ufo/dev/mods/wxbs-journal/build/2222/orinet_pos_9.pth'
#weightd_fname = '/home/old-ufo/dev/mods/wxbs-journal/build/2222/orinet_hn_9.pth'

checkpoint = torch.load(weightd_fname)
model.load_state_dict(checkpoint['state_dict'])

#model = OrientationDetector(patch_size = PSS)

#PSS=28
#coef = 1.
#model = YiNet()
####weightd_fname = '/home/old-ufo/dev/benchmark-orientation/matlab/src/KeypointOrientations/GHHPoolingEF/prelearned/efsift-360'
#weightd_fname = '/home/old-ufo/dev/benchmark-orientation/matlab/src/KeypointOrientations/GHHPooling/prelearned/sift'
#model.import_weights(weightd_fname)
#model.import_weights(')

model.eval()
if USE_CUDA:
    model.cuda()

try:
    input_img_fname = sys.argv[1]
    output_fname = sys.argv[2]
except:
    print "Wrong input format. Try ./extract_hardnet_desc_from_hpatches_file.py imgs/ref.png out.txt"
    sys.exit(1)

image = cv2.imread(input_img_fname,0)
h,w = image.shape
print(h,w)

n_patches =  h/w


descriptors_for_net = np.zeros((n_patches, 1))
t = time.time()
patches = np.ndarray((n_patches, 1, PSS, PSS), dtype=np.float32)
for i in range(n_patches):
    patch =  image[i*(w): (i+1)*(w), 0:w]
    patches[i,0,:,:] = cv2.resize(patch,(PSS,PSS)) / 255.
bs = 128;
outs = []
n_batches = n_patches / bs + 1
t = time.time()
for batch_idx in range(n_batches):
    if batch_idx == n_batches - 1:
        if (batch_idx + 1) * bs > n_patches:
            end = n_patches
        else:
            end = (batch_idx + 1) * bs
    else:
        end = (batch_idx + 1) * bs
    data_a = patches[batch_idx * bs: end, :, :, :].astype(np.float32)
    data_a = torch.from_numpy(data_a)
    if USE_CUDA:
        data_a = data_a.cuda()
    data_a = Variable(data_a, volatile=True)
    # compute output
    out_a = model(data_a)
    descriptors_for_net[batch_idx * bs: end,:] = out_a.data.cpu().numpy().reshape(-1, 1)
print descriptors_for_net.shape
et  = time.time() - t
print 'processing', et, et/float(n_patches), ' per patch', weightd_fname
np.savetxt(output_fname,  coef*descriptors_for_net, delimiter=' ', fmt='%10.5f')    