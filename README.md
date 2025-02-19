# WebServerBobby-FlaskPython

WebServerBobby-FlaskPython là một web server đơn giản giúp chạy ứng dụng Flask dễ dàng với hỗ trợ SSL.

## Hướng dẫn sử dụng

### 1. Cấu hình và chạy ứng dụng
- Mở ứng dụng WebServerBobby.
- Cấu hình SSL nếu cần thiết.
- Chọn tệp `main.py`.
- Nhấn **Run** để khởi chạy ứng dụng.
- Nhiều hướng dẫn chi tiết hơn sẽ có sẵn trên ứng dụng.

### 2. Cấu hình SSL
- Nếu muốn sử dụng **SSL**, cần chuẩn bị các tệp chứng chỉ:
  - `localhost.crt`
  - `localhost.key`
  - `localhost.csr`
- Các tệp này cần được đặt trong thư mục dự án.

### 3. Chạy ứng dụng mà không cần SSL
- Nếu không muốn sử dụng SSL, hãy chỉnh sửa dòng **66** trong `main.py`:
  ```python
  ssl=False
  ```

### 4. Lưu ý quan trọng
- Trong thư mục dự án sẽ có một tệp **`new_main.py`** để chạy ứng dụng.
- **Không xóa `new_main.py`**, vì tệp này cần thiết cho quá trình hoạt động của ứng dụng.

Chúc bạn sử dụng WebServerBobby-FlaskPython hiệu quả! 🚀
