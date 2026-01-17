# Core Algorithms & Methodology

This section details the mathematical and logical foundations of ORE's key reasoning engines.

## 1. Hybrid Retrieval

ORE aims to maximize recall by combining two distinct retrieval paradigms.

### A. Sparse Retrieval (BM25)
*   **Algorithm:** BM25Okapi.
*   **Purpose:** Captures exact keyword matches and specific terminology.
*   **Spam Detection Heuristic:** To filter out low-quality or "garbage" text, the system calculates the **Unique Token Ratio**:
    $$ R = \frac{|Unique Tokens|}{|Total Tokens|} $$
    *   If $R < 0.2$, the chunk is flagged as spam and its score is penalized (multiplied by 0.01).

### B. Dense Retrieval (Vector)
*   **Model:** `all-MiniLM-L6-v2` (SentenceTransformer).
*   **Metric:** L2 Distance (Euclidean).
*   **Scoring:** Raw L2 distance $d$ is converted to a similarity score $S$:
    $$ S = \frac{1}{1 + d} $$
    This ensures that a distance of 0 yields a max score of 1.0.
*   **Index:** FAISS `IndexFlatL2` for exact search (no approximation error).

## 2. Research Gap Identification

The system identifies "Research Gaps" deterministically using a co-occurrence matrix approach.

### Logic Flow
1.  **Entity Classification:** Entities are classified into categories (`Method` vs `Dataset`) based on keyword heuristics in their aliases (e.g., "algorithm" $\to$ Method, "corpus" $\to$ Dataset).
2.  **Matrix Construction:** A matrix $M$ is built where rows $i$ are Methods and columns $j$ are Datasets.
    $$ M_{ij} = \text{Count}(\text{Method}_i \cap \text{Dataset}_j) $$
    The count represents the number of chunks where both entities appear together.
3.  **Gap Detection:** A "Gap" is defined as a pair $(i, j)$ where $M_{ij} = 0$, provided both $i$ and $j$ are "active" (appear frequently elsewhere).
    *   *Interpretation:* "Method X has never been applied to Dataset Y in this corpus."

## 3. Semantic Clustering (Topic Synthesis)

To synthesize disparate chunks into a coherent report, ORE clusters content by topic.

### Algorithm
1.  **Vectorization:** TF-IDF (Term Frequency-Inverse Document Frequency) is computed on the text of the chunks.
    *   *Parameters:* English stop words removed, max features = 1000.
2.  **Deduplication:** Before clustering, identical texts are removed to prevent "Cluster Collapse" (where one repeated text pulls a centroid artificially).
3.  **K-Means Clustering:**
    *   **Objective:** Minimize within-cluster sum of squares.
    *   **K:** Default 5 (or dynamic based on corpus size).
    *   **Determinism:** `random_state=42` is strictly enforced to ensure the same input always yields the same clusters.
4.  **Labeling:** Cluster labels are derived from the top TF-IDF terms nearest to the cluster centroid.
