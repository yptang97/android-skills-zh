## 高影响迁移逻辑

### 1. 连接管理（v8+ 的重连机制变化）

**意图**：从开发者管理的状态（手动重试）转向由库管理的状态。

- **移除**：手动的 `startConnection()` 调用，或 `onServiceDisconnected()` 内的重试定时器。
- **增加**：在 `BillingClient.Builder` 中添加 `.enableAutoServiceReconnection()`。
- **逻辑**：在 v8+ 中，库会处理临时断连。你的 `onServiceDisconnected` 只能用于记录日志或更新 UI 状态（例如“Billing service temporarily unavailable”）。

### 2. 商品查询 \& 模型（v5-v8 的架构变化）

**意图**：支持 v5 引入、并在 v8 中进一步完善的“一个商品、多个优惠”模型。

- **数据模型替换**：
  - **旧版**：`SkuDetails`（ID 与价格一一对应）。
  - **新版**：`ProductDetails`。单个 `ProductDetails` 可以包含多个 `SubscriptionOfferDetails`（基础方案 + 优惠）。
- **结果处理（v8+ 逻辑）**：
  - **变化**：`queryProductDetailsAsync` 在监听器中不再返回列表。
  - **新意图**：你必须接收 `QueryProductDetailsResult` 对象。
  - **重构**：`kotlin
    // PBL 8+ Pattern
    billingClient.queryProductDetailsAsync(params) { result: QueryProductDetailsResult ->
    val responseCode = result.billingResult.responseCode
    val productDetailsList = result.productDetailsList // Retrieve list from result object
    // Process list...
    }`

### 3. 订阅现代化（v6 \& v7）

**意图**：用“基础方案”和“优惠”取代旧式的独立 SKU。

- **订阅升级/降级（v6+）**：

  - **旧版**：`BillingFlowParams` 中的 `setOldSkuPurchaseToken()`。
  - **新版**：使用 `SubscriptionUpdateParams`。你必须指定现有订阅的 `PurchaseToken` 以及 `ReplacementMode`（它取代了已废弃的 `ProrationMode`）。
  - **逻辑**：确认 `ReplacementMode` 与业务意图相符（例如 `CHARGE_FULL_PRICE` 与 `WITH_TIME_PRORATION`）。
- **分期计划（v7+）**：

  - **意图**：允许用户按月分期支付订阅费用。
  - **检查**：在 `SubscriptionOfferDetails` 中查找 `InstallmentPlanDetails`。如果应用支持高客单价订阅，则必须实现 `installmentPlanDetails` UI。

### 4. 购买处理 \& 历史记录（v6+）

**意图**：从仅本地保存的购买缓存转向实时状态查询。

- **有效购买**：
  - **已废弃**：`queryPurchases()`（同步）。
  - **必须使用**：`queryPurchasesAsync()`。你必须传入包含 `ProductType` 的 `QueryPurchasesParams`（`INAPP` 或 `SUBS`）。
- **购买历史（分页意图）**：
  - **v6+ 变化**：`queryPurchaseHistoryAsync` 已针对分页做了优化。
  - **逻辑**：如果应用有成千上万条历史交易，请确认你正确使用了 `PurchaseHistoryRecord` 列表，以避免内存开销。

### 5. 安全 \& 待处理交易（“始终开启”规则）

- **必须**：`enablePendingPurchases()` 从 v3 起就是必需的，但在 v8+ 中要确认它是在 `.build()` 之前调用的。你还必须在 `enablePendingPurchases()` 的 builder 上包含 `.enableOneTimeProducts()`。
- **可选**：如果应用销售预付订阅，你还必须包含 `.enablePrepaidPlans()`。
- **意图**：该配置用于处理“缓慢/延迟”的支付（例如现金或银行转账）。缺少它时，在新版本中应用会在初始化时崩溃。

### 6. SDK \& 环境要求

- **PBL 7.0**：要求 `compileSdk 34` 或更高。
- **PBL 8.0**：要求 `compileSdk 34` 或更高。
- **PBL 9.0**：要求 `compileSdk 35` 或更高。
- **Kotlin**：确认 `kotlin-stdlib` 已更新到至少 1.9.x，以支持新的库协程扩展。

### 7. 面向用户的功能（升级后的建议）

升级完成后，这些版本会启用以下功能：

- **v7**：**分期付款**（按年方案可按月支付）。
- **v8**：**预付方案**（用户可以在不自动续订的情况下充值时长）。
- **v8**：**个性化定价**（如果价格因用户而异，需展示法律声明）。
- **v9**：**应用内价格确认**（用户可以直接在应用内接受即将到来的订阅涨价，无需跳转到 Play Store；Google 限制最多每 7 天一次）。
