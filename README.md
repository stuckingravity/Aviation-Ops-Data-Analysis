# Flight Turnaround Analysis - Tarmac Technologies

A comprehensive analysis of airline ground operations data to identify delay patterns, root causes, and data quality improvements for AGOA.

## 📊 Project Overview

This case study analyzes 52 flight turnarounds across 3 airports (ORY, SFO, PPT) over a 15-day period (Feb 14-28, 2025) to:
- Measure operational KPIs (On-Time Performance, ADC Compliance)
- Identify delay responsibility (Ground Ops vs ATC)
- Perform root cause analysis using phase-based dependency logic
- Provide data platform recommendations for Tarmac Technologies

**Key Findings:**
- 76.9% OTP (below 80% target) — systemic issue across all airports
- 75% of delays caused by ground operations, not ATC
- Bag Delivery is the #1 root cause (43% of delays, €180K-370K annual impact)
- A35K aircraft shows 58% OTP vs 82% for A359 (requires dedicated procedures)

---

## 📁 Repository Structure

```
Aviation-Ops-Data-Analysis/
│
├── analysis/
│   ├── tarmac_metrics.ipynb                      # Data integrity checks (SQL)
│   └── turnaround_performance_analysis.ipynb     # KPI analysis & root cause logic
│
├── dashboard/
│   ├── turnaround_dashboard.html                 # Interactive flight-level dashboard
│   └── turnaround_dashboard.pdf                  # Static dashboard export
│
├── presentation/
│   └── Flight Turnaround Analysis - Tarmac Technologies.pdf
│       # 16-slide deck with business insights & recommendations
│
└── README.md
```


## 🎯 Methodology Highlights

### KPI 1: On-Time Performance (OTP)
- **Definition:** ATD - STD ≤ 15 minutes (IATA standard)
- **Result:** 76.9% (40/52 flights on-time)
- **Segmentation:** By airport and aircraft type to isolate performance drivers

### KPI 2: ADC Compliance
- **Definition:** Actual Door Close ≤ Target Door Close Time
- **Result:** 72.0% (36/50 valid flights)
- **Why this matters:** Isolates ground handling performance from ATC delays

### KPI 3: Delay Responsibility & Root Cause
- **Responsibility Split:** Ground Ops (75%) vs ATC/Pushback (17%) vs Unknown (8%)
- **Root Cause Logic:** Phase-based dependency analysis to identify the "first domino"
  - Phase 1: Arrival (Disembark, Offloading, Bag Delivery)
  - Phase 2: Ground Services (Cleaning, Catering, Cargo Transfer)
  - Phase 3: Departure Prep (Boarding, Loading, LDS)
  - Phase 4: Door Close & Pushback
- **Top Finding:** Bag Delivery delays cascade through Loading → LDS → ADC miss

---

## 🔍 Data Integrity Findings

Identified 4 critical data quality issues (detailed in `tarmac_metrics.ipynb`):

1. **Null Rates:** STA/ATA 15.3% (departure-only flights), ADC 1.8% (recording failure)
2. **is_punctual Bug:** Scheduled tasks always False, Checkpoint tasks always True (149 mislabeled)
3. **task_is_applicable:** 100% True (no variation — unused or filtered)
4. **Free-Text Standardization:** "Risk Identified" has 9 spellings for "no risk" (nil, NIL, N, ras, No...)

**Recommendations:**
- Add `turnaround_type` field (Full vs Departure-Only)
- Implement real-time ADC monitoring (alert if missing within 10min of ATD)
- Fix `is_punctual` logic & add `task_type` field
- Standardize free-text fields (Risk Identified → Yes/No checkbox)

---

## 🛠️ Technical Stack

- **Python 3.x**
  - pandas, numpy (data manipulation)
  - pandasql (SQL-style queries in Python)
  - matplotlib, plotly (visualizations)
- **SQL** (data validation & integrity checks)
- **Jupyter Notebooks** (reproducible analysis)

---

## 📈 Key Deliverables

### 1. Interactive Dashboard (`turnaround_dashboard.html`)
- Flight-level drill-down with filter by OTP/ADC status
- Top delayed tasks per flight with delay minutes
- Daily trends (OTP & ADC performance over time)

### 2. Executive Presentation (PDF, 16 slides)
- **Part I:** Operational Performance Analysis for Airline
  - Business Overview, KPIs, Methodology, Insights
- **Part II:** Data Platform Recommendations for Tarmac
  - Data integrity findings, proposed schema changes, value unlock

### 3. Analysis Notebooks
- `tarmac_metrics.ipynb`: SQL-based data integrity checks
- `turnaround_performance_analysis.ipynb`: KPI calculations, root cause analysis, visualizations

---

## 💡 Business Impact

**Annualized Cost of Bag Delivery Delays:**
- 6 of 14 delayed flights (43%) rooted in Bag Delivery
- 145 of 444 total delay minutes (33%) from this task

**Recommended Actions:**
1. Review Bag Delivery SLA with ground handlers (current 24min insufficient for A35K)
2. Pilot A35K-specific turnaround procedures (more crew/equipment for larger aircraft)
3. Implement real-time ADC monitoring to catch recording failures same-shift
4. Collect 3+ months of data before investing in A35K-specific interventions (statistical significance)

---

## 🚀 How to Use This Repository

### Run the Analysis
```bash
# Clone the repo
git clone https://github.com/stuckingravity/Aviation-Ops-Data-Analysis.git
cd Aviation-Ops-Data-Analysis

# Install dependencies
pip install pandas numpy pandasql matplotlib plotly jupyter

# Launch Jupyter
jupyter notebook
# Open analysis/turnaround_performance_analysis.ipynb
```

### View the Dashboard
Open `dashboard/turnaround_dashboard.html` in any browser (no server needed — fully static)

### Read the Presentation
See `presentation/Flight Turnaround Analysis - Tarmac Technologies.pdf` for business context

---

## 📝 Notes on Analytical Rigor

- **Null Handling:** Flights excluded from denominators only when outcome is unknowable (e.g., ADC missing → can't judge compliance). Departure-only flights kept for OTP but excluded from arrival-dependent metrics.
- **Cross-Midnight Fix:** Task times combined with flight dates; if task hour - STD hour > 12 → assigned to previous day (affects 5 SFO red-eye flights).
- **Statistical Caution:** A35K sample size (12 flights) too small for confident conclusions — flagged in presentation with recommendation to collect 3+ months before investment.

