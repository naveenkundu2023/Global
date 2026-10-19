# Indian Market Alpha & Intelligence Dashboard

A Streamlit dashboard focused on Nifty 50 alpha generation, sectoral indices, research reports, global & domestic news, and FII/DII flows.

## Features

1. **Top 15 Indices generating Alpha vs Nifty 50**  
   - 1M / 2M / 3M / 6M / 12M returns + Alpha (excess return)

2. **Top 5 Alpha Indices → Top 4 Stocks**  
   - Shows the leading stocks inside those indices and their individual Alpha vs Nifty 50

3. **Latest Research Reports** (Top 15, newest first)  
   - Scraped from Moneycontrol broker research section  
   - Columns: Stock, Broker, Rating, Target, Date, Horizon hint

4. **Global News**  
   - CNBC, Bloomberg, Financial Times, Reuters, etc. (via RSS)

5. **Domestic News**  
   - Moneycontrol, Economic Times, Dalal Street Investment Journal, Zee Business, Business Standard, etc.

6. **FII / DII Dashboard**  
   - Cash market net, buy/sell figures  
   - Index futures & options positioning (where available)  
   - Last 5 sessions summary + Nifty close

## Quick Start

```bash
git clone <your-repo-url>
cd <repo>
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py