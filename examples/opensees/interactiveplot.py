"""
Create interactive plot for disp and pwp
@author: Long Chen
"""

import matplotlib.pyplot as plt
from matplotlib import gridspec
from ipywidgets import interactive
import ipywidgets as widgets
import numpy as np


def pwpplot(timeStep):
    Step = int(timeStep / 0.01) - 1
    plt.subplot(211)
    plt.plot(time, uu)
    plt.plot(time[Step], uu[Step], "ro")
    plt.ylabel("pwp(kPa)")
    plt.grid()
    plt.subplot(212)
    plt.plot(time, acc_input)
    plt.plot(time[Step], acc_input[Step], "ro")
    plt.xlabel("time(s)")
    plt.ylabel("acceleration(g)")
    plt.grid()


def dispplot(timeStep):
    Step = int(timeStep / 0.01) - 1
    plt.figure(figsize=(7, 8))
    ax0 = plt.subplot(gs[0])
    ax0.plot(maxdisp[0, ::2], nodes[::2, 2], "b--")
    ax0.plot(mindisp[0, ::2], nodes[::2, 2], "b--")
    ax0.plot(disp[Step, ::4], nodes[::2, 2])
    plt.xlabel("displacement(m)")
    plt.ylabel("Elevation(m)")
    plt.grid()
    ax1 = plt.subplot(gs[1])
    ax1.plot(time, acc_input)
    ax1.plot(time[Step], acc_input[Step], "ro")
    plt.xlabel("time(s)")
    plt.ylabel("acceleration(g)")
    plt.grid()


def createpwpplot():
    global time, acc_input, uu
    pwp = np.loadtxt("porePressure.out")
    time = pwp[:, 0]
    pwp = np.delete(pwp, 0, 1)
    uexcess = pwp - pwp[0, :]
    uu = uexcess[0 : len(time), 12]
    acc = np.loadtxt("acceleration.out")
    acc_input = acc[:, 1]

    return interactive(
        pwpplot, timeStep=widgets.FloatSlider(min=0.01, max=time[-1], step=0.01)
    )


def createDispplot():
    global maxdisp, mindisp, nodes, disp, gs
    nodes = np.loadtxt("nodesInfo.dat")
    disp = np.loadtxt("displacement.out")
    disp = np.delete(disp, 0, 1)
    disp = (disp.transpose() - disp[:, 0]).transpose()
    ndof = 2
    nnodes = nodes.shape[0]
    maxdisp = np.amax(disp, axis=0)
    mindisp = np.amin(disp, axis=0)
    maxdisp = maxdisp.reshape(ndof, nnodes, order="F")
    mindisp = mindisp.reshape(ndof, nnodes, order="F")
    gs = gridspec.GridSpec(2, 1, height_ratios=[6, 1])

    return interactive(
        dispplot,
        timeStep=widgets.FloatSlider(min=0.01, max=time[-1], step=0.01),
        continuous_update=False,
    )


if __name__ == "__main__":
    createpwpplot()
