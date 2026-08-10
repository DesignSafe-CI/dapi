FROM tacc/tacc-base:ubuntu22.04-impi19.0.9-common

RUN pip3 install --no-cache-dir numpy || \
    (apt-get update && apt-get install -y --no-install-recommends \
     python3 python3-pip && rm -rf /var/lib/apt/lists/* && \
     pip3 install --no-cache-dir numpy)

COPY site_response.py /opt/app/site_response.py

CMD ["python3", "/opt/app/site_response.py"]
