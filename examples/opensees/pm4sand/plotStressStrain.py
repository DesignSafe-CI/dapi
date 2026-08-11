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

import matplotlib.pyplot as plt


def plot_stress_strain(stress, strain):
    """
    Plot stress strain curve
    """
    plt.figure()
    plt.plot(strain, stress)
    plt.xlabel("strain(%)")
    plt.ylabel("stress(kPa)")
    plt.grid()
    plt.savefig("stressstrain.eps")
    plt.savefig("stressstrain.png")
