#!/usr/bin/env python3


from itertools import chain
import random
import subprocess

import numpy as np
from geneticalgorithm import geneticalgorithm as ga


MAX_PRICE = 10
MAX_QTY = 10
MAX_MODAL_QTY = 3
ORD_ENCODED_SIZE = 5
MAX_TC_SIZE = 10
MAX_TS_SIZE = 40
TMP_FILE_ADDR = "/tmp/wdajdjkfhslfj"
TRACE_CALC_ADDR = "../me/GetTCTrace"
MAX_NGRAMS = 4
VERBOSE = False


class TestCase(object):
    def __init__(self, ords):
        self.ords = ords
        self.traces = self._calc_test_case_trace()

    @staticmethod
    def _translate_ord(ord):
        return " ".join([str(spec) for spec in ord])

    def _translate(self):
        return "\n".join([str(len(self.ords))] + [TestCase._translate_ord(ord) for ord in self.ords])

    def _calc_test_case_trace(self):
        with open(TMP_FILE_ADDR, 'w') as f:
            print(self._translate(), file=f)

        process = subprocess.Popen([TRACE_CALC_ADDR, TMP_FILE_ADDR], stdout=subprocess.PIPE)
        output, error = process.communicate()
        stmts = list(output.decode("utf-8").split())
        traces = []
        for i in range(MAX_NGRAMS):
            ngarms = []
            for j in range(i):
                ngarms.append(stmts[j:len(stmts)-(i-j-1)])
            traces += map(lambda x: '+'.join(x), zip(*ngarms))
        return set(traces)

    def __repr__(self):
        return self._translate() + "\n" + str(self.traces)


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
    def decode_tc(tc_encoded):
        ords = []
        for j in range(MAX_TC_SIZE):
            ord = [int(spec) for spec in tc_encoded[j * ORD_ENCODED_SIZE:(j + 1) * ORD_ENCODED_SIZE]]
            ord[2] = ord[2] == 1
            if ord[0] > 0 and ord[1] > 0 and ord[4] <= ord[1] and ord[3] <= ord[1]:
                ords.append(ord)
        if len(ords) > 0:
            return TestCase(ords)
        return None

    def decode_ts(ts_encoded):
        ts = []
        for i in range(MAX_TS_SIZE):
            is_in_idx = i * (MAX_TC_SIZE * ORD_ENCODED_SIZE + 1)
            ts_encoded[is_in_idx] = ts_encoded[is_in_idx] == 1
            if not ts_encoded[is_in_idx]:
                continue
            tc_encoded = ts_encoded[
                i * (MAX_TC_SIZE * ORD_ENCODED_SIZE + 1) + 1:(i + 1) * (MAX_TC_SIZE * ORD_ENCODED_SIZE + 1)
            ]
            tc = decode_tc(tc_encoded)
            if tc is not None:
                ts.append(tc)
        return ts

    def fitness(ts_encoded):
        traces = list(map(lambda tc: tc.traces, decode_ts(ts_encoded)))

        ts_size = len(traces)
        covered_stmts = set(chain(*traces))
        score = 3 * len(covered_stmts) - 1 * ts_size

        if VERBOSE:
            print(ts_size, len(covered_stmts), score)
        return score

    varbound = np.array((
        [[0, 1]] + [[0, MAX_PRICE], [0, MAX_QTY], [0, 1], [0, MAX_MODAL_QTY], [0, MAX_MODAL_QTY]] * MAX_TC_SIZE
        ) * MAX_TS_SIZE)
    model = ga(function=lambda x: -fitness(x), dimension=(MAX_TS_SIZE * (MAX_TC_SIZE * ORD_ENCODED_SIZE + 1)),
               variable_type='int', variable_boundaries=varbound,
               no_plot=True,
               algorithm_parameters=algorithm_param
               )

    best_variable, best_function, report = model.run()

    print("")
    ts = decode_ts(best_variable)
    print("%d tests" % len(ts))
    print("%d stmts" % len(set(chain(*map(lambda tc: tc.traces, ts)))))
    print(ts)
    print(report)


if __name__ == '__main__':
    main()
