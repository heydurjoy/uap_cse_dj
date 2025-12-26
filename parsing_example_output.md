# Publication Parsing Output Example

## Input Format Analysis

Based on the provided input, here's what the Format 2 parser extracts from each publication:

| # | Title | Year | Q Ranking | Status |
|---|-------|------|-----------|--------|
| 1 | Privacy-preserving on-screen activity tracking and classification in e-learning using federated learning | 2023 | Q1 | ✅ Extracted |
| 2 | Explainable federated learning for privacy-preserving bangla sign language detection | 2024 | Q1 | ✅ Extracted |
| 3 | Privacy Preserving Breast Cancer Prediction with Mammography Images Using Federated Learning | 2024 | Q2 | ✅ Extracted |
| 4 | Federated Transfer Learning for Vision-Based Fall Detection | 2023 | Q4 | ✅ Extracted |
| 5 | Federated learning-based architecture for personalized next emoji prediction for social media comments | 2024 | Q1 | ✅ Extracted |
| 6 | Privacy-Preserving Vision-Based Detection of Pox Diseases Using Federated Learning | 2024 | Q2 | ✅ Extracted |
| 7 | Incorporating residual connections into a multi-channel CNN for lung cancer detection in digital pathology | 2024 | Q2 | ✅ Extracted |
| 8 | From Centralization to Decentralization: Blockchain's Role in Transforming Social Media Platforms | 2025 | Q1 | ✅ Extracted |
| 9 | Deep learning for predicting essential proteins using topological features and gene ontology | 2025 | Q1 | ✅ Extracted |
| 10 | FallVision: A benchmark video dataset for fall detection | 2025 | Q3 | ✅ Extracted |
| 11 | Open problems and challenges in federated learning for IoT: A comprehensive review and strategic guide | 2025 | Q1 | ✅ Extracted |
| 12 | A Multisectoral Study of Mpox Epidemiology, Resistance Surveillance, and Policy Gaps: Toward a One Health Framework | 2025 | Q1 | ✅ Extracted |
| 13 | Federated Learning Strategies for Confidential Leukemia Detection from Medical Images | 2025 | Q4 | ✅ Extracted |
| 14 | Secure Collaborative Learning for CSV-Based Ovarian Cancer Diagnosis: A Federated Approach | 2025 | Q4 | ✅ Extracted |
| 15 | Privacy-Preserving Rheumatism Detection Using Federated Learning | 2025 | Q4 | ✅ Extracted |
| 16 | A Federated Approach | 2025 | Q4 | ✅ Extracted |
| 17 | Personalized Pomodoro Productivity Tracking with Privacy-Preserving Machine Learning in Human-Computer Interaction | 2025 | ❌ No Q Ranking | ⚠️ Skipped* |

*Note: Publication #17 has "NA" instead of a Q ranking (Q1-Q4), so it will be skipped because the parser requires both title AND Q ranking to be found.

## Parsing Logic Flow (Example: Publication #1)

```
Input Lines (from bottom to top, scanning upward):
─────────────────────────────────────────────────
Line 1: "48	2023"                    ← YEAR ANCHOR FOUND (2023)
Line 2: "IEEE Access 11, 79315-79329" ← Metadata (journal details)
Line 3: "IEEE Access"                 ← Metadata (journal name)
Line 4: "ABDC NA"                     ← Metadata (skip)
Line 5: "NA"                          ← Metadata (skip)
Line 6: "ABS NA"                      ← Metadata (skip)
Line 7: "NA"                          ← Metadata (skip)
Line 8: "SJR Q1; 0.849"              ← Metadata (skip)
Line 9: "Q1"                          ← Q RANKING FOUND (Q1) ✅
Line 10: "0.849"                      ← Metadata (skip)
Line 11: "D Mistry, MF Mridha..."     ← Metadata (authors, skip)
Line 12: "Privacy-preserving..."      ← TITLE FOUND ✅
─────────────────────────────────────────────────

Output:
{
  "title": "Privacy-preserving on-screen activity tracking and classification in e-learning using federated learning",
  "year": "2023",
  "q_rank": "Q1"
}
```

## Parsing Logic Flow (Example: Publication #17 - Edge Case)

```
Input Lines:
─────────────────────────────────────────────────
Line 1: "2025"                        ← YEAR ANCHOR FOUND (2025)
Line 2: "International Conference..." ← Metadata
Line 3: "NA"                          ← Metadata (this is where Q ranking would be)
Line 4: "NA"                          ← Metadata
... (more metadata lines)
Line N: "Personalized Pomodoro..."    ← TITLE FOUND ✅
─────────────────────────────────────────────────

Result: ❌ SKIPPED
Reason: Q ranking not found (only "NA" present, not Q1-Q4)
```

## Key Parsing Rules

1. **Year Detection**: Finds lines containing `20\d{2}` pattern (e.g., "48	2023", "2025")
   - Uses the **last occurrence** of the year in the line

2. **Q Ranking Scan**: Scans upward from year line
   - Looks for exact match: `^Q[1-4]$`
   - Stops if another year is found (different publication)

3. **Title Scan**: Scans upward from Q ranking (or year if no Q found)
   - Skips metadata lines (NA, ABS NA, numeric metrics, SJR patterns, etc.)
   - Stops at first meaningful line (length >= 10, not metadata)
   - Stops if another year is found

4. **Validation**: Only adds publication if:
   - ✅ Title found (length >= 10)
   - ✅ Q ranking found (Q1, Q2, Q3, or Q4)
   - ✅ Year found (2000-2100)

## Expected Results Summary

- **Total Publications in Input**: 17
- **Successfully Parsed**: 16
- **Skipped**: 1 (Publication #17 - no Q ranking)

