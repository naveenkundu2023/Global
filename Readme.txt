# Indian Market Alpha & Intelligence Dashboard

Streamlit dashboard for Nifty 50 alpha, sectoral indices, research reports, global & domestic news, and FII/DII flows.

## Features

1. Top 15 Indices generating Alpha vs Nifty 50 (1M / 2M / 3M / 6M / 12M)
2. Top 5 Alpha Indices → their top 4 stocks + Alpha
3. Latest Research Reports (Top 15)
4. Global News (CNBC, Bloomberg, FT, etc.)
5. Domestic News (Moneycontrol, ET, Business Standard, etc.)
6. FII / DII section

## Quick Start

```bash
git clone <your-repo-url>
cd <repo>
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
