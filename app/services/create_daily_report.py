# app/services/create_daily_report.py
from openai import OpenAI
from app.core.config import settings
import json

def build_prompt(payload: dict) -> str:
    return f"""
Bạn là chuyên gia viết báo cáo giám sát chất lượng Internet (văn phong hành chính – kỹ thuật).

NGUYÊN TẮC BẮT BUỘC:
1) CHỈ sử dụng dữ liệu trong JSON, KHÔNG tự bịa số liệu, KHÔNG suy đoán nguyên nhân nếu không có dữ liệu.
2) Nếu thiếu dữ liệu để kết luận ở mục nào, ghi đúng câu: "Thiếu dữ liệu để kết luận".
3) Khi so sánh ngày D với ngày D-1: phải nêu rõ số liệu ngày D, ngày D-1, và chênh lệch tuyệt đối + % (nếu có đủ).
4) Với KPI internet_latency: giá trị tăng nghĩa là độ trễ tăng (xấu hơn), giá trị giảm nghĩa là độ trễ giảm (tốt hơn).
5) Với danh sách tỉnh: dùng change_value để kết luận tăng/giảm so với ngày hôm trước:
   - change_value > 0: tăng (xấu hơn)
   - change_value < 0: giảm (tốt hơn)
   - change_value = 0: không đổi
6) Với bất thường theo giờ: dựa trên các trường *z*:
   - Nếu |z| >= 3.5: bất thường mức CAO
   - Nếu 3 <= |z| < 3.5: bất thường mức TRUNG BÌNH
   - Nếu |z| < 2: không coi là bất thường (không đưa vào báo cáo)

ĐẦU RA: Viết báo cáo NGẮN gọn, rõ ràng, đúng cấu trúc TEMPLATE dưới đây. Không thêm mục ngoài template.

TEMPLATE:
BÁO CÁO GIÁM SÁT KPI INTERNET LATENCY – MẠNG {{isp}} – NGÀY {{report_date}}

1. Tổng quan toàn mạng
- KPI: internet_latency
- Giá trị ngày {{report_date}}: ...
- Giá trị ngày {{prev_date}}: ...
- Chênh lệch tuyệt đối: ...
- Chênh lệch tương đối: ...%
- Nhận xét: ... (tốt hơn/xấu hơn theo quy tắc)

2. Biến động theo tỉnh/thành (ngày {{report_date}} so với {{prev_date}})
- Tóm tắt: số tỉnh tăng / giảm / không đổi (nếu có đủ dữ liệu)
- Top tỉnh tăng mạnh (xấu hơn): tối đa 5 tỉnh theo change_value giảm dần
- Top tỉnh giảm mạnh (tốt hơn): tối đa 5 tỉnh theo change_value tăng dần (âm lớn nhất)
Mỗi dòng:
  - {{province_name}} ({{area_name}}): kpi_value={{kpi_value}}, change_value={{change_value}} → (tăng/giảm/không đổi)

3. Điểm bất thường theo giờ trong ngày {{report_date}}
Chỉ liệt kê các điểm có |z| >= 3 theo từng KPI thành phần (latency/jitter/packet_loss) nếu có.
Mỗi điểm:
- Thời điểm: {{testing_time}} | Agent: {{account_login_vqt}} | Server: {{server_name}}
  + Latency: mean={{mean_average_latency}}, z={{mean_average_latency__z}} → mức (TRUNG BÌNH/CAO)
  + Jitter: mean={{mean_jitter}}, z={{mean_jitter__z}} → mức (TRUNG BÌNH/CAO)
  + Packet loss: mean={{mean_packet_loss_rate}}, z={{mean_packet_loss_rate__z}} → mức (TRUNG BÌNH/CAO)

4. Kết luận ngắn
- Tình trạng chung: ...
- Khu vực/tỉnh cần theo dõi: ... (dựa theo phần 2)
- Khung giờ cần theo dõi: ... (dựa theo phần 3)
Nếu thiếu dữ liệu ở phần nào, ghi rõ "Thiếu dữ liệu để kết luận".

DỮ LIỆU (JSON):
{json.dumps(payload, ensure_ascii=False, indent=2)}
""".strip()


def main():
    # 1) Khởi tạo client OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY
    )

    # 2) Payload dữ liệu bạn cung cấp (có thể thay bằng dữ liệu thật của bạn)
    payload = {
        "report_date": "2026-01-20",
        "prev_date": "2026-01-19",
        "isp": "Viettel",

        "network_kpi": [
            {
                "testing_time": "2026-01-20",
                "date_hour": "2026-01-20-00",
                "province_code": None,
                "province_name": None,
                "area_name": None,
                "country": "VNM",
                "location_level": "network",
                "isp": "Viettel",
                "kpi_code": "internet_latency",
                "kpi_value": 28.0,
                "created_at": "2026-01-21T00:20:55.607710"
            },
            {
                "testing_time": "2026-01-19",
                "date_hour": "2026-01-19-00",
                "province_code": None,
                "province_name": None,
                "area_name": None,
                "country": "VNM",
                "location_level": "network",
                "isp": "Viettel",
                "kpi_code": "internet_latency",
                "kpi_value": 24.69,
                "created_at": "2026-01-20T00:03:12.844798"
            }
        ],

        "province_changes": {
            "success": True,
            "aggregate_level": "daily",
            "kpi_code": "internet_latency",
            "isp": "Viettel",
            "total": 34,
            "data": [
                {
                    "testing_time": "2026-01-20",
                    "date_hour": "2026-01-20-00",
                    "province_code": "CMU",
                    "province_name": "Cà Mau",
                    "area_name": "Khu vực 3",
                    "country": "VNM",
                    "location_level": "province",
                    "isp": "Viettel",
                    "kpi_code": "internet_latency",
                    "kpi_value": 38.63,
                    "created_at": "2026-01-21T00:20:55.607710",
                    "change_value": 8.3
                },
                {
                    "testing_time": "2026-01-20",
                    "date_hour": "2026-01-20-00",
                    "province_code": "AGG",
                    "province_name": "An Giang",
                    "area_name": "Khu vực 3",
                    "country": "VNM",
                    "location_level": "province",
                    "isp": "Viettel",
                    "kpi_code": "internet_latency",
                    "kpi_value": 38.6,
                    "created_at": "2026-01-21T00:20:55.607710",
                    "change_value": 8.22
                },
                {
                    "testing_time": "2026-01-20",
                    "date_hour": "2026-01-20-00",
                    "province_code": "CTO",
                    "province_name": "Cần Thơ",
                    "area_name": "Khu vực 3",
                    "country": "VNM",
                    "location_level": "province",
                    "isp": "Viettel",
                    "kpi_code": "internet_latency",
                    "kpi_value": 38.65,
                    "created_at": "2026-01-21T00:20:55.607710",
                    "change_value": 8.15
                }
            ]
        },

        "hour_anomalies": [
            {
                "account_login_vqt": "CMU_Agent_1",
                "aggregate_level": "hour",
                "isp": "Viettel",
                "mean_average_latency": 118.28,
                "mean_jitter": 0.85,
                "mean_packet_loss_rate": 1.44,
                "sample_count": 45,
                "server_name": "Japan_Speedtest",
                "testing_time": "2026-01-20 14:00:00.000000",
                "mean_jitter__z": -0.12514475091984553,
                "mean_average_latency__z": 1.6148452512472187,
                "mean_packet_loss_rate__z": 6.94307119425173,

                "mean_jitter__mean_hist": 1.01125,
                "mean_jitter__std_hist": 1.2885078983718594,
                "mean_average_latency__mean_hist": 106.37916666666666,
                "mean_average_latency__std_hist": 7.369643205218445,
                "mean_packet_loss_rate__mean_hist": 0.10375000000000001,
                "mean_packet_loss_rate__std_hist": 0.19245805820143408
            },
            {
                "account_login_vqt": "CMU_Agent_1",
                "aggregate_level": "hour",
                "isp": "Viettel",
                "mean_average_latency": 129.63,
                "mean_jitter": 6.28,
                "mean_packet_loss_rate": 0.07,
                "sample_count": 44,
                "server_name": "Japan_Speedtest",
                "testing_time": "2026-01-20 18:00:00.000000",
                "mean_jitter__z": 7.647009897915379,
                "mean_average_latency__z": 3.586580261637429,
                "mean_packet_loss_rate__z": 0,

                "mean_jitter__mean_hist": 0.7445833333333334,
                "mean_jitter__std_hist": 0.7238668107616356,
                "mean_average_latency__mean_hist": 106.17041666666665,
                "mean_average_latency__std_hist": 6.540933597460614,
                "mean_packet_loss_rate__mean_hist": 0.125,
                "mean_packet_loss_rate__std_hist": 0.3053959178945694
            }
        ]
    }

    # 3) Tạo prompt
    prompt = build_prompt(payload)

    # (Tuỳ chọn) In prompt để debug
    # print(prompt)

    # 4) Gọi LLM
    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b:free",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    # 5) In báo cáo
    print(resp.choices[0].message.content)


if __name__ == "__main__":
    main()
