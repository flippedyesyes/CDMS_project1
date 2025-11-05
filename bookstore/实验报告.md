# Bookstore 实验报告

## 1. 实验要求与分工

### 1.1 实验目标
#### 实现一个提供网上购书功能的网站后端。<br>

- 网站支持书商在上面开商店，购买者可以通过网站购买。<br>
- 买家和卖家都可以注册自己的账号。<br>
- 一个卖家可以开一个或多个网上商店，
- 买家可以为自已的账户充值，在任意商店购买图书。<br>
- 支持 下单->付款->发货->收货 流程。<br>

**1.实现对应接口的功能，见项目的 doc 文件夹下面的 .md 文件描述 （60%）<br>**

1)用户权限接口，如注册、登录、登出、注销<br>

2)买家用户接口，如充值、下单、付款<br>

3)卖家用户接口，如创建店铺、填加书籍信息及描述、增加库存<br>

通过对应的功能测试，所有 test case 都 pass <br>

**2.为项目添加其它功能 ：（40%）<br>**

1)实现后续的流程 ：发货 -> 收货

2)搜索图书 <br>

- 用户可以通过关键字搜索，参数化的搜索方式；
- 如搜索范围包括，题目，标签，目录，内容；全站搜索或是当前店铺搜索。
- 如果显示结果较大，需要分页
- (使用全文索引优化查找)

3)订单状态，订单查询和取消定单<br>

- 用户可以查自已的历史订单，用户也可以取消订单。<br>
- 取消定单可由买家主动地取消定单，或者买家下单后，经过一段时间超时仍未付款，定单也会自动取消。 <br>

### 1.2 分工说明

| 成员 | 主要职责 | 涉及内容 |
| --- | --- | --- |
| 毛姝妍 | 基础接口与发货/收货流程；数据库与索引设计；性能基准测试 | 实现 60% 基础功能（用户/买家/卖家接口）以及 40% 扩展功能中发货、收货流程；对应测试用例；MongoDB 文档 schema 设计、索引设计；设计索引的性能测试 |
| 黄煜 | 搜索与订单状态功能；测试覆盖率优化 | 实现 40% 扩展功能中搜索图书、订单状态管理相关接口；对应测试；设计新的测试来覆盖异常情况，提高覆盖率。 |

## 2. 系统整体设计

### 2.1 目录结构（主要展示新增的文件）
```
bookstore
  |-- be                            
      |-- model                     
          |-- __init__.py
          |-- buyer.py              买家业务核心：Mongo 版下单/付款、取消订单（含库存回滚）、确认收货、自动过期扫描
          |-- db_conn.py            提供 Mongo 客户端缓存、集合句柄复用的基类
          |-- error.py              系统统一错误码与提示信息封装
          |-- mongo.py              读取环境变量建立 Mongo 连接并集中创建唯一/全文/复合索引
          |-- search.py             封装 `$text` 搜索、分页、店铺过滤及无关键字回退逻辑
          |-- seller.py             卖家业务：创建店、上/补货、计算 `search_text` 字段、校验并执行发货流程
          |-- store.py              应用启动入口，调用 `ensure_indexes()` 保证索引初始化完成
          |-- user.py               用户认证：注册/登录/登出/改密，JWT token 管理及 PyMongo 异常兜底
      |-- ....    
  |-- fe                            
      |-- test                      
          |-- test_add_book.py                     60%基础功能测试：验证卖家上架流程及错误分支
          |-- test_add_funds.py                    60%基础功能测试：买家充值成功/失败场景
          |-- test_add_stock_level.py              60%基础功能测试：库存补充与异常分支
          |-- test_bench.py                        60%基础功能测试：bench 程序可运行
          |-- test_create_store.py                 60%基础功能测试：创建店铺及重复创建
          |-- test_login.py                        60%基础功能测试：登录成功、密码错误、用户不存在
          |-- test_new_order.py                    60%基础功能测试：下单成功、库存不足、用户/店铺不存在
          |-- test_password.py                     60%基础功能测试：改密成功与错误密码
          |-- test_payment.py                      60%基础功能测试：付款流程及余额不足、重复支付
          |-- test_register.py                     60%基础功能测试：注册、注销及权限校验
          |-- test_order_edge_cases.py             40%拓展功能测试：订单状态异常、店铺/买家不匹配
          |-- test_order_management.py             40%拓展功能测试：订单列表、自动取消与库存恢复
          |-- test_search_books.py                 40%拓展功能测试：全文搜索分页、店铺过滤
          |-- test_shipping_flow.py                40%拓展功能测试：发货、重复发货、提前收货等流程
          |-- test_user_edge_cases.py              40%拓展功能测试：登出失效 token、错误密码改密等边界
          |-- test_buyer_model.py                  优化覆盖率测试：买家取消/列表/库存恢复等模型级验证
          |-- test_book_db.py                      优化覆盖率测试：BookDB自动灌库、已有数据不复写、分页读取
          |-- test_mongo_indexes.py                优化覆盖率测试：索引创建、已有索引冲突与异常抛出
          |-- test_seller_features.py              优化覆盖率测试：`search_text` 持久化及store范围校验
          |-- test_seller_errors_extended.py       优化覆盖率测试：卖家接口用户/店铺/库存错误分支
          |-- test_user_model.py                   优化覆盖率测试：用户模型注册/登录/改密/注销场景验证
          |-- test_user_model_errors.py            优化覆盖率测试：用户模型PyMongo异常、更新/删除miss分支
      |-- ....    
  |-- script                        
      |-- benchmark_indexes.py              有无索引性能测试
      |-- import_books_to_mongo.py          将 SQLite 书目批量导入 Mongo 集合
      |-- normalize_books_collections.py    清洗转换导入的书目文档结构
      |-- run_report_sample_tests.py        功能测试样例
      |-- sample_books_from_mongo.py        对大数据集booklx采样得到book进行后续的测试
      |-- test.sh                           运行测试生成 report
  |-- ....
```

### 2.2 数据库设计（单集合 + doc_type 分流）

系统统一使用 `bookstore` 数据库下的 `book` 集合。集合内通过字段 `doc_type` 区分文档类型，相当于在一个集合里维护四个“虚拟子集”：查询或索引时带上 `doc_type` 条件即可。这种设计避免建多个集合，索引与查询通过 `doc_type` 局部过滤匹配，既保证结构一致又方便扩展。

#### 2.2.1 书本文档 (`doc_type = "inventory"`)

| 字段 | 说明 |
| --- | --- |
| `store_id` | 上架店铺 ID（与 `book_id` 组成唯一键） |
| `book_id` | 书籍 ID |
| `book_info` | 书目信息的 JSON 字符串，保留原字段（title、author、publisher、pub_year、price、content 等） |
| `stock_level` | 当前库存数量 |
| `created_at` | 上架时间 |
| `updated_at` | 最近库存或书目更新时间 |
| `search_text` | 由标题、简介、目录、标签拼接，用于 Mongo `TEXT` 索引 |
| `title` | 书名（从 `book_info` 拆出，便于接口直接返回） |
| `book_intro` | 图书简介 |
| `content` | 目录 / 内容摘要 |
| `tags` | 标签数组（原来换行文本拆成列表） |

- 在导入书籍数据时，先保留原 book 的完整结构，序列化为 book_info JSON 字符串写入 doc_type="inventory" 文档中。
- 把常用字段（如 title、author、publisher 等）拆出来存放在文档顶层，虽然是冗余，但是加速了后续操作的效率。
- 去掉picture图片字段,极大地减小了内存的占用。
- 为了方便实现搜索图书的功能，将标题、简介、目录、标签进行拼接，生成search_text,利于做全文索引。

#### 2.2.2 用户文档 (`doc_type = "user"`)

| 字段 | 说明 |
| --- | --- |
| `user_id` | 用户唯一标识 |
| `password` | 登录密码 |
| `balance` | 账户余额（充值/付款会更新） |
| `token` | 当前登录 JWT |
| `terminal` | 登录终端标识 |
| `created_at` | 创建时间 |
| `updated_at` | 最近更新时间 |

#### 2.2.3 店铺文档 (`doc_type = "store"`)

| 字段 | 说明 |
| --- | --- |
| `store_id` | 店铺唯一标识 |
| `user_id` | 店铺所属卖家 |
| `created_at` | 店铺创建时间 |

#### 2.2.4 订单文档 (`doc_type = "order"`)

| 字段 | 说明 |
| --- | --- |
| `order_id` | 订单唯一标识 |
| `user_id` | 买家账号 |
| `store_id` | 店铺 ID |
| `items` | 订单明细列表（每项含 `book_id`、`count`、单价） |
| `status` | 订单状态（`pending` / `paid` / `shipped` / `delivered` / `cancelled`） |
| `total_price` | 订单总金额（整数，单位：分） |
| `expires_at` | pending 订单的超时取消时间 |
| `payment_time` | 付款时间（未付款则缺省） |
| `shipment_time` | 发货时间（未发货则缺省） |
| `delivery_time` | 收货时间（未收货则缺省） |
| `created_at` | 创建时间 |
| `updated_at` | 最近状态更新时间 |

### 2.3 索引设计（按文档类型划分）

- 四种文档都默认将id作为索引进行唯一标识。
- 我们手动创建的主要是`book_fulltext` 和`idx_order_status_expire`
- 前者是把`title`, `book_intro`, `content`, `tags`字段进行全文索引，这样单关键词、多关键词组合搜索都可以利用这一索引，避免全表扫描；
- 后者是把`status`, `expires_at`字段进行复合索引，订单自动取消时不需要全表遍历，直接命中 pending 状态下的最早 expires_at 的订单。

#### 2.3.1 书本文档索引 (`doc_type = "inventory"`)

| 索引名称 | Key | 说明 |
| --- | --- | --- |
| `uniq_inventory` | `("doc_type", 1)`, `("store_id", 1)`, `("book_id", 1)` | 唯一索引，保证同一店铺不能重复上架同一本书。 |
| `book_fulltext` | `TEXT` on `title`, `book_intro`, `content`, `tags` | 全文索引，支撑关键字搜索、多关键词组合。 |

#### 2.3.2 用户文档索引 (`doc_type = "user"`)

| 索引名称 | Key | 说明 |
| --- | --- | --- |
| `uniq_user_id` | `("doc_type", 1)`, `("user_id", 1)` | 唯一索引，确保同一个 `user_id` 只出现一次。 |

#### 2.3.3 店铺文档索引 (`doc_type = "store"`)

| 索引名称 | Key | 说明 |
| --- | --- | --- |
| `uniq_store_id` | `("doc_type", 1)`, `("store_id", 1)` | 唯一索引，防止重复建店。 |

#### 2.3.4 订单文档索引 (`doc_type = "order"`)

| 索引名称 | Key | 说明 |
| --- | --- | --- |
| `uniq_order_id` | `("doc_type", 1)`, `("order_id", 1)` | 唯一索引，保证订单 ID 不冲突。 |
| `idx_order_status_expire` | `("doc_type", 1)`, `("status", 1)`, `("expires_at", 1)` | 用于扫描待超时订单，支撑自动取消。 |
---

## 3. 功能实现

### 3.1 用户权限接口（60% 基础功能）

#### 3.1.1 注册 `POST /auth/register`
- **接口**  
  请求：`{"user_id": "...", "password": "..."}` → 成功返回 `200 {"message": "ok"}`。
- **后端逻辑**  
  1. `User.register` 检查 `doc_type="user"`、`user_id` 是否已存在。  
  2. 生成初始 `token`、`terminal`，设置 `balance=0`。  
  3. 插入用户文档，捕获 `DuplicateKeyError`、`PyMongoError` ,若存在，返回对应错误码。
- **数据库操作**  
  一次查询 `users` 表，一次插入 `users` 表，访问数据库两次。

#### 3.1.2 登录 `POST /auth/login`
- **接口**  
  请求：`{"user_id": "...", "password": "...", "terminal": "..."}` → 成功返回 `200 {"message": "ok", "token": "..."}`。
- **后端逻辑**  
  1. `User.login` 调用 `check_password` 读取并比对密码；失败返回 401。  
  2. 生成新的 JWT token，并更新 `token`、`terminal`、`updated_at`。  
  3. 若不存在或更新 0 行，视为授权失败。
- **数据库操作**  
  一次查询 `users` 表，一次更新 `users` 表，访问数据库两次。

#### 3.1.3 登出 `POST /auth/logout`
- **接口**  
  Header：`token`; 请求：`{"user_id": "..."}` → 成功返回 `200 {"message": "ok"}`。
- **后端逻辑**  
  1. `User.logout` 调用 `check_token`：读取 token、JWT 解码并检查过期。  
  2. 生成随机 `terminal/token` 写回，旧 token 即刻失效。  
  3. 若 token 不匹配 / 过期 / 用户不存在 → 返回 401。
- **数据库操作**  
  一次查询 `users` 表，一次更新 `users` 表，访问数据库两次。

#### 3.1.4 注销 `POST /auth/unregister`
- **接口**  
  请求：`{"user_id": "...", "password": "..."}` → 成功返回 `200 {"message": "ok"}`。
- **后端逻辑**  
  1. `User.unregister` 先用 `check_password` 校验身份。  
  2. 调用 `delete_one` 删除用户文档；删除数量≠1 则视为授权失败。  
  3. 捕获 `PyMongoError` 统一返回 528。
- **数据库操作**  
  一次查询 `users` 表，一次删除 `users` 表，访问数据库两次。

#### 3.1.5 修改密码 `POST /auth/password`
- **接口**  
  请求：`{"user_id": "...", "oldPassword": "...", "newPassword": "..."}` → 成功返回 `200 {"message": "ok"}`。
- **后端逻辑**  
  1. `User.change_password` 校验旧密码；若不匹配返回 401。  
  2. 生成新 token、刷新 `terminal`，写入 `new_password` 和 `updated_at`。  
  3. 若 `update_one` 无修改，视为授权失败。
- **数据库操作**  
  一次查询 `users` 表，一次更新 `users` 表，访问数据库两次。

### 3.2 买家接口（60% 基础功能）

#### 3.2.1 充值 `POST /buyer/add_funds`
- **接口**  
  Header：`token`; 请求：`{"user_id": "...", "password": "...", "add_value": 1000}` → 成功返回 `200 {"message": "ok"}`。
- **后端逻辑**  
  1. `Buyer.add_funds` 校验用户存在并比对密码。  
  2. 使用 `$inc` 增加余额，刷新 `updated_at`。
- **数据库操作**  
  一次查询 `users` 表，一次更新 `users` 表，访问数据库两次。

#### 3.2.2 下单 `POST /buyer/new_order`
- **接口**  
  Header：`token`; 请求：`{"user_id": "...", "store_id": "...", "books": [{"id": "...", "count": 2}, ...]}` → 成功返回 `200 {"order_id": "..."}`。
- **后端逻辑**  
  1. 校验用户、店铺存在。  
  2. 逐本检查库存：确保每个 `book_id` 都存在且库存充足。  
  3. 使用 `$inc` 扣减库存并记录 `updated_at`。  
  4. 生成 `pending` 订单文档，设置 `expires_at` 以便自动取消。
- **数据库操作**  
  多次查询 `users` / `stores` / `inventory` 表，逐本更新 `inventory` 表一次，最后插入 `orders` 表一次；整体访问数据库多次。

#### 3.2.3 付款 `POST /buyer/payment`
- **接口**  
  Header：`token`; 请求：`{"user_id": "...", "password": "...", "order_id": "..."}`
- **后端逻辑**  
  1. 校验密码、订单状态为 `pending`。  
  2. 确认余额充足，扣款。  
  3. 更新订单状态为 `paid`，写入 `payment_time`、`updated_at`。
- **数据库操作**  
  查询 `users` 表一次、查询 `orders` 表一次，之后更新 `users` 表一次、更新 `orders` 表一次，共访问数据库四次。

---

### 3.3 卖家接口（60% 基础功能）

#### 3.3.1 创建店铺 `POST /seller/create_store`
- **接口**  
  Header：`token`; 请求：`{"user_id": "...", "store_id": "..."}` → 成功返回 `200 {"message": "ok"}`。
- **后端逻辑**  
  1. 校验卖家存在。  
  2. 判断 `store_id` 是否已被占用。  
  3. 插入店铺文档。
- **数据库操作**  
  一次查询 `users` 表，一次查询 `stores` 表，一次插入 `stores` 表，访问数据库三次。

#### 3.3.2 添加书籍 `POST /seller/add_book`
- **接口**  
  Header：`token`; 请求包含 `book_info`、`stock_level` 等字段。
- **后端逻辑**  
  1. 校验卖家和店铺存在。  
  2. 判断该店铺是否已上架该 `book_id`。  
  3. 解析书籍信息：清洗并展开书目字段、构建 `search_text`。  
  4. 插入 `inventory` 文档，写入初始库存与时间戳。
- **数据库操作**  
  多次查询 `users` / `stores` / `inventory` 表以做校验，最终插入 `inventory` 表一次；访问数据库多次。

#### 3.3.3 增加库存 `POST /seller/add_stock_level`
- **接口**  
  Header：`token`; 请求：`{"user_id": "...", "store_id": "...", "book_id": "...", "add_stock_level": 10}`
- **后端逻辑**  
  1. 校验卖家、店铺、书籍是否存在。  
  2. 使用 `$inc` 增加库存并刷新 `updated_at`。
- **数据库操作**  
  查询 `users` 表一次、查询 `stores` 表一次、查询 `inventory` 表一次，之后更新 `inventory` 表一次；访问数据库四次。

### 3.4 发货、收货（40%扩展功能）

#### 3.4.1 发货 `POST /seller/ship_order`
- **接口**  
  Header：`token`; 请求：`{"user_id": "...", "store_id": "...", "order_id": "..."}`
- **后端逻辑**  
  1. 首先校验卖家身份与店铺归属，利用 `doc_type="store"` 文档确保订单店铺确实属于当前卖家。  
  2. 读取目标订单，确认状态为 `paid` 且 `store_id` 匹配。  
  3. 将订单状态改为 `shipped`，写入 `shipment_time`、`updated_at`。若状态异常或店铺不匹配，返回对应错误码。  
  4. 发货流程本身不修改库存，只标记物流节点，供后续查询。
- **数据库操作**  
  一次查询 `store` 文档，一次查询订单，一次更新订单，共访问数据库三次。

#### 3.4.2 收货 `POST /buyer/confirm_receipt`
- **接口**  
  Header：`token`; 请求：`{"user_id": "...", "order_id": "..."}`
- **后端逻辑**  
  1. 再次读取订单确认归属买家、状态为 `shipped`。  
  2. 更新为 `delivered`，写入 `delivery_time` 和 `updated_at`。  
  3. 买家不匹配或重复收货则返回状态错误。
- **数据库操作**  
  一次查询订单，一次更新订单，共访问数据库两次.

#### 3.5 图书搜索（40%扩展功能）

#### 3.5.1 搜索接口 `GET /search/books`
- **接口**  
  Query：`q=关键字&store_id=可选&page=1&page_size=20` → 返回 `200 {"books": [...], "total": n, ...}`。
- **后端逻辑**  
  1. 上架图书阶段已对原 SQLite 书目做预处理：`tags` 拆成数组、`price` 统一换算成分、去掉 `picture`，并把原始字段序列化到 `book_info`；同时展开 `title/book_intro/content/tags`，拼接 `search_text` 供全文检索使用。  
  2. 请求带 `q` 时，通过 `$text` 查询命中 `book_fulltext`，支持多关键词；未带关键字则退化为按 `updated_at` 排序的普通查询。  
  3. 传入 `store_id` 时追加店铺过滤，实现跨店/单店两种场景。  
  4. 通过 `skip/limit` 分页，全文检索结果按 `score + updated_at` 排序；返回包含总数、页码和书目详情。
- **数据库操作**  
  一次查询 `inventory` 文档集合（利用全文索引与分页），访问数据库一次。

#### 3.6 订单状态管理（40%扩展功能）

#### 3.6.1 取消订单 `POST /buyer/cancel_order`
- **接口**  
  Header：`token`; 请求：`{"user_id": "...", "order_id": "...", "password": "可选"}`
- **后端逻辑**  
  1. 入口调用 `cancel_expired_orders`，借助 `idx_order_status_expire` 快速定位 `pending` 且超时的订单，并直接执行取消流程，保证后续查询看到的是实时状态。  
  2. 手动取消时，确认订单属于当前买家且状态为 `pending`；若传入密码再校验一次，防止 token 泄漏导致误取消。  
  3. 遍历订单中的每件商品，调用 `_restore_inventory` 对 `store_id + book_id` 执行 `$inc`，恢复库存并刷新 `updated_at`。  
  4. 最后写入订单状态 `cancelled`、设置 `cancelled_at` 和 `updated_at`。若订单已不在 `pending` 或查无此单，返回对应错误码。
- **数据库操作**  
  多次查询 `orders`、`inventory` 文档，逐条恢复库存并更新订单状态，访问数据库多次。

#### 3.6.2 获取订单列表 `GET /buyer/orders`
- **接口**  
  Header：`token`; Query：`user_id=...&status=可选&page=1&page_size=20` → 返回 `200 {"orders": [...], "total": n, ...}`。
- **后端逻辑**  
  1. 同样先调用 `cancel_expired_orders`，确保列表结果不含超时 pending 订单。  
  2. 根据传入状态构建过滤条件，直接命中 `idx_order_user_status_updated`（`user_id + status + updated_at DESC`），在数据库端完成排序与分页。  
  3. 返回订单详情及 `payment_time`、`shipment_time`、`delivery_time` 等字段，便于区分当前流程与历史记录。
- **数据库操作**  
  一次查询 `orders` 文档集合，并统计总条数，访问数据库一次。

## 4. 测试与实验结果

### 4.1 功能实现测试

#### 4.1.1 pytest 测试结果
![pytest-82](./1762332966475.jpg)
- **基础功能 60%（33 项）**：对注册、登录、登出、修改密码、卖家创建店铺与上架补货、买家充值与下单付款等核心流程进行测试。
- **扩展功能 40%（19 项）**：对订单异常处理（自动取消、重复操作防护）、发货/收货流程、全文搜索、多用户边界行为进行测试。
- **处理异常 / 提高覆盖率（30 项）**：围绕 Mongo 迁移后的关键逻辑（索引初始化、书库灌装、买家/卖家模型）补充测试，同时模拟各种异常分支（PyMongo 报错、更新/删除 miss、权限错误等），提升覆盖率与稳定性。
#### 4.1.2 功能实现样例（扩展功能）
- 发货  

  | 测试情况 | 传参 | 结果 message |
  | --- | --- | --- |
  | 付款后发货成功 | (store_id, order_id) | new=200, pay=200, **ship=200**（进入 shipped 状态） |
  | 未付款无法发货 | (store_id, 未付款 order_id) | new=200, **ship=520**（保持 pending） |
  | 发货不存在的书 | (store_id, 错误 book_id) | **ship=518**，日志提示缺少库存文档 |
  | 发货不存在的订单 | (store_id, 错误 order_id) | **ship=518**，提示订单不存在 |
  | 店铺不存在 | (错误 store_id, order_id) | new=200, pay=200，**ship=513**（店铺校验失败） |

- 收货  

  | 测试情况 | 传参 | 结果 message |
  | --- | --- | --- |
  | 付款成功且发货成功后收货 | (buyer_id, password, order_id) | new=200, pay=200, ship=200，**confirm=200**（状态转为 delivered） |
  | 未付款订单 | (buyer_id, 错误状态 order_id) | new=200，**confirm=520**（保持 pending） |
  | 买家不存在 | (不存在的 buyer_id) | **HTTP 401**，拒绝收货 |
  | 订单不存在 | (buyer_id, 不存在的 order_id) | **confirm=518**，未找到订单 |

- 图书搜索 · 单关键词  

  | 测试情况 | 传参 | 结果 message |
  | --- | --- | --- |
  | 分页查询 | ("三毛", 0) | code=200，total=8（第一页返回 2 条） |
  | 全部显示查询 | ("三毛", 1) | code=200，total=8（第一页返回全部） |
  | 不存在的关键词 | ("三毛+", 1) | code=200，total=0（全文索引命中为空） |

- 图书搜索 · 多关键词  

  | 测试情况 | 传参 | 结果 message |
  | --- | --- | --- |
  | 查询成功 | ["三毛", "袁氏"] | code=200，total=8 |
  | 不存在关键词 | ["三毛++", "袁氏++"] | code=200，total=0 |

- 买家查询历史订单  

  | 测试情况 | 传参 | 结果 message |
  | --- | --- | --- |
  | 下单后查询历史订单，空 | (buyer_id) | code=200，total=0（pending 不计入历史） |
  | 发货后查询历史订单，空 | (buyer_id) | code=200，total=0（shipped 未归档） |
  | 收货后查询历史订单 | (buyer_id) | code=200，total=1（delivered 归入历史） |

- 买家查询当前订单  

  | 测试情况 | 传参 | 结果 message |
  | --- | --- | --- |
  | 下单后查询当前订单 | (buyer_id) | code=200，total=1（pending 在当前列表） |
  | 发货后查询当前订单 | (buyer_id) | code=200，total=1（shipped 仍在当前列表） |
  | 收货后查询当前订单，为空 | (buyer_id) | code=200，total=0（delivered 从当前移除） |


### 4.2 覆盖率结果
功能实现后，第一次运行得到覆盖率只有 86%，研究发现覆盖率低主要来源于 `be/model/buyer.py`、`be/model/seller.py`、`be/model/search.py`  `fe/test/test_bench.py` 等模块，他们的代码中存在很多未被执行的异常处理。这些代码都是对一些特殊情况的处理，比如买家取消，库存回滚、用户认证的错误码返回等。因此添加了一些测试用例，来覆盖了这些异常处理逻辑。

- **买家模型**：新增用例覆盖取消订单、订单列表、库存恢复的模型级验证，确保 `_restore_inventory`、自动过期等逻辑被执行。
- **BookDB**：构造临时 SQLite 库测试 `_ensure_seed_data` 的“空库自动灌库”“已有数据不复写”“分页读取”三种场景。
- **Mongo 索引**：验证索引创建、已有索引冲突和异常抛出场景，确认 `ensure_indexes` 的异常分支不再漏测。
- **搜索文本**：检查 `search_text` 拼接结果以及 `store` 范围过滤，避免搜索响应遗漏字段。
- **卖家接口错误分支**：模拟用户不存在、店铺不匹配、库存缺失等情况，触发卖家模型中的错误返回。
- **用户模型主流程**：补齐注册/登录/改密/注销的正常路径覆盖。
- **用户模型异常**：通过 Mock 强制 PyMongo 抛错、update/delete miss，确保对应的 528/530 错误码得以测试。

- **最终得到总覆盖率：93%**

| Name | Stmts | Miss | Branch | BrPart | Cover |
| --- | ---: | ---: | ---: | ---: | ---: |
| be/_init_.py | 0 | 0 | 0 | 0 | 100% |
| be/app.py | 3 | 3 | 2 | 0 | 0% |
| be/model/_init_.py | 0 | 0 | 0 | 0 | 100% |
| be/model/buyer.py | 194 | 42 | 80 | 14 | 79% |
| be/model/db_conn.py | 11 | 0 | 0 | 0 | 100% |
| be/model/error.py | 25 | 1 | 0 | 0 | 96% |
| be/model/mongo.py | 44 | 3 | 10 | 4 | 87% |
| be/model/search.py | 43 | 7 | 8 | 2 | 82% |
| be/model/seller.py | 106 | 30 | 46 | 8 | 75% |
| be/model/store.py | 5 | 0 | 0 | 0 | 100% |
| be/model/user.py | 140 | 20 | 30 | 2 | 87% |
| be/serve.py | 38 | 1 | 2 | 1 | 95% |
| be/view/_init_.py | 0 | 0 | 0 | 0 | 100% |
| be/view/auth.py | 42 | 0 | 0 | 0 | 100% |
| be/view/buyer.py | 67 | 4 | 4 | 1 | 93% |
| be/view/search.py | 21 | 4 | 2 | 1 | 78% |
| be/view/seller.py | 39 | 0 | 0 | 0 | 100% |
| fe/_init_.py | 0 | 0 | 0 | 0 | 100% |
| fe/access/_init_.py | 0 | 0 | 0 | 0 | 100% |
| fe/access/auth.py | 31 | 0 | 0 | 0 | 100% |
| fe/access/book.py | 119 | 8 | 20 | 4 | 91% |
| fe/access/buyer.py | 58 | 0 | 6 | 0 | 100% |
| fe/access/new_buyer.py | 8 | 0 | 0 | 0 | 100% |
| fe/access/new_seller.py | 8 | 0 | 0 | 0 | 100% |
| fe/access/search.py | 12 | 0 | 2 | 0 | 100% |
| fe/access/seller.py | 37 | 0 | 0 | 0 | 100% |
| fe/bench/_init_.py | 0 | 0 | 0 | 0 | 100% |
| fe/bench/run.py | 13 | 0 | 6 | 0 | 100% |
| fe/bench/session.py | 47 | 0 | 12 | 2 | 97% |
| fe/bench/workload.py | 125 | 1 | 20 | 2 | 98% |
| fe/conf.py | 11 | 0 | 0 | 0 | 100% |
| fe/conftest.py | 19 | 0 | 0 | 0 | 100% |
| fe/test/gen_book_data.py | 49 | 1 | 16 | 2 | 95% |
| fe/test/test_add_book.py | 37 | 0 | 10 | 0 | 100% |
| fe/test/test_add_funds.py | 23 | 0 | 0 | 0 | 100% |
| fe/test/test_add_stock_level.py | 40 | 0 | 10 | 0 | 100% |
| fe/test/test_bench.py | 6 | 2 | 0 | 0 | 67% |
| fe/test/test_book_db.py | 42 | 0 | 0 | 0 | 100% |
| fe/test/test_buyer_model.py | 60 | 0 | 0 | 0 | 100% |
| fe/test/test_create_store.py | 20 | 0 | 0 | 0 | 100% |
| fe/test/test_login.py | 28 | 0 | 0 | 0 | 100% |
| fe/test/test_mongo_indexes.py | 26 | 4 | 2 | 0 | 79% |
| fe/test/test_new_order.py | 40 | 0 | 0 | 0 | 100% |
| fe/test/test_order_edge_cases.py | 64 | 1 | 4 | 1 | 97% |
| fe/test/test_order_management.py | 95 | 0 | 0 | 0 | 100% |
| fe/test/test_password.py | 33 | 0 | 0 | 0 | 100% |
| fe/test/test_payment.py | 60 | 1 | 4 | 1 | 97% |
| fe/test/test_register.py | 31 | 0 | 0 | 0 | 100% |
| fe/test/test_search_books.py | 60 | 0 | 0 | 0 | 100% |
| fe/test/test_seller_errors_extended.py | 48 | 0 | 0 | 0 | 100% |
| fe/test/test_seller_features.py | 25 | 0 | 0 | 0 | 100% |
| fe/test/test_shipping_flow.py | 43 | 1 | 4 | 1 | 96% |
| fe/test/test_user_edge_cases.py | 22 | 0 | 0 | 0 | 100% |
| fe/test/test_user_model_errors.py | 77 | 0 | 0 | 0 | 100% |
| **TOTAL** | **2195** | **134** | **300** | **46** | **93%** |


### 4.3 索引的性能分析

#### 4.3.1 对于图书搜索 复合索引 `book_fulltext`

| State | DocsExamined | Cost(ms) |
| --- | --- | --- |
| none | 200 | 1 |
| full | 0 | 0 |

-  全文索引 `book_fulltext` 直接命中倒排表，不必进行全表扫描，查询耗时趋近 0。

#### 4.3.2 对于订单超时扫描 复合索引`idx_order_status_expire``

| State | DocsExamined | Cost(ms) |
| --- | --- | --- |
| none | 5 000 | 27 |
| full | 5 000 | 20 |

- 复合索引 `idx_order_status_expire` 将扫描限定在目标状态上，耗时约减少 25%，支撑自动取消任务。

#### 4.3.3 索引对写入的影响
批量写入 500 条订单计算平均消耗时间

| State | AvgCost(ms) |
| --- | --- |
| none | 15 |
| full | 18 |

- 维护索引带来约 3ms 的写入开销，但相对于搜索与订单查询的收益可以接受。
                                                        
## 5. git版本管理

- **分支策略**：先clone了助教发的仓库，创立新的分支，在 `clean-master` 上完成开发，清理历史提交中的大文件并更新 `.gitignore`，再依次提交基础功能、扩展功能、测试与性能脚本。
![git-process-1](./git%20process1.png) 
- 可以看到图中的提交记录按照时间顺序对于每次的功能实现版本有保存。 
![git-process-2](./git%20process2.png)
- 这是vscode中版本维护的线图，将vscode与远程github连接，commit,push都很方便

- **关键submit**：
  1. **数据迁移**：完成 MongoDB 模型替换 SQLite，确保接口保持兼容，实现60%基础功能。
  2. **扩展功能**：实现发货/收货、搜索、订单查询等 40% 功能并通过教师用例。
  3. **测试强化**：新增异常/边界测试，覆盖率提升到 93%，并整理 `doc/test_samples.md`。
  4. **性能与报告**：完成索引测试脚本、运行实验样例、撰写实验报告。

- **过程中遇到的问题**：
  - 一开始我们将book.db存在了bookstore中直接提交，大文件推送失败，于是我们利用 `.gitignore`，并撤销之前的提交，重新提交。
  - 平常运行测试时用的是采样得到的小样本book,进行索引测试时，效果难以体现，于是使用 `book_lx` 大数据集并调整查询参数，结果对比明显。

本项目仓库：https://github.com/flippedyesyes/CDMS_project1