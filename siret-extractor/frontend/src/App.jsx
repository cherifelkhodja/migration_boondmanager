import { useState, useEffect, useCallback } from 'react';
import { Moon, Sun, Building2, AlertTriangle } from 'lucide-react';
import FileUploader from './components/FileUploader';
import ProgressBar from './components/ProgressBar';
import ResultsTable from './components/ResultsTable';
import {
  extractSirets,
  uploadCsvFile,
  getJobStatus,
  getJobResults,
  downloadResults,
} from './services/api';

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [siretInput, setSiretInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode) {
      setDarkMode(JSON.parse(savedMode));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const pollJobStatus = useCallback(async (id) => {
    try {
      const status = await getJobStatus(id);
      setProgress({ current: status.progress, total: status.total });

      if (status.status === 'completed') {
        const jobResults = await getJobResults(id);
        setResults(jobResults.data);
        setIsProcessing(false);
      } else if (status.status === 'failed') {
        setError('Le traitement a echoue. Veuillez reessayer.');
        setIsProcessing(false);
      } else {
        setTimeout(() => pollJobStatus(id), 1000);
      }
    } catch (err) {
      console.error('Error polling status:', err);
      setError('Erreur lors de la verification du statut.');
      setIsProcessing(false);
    }
  }, []);

  const handleExtract = async () => {
    if (!siretInput.trim()) {
      setError('Veuillez entrer au moins un numero SIRET.');
      return;
    }

    const sirets = siretInput
      .split(/[\n,;]+/)
      .map((s) => s.trim().replace(/\s/g, ''))
      .filter((s) => s);

    if (sirets.length === 0) {
      setError('Aucun SIRET valide trouve.');
      return;
    }

    setError(null);
    setResults(null);
    setIsProcessing(true);
    setProgress({ current: 0, total: sirets.length });

    try {
      const response = await extractSirets(sirets);
      setJobId(response.job_id);
      pollJobStatus(response.job_id);
    } catch (err) {
      console.error('Error starting extraction:', err);
      setError('Erreur lors du demarrage de l\'extraction.');
      setIsProcessing(false);
    }
  };

  const handleFileUpload = async (file) => {
    setError(null);
    setResults(null);
    setIsProcessing(true);
    setProgress({ current: 0, total: 0 });

    try {
      const response = await uploadCsvFile(file);
      setJobId(response.job_id);
      pollJobStatus(response.job_id);
    } catch (err) {
      console.error('Error uploading file:', err);
      const message = err.response?.data?.detail || 'Erreur lors du chargement du fichier.';
      setError(message);
      setIsProcessing(false);
    }
  };

  const handleDownload = async (format) => {
    if (!jobId) return;

    try {
      await downloadResults(jobId, format);
    } catch (err) {
      console.error('Error downloading:', err);
      setError('Erreur lors du telechargement.');
    }
  };

  const handleReset = () => {
    setSiretInput('');
    setResults(null);
    setError(null);
    setJobId(null);
    setProgress({ current: 0, total: 0 });
  };

  return (
    <div className={`min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors duration-200`}>
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Building2 className="w-8 h-8 text-blue-500" />
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              SIRET Extractor
            </h1>
          </div>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200
              dark:hover:bg-gray-600 transition-colors"
            aria-label="Toggle dark mode"
          >
            {darkMode ? (
              <Sun className="w-5 h-5 text-yellow-500" />
            ) : (
              <Moon className="w-5 h-5 text-gray-600" />
            )}
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {!results ? (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Importer des numeros SIRET
              </h2>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Fichier CSV
                  </label>
                  <FileUploader onFileUpload={handleFileUpload} disabled={isProcessing} />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    Le fichier doit contenir une colonne "SIRET" ou une seule colonne avec les numeros.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Ou saisir manuellement
                  </label>
                  <textarea
                    value={siretInput}
                    onChange={(e) => setSiretInput(e.target.value)}
                    placeholder="Entrez les numeros SIRET (un par ligne)"
                    disabled={isProcessing}
                    className="w-full h-48 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl
                      bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                      focus:ring-2 focus:ring-blue-500 focus:border-transparent
                      disabled:opacity-50 disabled:cursor-not-allowed
                      resize-none font-mono text-sm"
                  />
                  <button
                    onClick={handleExtract}
                    disabled={isProcessing || !siretInput.trim()}
                    className="mt-3 w-full py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400
                      text-white font-medium rounded-xl transition-colors
                      disabled:cursor-not-allowed"
                  >
                    Extraire les informations
                  </button>
                </div>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-3 p-4 bg-red-50 dark:bg-red-900/20
                border border-red-200 dark:border-red-800 rounded-xl">
                <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
                <p className="text-red-700 dark:text-red-400">{error}</p>
              </div>
            )}

            {isProcessing && (
              <ProgressBar
                progress={progress.current}
                total={progress.total}
                status="processing"
              />
            )}
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Resultats de l'extraction
              </h2>
              <button
                onClick={handleReset}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-900
                  dark:hover:text-white border border-gray-300 dark:border-gray-600
                  rounded-lg transition-colors"
              >
                Nouvelle extraction
              </button>
            </div>

            <ResultsTable data={results} onDownload={handleDownload} />
          </div>
        )}
      </main>

      <footer className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
        SIRET Extractor - Donnees issues de l'API INSEE SIRENE et RNE INPI
      </footer>
    </div>
  );
}

export default App;
