# Eldorado API — ĐỀ XUẤT CẢI TIẾN

> Ngày: 2026-07-06
> Status: Đang xem xét

---

## Ưu tiên cao — Implement ngay được (API đã sẵn)

### 1. 📊 Revenue Dashboard

**Client đã có:** `get_payments()`, `get_pending_sum()`, `get_historical_seller_stats()`, `get_fees()`
**UI hiện tại:** Chưa dùng bất kỳ API nào trong số này.

**Đề xuất:** Thêm section "Doanh Thu Eldorado" sau profile card:
- Tổng đã nhận: `$xxx.xx` (từ `get_payments()`)
- Đang chờ: `$xx.xx` (từ `get_pending_sum()`)
- Phí sàn: `xx%` (từ `get_fees()`)
- Biểu đồ doanh thu theo tháng (`get_payments()` + groupby month)

---

### 2. 📈 Competitor Price Spy

**Client đã có:** `spy_search()` — search toàn bộ marketplace theo pet name / mutation / M/s
**UI hiện tại:** Không dùng.

**Đề xuất:** Khi expand 1 listing → thêm nút "Xem đối thủ":
- Gọi `spy_search()` với tên pet hiện tại
- Hiển thị top 5 listing rẻ nhất của đối thủ
- Gợi ý giá tối ưu: `(giá đối thủ thấp nhất + giá bạn) / 2`

---

### 3. 💰 Price History Tracking

**Vấn đề:** Mỗi lần `change_price()` → không lưu lịch sử. Không biết đã giảm bao nhiêu lần, từ giá nào.

**Đề xuất:** Lưu price history vào `session_state` hoặc Supabase:
```python
# Mỗi lần change_price thành công:
_price_history.append({
    "time": now_vn().isoformat(),
    "old": old_price,
    "new": new_price,
    "listing": title,
})
```
Hiển thị mini timeline trong expand panel.

---

### 4. 🔔 Order Notification Sound

**Vấn đề:** Notifications chỉ hiện text. Người bán bận có thể miss đơn hàng.

**Đề xuất:** Thêm JS beep khi có Pending order mới:
```python
if _pending_count > 0:
    _cmp.html(
        '<script>new Audio("data:audio/wav;base64,...").play()</script>',
        height=0,
    )
```

---

## Ưu tiên trung bình

### 5. 📦 Bulk Create Listings

**Vấn đề:** Chỉ có bulk delete / pause / resume. Không có bulk create.

**Đề xuất:** Import từ Excel/CSV → tạo listings hàng loạt:
- Upload CSV với columns: `title, price, mutation, ms`
- Preview table trước khi submit
- Tạo tuần tự với progress bar (đã có `upload_image()` + `create_listing()`)

---

### 6. 🔄 Auto-Reprice Rules

**Vấn đề:** "Giảm giá toàn bộ" hiện tại chỉ giảm 1 lần. Không có tự động.

**Đề xuất:** Thêm expander "Quy tắc tự động":
- Nếu listing Active > 7 ngày → giảm 5%
- Nếu listing Active > 14 ngày → giảm 10%
- Giá tối thiểu: `$x.xx`
- Chạy mỗi khi refresh listings

---

### 7. 📊 Listing Performance Stats

**Vấn đề:** API trả về listing data nhưng không hiển thị view / click / conversion.

**Đề xuất:** Nếu API có `viewCount`, `clickCount` trong offer data:
- Hiển thị conversion rate (views → orders)
- Flag listings "dead" (0 views trong 7 ngày)
- Gợi ý: "Listing này không ai xem → thử đổi title hoặc giảm giá"

---

### 8. 💸 Offline Mode Toggle

**Client đã có:** `switch_offline()`, `switch_online()`, `get_offline_status()`
**UI hiện tại:** Không dùng.

**Đề xuất:** Thêm toggle trong profile card:
```python
_offline = eld_client.get_offline_status()
st.toggle("Offline Mode", value=_offline, ...)
```

---

## Ưu tiên thấp (nice-to-have)

### 9. 🏷️ Volume Discount Config

Client gửi `volumeDiscounts: []` khi tạo listing. Có thể cho user set discount:
- Mua 2: giảm 5%
- Mua 5: giảm 10%
- Mua 10: giảm 15%

---

### 10. 📱 Mobile-Optimized Order Cards

Order cards hiện tại dùng 4 columns → trên mobile bị bóp méo. Cần responsive layout.

---

### 11. 🧮 Fee Calculator

Hiển thị phí thực tế sau khi bán:
```
Giá list:   $5.00
Phí sàn:   -$0.75  (15%)
Phí thanh toán: -$0.30
Thu về:     $3.95
```

---

## API Reference (eldorado_client.py)

| Method | Endpoint | Trạng thái UI |
|---|---|---|
| `get_payments()` | `/userpayment/me/payments` | ❌ Chưa dùng |
| `get_pending_sum()` | `/orders/me/pendingOrdersSum` | ❌ Chưa dùng |
| `get_historical_seller_stats()` | `/orders/me/statesCount` | ❌ Chưa dùng |
| `get_fees()` | `/fees/me/feesForGame/{id}` | ❌ Chưa dùng |
| `spy_search()` | `/v1/item-management/offers` | ❌ Chưa dùng |
| `switch_offline()` | `/offerUser/me/switchOffline` | ❌ Chưa dùng |
| `switch_online()` | `/offerUser/me/switchOnline` | ❌ Chưa dùng |
| `get_offline_status()` | `/offerUser/me` | ❌ Chưa dùng |
| `get_all_listings()` | `/v1/item-management/me/offers/me/search` | ✅ Đã dùng |
| `create_listing()` | `/v1/item-management/me/offers/item` | ✅ Đã dùng |
| `change_price()` | `/v1/item-management/me/offers/{id}/price` | ✅ Đã dùng |
| `delete_listing()` | `/v1/item-management/me/offers/{id}` | ✅ Đã dùng |
| `change_state()` | `/v1/item-management/me/offers/{id}/pause\|resume` | ✅ Đã dùng |
| `get_orders()` | `/orders/me/seller/orders` | ✅ Đã dùng |
| `get_notifications()` | `/notifications/me` | ✅ Đã dùng |
| `mark_delivered()` | `/orders/me/{id}/deliver` | ✅ Đã dùng |
