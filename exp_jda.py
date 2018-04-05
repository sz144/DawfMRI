#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  5 13:51:16 2018

@author: shuoz
"""

import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.svm import SVC
import load_data
from JDA.JDA import JDA
import create_domain
import pandas as pd

def cal_meanstd(alist):
    mean = np.mean(alist)
    std = np.std(alist)
    alist.append(mean)
    alist.append(std)
    return np.asarray(alist)

# init parameters
max_iter = 3
kfold = 5

# load data
data, label = load_data.load_whole_brain()
#data, label = load_data.load_ica()

# create target and source domain data
src_pos = 2
src_neg = 9
tar_pos = 3
tar_neg = 6

Xs, ys = create_domain.create(data, label, src_pos, src_neg)
Xt, yt = create_domain.create(data, label, tar_pos, tar_neg)
ns = len(ys)
nt = len(yt)


acc_all = []
auc_all = []
pred_all = []
dec_all = []

for _iter in range(1):
    # set k-fold cv
    rand_seed = (_iter + 5) * 10
    skf = StratifiedKFold(n_splits=kfold, shuffle=True, random_state= rand_seed)
    # init results
    pred = np.zeros(nt)
    dec = np.zeros(nt)
    
    # init clf
    svm = SVC(kernel='linear')
    for train, test in skf.split(Xt,yt):
        y_train = np.hstack((ys,yt[train])) #label
        Z_train = np.vstack((Xs, Xt[train]))
    
        # predict labels for test samples
        yt_ = np.zeros(nt)
        yt_[train] = yt[train]
        svm.fit(Z_train, y_train)
        yt_[test] = svm.predict(Xt[test])
        print(accuracy_score(yt[test],yt_[test]))
        # jda
        options = {"k": 100, "lmbda": 1000, "ker": 'linear', "gamma": 1.0}
        
        for i in range(max_iter):
            svm_ = SVC(C = 100, kernel='linear', max_iter = 1000)
            Z, A, phi = JDA(Xs.T, Xt.T, ys, yt_, options)
            Zs = Z[:, :ns].T
            Zt = Z[:, ns:].T
            
            Z_train = np.vstack((Zs,Zt[train]))
            svm_.fit(Z_train, y_train)
            yt_[test] = svm_.predict(Zt[test]) # update labels for test samples
            
            if i == max_iter-1:
                pred[test] = yt_[test]
                dec[test] = svm_.decision_function(Zt[test])
    acc_all.append(accuracy_score(yt,pred))
    auc_all.append(roc_auc_score(yt,dec))
    pred_all.append(pred)
    dec_all.append(dec)
    
#pred_all = np.asanyarray(pred_all)
dec_all = np.asarray(dec_all)
acc_all = cal_meanstd(acc_all)
auc_all = cal_meanstd(auc_all)
print('mean accuracy: %s'%acc_all[len(acc_all)-2])
print('mean auc: %s'%auc_all[len(auc_all)-2])
# save result
df1 = pd.DataFrame(dec_all)
df2 = pd.concat([pd.DataFrame(acc_all), pd.DataFrame(auc_all)], axis=0)

df1.to_csv("jda_%sfold_dec_%svs%swith%svs%s.csv"%(kfold, tar_pos, tar_neg, src_pos, src_neg))
df1.to_csv("jda_%sfold_acc_%svs%swith%svs%s.csv"%(kfold, tar_pos, tar_neg, src_pos, src_neg))       
