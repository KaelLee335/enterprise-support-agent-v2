# RAG Embedding Distance Calibration (Exploratory)

- Generated: 2026-11-22 08:34 UTC
- Embedding model: `BAAI/bge-large-zh-v1.5`
- Vector collection: `support_agent_policies_13de830c7c0d` (12 chunks)
- Retrieval setting under review: Top-K=4; all collection distances recorded for ranking analysis
- Probe set: 12 answerable probes + 12 unsupported probes, all synthetic and fictional
- Scope: embedding API only; no chat model call; no vector-store/database writes; no answer behavior change.
- Distance meaning: raw Chroma distance from the existing store's configured metric; smaller is closer. It is not a probability.

## Summary

- Target document appeared in Top-4 for 12/12 answerable probes (100.0%).
- Answerable target-document distance: min/median/max = 0.6516 / 0.7711 / 1.1380.
- Answerable nearest-document distance: min/median/max = 0.6516 / 0.7711 / 1.0804.
- Unsupported nearest-document distance: min/median/max = 0.9072 / 0.9932 / 1.1817.

### Distribution details

| Probe group / distance | Min | P25 | Median | P75 | Max |
|---|---:|---:|---:|---:|---:|
| Answerable: target document | 0.6516 | 0.7483 | 0.7711 | 0.8118 | 1.1380 |
| Answerable: nearest document | 0.6516 | 0.7483 | 0.7711 | 0.8118 | 1.0804 |
| Unsupported: nearest document | 0.9072 | 0.9303 | 0.9932 | 1.1548 | 1.1817 |

## Probe results

| ID | Group | Expected document | Expected rank | Expected distance | Nearest distance | Top-4 | Retrieved order (all chunks) | Question |
|---|---|---|---:|---:|---:|:---:|---|---|
| IN-01 | answerable | POL-01 | 1 | 0.6783 | 0.6783 | yes | POL-01 → POL-10 → POL-03 → POL-04 → RET-01 → POL-02 → QUA-01 → POL-05 → POL-06 → POL-08 → POL-09 → POL-07 | 我是在你们演示商城买的键盘，这个售后规则适用吗？ |
| IN-02 | answerable | POL-02 | 1 | 0.9454 | 0.9454 | yes | POL-02 → POL-03 → POL-05 → QUA-01 → POL-06 → RET-01 → POL-01 → POL-04 → POL-09 → POL-08 → POL-10 → POL-07 | 刚签收几天，包装配件都在，只是觉得不合适，能退吗？ |
| IN-03 | answerable | POL-03 | 1 | 0.7789 | 0.7789 | yes | POL-03 → POL-04 → QUA-01 → POL-02 → POL-01 → POL-05 → POL-06 → RET-01 → POL-07 → POL-09 → POL-10 → POL-08 | 鼠标有质量问题，收货两周内可以换新吗？ |
| IN-04 | answerable | POL-04 | 1 | 0.8151 | 0.8151 | yes | POL-04 → POL-01 → POL-03 → POL-10 → POL-05 → POL-02 → POL-06 → POL-09 → QUA-01 → POL-08 → RET-01 → POL-07 | 键盘进了水还能走免费保修吗？ |
| IN-05 | answerable | POL-05 | 1 | 0.7737 | 0.7737 | yes | POL-05 → POL-03 → QUA-01 → POL-02 → POL-06 → POL-04 → POL-09 → POL-10 → RET-01 → POL-01 → POL-08 → POL-07 | 质量问题确认以后，退回去的邮费谁出？ |
| IN-06 | answerable | POL-06 | 1 | 0.7169 | 0.7169 | yes | POL-06 → POL-02 → POL-07 → POL-08 → POL-09 → POL-03 → QUA-01 → POL-01 → POL-05 → RET-01 → POL-10 → POL-04 | 商家显示退款中，什么时候银行卡能看到钱？ |
| IN-07 | answerable | POL-07 | 1 | 0.7588 | 0.7588 | yes | POL-07 → POL-06 → POL-09 → POL-02 → QUA-01 → POL-03 → POL-08 → POL-10 → POL-05 → POL-04 → POL-01 → RET-01 | 显示已经发货了，大概几天能送到？ |
| IN-08 | answerable | POL-08 | 1 | 0.7587 | 0.7587 | yes | POL-08 → POL-09 → POL-07 → POL-03 → POL-06 → POL-01 → POL-10 → POL-02 → POL-05 → QUA-01 → POL-04 → RET-01 | 订单号格式是什么？可以一次查好几个吗？ |
| IN-09 | answerable | POL-09 | 1 | 0.8107 | 0.8107 | yes | POL-09 → POL-08 → POL-10 → POL-07 → POL-05 → POL-03 → POL-01 → POL-02 → POL-06 → QUA-01 → POL-04 → RET-01 | 电子发票需要把抬头和税号发给机器人吗？ |
| IN-10 | answerable | POL-10 | 3 | 1.1380 | 1.0804 | yes | POL-09 → POL-01 → POL-10 → POL-02 → POL-08 → POL-03 → POL-05 → POL-06 → RET-01 → POL-04 → QUA-01 → POL-07 | 政策里没写的情况应该怎么处理？ |
| IN-11 | answerable | QUA-01 | 1 | 0.7684 | 0.7684 | yes | QUA-01 → RET-01 → POL-03 → POL-02 → POL-10 → POL-05 → POL-09 → POL-04 → POL-08 → POL-06 → POL-01 → POL-07 | 定制商品签收后发现质量瑕疵，提交申请要准备什么？ |
| IN-12 | answerable | RET-01 | 1 | 0.6516 | 0.6516 | yes | RET-01 → POL-02 → QUA-01 → POL-03 → POL-06 → POL-05 → POL-01 → POL-04 → POL-10 → POL-09 → POL-08 → POL-07 | 定制商品不喜欢的话能不能七天无理由退？ |
| OUT-01 | unsupported | none | — | — | 1.1562 | no | POL-03 → POL-09 → POL-02 → POL-06 → POL-08 → POL-04 → QUA-01 → POL-10 → POL-01 → POL-05 → POL-07 → RET-01 | 你们会员积分什么时候过期，能兑换什么礼品？ |
| OUT-02 | unsupported | none | — | — | 1.1817 | no | POL-08 → POL-03 → POL-09 → POL-06 → POL-01 → POL-05 → QUA-01 → RET-01 → POL-02 → POL-10 → POL-07 → POL-04 | 能帮我把购物车里的商品改成分期付款吗？ |
| OUT-03 | unsupported | none | — | — | 1.1498 | no | POL-09 → POL-01 → POL-08 → POL-10 → RET-01 → POL-06 → POL-05 → QUA-01 → POL-03 → POL-02 → POL-04 → POL-07 | 这个店铺的优惠券可以和员工折扣一起使用吗？ |
| OUT-04 | unsupported | none | — | — | 1.1544 | no | POL-10 → POL-03 → POL-04 → POL-09 → POL-07 → POL-02 → POL-01 → POL-06 → QUA-01 → POL-05 → POL-08 → RET-01 | 你们办公桌的安装师傅周末会上门吗？ |
| OUT-05 | unsupported | none | — | — | 0.9132 | no | POL-04 → POL-03 → POL-10 → POL-01 → POL-05 → POL-02 → POL-06 → POL-08 → QUA-01 → POL-09 → POL-07 → RET-01 | 海外买的显示器坏了，保修能寄到哪个国家维修？ |
| OUT-06 | unsupported | none | — | — | 0.9072 | no | POL-09 → POL-05 → POL-08 → POL-01 → POL-03 → POL-10 → POL-02 → POL-04 → QUA-01 → POL-06 → RET-01 → POL-07 | 能不能把发票金额改高一点方便报销？ |
| OUT-07 | unsupported | none | — | — | 1.1759 | no | POL-10 → POL-09 → POL-08 → POL-03 → POL-06 → POL-02 → POL-04 → QUA-01 → POL-07 → POL-01 → POL-05 → RET-01 | 你们门店周末几点营业，地址在哪里？ |
| OUT-08 | unsupported | none | — | — | 0.9309 | no | POL-09 → POL-01 → POL-04 → POL-10 → POL-05 → POL-02 → POL-03 → POL-08 → POL-06 → QUA-01 → RET-01 → POL-07 | 购买办公设备可以开增值税专用发票吗？ |
| OUT-09 | unsupported | none | — | — | 1.0113 | no | POL-09 → POL-08 → POL-07 → POL-10 → POL-01 → POL-03 → POL-02 → POL-06 → POL-05 → POL-04 → QUA-01 → RET-01 | 能帮我开一张采购订单并同步到公司的ERP系统吗？ |
| OUT-10 | unsupported | none | — | — | 0.9453 | no | POL-01 → POL-04 → POL-03 → POL-05 → POL-02 → POL-10 → POL-09 → POL-06 → POL-08 → QUA-01 → RET-01 → POL-07 | 你们有没有以旧换新补贴，旧键盘能抵多少钱？ |
| OUT-11 | unsupported | none | — | — | 0.9752 | no | POL-07 → POL-09 → POL-06 → POL-03 → POL-02 → QUA-01 → POL-10 → POL-04 → POL-05 → POL-08 → POL-01 → RET-01 | 能不能保证今天下单明天上午十点前送到？ |
| OUT-12 | unsupported | none | — | — | 0.9285 | no | POL-08 → POL-03 → POL-05 → QUA-01 → POL-02 → POL-06 → POL-09 → POL-01 → POL-04 → POL-07 → POL-10 → RET-01 | 换货之后的新商品序列号在哪里查询？ |

## Interpretation and limits

- These probes are a small, deliberately constructed calibration sample. They are not the 45-case development set or the 15-case OOS evaluation set, and they do not establish a generalizable cutoff.
- Unsupported questions may still be close to generic fallback policies such as POL-10. Distance alone cannot determine whether a question is answerable; a single threshold can reject supported paraphrases or admit unsupported questions when the distributions overlap.
- The results support deciding whether a candidate threshold deserves a larger labeled test, not applying one. No threshold is recommended for production/demo behavior from this report alone.
- Synthetic questions and policy text were sent to the already-configured SiliconFlow Embedding endpoint. No real customer information was included.
