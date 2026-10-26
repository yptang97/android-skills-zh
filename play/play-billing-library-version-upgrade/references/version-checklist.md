## Play Billing Library：按版本划分的智能检查清单

使用这份检查清单，核实从 \[当前版本\] 到 \[目标版本\] 之间的每一项技术要求都已满足。

## PBL v1.x 到 v3.x

- \[ \] **\[v1.0\] Builder 模式**：确认使用了 `BillingClient.newBuilder(context)`。
- \[ \] **\[v2.0\] 强制确认**：确认在 3 天内调用了 `acknowledgePurchase()` 或 `consumeAsync()`。
- \[ \] **\[v2.0\] 响应类型**：逻辑必须处理 `BillingResult` 对象，而不是原始整数。
- \[ \] **\[v3.0\] 旧接口移除**：确认 `ChildDirected` 和 `UnderAgeOfConsent` 参数已删除。

## PBL v4.x 系列

- \[ \] **异步购买**：确认 `queryPurchases()` 已替换为 `queryPurchasesAsync()`。
- \[ \] **多 SKU 访问器**：在 `Purchase` 对象中，把 `getSku()` 替换为 `getSkus()`（返回列表）。
- \[ \] **订阅重构**：确认变更逻辑使用了 `setSubscriptionUpdateParams()`。

## PBL v5.x 系列

- \[ \] **数据模型替换**：把所有 `SkuDetails` 实例替换为 `ProductDetails`。
- \[ \] **个性化定价**：为欧盟的价格披露实现 `setIsOfferPersonalized()`。

## PBL v6.x 系列

- \[ \] **替换模式**：把 `ProrationMode` 替换为 `ReplacementMode` 枚举。
- \[ \] **用户自选结算**：把 `AlternativeBillingListener` 替换为 `UserChoiceBillingListener`。

## PBL v7.x 系列

- \[ \] **SDK 合规**：`compileSdk` 设为 34 或更高。
- \[ \] **待处理购买**：把无参数的 `enablePendingPurchases()` 替换为 `enablePendingPurchases(PendingPurchaseParams)`。
- \[ \] **API 清理**：把 `setOldSkuPurchaseToken()` 替换为 `setOldPurchaseToken()`。

## PBL v8.x 系列

- \[ \] **SDK 合规**：`compileSdk` 设为 34 或更高。
- \[ \] **术语调整**：在 UI/字符串中把 "in-app items" 改名为 "one-time products"。
- \[ \] **签名强制要求**：`onProductDetailsResponse` 的签名必须是 `(BillingResult, QueryProductDetailsResult)`。
- \[ \] **SUBS 优惠令牌**：对于 `SUBS` 类型，`ProductDetailsParams` 必须包含 `offerToken`。
- \[ \] **自动重连**：确认 builder 中使用了 `enableAutoServiceReconnection()`。
- \[ \] **最低 SDK 提升**：确认 `minSdkVersion` 至少为 23。

## PBL v9.x 系列

- \[ \] **SDK 合规**：`compileSdk` 设为 35 或更高。
- \[ \] **API 移除**：确保所有 `SkuDetails`、`SkuDetailsParams` 和 `SkuDetailsResponseListener` 的用法都已移除，并替换为对应的 `ProductDetails` 等价实现。
- \[ \] **受限商店错误处理**：如果面向受限的设备模式（例如儿童模式），确保 `androidx.core` 为 v1.9+，并更新错误处理逻辑，改为捕获 `BILLING_UNAVAILABLE` 而不是 `ERROR`。
- \[ \] **外部支付计划空值安全**：如果使用开发者提供结算，更新 `DeveloperProvidedBillingDetails.getLinkUri()` 的逻辑，在解析前显式检查 `null` 和空字符串（`""`）两种取值。

## 未来版本（PBL 10.0.0+）

- \[ \] **动态清单生成**：对于任何 \>=10.0.0 的版本，你**必须**为 [版本说明](https://developer.android.com/google/play/billing/release-notes) 中出现的每个新版本标题合成一份新的检查清单。
- \[ \] **识别版本差异**：查阅新版本的 "Breaking Changes" 和 "Removed APIs"，整理出一份供 `grep` 使用的术语清单。
