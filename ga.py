#!/usr/bin/env python3


from itertools import chain
from sys import argv, stderr

import numpy as np
from geneticalgorithm import geneticalgorithm as ga

from haskell_adaptor import ArrayDecoder, save_test_suite_feed, get_coverage


MAX_PRICE = 10
MAX_QTY = 10
MAX_MODAL_QTY = 3
ORD_ENCODED_SIZE = 9
MAX_TC_SIZE = 10
MAX_TS_SIZE = 40
BROKER_NUMBERS = 5
SHAREHOLDER_NUMBERS = 10
MIN_CREDIT = 50
MAX_CREDIT = 200
MIN_SHARE = 5
MAX_SHARE = 20

VERBOSE = False


algorithm_param = {
    'max_num_iteration': 1,
    'population_size': 100,
    'mutation_probability': 0.1,
    'elit_ratio': 0.01,
    'crossover_probability': 0.5,
    'parents_portion': 0.3,
    'crossover_type': 'uniform',
    'max_iteration_without_improv': None
}


def main():
    def fitness(ts_encoded):
        traces = list(map(lambda tc: tc.traces, decoder.decode_ts(ts_encoded)))
        ts_size = len(traces)
        covered_stmts = set(chain(*traces))
        # score = 5 * len(covered_stmts) - 1 * ts_size
        coverage = get_coverage()
        score = coverage.branch
        if VERBOSE:
            print(ts_size, len(covered_stmts), score)
        return int(score)

    if len(argv) != 2:
        print("usage:\t%s <output feed file>" % argv[0], file=stderr)
        exit(2)

    decoder = ArrayDecoder(BROKER_NUMBERS, SHAREHOLDER_NUMBERS, ORD_ENCODED_SIZE, MAX_TC_SIZE, MAX_TS_SIZE)

    varbound = np.array((
        [(0, 1)]
        + [(MIN_CREDIT, MAX_CREDIT)] * BROKER_NUMBERS
        + [(MIN_SHARE, MAX_SHARE)] * SHAREHOLDER_NUMBERS
        + [(0, MAX_PRICE)]  # reference price
        + [
            (0, MAX_TC_SIZE*3-1),  # order ID
            (1, BROKER_NUMBERS),  # broker ID
            (1, SHAREHOLDER_NUMBERS),  # shareholder ID
            (0, MAX_PRICE),  # price
            (0, MAX_QTY),  # quantity
            (0, 1),  # side (is BUY)
            (0, MAX_MODAL_QTY),  # minimum quantity
            (0, 1),  # FAK (is FAK)
            (0, MAX_MODAL_QTY),  # disclosed quantitys
        ] * MAX_TC_SIZE
    ) * MAX_TS_SIZE)
    model = ga(function=lambda x: -fitness(x), dimension=(MAX_TS_SIZE * decoder.tc_encoded_size),
               variable_type='int', variable_boundaries=varbound,
               convergence_curve=False,
               algorithm_parameters=algorithm_param
               )

    best_variable, best_function, report = model.run()

    print("")
    ts = decoder.decode_ts(best_variable)
    print("%d tests" % len(ts))
    print("%d stmts" % len(set(chain(*map(lambda tc: tc.traces, ts)))))
    print("report: %s" % report)
    print("\n\n".join(map(lambda tc: repr(tc), ts)))
    save_test_suite_feed(ts, argv[1])


if __name__ == '__main__':
    main()
