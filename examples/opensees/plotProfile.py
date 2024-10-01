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

from plotStressStrain import plot_stress_strain

import numpy as np
import matplotlib.pyplot as plt


def plot_profile(ndof=2, nstraincomp=3, nstresscomp=3):
    """
    Plot maximum displacement, PGA and maximum shear strain and maximum cyclic stress ratio
    """
    nodes = np.loadtxt('nodesInfo.dat')
    disp = np.loadtxt('displacement.out')
    acc = np.loadtxt('acceleration.out')
    strain = np.loadtxt('strain.out')
    stress = np.loadtxt('stress.out')

    time = acc[:,0]
    disp = np.delete(disp, 0, 1)
    acc = np.delete(acc, 0, 1)
    strain = np.delete(strain, 0, 1)
    stress = np.delete(stress, 0, 1)

    # Bandaid to remove last 2 nodes associated with dashpot (not correct for all Openees) 
    #disp = disp[:,0:-4]
    #acc = acc[:,0:-4]
	
	# subtact base displacement
    disp = (disp.transpose() - disp[:,0]).transpose()
    maxdisp = np.amax(np.abs(disp), axis=0)
    pga = np.amax(np.abs(acc), axis=0)
    maxstrain = np.amax(np.abs(strain), axis=0)
    maxstressratio = np.amax(np.abs(stress[:, 2::nstresscomp]), axis=0)
    maxstressratio = maxstressratio / np.abs(stress[0, 1::nstresscomp])

    [nstep, temp] = strain.shape
    nelem = int(temp / nstraincomp)
    nnodes = nodes.shape[0]
	
    stress = stress.reshape(nstep, nstresscomp, nelem, order="F")
    strain = strain.reshape(nstep, nstraincomp, nelem, order="F")
    maxdisp = maxdisp.reshape(ndof, nnodes, order="F")
    pga = pga.reshape(ndof, nnodes, order="F")
    maxstrain = maxstrain.reshape(nstraincomp, nelem, order="F")

    plt.figure(figsize=(12, 6))
    plt.subplot(1, 4, 1)
    plt.plot(maxdisp[0, ::2], nodes[::2, 2])
    plt.xticks(np.arange(0.0, max(maxdisp[0, ::2]), 0.2))
    plt.grid()
    plt.xlabel('Maximum Displacement(m)')
    plt.ylabel('Elevation(m)')

    plt.subplot(1, 4, 2)
    plt.plot(pga[0, ::2] / 9.81, nodes[::2, 2])
    plt.xticks(np.arange(0.0, max(pga[0, ::2]) / 9.81, 0.2))
    plt.grid()
    plt.xlabel('PHA(g)')

    plt.subplot(1, 4, 3)
    plt.plot(maxstrain[2, :]*100.0, nodes[:-2:2, 2] + np.diff(nodes[::2, 2]))
    plt.grid()
    plt.xlabel('Maximum Shear Strain(%)')

    plt.subplot(1, 4, 4)
    plt.plot(maxstressratio, nodes[:-2:2, 2] + np.diff(nodes[::2, 2]))
    plt.xticks(np.arange(0.0, max(maxstressratio), 0.2))
    plt.grid()
    plt.xlabel('$(\\tau / \sigma_{v0})_{max} $')
    plt.savefig('profilePlot.eps')
    plt.savefig('profilePlot.png')

    plot_stress_strain(stress[:, 2, 6], strain[:, 2, 6])
	
if __name__ == "__main__":
    plot_profile()
