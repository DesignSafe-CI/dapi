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

import os

import numpy as np
import matplotlib.pyplot as plt

from respSpectra import resp_spectra


def plot_acc(data_dir="."):
    """
    Plot acceleration time history and response spectra

    Args:
        data_dir: Directory containing the Profile*_acc*.out recorder
            outputs. Defaults to the current directory, so existing
            callers are unaffected; pass the job archive path to avoid
            os.chdir in notebooks.
    """
    plt.figure()

    for motion in ["motion1"]:
        for profile in ["A", "B", "C", "D"]:
            acc = np.loadtxt(
                os.path.join(data_dir, f"Profile{profile}_acc{motion}.out")
            )
            [p, umax, vmax, amax] = resp_spectra(acc[:, -1], acc[-1, 0], acc.shape[0])
            plt.semilogx(p, amax)

    # response spectra on log-linear plot

    plt.ylabel("$S_a (g)$")
    plt.xlabel("$Period (s)$")
    # plt.savefig('logSpectra.eps')
    # plt.savefig('logSpectra.png')


if __name__ == "__main__":
    plot_acc()
