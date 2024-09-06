"""
Script to generate example colormaps for plotted forecast parameters
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from k_index import bar_color


if __name__ == "__main__":
    plt.style.use({'text.color': '#2f81f7', 'xtick.color': '#2f81f7'})

    # cloud cover
    fig, ax = plt.subplots(figsize=(8, 1))
    gradient = np.linspace(0, 1, 101)
    gradient = np.vstack((gradient, gradient))
    ax.imshow(gradient, cmap='coolwarm', aspect='auto')
    ax.get_yaxis().set_visible(False)
    ax.set(xlim=(0, 100), title='Cloud Cover')
    ax.grid(False)
    ax.xaxis.set_major_formatter(lambda x, _: fr'{int(x)}%')

    fig.tight_layout()
    fig.savefig('./icons/cloud_cover_scale.png', dpi=200, transparent=True)
    plt.show()

    # seeing/transparency
    fig, ax = plt.subplots(figsize=(8, 1))
    labels = ['Poor', 'Below Average', 'Average', 'Above Average', 'Excellent']
    gradient = np.linspace(0, 1, 5)
    gradient = np.vstack((gradient, gradient))
    ax.imshow(gradient, cmap='coolwarm_r', aspect='auto')
    ax.get_yaxis().set_visible(False)
    ax.set(xlim=(-0.5, 4.5), title='Transparency, Seeing')
    ax.grid(False)
    ax.xaxis.set_major_formatter(lambda x, _: fr'{int(x+1)} ({labels[int(x)] if int(x) < len(labels) else ""})')
    fig.tight_layout()
    fig.savefig('./icons/seeing_transparency_scale.png', dpi=200, transparent=True)
    plt.show()

    # Kp
    fig, ax = plt.subplots(figsize=(8, 2))
    kp_cmap = mcolors.LinearSegmentedColormap.from_list('kp_cmap', [bar_color(k) for k in range(10)])
    gradient = np.linspace(0, 9, 10)
    gradient = np.vstack((gradient, gradient))
    #ax.imshow(gradient, cmap=kp_cmap, aspect='auto')
    k_values = range(1, 10)
    ax.bar(k_values, k_values, color=[bar_color(k) for k in k_values], edgecolor='black', width=1)
    ax.set(xlim=(0.5, 9.5), ylim=(0, 9), title='Planetary k-index (Kp)')
    for i in [5, 6, 7, 8, 9]:
        ax.text(i-0.17, 2, f'G{int(i-4)}', c='black', size=15)

    ax.get_yaxis().set_visible(False)
    ax.xaxis.set_ticks(range(1, 10))
    ax.grid(False)

    fig.tight_layout()
    fig.savefig('./icons/kp_scale.png', dpi=200, transparent=True)

    plt.show()
