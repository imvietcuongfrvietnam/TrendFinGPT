FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get install -y \
    mongodb-clients \
    postgresql-client \
    curl \
    vim \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
    
CMD ["sleep", "infinity"]
