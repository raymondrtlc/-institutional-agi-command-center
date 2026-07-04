# Institutional AGI Command Center
## SPY / ES Futures Real-Time Analysis System

**Real-time institutional trading analysis platform with multi-indicator fusion, gamma profiling, and AI ensemble forecasting.**

### 🎯 Core Features

#### 1. Live Market Data
- ✅ ES (E-mini S&P 500) futures real-time OHLCV
- ✅ Multi-timeframe scanning (Monthly → 5-min)
- ✅ Dark pool tape monitoring
- ✅ Option flow analysis (0DTE positioning)
- ✅ Gamma exposure & flip detection

#### 2. Technical Analysis Suite
- ✅ **量价分析** (Price-Volume Analysis)
- ✅ **缠论** (Elliott Wave + Trend Continuation)
- ✅ **Wyckoff Accumulation/Distribution**
- ✅ Candlestick reversal patterns (multi-TF)
- ✅ Market structure & order flow analysis

#### 3. Market Intelligence
- ✅ Reuters/CNBC/WSJ/CNN real-time news feed
- ✅ Earnings calendar & impact projection
- ✅ Economic events (NFP, CPI, FOMC, etc.)
- ✅ MAG7 leadership analysis
- ✅ Sector rotation tracking
- ✅ Short squeeze probability scoring

#### 4. Quantitative Analysis
- ✅ Gamma exposure (dealer positioning)
- ✅ Max Pain analysis
- ✅ CNN Fear & Greed Index
- ✅ Market breadth indicators
- ✅ Bond/FX/Oil/Gold correlations

#### 5. AI Ensemble Forecasting
- ✅ ARIMA (statistical baseline)
- ✅ LSTM (sequence modeling)
- ✅ BiLSTM-Attention (bidirectional context)
- ✅ XGBoost (non-linear patterns)
- ✅ TabPFN (tabular deep learning)
- ✅ DLSTM (deep LSTM layers)
- ✅ AutoML model selection

#### 6. Risk & Probability
- ✅ Bull/Base/Bear probability tree
- ✅ Entry/Exit zone identification
- ✅ Reversal probability scoring
- ✅ Support/Resistance zone mapping
- ✅ Squeeze setup detection

#### 7. Dashboard & Visualization
- ✅ 15-min real-time price path forecast
- ✅ Multi-timeframe heatmap
- ✅ Option flow chart
- ✅ Gamma/Dark pool overlay
- ✅ Probability distribution charts
- ✅ Comparative ML model forecasts

---

## 📁 Project Structure

```
institutional-agi-command-center/
├── README.md (this file)
├── requirements.txt
├── config/
│   ├── settings.yaml
│   ├── api_keys.example.env
│   └── model_config.json
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── data_engine.py (Central data orchestration)
│   │   ├── feed_manager.py (Real-time OHLCV streams)
│   │   └── cache_manager.py (Time-series cache)
│   ├── market_data/
│   │   ├── futures_data.py (ES/MES futures)
│   │   ├── options_data.py (Option chain, Greeks)
│   │   ├── news_aggregator.py (Reuters, CNBC, WSJ, CNN)
│   │   ├── economic_calendar.py (NFP, CPI, FOMC)
│   │   └── dark_pool.py (Dark pool tape)
│   ├── technical_analysis/
│   │   ├── price_volume.py (量价分析)
│   │   ├── chan_theory.py (缠论 - Elliott + Continuation)
│   │   ├── wyckoff.py (Accumulation/Distribution)
│   │   ├── candlestick.py (Reversal patterns)
│   │   ├── multitf_sync.py (Multi-timeframe coherence)
│   │   ├── support_resistance.py (S/R zones)
│   │   └── market_structure.py (Order flow, breakouts)
│   ├── market_intelligence/
│   │   ├── gamma_exposure.py (Dealer positioning, flips)
│   │   ├── option_flow.py (Flow analysis, max pain)
│   │   ├── mag7_analysis.py (Leadership tracking)
│   │   ├── sector_rotation.py (Sector strength)
│   │   ├── breadth_analysis.py (Market breadth)
│   │   ├── fear_greed.py (CNN Fear & Greed Index)
│   │   ├── squeeze_detector.py (Short squeeze probability)
│   │   └── correlation_monitor.py (Bond/FX/Oil/Gold)
│   ├── ml_ensemble/
│   │   ├── models/
│   │   │   ├── arima_model.py
│   │   │   ├── lstm_model.py
│   │   │   ├── bilstm_attention_model.py
│   │   │   ├── xgboost_model.py
│   │   │   ├── tabpfn_model.py
│   │   │   └── dlstm_model.py
│   │   ├── ensemble.py (Model aggregation)
│   │   ├── feature_engineering.py (Technical + Market features)
│   │   ├── automl.py (AutoML model selection)
│   │   └── probability_tree.py (Bull/Base/Bear scenarios)
│   ├── visualization/
│   │   ├── dashboard.py (Main Streamlit dashboard)
│   │   ├── charts.py (Plotly + Matplotlib)
│   │   ├── multitf_heatmap.py (Timeframe alignment)
│   │   ├── probability_viz.py (Forecast distributions)
│   │   ├── option_flow_viz.py (Flow charts)
│   │   └── gamma_overlay.py (Gamma + price chart)
│   ├── risk_management/
│   │   ├── entry_exit_zones.py
│   │   ├── stop_loss_calculator.py
│   │   └── position_sizer.py
│   └── utils/
│       ├── logger.py
│       ├── validators.py
│       ├── helpers.py
│       └── constants.py
├── notebooks/
│   ├── 01_eda_es_data.ipynb
│   ├── 02_technical_indicator_backtest.ipynb
│   ├── 03_ml_model_training.ipynb
│   └── 04_live_analysis_demo.ipynb
├── tests/
│   ├── test_technical_analysis.py
│   ├── test_ml_models.py
│   ├── test_data_feeds.py
│   └── test_market_intelligence.py
├── scripts/
│   ├── backtest_engine.py
│   ├── paper_trading.py
│   └── live_monitor.py
└── docker/
    ├── Dockerfile
    └── docker-compose.yml
```

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/raymondrtlc/-institutional-agi-command-center.git
cd -institutional-agi-command-center
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Keys
```bash
cp config/api_keys.example.env config/api_keys.env
# Edit with your API keys for:
# - AlphaVantage / Polygon.io (Options/Futures)
# - NewsAPI / MediaStack (News feeds)
# - OpenAI (for economic event analysis)
```

### 3. Run Live Dashboard
```bash
streamlit run src/visualization/dashboard.py
```

### 4. Run Analysis in Jupyter
```bash
jupyter notebook notebooks/04_live_analysis_demo.ipynb
```

---

## 📊 Key Modules Overview

### **Data Engine** (`src/core/data_engine.py`)
Orchestrates real-time data from multiple sources with conflict resolution and time-series coherence.

### **Technical Analysis** (`src/technical_analysis/`)
- **量价分析**: Volume profile, VWAP, OBV, accumulation/distribution
- **缠论**: Fractal structure, trend lines, continuation patterns
- **Wyckoff**: Schematic (accumulation → markup → distribution → markdown)
- **Multi-TF Sync**: Ensures signals align across Monthly/Weekly/Daily/4H/1H/30min/15min/5min

### **Market Intelligence** (`src/market_intelligence/`)
Fuses:
- Option gamma exposure (dealer short/long positioning)
- Real-time news impact scoring
- Economic calendar events
- MAG7 (NVIDIA, Tesla, Apple, Microsoft, Google, Amazon, Meta) dominance
- Short squeeze probability from borrow rates + option flow

### **ML Ensemble** (`src/ml_ensemble/`)
**Comparative forecasting** (all models score independently):
1. **ARIMA**: Statistical mean reversion
2. **LSTM**: Univariate sequence patterns
3. **BiLSTM-Attention**: Bidirectional + attention weights
4. **XGBoost**: Non-linear feature interactions
5. **TabPFN**: Few-shot deep learning on tabular data
6. **DLSTM**: Deep stacked LSTM layers

**Ensemble aggregates** via:
- Weighted voting (model confidence)
- Probability weighting (prediction intervals)
- Kalman filtering (smooth forecasts)

### **Dashboard** (`src/visualization/dashboard.py`)
Real-time Streamlit dashboard showing:
1. **15-min ES price path forecast** (next 2 hours)
2. **Multi-timeframe heatmap** (alignment score per TF)
3. **Option flow chart** (calls vs puts, IV rank)
4. **Gamma exposure overlay** (price levels, dealer positioning)
5. **Probability tree** (Bull/Base/Bear scenarios with %)
6. **News feed** (Reuters, CNBC, WSJ, CNN with impact scoring)
7. **Comparative ML forecasts** (model-by-model confidence)
8. **Sector heatmap** (relative strength)
9. **Economic calendar** (next events + impact)
10. **Short squeeze meter** (probability score)

---

## 🔄 Data Flow

```
Live Market Data (ES OHLCV, Options, News)
    ↓
[Data Engine] → Validation + Coherence Check
    ↓
[Technical Analysis] → Indicators + Patterns
    ↓
[Market Intelligence] → Gamma, News, Breadth
    ↓
[Feature Engineering] → 50+ technical features
    ↓
[ML Ensemble] → 6 models in parallel
    ↓
[Probability Tree] → Bull/Base/Bear scenarios
    ↓
[Dashboard] → Real-time visualization + 15-min forecast
    ↓
[Risk Management] → Entry/Exit zones + Position sizing
```

---

## 📈 Timeframe Analysis Strategy

**Scan Order (Institutional approach)**:
1. **Monthly** → Market regime (bull/bear/correction)
2. **Weekly** → Major structure (impulse/consolidation)
3. **Daily** → Week confirmation + swing setup
4. **4H** → Mid-term bias
5. **1H** → Trade setup initiation
6. **30min** → Entry refinement
7. **15min** → Entry/Exit execution (primary trading TF)
8. **5min** → Micro structure validation

**Pattern Recognition**:
- Reversal UP: Double bottom, inverse H&S, bullish divergence
- Reversal DOWN: Double top, H&S, bearish divergence
- Continuation: Flag, pennant, wedge breakout

---

## 🎲 Probability Model

**Each ML model outputs**:
- Point forecast (15-min price target)
- Prediction interval (confidence bounds)
- Probability of up/down move

**Probability Tree combines**:
```
Bull Scenario (60% confidence)
├─ ES +15 to +35 pts (70% prob)
├─ Reversal at 4850 support (technical + option gamma)
└─ Triggers if: Breadth > 2:1, Gamma > $500M short

Base Scenario (25% confidence)
├─ Range-bound 4820-4880 (consolidation)
└─ Triggers if: Conflicting TF signals

Bear Scenario (15% confidence)
├─ ES -20 to -45 pts (break below major support)
└─ Triggers if: Breadth collapses, Gamma turns long
```

---

## 🔧 Technology Stack

| Layer | Tools |
|-------|-------|
| **Data** | pandas, numpy, yfinance, Polygon.io, AlphaVantage |
| **ML** | PyTorch, TensorFlow, XGBoost, statsmodels, TabPFN |
| **News** | NewsAPI, MediaStack, webscraping |
| **Viz** | Streamlit, Plotly, Matplotlib |
| **API** | FastAPI (optional live server) |
| **Cloud** | AWS/GCP (optional deployment) |

---

## ⚡ Performance Targets

- **Data latency**: < 500ms (OHLCV update)
- **Indicator calc**: < 200ms (all 50+ features)
- **ML inference**: < 1s (6-model ensemble)
- **Dashboard refresh**: 2-5s (Streamlit throttle)
- **Forecast horizon**: 15-min to 2-hour ahead

---

## 📝 Development Roadmap

### Phase 1: Data Foundation ✅ (This sprint)
- [x] Project skeleton
- [ ] Data engine + feed manager
- [ ] ES OHLCV real-time stream
- [ ] Options data pipeline
- [ ] News aggregator stub

### Phase 2: Technical Analysis 🔄
- [ ] 量价分析 full implementation
- [ ] 缠论 pattern recognition
- [ ] Wyckoff schematic detector
- [ ] Multi-TF coherence checker

### Phase 3: Market Intelligence 🔄
- [ ] Gamma exposure calculator
- [ ] Option flow real-time
- [ ] News sentiment scoring
- [ ] Economic calendar integration

### Phase 4: ML Ensemble 🔄
- [ ] ARIMA baseline
- [ ] LSTM univariate
- [ ] XGBoost multivariate
- [ ] BiLSTM-Attention
- [ ] TabPFN integration
- [ ] Ensemble aggregator

### Phase 5: Dashboard & Live Trading 🔄
- [ ] Streamlit dashboard
- [ ] 15-min forecast path
- [ ] Paper trading integration
- [ ] Backtest engine

---

## 📞 Support & Contributions

For issues, feature requests, or analysis improvements, open an issue on this repo.

**Disclaimer**: This is a research/educational tool. Not investment advice. Always manage risk appropriately.

---

**Built with institutional-grade rigor. Trade with discipline.**
