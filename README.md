# Healthcare Data Warehouse

Đồ án kho dữ liệu y tế xây dựng quy trình từ dữ liệu nhập viện dạng CSV đến mô
hình đa chiều phục vụ phân tích. Project sử dụng Python để chuẩn bị nguồn, SQL
Server Integration Services (SSIS) để ETL và SQL Server Analysis Services
(SSAS) để xây dựng OLAP cube.

> Dữ liệu trong repository là dữ liệu mẫu phục vụ học tập, không phải hồ sơ y tế
> thực tế. Không sử dụng project này cho quyết định lâm sàng.

## Kiến trúc

```text
       data/healthcare_admissions.csv
                 |
                 v
       prepare_sources.py
                 |
                 v
      Healthcare_Staging (SQL Server)
                 |
                 v
    HealthcareETL (SSIS package)
                 |
                 v
          HealthcareDW
       dimensions + fact tables
                 |
                 v
       HealthcareCube (SSAS)
```

Mô hình đích gồm các chiều bệnh nhân, bác sĩ, bệnh viện, bảo hiểm, thuốc, ngày,
loại nhập viện, tình trạng bệnh và kết quả xét nghiệm. Hai bảng fact lưu chi tiết
lần nhập viện và tổng hợp bệnh viện theo tháng.

## Cấu trúc repository

| Đường dẫn | Nội dung |
| --- | --- |
| `scripts/prepare_sources.py` | Tách và kiểm tra dữ liệu nguồn một cách tái lập |
| `data/` | Dataset gốc và notebook minh họa |
| `ssis/HealthcareETL/` | Project SSIS nạp staging vào data warehouse |
| `ssas/HealthcareCube/` | Project SSAS multidimensional |
| `.github/workflows/` | Kiểm tra dữ liệu tự động trên GitHub Actions |

Các database backup, file log, dữ liệu trung gian, build output và project thử
nghiệm được giữ cục bộ nhưng bị loại khỏi Git bằng `.gitignore`.

## Yêu cầu

- Python 3.10 trở lên
- SQL Server và SQL Server Management Studio
- Visual Studio 2022 với extension SQL Server Integration Services Projects
- Microsoft Analysis Services Projects
- OLE DB Driver for SQL Server 19

Project SSDT hiện đặt target là SQL Server 2025. Nếu dùng phiên bản khác, cập
nhật `TargetServerVersion` trong thuộc tính project trước khi build.

## Chuẩn bị dữ liệu

Tạo môi trường Python và sinh hai file nguồn cho staging:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/prepare_sources.py \
  --input data/healthcare_admissions.csv \
  --output-dir data
```

Kết quả gồm `patient_source.csv` và `operation_source.csv`. Script kiểm tra khóa
`source_id`, quan hệ giữa hai file và thứ tự ngày nhập/xuất viện trước khi kết
thúc.

## Chạy ETL và cube

1. Restore các database nguồn/staging và warehouse trên SQL Server cục bộ.
2. Mở `ssis/HealthcareETL.slnx` trong Visual Studio.
3. Cập nhật hai connection manager để trỏ đến SQL Server, `Healthcare_Staging`
   và `HealthcareDW` trên máy của bạn.
4. Chạy `HealthcareWarehouseLoad.dtsx`, sau đó kiểm tra bảng fact và log ETL.
5. Mở `ssas/HealthcareCube.slnx`, cập nhật data source, deploy và
   process cube trên Analysis Services.

Connection hiện dùng Windows Integrated Security và chứa tên SQL Server của máy
phát triển. Repository không chứa mật khẩu; mỗi môi trường cần cấu hình lại
connection manager hoặc SSIS environment trước khi chạy.

## Kiểm tra

Chạy lại bước chuẩn bị dữ liệu vào một thư mục tạm để xác nhận schema và ràng
buộc dữ liệu:

```bash
python scripts/prepare_sources.py \
  --input data/healthcare_admissions.csv \
  --output-dir /tmp/healthcare-extracts
```

