# 🚀 Real-Time Stream Analytics Engine

An end-to-end Big Data Analytics (BDA) project combining **Cloud NoSQL (MongoDB)**, **Probabilistic Data Structures (Bloom Filter)**, and **Streaming Cardinality Estimation (Flajolet-Martin Algorithm)** with an interactive **Streamlit Dashboard**.

---

## 📌 Project Overview

Processing high-velocity streaming data (such as web server logs or clickstreams) poses significant memory and CPU challenges for traditional relational databases. This project demonstrates how modern streaming architectures leverage probabilistic algorithms and NoSQL databases to analyze millions of events on-the-fly with minimal memory footprint.

### Key Objectives
1. **Data Ingestion & Descriptive Analytics (MongoDB):** Ingest 50,000+ streaming web logs into MongoDB Atlas and compute aggregations (top pages, user action breakdown).
2. **Duplicate / Returning User Detection (Bloom Filter):** Use a bit array with MurmurHash3 (`mmh3`) to identify repeat visitors in $O(k)$ time using only kilobytes of RAM.
3. **Cardinality Estimation (Flajolet-Martin PCSA):** Estimate distinct visitors in the stream by counting trailing zeros of hashed IDs using Probabilistic Counting with Stochastic Averaging (PCSA).
4. **Interactive Dashboard & Visualization:** An interactive Streamlit web dashboard to trigger pipeline experiments and visualize accuracy/memory trade-offs.

---

## 🏗️ Architecture Pipeline

```
[ Web Log Generator ]
         │
         ▼ (50,000+ logs)
[ MongoDB Atlas (Cloud NoSQL) ]
         │
         ├──► [ MongoDB Aggregation ] ──► Top Pages & Action Distribution
         │
         ├──► [ Bloom Filter ] ────────► Real-Time Duplicate Detection (Bits)
         │
         └──► [ Flajolet-Martin PCSA ] ─► Distinct User Cardinality Estimation
                     │
                     ▼
       [ Streamlit Interactive Dashboard ]
```

---

## 📁 Repository Structure

```text
├── dashboard.py                  # Streamlit Web Dashboard (interactive UI)
├── ingest_data.py                # MongoDB Atlas ingestion & synthetic stream generator
├── bloom_filter.py               # Standalone Bloom Filter duplicate detector
├── flajolet_martin.py            # Standalone Flajolet-Martin PCSA cardinality estimator
├── visualization.py              # Matplotlib visualization script
├── visualization.R               # R (ggplot2) visualization script
├── Mini_Project_Report_Template.html # Formatted report template (Times New Roman)
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment configuration template
└── .gitignore                    # Git ignore file
```

---

## ⚡ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/bda-stream-analytics.git
cd bda-stream-analytics
```

### 2. Set Up a Virtual Environment & Install Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run the Interactive Dashboard
```bash
streamlit run dashboard.py
```
Open your browser at `http://localhost:8501`.

---

## 🔬 Standalone CLI Scripts

### Step 1: Ingest Data to MongoDB
Configure your `MONGO_URI` environment variable, then run:
```bash
python ingest_data.py
```

### Step 2: Run Bloom Filter Duplicate Detection
```bash
python bloom_filter.py
```

### Step 3: Run Flajolet-Martin Cardinality Estimation
```bash
python flajolet_martin.py
```

### Step 4: Generate Plot
```bash
python visualization.py
```

---

## 📊 Theoretical Highlights

### 1. Bloom Filter
- **Space complexity:** $m = -\frac{n \ln(p)}{(\ln 2)^2}$ bits.
- **Optimal hash functions:** $k = \frac{m}{n} \ln(2)$.
- Guarantees zero false negatives with bounded false positives ($p \le 1\%$).

### 2. Flajolet-Martin Algorithm (PCSA)
- Counts trailing zeros $R$ in binary hashes: $P(R = r) = 2^{-(r+1)}$.
- Employs **Stochastic Averaging** with $m = 2^k$ buckets to minimize estimation variance.
- Correction factor: $\phi \approx 0.77351$.
- Estimate: $\hat{N} = \frac{m}{\phi} \cdot 2^{\frac{1}{m} \sum_{i=1}^{m} R_i}$.

---

## 📜 License
This project is open-source under the MIT License.
