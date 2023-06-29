import numpy as np
from datasketch import MinHash, MinHashLSH
from fastdtw import fastdtw

# 生成随机时间序列
N = 10
M = 10
data = np.random.rand(N, M)

# 使用MinHash和LSH进行索引
num_perm = 128
lsh = MinHashLSH(threshold=0.3, num_perm=num_perm)
for i in range(N):
    m = MinHash(num_perm=num_perm)
    for j in range(M):
        m.update(str(data[i][j]).encode('utf-8'))
    lsh.insert(i, m)

# 查找相似的时间序列
query = data[5].copy() + 0.1
# np.random.rand(M)
query_m = MinHash(num_perm=num_perm)
for j in range(M):
    query_m.update(str(query[j]).encode('utf-8'))
matches = lsh.query(query_m)
min_dist = float('inf')
min_idx = None
for i in matches:
    dist, _ = fastdtw(data[i], query)
    if dist < min_dist:
        min_dist = dist
        min_idx = i
print('Most similar time series is %d with distance %f' % (min_idx, min_dist))
