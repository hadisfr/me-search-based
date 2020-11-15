#!/usr/bin/env python3


from itertools import chain
import subprocess
from sys import argv, stderr

import numpy as np
from geneticalgorithm import geneticalgorithm as ga

MAX_PRICE = 10
MAX_QTY = 10
MAX_MODAL_QTY = 3
ORD_ENCODED_SIZE = 8
MAX_TC_SIZE = 10
MAX_TS_SIZE = 40
BROKER_NUMBERS = 5
SHAREHOLDER_NUMBERS = 10
MIN_CREDIT = 50
MAX_CREDIT = 200
MIN_SHARE = 5
MAX_SHARE = 20
TC_ENCODED_SIZE = 1 + BROKER_NUMBERS + SHAREHOLDER_NUMBERS + MAX_TC_SIZE * ORD_ENCODED_SIZE

TMP_FILE_ADDR = "/tmp/wdajdjkposlf"
TRACE_CALC_ADDR = "../me-spec/GetTCTrace"
TRACE_FEDD_ADDR = "../me-spec/GetTCTrades"
VERBOSE = False


class TestCase(object):
    def __init__(self, credits, shares, ords):
        self.credits = credits
        self.shares = shares
        self.ords = ords
        self.traces = self._calc_test_case_trace()

    @staticmethod
    def _translate_ord(ord):
        return " ".join([str(spec) for spec in ord])

    @staticmethod
    def _translate_credit(broker, credit):
        return "SetCreditRq %d %d" % (broker + 1, credit)

    @staticmethod
    def _translate_share(shareholder, share):
        return "SetOwnershipRq %d %d" % (shareholder + 1, share)

    def _translate(self):
        return "\n".join(sum([
            [str(len(self.credits) + len(self.shares))],
            [str(len(self.ords))],
            [TestCase._translate_credit(broker, credit) for (broker, credit) in enumerate(self.credits)],
            [TestCase._translate_share(shareholder, share) for (shareholder, share) in enumerate(self.shares)],
            [TestCase._translate_ord(ord) for ord in self.ords],
        ], []))

    def _calc_test_case_trace(self):
        with open(TMP_FILE_ADDR, 'w') as f:
            print(self._translate(), file=f)

        process = subprocess.Popen([TRACE_CALC_ADDR, TMP_FILE_ADDR], stdout=subprocess.PIPE)
        output, error = process.communicate()
        return set(output.decode("utf-8").split())

    def gen_test_case_feed(self):
        with open(TMP_FILE_ADDR, 'w') as f:
            print(self._translate(), file=f)

        process = subprocess.Popen([TRACE_FEDD_ADDR, TMP_FILE_ADDR], stdout=subprocess.PIPE)
        output, error = process.communicate()
        return output.decode("utf-8")

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
        credits = tc_encoded[:BROKER_NUMBERS]
        shares = tc_encoded[BROKER_NUMBERS:SHAREHOLDER_NUMBERS + BROKER_NUMBERS]
        ords_encoded = tc_encoded[SHAREHOLDER_NUMBERS + BROKER_NUMBERS:]
        ords = []
        for j in range(MAX_TC_SIZE):
            ord = [int(spec) for spec in ords_encoded[j * ORD_ENCODED_SIZE:(j + 1) * ORD_ENCODED_SIZE]]
            ord[4] = ord[4] == 1  # side
            ord[6] = ord[6] == 1  # fak
            if (
                ord[2] == 0  # pice
                or ord[3] == 0  # quantity
                or ord[5] > ord[3]  # minimum quantity
                or ord[7] > ord[3]  # disclosed quantity
            ):
                continue
            if ord[7] > 0 and ord[6]:  # iceberg with fak
                continue
            ords.append(ord)
        if len(ords) > 0:
            return TestCase(credits, shares, ords)
        return None

    def decode_ts(ts_encoded):
        ts = []
        for i in range(MAX_TS_SIZE):
            is_in_idx = i * TC_ENCODED_SIZE
            ts_encoded[is_in_idx] = ts_encoded[is_in_idx] == 1
            if not ts_encoded[is_in_idx]:
                continue
            tc_encoded = ts_encoded[
                i * TC_ENCODED_SIZE + 1:(i + 1) * TC_ENCODED_SIZE
            ]
            tc = decode_tc(tc_encoded)
            if tc is not None:
                ts.append(tc)
        return ts

    def fitness(ts_encoded):
        traces = list(map(lambda tc: tc.traces, decode_ts(ts_encoded)))

        ts_size = len(traces)
        covered_stmts = set(chain(*traces))
        score = 5 * len(covered_stmts) - 1 * ts_size

        if VERBOSE:
            print(ts_size, len(covered_stmts), score)
        return score

    def gen_test_suite_feed(ts):
        return "\n".join([
            str(len(ts)),
            "".join(map(lambda tc: tc.gen_test_case_feed(), ts)),
        ])

    def save_test_suite_feed(ts, addr):
        with open(addr, "w") as f:
            f.write(gen_test_suite_feed(ts))

    if len(argv) != 2:
        print("usage:\t%s <output feed file>" % argv[0], file=stderr)
        exit(2)

    varbound = np.array((
        [(0, 1)]
        + [(MIN_CREDIT, MAX_CREDIT)] * BROKER_NUMBERS
        + [(MIN_SHARE, MAX_SHARE)] * SHAREHOLDER_NUMBERS
        + [
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
    model = ga(function=lambda x: -fitness(x), dimension=(MAX_TS_SIZE * TC_ENCODED_SIZE),
               variable_type='int', variable_boundaries=varbound,
               no_plot=True,
               algorithm_parameters=algorithm_param
               )

    best_variable, best_function, report = model.run()

    print("")
    ts = decode_ts(best_variable)
    print("%d tests" % len(ts))
    print("%d stmts" % len(set(chain(*map(lambda tc: tc.traces, ts)))))
    print("report: %s" % report)
    print("\n\n".join(map(lambda tc: repr(tc), ts)))
    save_test_suite_feed(ts, argv[1])


if __name__ == '__main__':
    main()
