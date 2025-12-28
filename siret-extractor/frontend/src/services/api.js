import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const extractSirets = async (sirets) => {
  const response = await api.post('/extract', { sirets });
  return response.data;
};

export const uploadCsvFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getJobStatus = async (jobId) => {
  const response = await api.get(`/job/${jobId}/status`);
  return response.data;
};

export const getJobResults = async (jobId) => {
  const response = await api.get(`/job/${jobId}/results`);
  return response.data;
};

export const downloadResults = async (jobId, format = 'csv') => {
  const response = await api.get(`/job/${jobId}/download`, {
    params: { format },
    responseType: 'blob',
  });

  const contentDisposition = response.headers['content-disposition'];
  let filename = `extraction_${jobId}.${format}`;

  if (contentDisposition) {
    const match = contentDisposition.match(/filename=([^;]+)/);
    if (match) {
      filename = match[1].replace(/"/g, '');
    }
  }

  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export default api;
