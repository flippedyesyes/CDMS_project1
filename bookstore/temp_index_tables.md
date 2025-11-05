#### 搜索 `$text + store`

| State | DocsExamined | Cost(ms) |
| --- | --- | --- |
| none | 200 | 1 |
| full | 0 | 0 |

> 全文索引 `book_fulltext` 直接命中倒排表，完全消除了全表扫描，查询耗时趋近 0。

#### 待支付订单扫描 `(status + expires_at)`

| State | DocsExamined | Cost(ms) |
| --- | --- | --- |
| none | 5 000 | 27 |
| full | 5 000 | 20 |

> 复合索引 `idx_order_status_expire` 将扫描限制在目标状态上，耗时约减少 25%，支撑自动取消任务。

#### 批量写入 500 条订单（平均值）

| State | AvgCost(ms) |
| --- | --- |
| none | 15 |
| full | 18 |

> 维护索引带来 3ms 级别的写入开销，但相对于查询收益可以接受。
