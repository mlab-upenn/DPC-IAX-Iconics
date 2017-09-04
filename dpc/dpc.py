# -*- coding: utf-8 -*-
"""
Created on Thu Jun 29 17:57:14 2017

@author: Achin Jain (achinj@seas.upenn.edu)

DPC toolbox

"""

from __future__ import division

import warnings
import numpy as np
import tensorflow as tf
tf.logging.set_verbosity(tf.logging.ERROR)
import casadi as cs
from cvxopt import matrix, solvers

from sklearn.ensemble.forest import _generate_sample_indices

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import gridspec

class gaussian_process:
    
    def __init__(self, model, normalizer_c, normalizer_d, normalizer_y,
                 features_c, features_d, output, 
                 n_control, n_disturbance):
        self.model = model
        self.normalizer_c = normalizer_c
        self.normalizer_d = normalizer_d
        self.normalizer_y = normalizer_y
        self.features_c = features_c
        self.features_d = features_d
        self.output = output
        self.n_control = n_control
        self.n_disturbance = n_disturbance
        self.n_features = n_control + n_disturbance
        self.n_samples = model.X_train_.shape[0]
        self.LLinv = np.linalg.inv(np.dot(model.L_,model.L_.T))
    
    def predict(self, X_control, X_diturbance):
        
        y_mean = []
        y_std = []
        return y_mean, y_std
        
    def control(self, X_disturbance, y_track):
        
        # functions in casadi data structures
        def RBF(n):
            
            if n==1:
                sX = 1
                sY = n
                n_features = self.n_features
                X = cs.SX.sym('X', sX, n_features)
                Y = cs.SX.sym('Y', sY, n_features)
                length_scale = cs.SX.sym('l', 1, n_features)
    
                X_ = X / cs.repmat(length_scale, sX , 1)
                Y_ = Y / cs.repmat(length_scale, sY , 1)
                dist = cs.SX.zeros((sX, sY)) 
                for i in xrange(0, sX):
                    for j in xrange(0, sY):
                        dist[i, j] = cs.sum2((X_[i, :] - Y_[j, :])**2)
                K = cs.exp(-.5 * dist)            
                self.RBF1 = cs.Function('RBF1', [X, Y, length_scale], [K])
                
            else:
                sX = 1
                sY = n
                n_features = self.n_features
                X = cs.SX.sym('X', sX, n_features)
                Y = self.model.X_train_
                length_scale = cs.SX.sym('l', 1, n_features)
    
                X_ = X / cs.repmat(length_scale, sX , 1)
                Y_ = Y / cs.repmat(length_scale, sY , 1)
                dist = cs.SX.zeros((sX, sY)) 
                for i in xrange(0, sX):
                    for j in xrange(0, sY):
                        dist[i, j] = cs.sum2((X_[i, :] - Y_[j, :])**2)
                K = cs.exp(-.5 * dist)
                self.RBFn = cs.Function('RBFn', [X, length_scale], [K])
        
        
        def Constant(n):
            
            sX = 1
            sY = n
            K = cs.SX.ones((sX, sY))
            return K
        
        def RationalQuadratic(n):
            
                        
            if n==1:
                sX = 1
                sY = n
                X = cs.SX.sym('X', sX, self.n_features)
                Y = cs.SX.sym('Y', sY, self.n_features)
                alpha= cs.SX.sym('a')
                length_scale = cs.SX.sym('l')
                
                dist = cs.SX.zeros((sX, sY)) 
                for i in xrange(0, sX):
                    for j in xrange(0, sY):
                        dist[i, j] = cs.sum2((X[i, :] - Y[j, :])**2)
                        
                K = (1 + dist / (2 * alpha * length_scale ** 2)) ** (-alpha)
                self.RationalQuadratic1 = cs.Function('RQ1', [X, Y, alpha, length_scale], [K])
                
            else:
                sX = 1
                sY = n
                X = cs.SX.sym('X', sX, self.n_features)
                Y = self.model.X_train_
                alpha= cs.SX.sym('a')
                length_scale = cs.SX.sym('l')
                
                dist = cs.SX.zeros((sX, sY)) 
                for i in xrange(0, sX):
                    for j in xrange(0, sY):
                        dist[i, j] = cs.sum2((X[i, :] - (Y[j, :].reshape(1,-1)))**2)
                        
                K = (1 + dist / (2 * alpha * length_scale ** 2)) ** (-alpha)
                self.RationalQuadraticn = cs.Function('RQn', [X, alpha, length_scale], [K])
        
        def linsolve_lower(A, b):
    
            n = A.shape[0]
            x = cs.SX.zeros(n,1)
            for i in range(n):
                temp = 0
                for j in range(i):
                    temp = temp + A[i,j]*x[j]
                x[i] = (b[i] - temp)/A[i,i]
            return x

        def linsolve_uppper(A, b):
            
            n = A.shape[0]
            x = cs.SX.zeros(n,1)
            for i in range(n-1,-1,-1):
                temp = 0
                for j in range(n-1,i,-1):
                    temp = temp + A[i,j]*x[j]
                x[i] = (b[i] - temp)/A[i,i]
            return x
    
        def cost_function(y_mean, y_std, y_track):
            
            J = (y_mean - y_track)**2 + 1*y_std
            return J

        
        # model in casadi data structures
        def predict():
            
            Xc = cs.SX.sym('control', self.n_control, 1)
            Xd = cs.SX.sym('disturbance', self.n_disturbance, 1)
            
            X1 = cs.vertcat(Xd, Xc).T
            X2 = cs.DM(self.model.X_train_)
            
            RBF_length_scale = self.model.kernel_.get_params()['k1__k1__k2__length_scale'].reshape(1,-1)
            RBF_constant = self.model.kernel_.get_params()['k1__k1__k1__constant_value']
            Constant_constant = self.model.kernel_.get_params()['k1__k2__constant_value']
            RQ_constant = self.model.kernel_.get_params()['k2__k1__constant_value']
            RQ_alpha = self.model.kernel_.get_params()['k2__k2__alpha']
            RQ_length_scale = self.model.kernel_.get_params()['k2__k2__length_scale']
            
            # mean
            K1 = RBF_constant*self.RBFn(X1, RBF_length_scale)
            K2 = Constant_constant*Constant(self.n_samples)
            K3 = RQ_constant*self.RationalQuadraticn(X1, RQ_alpha, RQ_length_scale)
            K = (K1 + K2) * K3
            y_mean = cs.mtimes(K, self.model.alpha_) + self.model.y_train_mean
            y_mean = 0.5*(y_mean+1)*(self.normalizer_y.data_max_- self.normalizer_y.data_min_) + self.normalizer_y.data_min_
            
            # variance: solve L L^T x = K^T        
#            v = linsolve_lower(self.model.L_, K.T)    
#            x = linsolve_uppper(self.model.L_.T, v)
            x = cs.mtimes(self.LLinv,K.T)
            
            K1 = RBF_constant*self.RBF1(X1, X1, RBF_length_scale)
            K2 = Constant_constant*Constant(1)
            K3 = RQ_constant*self.RationalQuadratic1(X1, X1, RQ_alpha, RQ_length_scale)
            K_ = (K1 + K2) * K3
            y_var = K_ - cs.mtimes(K, x)
            y_var = cs.fmax(0, y_var)
            y_std = y_var**0.5
            y_std = y_std*(self.normalizer_y.data_max_-self.normalizer_y.data_min_)/2
            
            predict = cs.Function('predict', [Xc, Xd], [y_mean, y_std])
            self.predict_ = predict
    
        
        def optimize(nlp, args):
            
            opts = {"ipopt.tol":1e-5, "ipopt.print_level":0, 
                    "print_time":False, "expand":True,}
            solver = cs.nlpsol("solver", "ipopt", nlp, opts)
            res = solver(**args)
            u_opt = np.double(res['x']).reshape(1,-1)
            u = self.normalizer_c.inverse_transform(u_opt).flatten()          
            
            return u
            
        # optimization
        X_disturbance = self.normalizer_d.transform(X_disturbance)
        n_control = self.n_control
        Xc = cs.SX.sym('U', n_control, 1)
        Xd = cs.DM(X_disturbance)
        
        if not hasattr(self, 'predict_'):
            RBF(1)
            RBF(self.n_samples)
            RationalQuadratic(1)
            RationalQuadratic(self.n_samples)
            predict()
        
        y_mean, y_std = self.predict_(Xc, Xd)
        J = cost_function(y_mean, y_std, y_track)    
        nlp = {'x': Xc, 'f': J}
        args = {"lbx" : cs.repmat(-1.0, n_control, 1), 
                "ubx": cs.repmat(1.0, n_control, 1)}
        u = optimize(nlp, args)
        
        return u
        
    def plot_closed_loop(self, y_true, y_sim, y_mean, y_std):
    
#        sns.set_style('white')
        n_samples = y_true.shape[0]
        plt.figure(figsize=(11, 8))
        gs = gridspec.GridSpec(3,1)
        
        
        plt.subplot(gs[:-1,:])
        xplot = np.linspace(1, n_samples, n_samples)
        plt.plot(xplot, y_mean, ls='-', lw=2, zorder=9, 
                 label='mean prediction')
        plt.plot(xplot, y_sim, '#990000', ls='-', lw=1.5, zorder=9, 
                 label='closed loop simulation')
        plt.plot(xplot, y_true, 'y', ls='--', lw=1.5, zorder=9, 
                 label='tracking signal')
        plt.fill_between(xplot, (y_mean+2*y_std), (y_mean-2*y_std),
                         alpha=0.2, color='m', label='95% confidence interval')
        plt.legend(loc=0)
        plt.title('closed loop simulation vs prediction')    
        plt.xlim(0, n_samples)
        plt.ylim(0, 450e3)
        
        plt.subplot(gs[2,:])
        xplot = np.linspace(1, n_samples, n_samples)
        plt.plot(xplot, np.abs(y_true-y_sim), '#990000', 
                 ls='-', lw=1.5, zorder=9)
        plt.fill_between(xplot, 0*xplot, 2*y_std,
                         alpha=0.2, color='m')
        plt.title("model error and predicted variance")
        plt.xlim(0, n_samples)
        
        plt.tight_layout()    
        plt.show()
        
    def plot_control(self, inputs):
        
        plt.figure()
        for i in range(self.n_control):
            plt.plot(inputs[i], label = self.features_c.keys()[i])
        plt.ylim([np.min(np.min(inputs))-5,5+np.max(np.max(inputs))])
        plt.legend(loc=0)
        plt.show()


class random_forest:
    
    def __init__(self, model, features_c, features_d, output, 
                 n_control, n_disturbance, n_samples=None,
                 linear_models=None):
        self.model = model      
        self.features_c = features_c
        self.features_d = features_d
        self.output = output
        self.n_control = n_control
        self.n_disturbance = n_disturbance
        self.n_features = n_control + n_disturbance
        self.n_samples = n_samples
        self.linear_models = linear_models
        
    def train_linearmodels(self, Xd_train, Xc_train, y_train, **kwargs):
        
        """
        kwargs = {"lin_coeffs":[0,-1,-1,-1,-1,-1]}
        
        """
        
        def calculate_inbag(forest, n_samples):
            n_trees = forest.n_estimators
            inbag = np.zeros((n_samples, n_trees))
            for t_idx in range(n_trees):
                sample_idx = _generate_sample_indices(forest.estimators_[t_idx].random_state, 
                                                      n_samples)
                inbag[:, t_idx] = np.bincount(sample_idx, minlength=n_samples)
            return inbag

        inbag_all = calculate_inbag(self.model, self.n_samples)
        leaves = self.model.apply(Xd_train)
        linearmodels = {}
        n_trees = self.model.n_estimators
        
        for idt in range(n_trees):
            unique_leaves = set(leaves[:,idt])
            leafmodels = {}
            
            for idl in unique_leaves:
                indices = [i for i, x in enumerate(leaves[:,idt]) if x == idl]
                indices_inbag = []
                
                for idi, val in enumerate(indices):
                    if inbag_all[val,idt]>0:
                        indices_inbag.append(val)
                # len(inbag_all[inbag_all[indices,0]>0,0]) # no of distict samples
                X = Xc_train[indices_inbag,:]
                y = y_train[indices_inbag]
                # P = matrix(2*np.dot(np.transpose(X),X))
                # q = matrix(-2*np.dot(np.transpose(X),y))
                P = 2*matrix(X).T*matrix(X)                
                q = -2*matrix(X).T*matrix(y)
                
                solvers.options['show_progress'] = False
                if "lin_coeffs" in kwargs:
                    Aineq = matrix(np.diag(kwargs['lin_coeffs']), tc='d')
                    bineq = matrix(np.zeros(shape=(1+self.n_control,1)), tc='d')                    
                    sol = solvers.qp(P, q, Aineq, bineq)
                else:
                    warnings.warn('No lin_ceoffs provided, solving unonstrained linear regression in the leaves.')
                    sol = solvers.qp(P, q)

                leafmodels[idl] = np.transpose(np.array(sol['x']))
            linearmodels[idt] = leafmodels
            
            if np.mod(idt+1,10)==0:
                print('done: %s%%' %( np.round( np.int(100*(idt+1)/n_trees),0 )))
            elif(idt==n_trees-1):
                print('done: 100%')
                
        return linearmodels
   
        
    def find_linearmodels(self, linearmodels, x):
        
        leaves = self.model.apply(x)
        numcoeff = (linearmodels[0][set(linearmodels[0]).pop()]).shape[1]
        coeff = np.zeros(shape=(leaves.shape[0],numcoeff))
        for iddata in range(leaves.shape[0]):
            for idt in range(leaves.shape[1]):
                coeff[iddata] = linearmodels[idt][leaves[iddata,idt]] + coeff[iddata]
            coeff[iddata] = coeff[iddata]/leaves.shape[1]
        return coeff
            
    def control(self, X_disturbance, y_track, **kwargs):
        
        def predict(Xd):
            
            Xc = cs.SX.sym('control', self.n_control, 1)            
            coeffs = self.find_linearmodels(self.linear_models, Xd)
            Xc_leaf = cs.vertcat(1, Xc).T 
            y_pred = cs.sum2(coeffs*Xc_leaf)
            
            predict = cs.Function('predict', [Xc], [y_pred])            
            self.predict_ = predict            
            
        def cost_function(y_mean, y_track):
            
            J = (y_mean - y_track)**2
            return J
        
        def optimize(nlp, **args):
            
            opts = {"ipopt.tol":1e-5, "ipopt.print_level":0, 
                    "print_time":False, "expand":True,}
            solver = cs.nlpsol("solver", "ipopt", nlp, opts)            
            if hasattr(self, 'previous_input'):
                args['lbx'] = np.maximum(args['lbx'], self.previous_input-np.inf)
                args['ubx'] = np.minimum(args['ubx'], self.previous_input+np.inf)
            res = solver(**args)
            u_opt = np.double(res['x']).reshape(1,-1)      
            u = u_opt.ravel()
            self.previous_input = u            
            
            return u
            
        # optimization
        n_control = self.n_control
        Xc = cs.SX.sym('U', n_control, 1)
        Xd = X_disturbance
        
        predict(Xd) 
        y_mean = self.predict_(Xc)
        J = cost_function(y_mean, y_track)    
        nlp = {'x': Xc, 'f': J}
            
        u = optimize(nlp, **kwargs)
        
        return u
            
    def plot_closed_loop(self, y_true, y_sim, y_pred):
    
#        sns.set_style('white')
        n_samples = y_true.shape[0]
        plt.figure(figsize=(11, 8))
        gs = gridspec.GridSpec(3,1)
        
        
        plt.subplot(gs[:-1,:])
        xplot = np.linspace(1, n_samples, n_samples)
        plt.plot(xplot, y_pred, ls='-', lw=2, zorder=9, 
                 label='prediction')
        plt.plot(xplot, y_sim, '#990000', ls='-', lw=1.5, zorder=9, 
                 label='closed loop simulation')
        plt.plot(xplot, y_true, 'y', ls='--', lw=1.5, zorder=9, 
                 label='tracking signal')

        plt.legend(loc=0)
        plt.title('closed loop simulation vs prediction')    
        plt.xlim(0, n_samples)
        plt.ylim(0, 450e3)
        
        plt.subplot(gs[2,:])
        xplot = np.linspace(1, n_samples, n_samples)
        plt.plot(xplot, np.abs(y_true-y_sim), '#990000', 
                 ls='-', lw=1.5, zorder=9)
        plt.title("model error")
        plt.xlim(0, n_samples)
        
        plt.tight_layout()    
        plt.show()
        
    def plot_control(self, inputs):
        
        plt.figure()
        for i in range(self.n_control):
            plt.plot(inputs[i], label = self.features_c.keys()[i])
        plt.ylim([np.min(np.min(inputs))-5,5+np.max(np.max(inputs))])
        plt.legend(loc=0)
        plt.show()
        
    def plot_true_predicted(self, y_pred_noleaf, y_pred_leaf, y_true):
    
        sns.set()
        plt.figure()
        l = y_true.shape[0]
        plt.plot(range(l), y_true, linewidth=2, label='true')
        plt.plot(range(l), y_pred_leaf, linewidth=2, label='forest + linear model')
        plt.plot(range(l), y_pred_noleaf, linewidth=2, label='only forest', linestyle='--')
        plt.xlabel('time index')
        plt.ylabel(self.output.keys()[0])
        plt.show()
        plt.legend(loc=1)
        

class neural_net:
    
    def __init__(self, path, normalizer_c, normalizer_d, normalizer_y,
                 features_c, features_d, output, 
                 n_control, n_disturbance):
        self.path = path
        self.normalizer_c = normalizer_c
        self.normalizer_d = normalizer_d
        self.normalizer_y = normalizer_y
        self.features_c = features_c
        self.features_d = features_d
        self.output = output
        self.n_control = n_control
        self.n_disturbance = n_disturbance
        self.n_features = n_control + n_disturbance
        
        
    def find_linearmodels(self, X_disturbance):
        
        with tf.Session() as sess:
            saver = tf.train.import_meta_graph(self.path + '.meta')
            saver.restore(sess, self.path)
            
            graph = tf.get_default_graph()
            # ypred_op = graph.get_tensor_by_name("output/add_1:0")
            weights_op = graph.get_tensor_by_name("output/add:0")
            bias_op = graph.get_tensor_by_name("output/biases_1:0")
            # Xc = graph.get_tensor_by_name("inputXc:0")
            Xd = graph.get_tensor_by_name("inputXd:0")
            # y = graph.get_tensor_by_name("outputy:0")
            weights, bias = sess.run([weights_op, bias_op], 
                                 feed_dict={Xd: X_disturbance})
            coeff = np.concatenate((bias, weights.flatten()), axis=0).reshape(1,-1)
            
        return coeff
            
    def control(self, y_track, coeffs):
        
        def predict(coeffs):
            
            Xc = cs.SX.sym('control', self.n_control, 1)            
#            coeffs = self.find_linearmodels(Xd)
            Xc_ = cs.vertcat(1, Xc).T 
            y_pred = cs.sum2(coeffs*Xc_)
            y_pred = 0.5*(y_pred+1)*(self.normalizer_y.data_max_- self.normalizer_y.data_min_) + self.normalizer_y.data_min_
            
            predict = cs.Function('predict', [Xc], [y_pred])            
            self.predict_ = predict            
            
        def cost_function(y_mean, y_track):
            
            J = (y_mean - y_track)**2
            return J
        
        def optimize(nlp, args):
            
            opts = {"ipopt.tol":1e-5, "ipopt.print_level":0, 
                    "print_time":False, "expand":True,}
            solver = cs.nlpsol("solver", "ipopt", nlp, opts)            
            if hasattr(self, 'previous_input'):
                args['lbx'] = np.maximum(args['lbx'], self.previous_input-np.inf)
                args['ubx'] = np.minimum(args['ubx'], self.previous_input+np.inf)
            res = solver(**args)
            u_opt = np.double(res['x']).reshape(1,-1)      
            u = self.normalizer_c.inverse_transform(u_opt).flatten()  
            self.previous_input = u            
            
            return u
            
        # optimization
#        X_disturbance = self.normalizer_d.transform(X_disturbance)
        n_control = self.n_control
        Xc = cs.SX.sym('U', n_control, 1)
#        Xd = X_disturbance
        
        predict(coeffs) 
        y_mean = self.predict_(Xc)
        J = cost_function(y_mean, y_track)    
        nlp = {'x': Xc, 'f': J}
        lbx = np.array([22,24,22,12,3.7]).reshape(1,-1)
        lbx = self.normalizer_c.transform(lbx)
        ubx = np.array([26,28,26,14,9.7]).reshape(1,-1)
        ubx = self.normalizer_c.transform(ubx)
        args = {"lbx" : lbx, 
                "ubx" : ubx}
        u = optimize(nlp, args)
        
        return u
            
    def plot_closed_loop(self, y_true, y_sim, y_pred):
    
#        sns.set_style('white')
        n_samples = y_true.shape[0]
        plt.figure(figsize=(11, 8))
        gs = gridspec.GridSpec(3,1)
        
        
        plt.subplot(gs[:-1,:])
        xplot = np.linspace(1, n_samples, n_samples)
        plt.plot(xplot, y_pred, ls='-', lw=2, zorder=9, 
                 label='prediction')
        plt.plot(xplot, y_sim, '#990000', ls='-', lw=1.5, zorder=9, 
                 label='closed loop simulation')
        plt.plot(xplot, y_true, 'y', ls='--', lw=1.5, zorder=9, 
                 label='tracking signal')

        plt.legend(loc=0)
        plt.title('closed loop simulation vs prediction')    
        plt.xlim(0, n_samples)
        plt.ylim(0, 450e3)
        
        plt.subplot(gs[2,:])
        xplot = np.linspace(1, n_samples, n_samples)
        plt.plot(xplot, np.abs(y_true-y_sim), '#990000', 
                 ls='-', lw=1.5, zorder=9)
        plt.title("model error")
        plt.xlim(0, n_samples)
        
        plt.tight_layout()    
        plt.show()
        
    def plot_control(self, inputs):
        
        plt.figure()
        for i in range(self.n_control):
            plt.plot(inputs[i], label = self.features_c.keys()[i])
        plt.ylim([np.min(np.min(inputs))-5,5+np.max(np.max(inputs))])
        plt.legend(loc=0)
        plt.show()
        
    def plot_true_predicted(self, y_pred_noleaf, y_pred_leaf, y_true):
    
        sns.set()
        plt.figure()
        l = y_true.shape[0]
        plt.plot(range(l), y_true, linewidth=2, label='true')
        plt.plot(range(l), y_pred_leaf, linewidth=2, label='forest + linear model')
        plt.plot(range(l), y_pred_noleaf, linewidth=2, label='only forest', linestyle='--')
        plt.xlabel('time index')
        plt.ylabel(self.output.keys()[0])
        plt.show()
        plt.legend(loc=1)