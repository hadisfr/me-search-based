#!/usr/bin/env python3


from itertools import chain
import random
import subprocess
import string
from sys import argv, stderr

from simanneal import Annealer

MAX_PRICE = 10
MAX_QTY = 10
MAX_MODAL_QTY = 3
ORD_ENCODED_SIZE = 5
MAX_TC_SIZE = 10
MAX_TS_SIZE = 40
TMP_FILE_ADDR = "/tmp/wdajdjkfhslfj"
TRACE_CALC_ADDR = "../me/GetTCTrace"
TRACE_FEDD_ADDR = "../me/GetTCTrades"
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
        tmp_file_addr = TMP_FILE_ADDR + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        with open(tmp_file_addr, 'w') as f:
            print(self._translate(), file=f)

        process = subprocess.Popen([TRACE_CALC_ADDR, tmp_file_addr], stdout=subprocess.PIPE)
        output, error = process.communicate()
        return set(output.decode("utf-8").split())

    def gen_test_case_feed(self):
        tmp_file_addr = TMP_FILE_ADDR + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        with open(tmp_file_addr, 'w') as f:
            print(self._translate(), file=f)

        process = subprocess.Popen([TRACE_FEDD_ADDR, tmp_file_addr], stdout=subprocess.PIPE)
        output, error = process.communicate()
        return output.decode("utf-8")

    def __repr__(self):
        return self._translate() + "\n" + str(self.traces)


def gen_random_ord():
    price = random.randint(1, MAX_PRICE)
    qty = random.randint(1, MAX_QTY)
    is_buy = random.random() < 0.5
    min_qty = 0 if random.random() < 0.5 else random.randint(0, qty)
    disclosed_qty = 0 if random.random() < 0.5 else random.randint(0, qty)
    return [price, qty, is_buy, min_qty, disclosed_qty]


def gen_random_test_case():
    ord_num = MAX_TC_SIZE
    return TestCase([gen_random_ord() for i in range(ord_num)])


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


varbound = (
    [(0, 1)] + [(0, MAX_PRICE), (0, MAX_QTY), (0, 1), (0, MAX_MODAL_QTY), (0, MAX_MODAL_QTY)] * MAX_TC_SIZE
    ) * MAX_TS_SIZE


class TestSuiteOptimizer(Annealer):
    def __init__(self):
        init_state = [random.randint(l, u) for (l, u) in varbound]
        super(TestSuiteOptimizer, self).__init__(init_state)

    def move(self):
        idx = random.randint(0, len(self.state) - 1)
        self.state[idx] = random.randint(varbound[idx][0], varbound[idx][1])
        # idx = random.randint(0, MAX_TS_SIZE - 1) * (MAX_TC_SIZE * ORD_ENCODED_SIZE + 1)
        # self.state[idx] = 0 if self.state[idx] == 1 else 0

    def energy(self):
        traces = list(map(lambda tc: tc.traces, decode_ts(self.state)))

        ts_size = len(traces)
        covered_stmts = set(chain(*traces))
        score = -(5 * len(covered_stmts) - 1 * ts_size)

        if VERBOSE:
            print(ts_size, len(covered_stmts), score)
        return score


def gen_test_suite_feed(ts):
    return "".join(map(lambda tc: tc.gen_test_case_feed(), ts))


def save_test_suite_feed(ts, addr):
    with open(addr, "w") as f:
        f.write(gen_test_suite_feed(ts))


def main():
    if len(argv) != 2:
        print("usage:\t%s <output feed file>" % argv[0], file=stderr)
        exit(2)

    optimizer = TestSuiteOptimizer()
    # optimizer.set_schedule(optimizer.auto(minutes=1))
    optimizer.copy_strategy = "slice"

    state, score = optimizer.anneal()

    print("")
    print(score)
    ts = decode_ts(state)
    print("%d tests" % len(ts))
    print("%d stmts" % len(set(chain(*map(lambda tc: tc.traces, ts)))))
    print("\n\n".join(map(lambda tc: repr(tc), ts)))
    save_test_suite_feed(ts, argv[1])


if __name__ == '__main__':
    main()
