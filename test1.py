#!/usr/bin/env python3


from itertools import compress, chain
from sys import argv

import numpy as np
from geneticalgorithm import geneticalgorithm as ga


def get_input(addr):
    lines = []
    with open(addr) as f:
        lines = [line[:-1] for line in f.readlines()][2:]
    return [line.split() for line in lines]


algorithm_param = {
    'max_num_iteration': 1000,
    'population_size': 100,
    'mutation_probability': 0.1,
    'elit_ratio': 0.01,
    'crossover_probability': 0.5,
    'parents_portion': 0.3,
    'crossover_type': 'uniform',
    'max_iteration_without_improv': None
}


def main():
    traces = []

    def fitness(in_use):
        # selected = traces
        selected = compress(traces, in_use)
        number_of_testcases = sum(in_use)
        covered_stmts = set(chain(*selected))
        return 5 * len(covered_stmts) - 1 * number_of_testcases

    traces = get_input(argv[1])
    # print(fitness(traces))

    model = ga(function=lambda x: -fitness(x), dimension=len(traces), variable_type='bool',
               no_plot=True,
               algorithm_parameters=algorithm_param
               )

    best_variable, best_function, report = model.run()

    print("")
    print("%d tests" % sum(best_variable))
    print("%d stmts" % len(set(chain(*(compress(traces, best_variable))))))
    print(best_variable)
    print(set(chain(*compress(traces, best_variable))))
    print(report)


if __name__ == '__main__':
    main()
