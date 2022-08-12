# ta_cn 中国版技术指标

## 项目背景
初学量化，技术指标一般使用`TA-Lib`，但存在以下问题
1. 部分技术指标与国内不同。但大部分中国股民都是参考国内技术指标进行交易。需要实现中国版指标
2. `TA-Lib`只支持单支序列，要计算多支股票需循环，耗时久。

在实现遗传算法挖因子时，意识到如果能将常用的操作都转成算子，将大大简化策略的研究，
特别是将`+`、`-`、`*`、`/`等中缀操作符转成`ADD()`、`SUB()`、`MUL()`、`DIV()`前缀函数，可直接输到遗传算法工具中

所以开始参考`Alpha101`和各券商金融工程研报，试着实现一些算子，但后期实现中发现一些问题
1. 每家金工的研报指标命名上都有区别，难以统一
2. 指标太多，实现工作太大

直到看到了`MyTT`这个项目才意识到，指标命名参考股票软件的公式才是最方便直接的，可以直接到各股软中复制公式。遇到性能问题再针对性转换即可。

## 本人为何不直接用`MyTT`，而是重复造轮子呢？
1. 大部分公式只支持单条数据，遇到几千支股票的DataFrame，循环太慢
2. `TA-Lib`与国内指标不同，区别在哪，没有对比。错过了很好的教学机会
3. 为了行数短牺牲了可读性
4. 部分函数直接复制于股票软件，代码没有优化，有重复计算

## 目标
1. 按通达信等国内常用软件命名和分类各指标
2. 支持二维矩阵计算
3. 国内外计算方法区别很大时，两个版本都提供，同时说明区别处

## 实现方案优先级
1. bottleneck。支持二维数据，优先使用
2. TA-Lib。封装了常用函数，次要选择
3. numba。速度受影响，最后才用它

## 安装
1. 只想使用二维矩阵TA-Lib，只需安装基础版即可
```commandline
pip install ta_cn -i https://mirrors.aliyun.com/pypi/simple --upgrade
```

2. 使用中国版指标加速
```commandline
pip install ta_cn[cn] -i https://mirrors.aliyun.com/pypi/simple --upgrade
```

## 常见使用方法
1. 转发原生talib，输入一维向量
    - 优点: 本库提供了跳过空值的功能
    - 缺点: 不要在大量循环中调用，因为跳过空值的功能每调用一次就要预分配内存
2. 封装原生talib，输入二维矩阵，同时支持参数一维向量化
    - 优点：可为不同股票指定不同参数，可用于按天遍历计算指标。只分配一次内存
3. 直接调用包中定义的指标，如KDJ等
    - 优点：符合中国习惯的技术指标
    - 缺点：指标数目前比较少。一般没有跳过空值功能
4. 输入为复合索引时序，分组计算
    - 优点：使用简单，可进行指标嵌套
    - 缺点：速度会慢一些。准备工作偏复杂
    
## 跳过空值
1. TA-Lib遇到空值后面结果全为NaN
2. 跳过NaN后，导致数据长度不够，部分函数可能报错
3. 方案一：将所有数据进行移动，时序指标移动到最后，横截面指标移动到最右。
    - 优点：原指标不需要改动，只要提前处理数据。处理速度也快
    - 缺点：时序指标与横截面指标不能混合使用，得分别处理
4. 方案二：预先初始化空白区，计算指标时屏蔽NaN,算完后回填
    - 优点：外部调用简单，不需要对数据提前处理
    - 缺点：由于有大量的是否跳过NaN的处理，所以速度慢
    
### 常见示例
```python
import numpy as np

# 新版talib,只要替换引用，并添加一句init即可
import ta_cn.talib as ta
from ta_cn.utils_wide import pushna, pullna

# 原版talib,不支持二维数据
# import talib as ta

# 准备数据
h = np.random.rand(1000000).reshape(-1, 5000) + 10
l = np.random.rand(1000000).reshape(-1, 5000)
c = np.random.rand(1000000).reshape(-1, 5000)
# 指定模式，否则对talib封装的所有函数都不存在
ta.init(mode=1, skipna=False)

# 几个调用函数演示
r = ta.ATR(h, l, c, timeperiod=10)
print(r)
x, y, z = ta.BBANDS(c, timeperiod=10, nbdevup=2, nbdevdn=2)
print(z)

# 将少量值设置为空，用来模拟停牌
c[c < 0.4] = np.nan

# 提前处理数据，跳过停牌进行计算，再还原的演示
# 嵌套指标时，全为时序指标使用down,或全为截面使用right。混合时此方法不要轻易使用
arr, row, col = pushna(c, direction='down')
rr = ta.SMA(arr, timeperiod=10)
r = pullna(rr, row, col)
print(r)

# 使用skip_na在内部跳过停牌
ta.init(mode=1, skipna=True)
r = ta.SMA(c, timeperiod=10)
print(r)

# 使用多参数
ta.init(mode=2, skipna=True)
r = ta.SMA(c, timeperiod=[10, 20])
print(r)

```

### 使用ta_cn中定义的公式
```python
import numpy as np

# ta_cn.talib库底层是循环调用talib，部分计算效率不高
# 可导入ta_cn中的公式，只加这一句即导入多个文件中的函数
from ta_cn.imports import *
# 准备数据
from ta_cn.talib import set_compatibility_enable, set_compatibility

h = np.random.rand(10000000).reshape(-1, 50000) + 10
l = np.random.rand(10000000).reshape(-1, 50000)
c = np.random.rand(10000000).reshape(-1, 50000)

r = ATR_CN(h, l, c, timeperiod=10)
print(r)

# 设置参数，让MACD中的EMA算法与国内算法相同
set_compatibility_enable(True)
set_compatibility(1)
set_compatibility_enable(False)

x, y, z = MACD(c)
print(z)
```

### 输入DataFrame，输出是ndarray?
只要通过np_to_pd，并传入index/columns两参数即可还原成DataFrame
```python
import pandas as pd

from ta_cn.imports import *
from ta_cn.utils import np_to_pd

pd._testing._N = 250
pd._testing._K = 30
h = pd._testing.makeTimeDataFrame() + 10
l = pd._testing.makeTimeDataFrame()
c = pd._testing.makeTimeDataFrame()

r = ATR_CN(h, l, c)
# 返回的数据可能是np.ndarray
print(r[-5:])

# 可以再封装回pd.DataFrame
d = np_to_pd(r, copy=False, index=c.index, columns=c.columns)
print(d.iloc[-5:])

```
## 分组计算
二维矩阵计算，的确方便，`Alpha101`中的公式很快就可以实现，即支持时序又支持截面，但其中有一个难点，
就是NaN值的处理。`pushna`和`pullna`可用于解决此问题，但在公式中嵌入就比较棘手。所以我们还提供了分组封装功能
可以将指定的指标转换成支持长表输入。
```python
import pandas as pd

import ta_cn.talib as ta
from ta_cn.alpha import RANK
from ta_cn.preprocess import demean
from ta_cn.utils_long import series_groupby_apply, dataframe_groupby_apply

ta.init(mode=1, skipna=True)

pd._testing._N = 500
pd._testing._K = 30

open_ = pd._testing.makeTimeDataFrame() + 5
high = pd._testing.makeTimeDataFrame() + 10
low = pd._testing.makeTimeDataFrame() + 5
close = pd._testing.makeTimeDataFrame() + 5
group = close.copy() * 100 // 1 % 5

df = {
    'open_': open_.stack(),
    'high': high.stack(),
    'low': low.stack(),
    'close': close.stack(),
    'group': group.stack(),
}
df = pd.DataFrame(df)
df.index.names = ['date', 'asset']
kwargs = df.to_dict(orient='series')

# 套上装饰器，实现组内计算
SMA = series_groupby_apply(ta.SMA, by='asset', dropna=True, to_args=[], to_kwargs=['timeperiod'])
ATR = dataframe_groupby_apply(ta.ATR, by='asset', dropna=True, to_df=[0, 1, 2], to_kwargs={3: 'timeperiod'})
# 横截面
RANK = series_groupby_apply(RANK, by='date', dropna=True)
# 行业中性化
indneutralize = dataframe_groupby_apply(demean, by=['date', 'group'], dropna=False, to_df=[0, 'group'], to_kwargs={})

# 单输入
r = SMA(df['close'], 10)
print(r.unstack())
# 多输入
r = ATR(df['high'], df['low'], df['close'], 10)
print(r.unstack())
# 横截面
r = RANK(df['close'])
print(r.unstack())
r = indneutralize(df['close'], group=df['group'])

print(r.unstack())

```

## 指标对比清单
参考 [指标对比](指标对比.xlsx) 未完工，待补充

## Alpha101/Alpha191
本项目，试着用公式系统实现`Alpha101`、`Alpha191`，请参考examples文件下的测试示例。它最大的特点是尽量保持原公式的形式，
少改动，防止乱中出错。然后再优化代码提高效率。

## 停牌处理2
1. 板块指数，停牌了也要最近的行情进行计算，否则指数过小
2. 停牌期的开高低收都是最近的收盘价，收盘价可以ffill

## 参考项目
1. [TA-Lib](https://github.com/TA-Lib/ta-lib) TA-Lib C语言版，非官方镜像
2. [ta-lib](https://github.com/mrjbq7/ta-lib) TA-Lib Python版封装
3. [MyTT](https://github.com/mpquant/MyTT) My麦语言 T通达信 T同花顺
4. [funcat](https://github.com/cedricporter/funcat) 公式移植
5. [pandas-ta](https://github.com/twopirllc/pandas-ta) 支持Pandas扩展的技术指标
6. [ta](https://github.com/bukosabino/ta) 通过类实现的技术指标

## 交流群
ta_cn技术指标交流群: 601477228