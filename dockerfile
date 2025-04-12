# Sử dụng image Ubuntu làm base
FROM ubuntu:20.04

# Cập nhật và cài đặt các phần mềm cần thiết
RUN apt-get update && \
    apt-get install -y \
    mongodb-clients \
    postgresql-client \
    curl \
    vim \
    && apt-get clean

# Giữ container chạy
CMD ["sleep", "infinity"]
