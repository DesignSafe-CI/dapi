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
# -------------------------------------------------------

import numpy as np
import matplotlib.pyplot as plt


def plot_porepressure():
    """
    Plot pore water pressure
    """
    porepressure = np.loadtxt("porePressure.out")
    time = porepressure[:, 0]
    porepressure = np.delete(porepressure, 0, 1)
    uexcess = porepressure - porepressure[0, :]

    plt.figure()
    plt.plot(time, uexcess[:, 12])
    plt.xlabel("Time(s)")
    plt.ylabel("u_excess(kPa)")
    plt.grid()
    plt.savefig("porePressure.eps")
    plt.savefig("porePressure.png")


if __name__ == "__main__":
    plot_porepressure()
