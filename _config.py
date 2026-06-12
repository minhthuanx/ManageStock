"""
Configuration constants, schemas, and column mapping.
"""
import re

# ─── Column Mapping (Python display name → Supabase snake_case) ──────────
COL_MAP = {
    "STT":           "stt",
    "Tên Pet":       "ten_pet",
    "M/s":           "ms",
    "Mutation":      "mutation",
    "Số Trait":      "so_trait",
    "NameStock":     "namestock",
    "Giá Nhập":      "gia_nhap",
    "Giá Bán":       "gia_ban",
    "Lợi Nhuận":     "loi_nhuan",
    "Doanh Thu":     "doanh_thu",
    "Ngày Nhập":     "ngay_nhap",
    "Ngày Bán":      "ngay_ban",
    "Auto Title":    "auto_title",
    "Trạng Thái":    "trang_thai",
    "time_nhap":     "time_nhap",
    "time_ban":      "time_ban",
    "Ngày Tồn":      "ngay_ton",
    "Place":         "place",
    # bulk
    "ID":                   "id",
    "Tên Lô":               "ten_lo",
    "Số Lượng Gốc":         "so_luong_goc",
    "Còn Lại":              "con_lai",
    "Giá Nhập Tổng":        "gia_nhap_tong",
    "Doanh Thu Tích Lũy":   "doanh_thu_tich_luy",
    "Số Lượng Bán":         "so_luong_ban",
    "Lợi Nhuận Giao Dịch":  "loi_nhuan_giao_dich",
    "Doanh Thu Giao Dịch":  "doanh_thu_giao_dich",
}
REVERSE_MAP = {v: k for k, v in COL_MAP.items()}

# ─── File Paths ───────────────────────────────────────────────────────────
DB_FILE       = "inventory.csv"
BULK_FILE     = "bulk_inventory.csv"
BULK_HISTORY  = "bulk_history.csv"
PET_LIST_FILE = "pet_list.csv"
NS_LIST_FILE  = "namestock_list.csv"
TRAIT_LIST    = "traits_list.csv"
OWNER_NS_FILE = "owner_namestock.txt"
BACKUP_DIR    = "backups"

EXCHANGE_RATE = 20400

# ─── Schemas ──────────────────────────────────────────────────────────────
MAIN_SCHEMA = {
    "STT":         0,
    "id":          0,
    "Tên Pet":     "",
    "M/s":         0.0,
    "Mutation":    "Normal",
    "Số Trait":    "None",
    "NameStock":   "",
    "Giá Nhập":    0.0,
    "Giá Bán":     0.0,
    "Lợi Nhuận":   0.0,
    "Doanh Thu":   0.0,
    "Ngày Nhập":   "",
    "Ngày Bán":    "-",
    "Auto Title":  "",
    "Trạng Thái":  "Còn hàng",
    "time_nhap":   "",
    "time_ban":    "",
    "Ngày Tồn":    0,
    "Place":       "",
}

BULK_SCHEMA = {
    "ID":                  0,
    "Tên Lô":              "",
    "Số Lượng Gốc":        0,
    "Còn Lại":             0,
    "Ngày Nhập":           "",
    "Giá Nhập Tổng":       0.0,
    "Doanh Thu Tích Lũy":  0.0,
    "Lợi Nhuận":           0.0,
    "Trạng Thái":          "Available",
    "Auto Title":          "",
    "NameStock":           "",
}

HISTORY_SCHEMA = {
    "Ngày Bán":             "",
    "Tên Lô":               "",
    "Số Lượng Bán":         0,
    "Lợi Nhuận Giao Dịch":  0.0,
    "Doanh Thu Giao Dịch":  0.0,
}

LIST_SCHEMA = {"Name": ""}

MUTATION_OPTIONS = [
    "Normal", "Gold", "Diamond", "Bloodrot", "Candy",
    "Divine", "Lava", "Galaxy", "Yin-Yang", "Radioactive",
    "Cursed", "Rainbow", "Cyber",
]

MUTATION_ICONS = {
    "gold": "👑", "diamond": "💎", "bloodrot": "🩸", "candy": "🍬",
    "divine": "✨", "lava": "🌋", "galaxy": "🌌", "yin-yang": "☯️",
    "radioactive": "☢️", "cursed": "😈", "rainbow": "🌈", "cyber": "🤖",
}
