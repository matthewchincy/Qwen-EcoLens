# Qwen-EcoLens 🌍🍽️

**Qwen-EcoLens** is an open-source AI-powered Nutrition & ESG (Environmental, Social, and Governance) Tracker. It allows users to send food images to a Telegram bot, which analyzes them using Alibaba Cloud's **Qwen-VL** model to provide detailed nutritional info, carbon footprint estimates, and ESG scores.

## 🚀 Features

*   **AI Image Analysis**: Identifies dishes and ingredients using **Qwen-VL-Max**.
*   **Generative Video**: Creates cinematic educational videos using **Wan2.6-T2V** (running in isolated subprocess).
*   **Nutrition Tracking**: Estimates calories and healthiness (❤️/🍔).
*   **ESG & Carbon Footprint**: Calculates Carbon Emission (kg CO2e), ESG Score (1-10), and Eco-Friendly status (✅/⚠️).
*   **Multilingual**: Supports English, Bahasa Melayu, and Chinese (Auto-switching).
*   **Lazy OSS Upload**: Optimizes costs by resizing images locally and only uploading to Alibaba Cloud OSS *after* successful AI analysis.
*   **Admin Tools**: Built-in credit management and stats visualization.
*   **Async Database**: Stores user history and logs in MySQL using SQLAlchemy usage `aiomysql`.

## 🛠️ Tech Stack

*   **Backend**: Python 3.9+, FastAPI
*   **Database**: MySQL 8.0+
*   **AI Model**: Alibaba Cloud Qwen-VL (via Dashscope/OpenAI SDK)
*   **Storage**: Alibaba Cloud OSS (Object Storage Service)
*   **Bot Framework**: `python-telegram-bot`
*   **Tools**: Docker (optional), Ngrok (for local webhooks)

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/Qwen-EcoLens.git
    cd Qwen-EcoLens
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**:
    Copy `.env.example` to `.env` and fill in your credentials:
    ```bash
    cp .env.example .env
    ```
    *   `DASHSCOPE_API_KEY`: Your Alibaba Cloud Dashscope API Key.
    *   `TELEGRAM_BOT_TOKEN`: From @BotFather.
    *   `DATABASE_URL`: `mysql+aiomysql://user:pass@localhost:3306/db_name`
    *   `OSS_...`: Alibaba Cloud OSS credentials.

## 🐳 Docker Installation (Recommended)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/Qwen-EcoLens.git
    cd Qwen-EcoLens
    ```

2.  **Configure Environment**:
    Copy `.env.example` to `.env` and fill in your credentials:
    ```bash
    cp .env.example .env
    ```

3.  **Run with Docker Compose**:
    ```bash
    docker-compose up --build
    ```
    This will start both the **App** (Port 8000) and **MySQL** (Port 3307).

## 📦 Manual Installation

1.  **Create a Virtual Environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**:
    Ensure `.env` is set up.

4.  **Run the Server**:
    ```bash
    uvicorn app.main:app --reload
    ```

## 🏃 Usage

1.  **Start the Server**:
    ```bash
    uvicorn app.main:app --reload
    ```

2.  **Expose Webhook (Local)**:
    ```bash
    ngrok http 8000
    ```
    Update `WEBHOOK_URL` in `.env` with your ngrok URL.

3.  **Register Webhook**:
    ```bash
    python3 register_webhook.py
    ```

4.  **Chat with Bot**:
    Send a photo of food to your Telegram bot and get instant ESG/Nutrition insights!

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a PR.

## 📄 License

MIT License.

## 🙏 Acknowledgements

*   **Alibaba Cloud**: For Qwen-VL and Wan2.6 models.
*   **FastAPI**: For the high-performance web framework.
*   **Python Telegram Bot**: For the robust wrapper.