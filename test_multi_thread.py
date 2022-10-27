#!/usr/bin/python

import time
import os
from timeit import default_timer as timer
from multiprocessing import Pool, cpu_count


def square2(n):
    print os.getpid()
    time.sleep(20)
    return n * n


def main():

    start = timer()

    values = (2, 4, 6, 8, 10)
    p = Pool(5)
    # res = p.map(square, values)
    for value in values:
        p.apply_async(square2, args=(value,))
    # print res
    # print res.get(timeout=1)
    p.close()
    p.join()
    # print res
    # p.join()
    # with Pool() as pool:
    #     res = pool.map(square, values)
    #     print(res)

    end = timer()



if __name__ == '__main__':
    main()
