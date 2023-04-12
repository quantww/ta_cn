import time

import numpy as np
import talib as ta

from ta_cn.regress import SLOPE_YX, ts_simple_regress
from ta_cn.tdx.reference import REF

a = np.random.rand(1000)  # .reshape(-1, 10)
b = np.random.rand(1000)  # .reshape(-1, 10)

r1 = SLOPE_YX(a, b, 30)
t1 = time.time()
x, r2, z = ts_simple_regress(a, b, 30, rettype=[0, 2, 1])
t2 = time.time()
t3 = time.time()
print(t2 - t1, t3 - t2)
print(r1[-10:])
print(r2[-10:])
#####################

c = ta.BETA(a, b, 30)
print(c[-10:])
# 为何算起来有不小的误差
c = SLOPE_YX(b / REF(b, 1) - 1, a / REF(a, 1) - 1, 30)
print(c[-10:])
