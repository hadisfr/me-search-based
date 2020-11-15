#!/usr/bin/env python3

import ast
from sys import argv, stderr
from itertools import cycle

import numpy as np
from matplotlib import pyplot as plt
plt.rcParams['svg.fonttype'] = 'none'


def read_reports(addr):
    reports = []
    pref = "report: "
    with open(addr) as f:
        for line in f:
            if line.startswith(pref):
                reports.append(ast.literal_eval(line[len(pref):-1]))
    return reports


def plot(reports):
    linecycler = cycle(["-", "--", "-.", ":"])
    for i in range(len(reports)):
        plt.plot(np.array(reports[i]), linestyle=next(linecycler), label="run #%d" % (i + 1))
    plt.xlabel('Iteration')
    plt.ylabel('Objective function')
    # plt.title('Genetic Algorithm')
    # plt.legend()
    # plt.show()


if __name__ == '__main__':
    if len(argv) != 3:
        print("usage:\t%s <run log file> <output graph file>" % argv[0], file=stderr)
        exit(2)

    reports = read_reports(argv[1])
    plot(reports)
    plt.savefig(argv[2])
