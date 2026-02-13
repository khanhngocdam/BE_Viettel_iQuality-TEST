from collections import defaultdict
import re
from datetime import datetime

from app.services.get_kpi_data import AggregateLevel

kpi_code_map = {
        "internet_latency": "Độ trễ mạng",
        "internet_jitter": "Độ biến thiên mạng",
        "internet_packet_loss_rate": "Tỷ lệ mất gói tin",
        "internet_dns_time": "Thời gian phân giải DNS",
        "internet_data_downloading": "Tốc độ tải xuống",
        "internet_web_browsing": "Thời gian duyệt web",
    }


def _period_key(entry: dict, aggregate_level: AggregateLevel) -> str:
    """Lấy key nhóm theo tuần hoặc ngày từ một record."""
    if aggregate_level == AggregateLevel.weekly:
        return entry["week_of_year"]
    # daily (hoặc monthly nếu sau này cần): dùng date_hour, chuẩn hóa về YYYY-MM-DD
    date_hour = entry.get("date_hour", "")
    if not date_hour:
        return date_hour
    # date_hour có dạng "YYYY-MM-DD-HH24" hoặc "YYYY-MM-DD"
    parts = date_hour.split("-")
    if len(parts) >= 3:
        return f"{parts[0]}-{parts[1]}-{parts[2]}"
    return date_hour


def _period_label(period_key: str, aggregate_level: AggregateLevel) -> str:
    """Chuyển period key thành label hiển thị dạng text (Tuần 01 năm 2025 / Ngày DD/MM/YYYY)."""
    if aggregate_level == AggregateLevel.weekly:
        match = re.match(r"W(\d{2})-(\d{4})", period_key)
        if match:
            return f"Tuần {match.group(1)} năm {match.group(2)}"
        return f"Tuần {period_key}"
    # daily: period_key là "YYYY-MM-DD"
    try:
        dt = datetime.strptime(period_key, "%Y-%m-%d")
        return f"Ngày {dt.strftime('%d/%m/%Y')}"
    except ValueError:
        return f"Ngày {period_key}"


# Hàm xử lý và format dữ liệu đầu ra (hỗ trợ theo tuần hoặc theo ngày)
def promt_internet_kpi_general(data, aggregate_level: AggregateLevel = AggregateLevel.weekly):
    result = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

    for entry in data:
        period = _period_key(entry, aggregate_level)
        isp = entry["isp"]
        kpi_code = entry["kpi_code"]
        kpi_value = entry["kpi_value"]
        result[period][isp][kpi_code] = kpi_value
    isp_order = ["Viettel", "VNPT", "FPT"]
    output = f"Chỉ số {kpi_code_map[data[0]['kpi_code']]} thể hiện tỉ lệ mẫu đo tồi, không đạt yêu cầu của các nhà mạng:\n"

    for period_key, isps in result.items():
        output += f"\n{_period_label(period_key, aggregate_level)}:\n"
        for isp in isp_order:
            if isp in isps:
                for kpi_code, kpi_value in isps[isp].items():
                    output += f"    {isp} - {kpi_code_map[kpi_code]}: tỉ lệ mẫu tồi là {kpi_value}\n"

    return output


def _period_text_for_change(data: list, aggregate_level: AggregateLevel) -> str:
    """Parse period từ data (record đầu) thành text dùng trong prompt (tuần X năm Y hoặc ngày DD/MM/YYYY)."""
    if not data:
        return ""
    if aggregate_level == AggregateLevel.weekly:
        week_of_year = data[0].get("week_of_year", "")
        match = re.match(r"W(\d{2})-(\d{4})", week_of_year)
        if match:
            return f"tuần {match.group(1)} năm {match.group(2)}"
        return "tuần " + week_of_year
    # daily: dùng date_hour (YYYY-MM-DD-HH24 hoặc YYYY-MM-DD)
    date_hour = data[0].get("date_hour", "")
    parts = date_hour.split("-")
    if len(parts) >= 3:
        try:
            dt = datetime.strptime(f"{parts[0]}-{parts[1]}-{parts[2]}", "%Y-%m-%d")
            return f"ngày {dt.strftime('%d/%m/%Y')}"
        except ValueError:
            pass
    return "ngày " + date_hour


def promt_kpi_change(data, kpi_code, isp, aggregate_level: AggregateLevel = AggregateLevel.weekly):
    period_text = _period_text_for_change(data, aggregate_level)
    prev_label = "tuần trước" if aggregate_level == AggregateLevel.weekly else "ngày trước"

    output = f"Chỉ số {kpi_code_map[kpi_code]} (tỉ lệ mẫu đo không đạt yêu cầu) chi tiết các tỉnh thành của {isp} {period_text} so với {prev_label}:\n"

    grouped_by_area = defaultdict(list)
    for entry in data:
        area_name = entry["area_name"]
        province_name = entry["province_name"]
        kpi_value = entry["kpi_value"]
        change_value = entry["change_value"]
        previous_value = kpi_value - change_value
        change_text = "tăng" if change_value > 0 else "giảm"
        grouped_by_area[area_name].append(
            f"{province_name}: {kpi_value} (tỉ lệ mẫu tồi), giá trị của {prev_label} là {previous_value} tức {change_text} {abs(change_value)}."
        )

    for area, provinces in grouped_by_area.items():
        output += f"\n{area}:\n"
        for province_info in provinces:
            output += f"  - {province_info}\n"

    promt_system = f"""
Hãy đưa ra phân tích, nhận định một cách ngắn gọn về {kpi_code_map[kpi_code]} ( tỉ lệ mẫu đo tồi, không đạt yêu cầu ) của mạng {isp} trong {period_text}, bạn có thể phân tích theo khu vực, theo thời gian,
so sánh giữa các nhà mạng với nhau, hoặc xu hướng và sự tăng giảm bất thường của {period_text} so với quá khứ.
Bạn cần linh hoạt và chỉ phân tích những thông tin nổi bật, không dài dòng lan man, không suy diễn nguyên nhân mà tập trung vào dữ liệu:
Tỉ lệ mẫu tồi là tỉ lệ mẫu đo không đạt yêu cầu, chỉ số càng cao thì chất lượng càng xấu, nếu chỉ số này giảm thì chất lượng cải thiện, bạn coi tỉ lệ mẫu tồi là 1 KPI mạng, đừng nhận xét nó là %.
"""
    return promt_system + output
