# ベースイメージの指定
FROM python:3

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    graphviz \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# ワーキングディレクトリの設定
WORKDIR /app

# 必要なPythonパッケージのインストール
COPY requirements.txt .
RUN pip install -r requirements.txt

# ソースコードのコピー
COPY . .

# コンテナ内で実行するコマンド
#CMD ["python", "your_script.py"]
