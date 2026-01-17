import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

export const api = {
  // Phase 1
  analyzeQuery: (query: string) => axios.post(`${API_URL}/query/analyze`, { query }),

  // Phase 2
  startIngestion: (query: string) => axios.post(`${API_URL}/ingest/start`, { query }),

  // Phase 5
  search: (query: string) => axios.post(`${API_URL}/search/`, { query }),

  // Phase 6-9
  cluster: (paperId?: number) => axios.post(`${API_URL}/analyze/cluster`, { paper_id: paperId }),
  contradiction: (query: string) => axios.post(`${API_URL}/analyze/contradiction`, { query }),
  getGraph: () => axios.post(`${API_URL}/analyze/graph`, {}),
  getGaps: () => axios.post(`${API_URL}/analyze/gaps`, {})
};
