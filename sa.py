#!/usr/bin/env python3


from itertools import chain
import random
from sys import argv, stderr

from simanneal import Annealer

from haskell_adaptor import ArrayDecoder, save_test_suite_feed


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

VERBOSE = False


varbound = (
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
    ) * MAX_TS_SIZE


class TestSuiteOptimizer(Annealer):
    def __init__(self, decoder):
        init_state = [random.randint(l, u) for (l, u) in varbound]
        self.decoder = decoder
        super(TestSuiteOptimizer, self).__init__(init_state)

    def move(self):
        idx = random.randint(0, len(self.state) - 1)
        self.state[idx] = random.randint(varbound[idx][0], varbound[idx][1])
        # idx = random.randint(0, MAX_TS_SIZE - 1) * self.decoder.tc_encoded_size
        # self.state[idx] = 0 if self.state[idx] == 1 else 0

    def energy(self):
        traces = list(map(lambda tc: tc.traces, self.decoder.decode_ts(self.state)))

        ts_size = len(traces)
        covered_stmts = set(chain(*traces))
        score = -(5 * len(covered_stmts) - 1 * ts_size)

        if VERBOSE:
            print(ts_size, len(covered_stmts), score)
        return score


def main():
    if len(argv) != 2:
        print("usage:\t%s <output feed file>" % argv[0], file=stderr)
        exit(2)

    decoder = ArrayDecoder(BROKER_NUMBERS, SHAREHOLDER_NUMBERS, ORD_ENCODED_SIZE, MAX_TC_SIZE, MAX_TS_SIZE)

    optimizer = TestSuiteOptimizer(decoder)
    # optimizer.set_schedule(optimizer.auto(minutes=1))
    optimizer.copy_strategy = "slice"

    state, score = optimizer.anneal()

    print("")
    print(score)
    ts = decoder.decode_ts(state)
    print("%d tests" % len(ts))
    print("%d stmts" % len(set(chain(*map(lambda tc: tc.traces, ts)))))
    print("\n\n".join(map(lambda tc: repr(tc), ts)))
    save_test_suite_feed(ts, argv[1])


if __name__ == '__main__':
    main()
