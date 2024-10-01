#########################################################
#
# Postprocessing python script
#
# Copyright: UW Computational Mechanics Group
#            Pedro Arduino
#
# Participants: Alborz Ghofrani
#               Long Chen
#
#-------------------------------------------------------

import numpy as np
import matplotlib.pyplot as plt

from respSpectra import resp_spectra


def plot_acc(ndof=2):
    """
    Plot acceleration time history and response spectra
    """
    acc = np.loadtxt('acceleration.out')
    time = acc[:, 0]
    acc = np.delete(acc, 0, 1)
    # Bandaid to remove last 2 nodes associated with dashpot (not for all Openees) 
    #acc = acc[:,0:-4]
    
    [nstep, temp] = acc.shape
    nnode = int(temp/ndof)
    a = acc.reshape(nstep, ndof, nnode, order="F") / 9.81
    
    # plot acceleration time history
    plt.figure() 
    plt.plot(time, a[:, 0, nnode-1])
    plt.grid()
    plt.xlabel('time (sec)')
    plt.ylabel('acceleration (g)')
    plt.savefig('surfaceAccel.eps')
    plt.savefig('surfaceAccel.png')
       
    # build response spectra
    [p, umax, vmax, amax] = resp_spectra(a[:, 0, nnode-1], time[-1], nstep)
    
    # response spectra on log-linear plot
    plt.figure()
    plt.subplot(3, 1, 1)
    plt.semilogx(p, amax)
    plt.grid()
    plt.ylabel('$S_a (g)$')
    plt.subplot(3, 1, 2)
    plt.semilogx(p, vmax)
    plt.grid()
    plt.ylabel('$S_v (m/s)$')
    plt.subplot(3, 1, 3)
    plt.semilogx(p, umax)
    plt.grid()
    plt.ylabel('$S_d (m)$')
    plt.xlabel('$Period (s)$')
    plt.savefig('logSpectra.eps')
    plt.savefig('logSpectra.png')

if __name__ == "__main__":
    plot_acc()
