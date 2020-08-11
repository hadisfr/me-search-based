#!/usr/bin/env python3


from itertools import compress, chain
from sys import argv, stderr
import random
from simanneal import Annealer


class TestSuiteOptimizer(Annealer):
    def __init__(self, addr):
        self.traces = self._get_input(addr)
        # init_state = [True] * len(self.traces)
        init_state = random.choices([True, False], k=len(self.traces))
        super(TestSuiteOptimizer, self).__init__(init_state)

    def _get_input(self, addr):
        lines = []
        with open(addr) as f:
            lines = [line[:-1] for line in f.readlines()][2:]
        res = [line.split() for line in lines]
        print("reading done", file=stderr)
        return res

    def move(self):
        idx = random.randint(0, len(self.state) - 1)
        self.state[idx] = not self.state[idx]

    def energy(self):
        selected = compress(self.traces, self.state)
        number_of_testcases = sum(self.state)
        covered_stmts = set(chain(*selected))
        return -(3 * len(covered_stmts) - 1 * number_of_testcases)


def main():
    optimizer = TestSuiteOptimizer(argv[1])
    optimizer.set_schedule(optimizer.auto(minutes=1))
    optimizer.copy_strategy = "slice"

    state, score = optimizer.anneal()
    print("")
    print("%d tests" % sum(state))
    print("%d stmts" % len(set(chain(*(compress(optimizer.traces, state))))))
    if sum(state) < 20:
        print(state)
    print(set(chain(*compress(optimizer.traces, state))))


if __name__ == '__main__':
    main()
