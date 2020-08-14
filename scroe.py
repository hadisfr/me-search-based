#!/usr/bin/env python3


from itertools import chain
import subprocess
from sys import argv

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


def get_tc_traces(tc_str):
    with open(TMP_FILE_ADDR, 'w') as f:
        print(tc_str, file=f)

    process = subprocess.Popen([TRACE_CALC_ADDR, TMP_FILE_ADDR], stdout=subprocess.PIPE)
    output, error = process.communicate()
    traces = output.decode("utf-8")[:-1]
    traces = traces.replace(" HNO-", "*HNO-").split("*")
    return traces


def get_ts_traces(addr):
    res = []
    with open(addr) as f:
        while True:
            num = f.readline()
            if num == "":
                break
            num = int(num)
            orders = []
            for i in range(num):
                orders.append(f.readline())
            tc = str(num) + '\n' + ''.join(orders)
            res += get_tc_traces(tc)
    return set(res)


def get_all_traces(addr):
    with open(addr) as f:
        traces = f.readlines()
    return {trace[:-1] for trace in traces
            # if '4' not in trace
            }


def main():
    actual = get_ts_traces(argv[1])
    expected = get_all_traces(argv[2])
    print("actual: %d" % len(actual))
    print("expected: %d" % len(expected))
    print("actual - expected: %d" % len(actual.difference(expected)))
    # print((actual.difference(expected)))
    print("expected - actual: %d" % len(expected.difference(actual)))
    # print((expected.difference(actual)))


if __name__ == '__main__':
    main()
