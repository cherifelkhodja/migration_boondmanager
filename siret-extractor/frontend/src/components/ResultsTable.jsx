import { useState, useMemo } from 'react';
import { Download, AlertCircle, CheckCircle2, ChevronUp, ChevronDown, Search } from 'lucide-react';

const columns = [
  { key: 'siret', label: 'SIRET', width: '140px' },
  { key: 'raison_sociale', label: 'Raison sociale', width: '200px' },
  { key: 'rcs', label: 'RCS', width: '180px' },
  { key: 'forme_juridique', label: 'Forme', width: '80px' },
  { key: 'capital', label: 'Capital', width: '120px' },
  { key: 'tva_intracommunautaire', label: 'TVA', width: '150px' },
  { key: 'code_ape', label: 'APE', width: '80px' },
  { key: 'adresse', label: 'Adresse', width: '200px' },
  { key: 'code_postal', label: 'CP', width: '70px' },
  { key: 'ville', label: 'Ville', width: '120px' },
  { key: 'civilite_contact', label: 'Civ.', width: '50px' },
  { key: 'nom_contact', label: 'Nom', width: '120px' },
  { key: 'prenom_contact', label: 'Prenom', width: '100px' },
  { key: 'fonction_contact', label: 'Fonction', width: '120px' },
];

function ResultsTable({ data, onDownload }) {
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');
  const [searchTerm, setSearchTerm] = useState('');

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const filteredAndSortedData = useMemo(() => {
    let result = [...data];

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter((row) =>
        Object.values(row).some((value) =>
          String(value || '').toLowerCase().includes(term)
        )
      );
    }

    if (sortColumn) {
      result.sort((a, b) => {
        const aVal = a[sortColumn] || '';
        const bVal = b[sortColumn] || '';
        const comparison = String(aVal).localeCompare(String(bVal), 'fr');
        return sortDirection === 'asc' ? comparison : -comparison;
      });
    }

    return result;
  }, [data, sortColumn, sortDirection, searchTerm]);

  const successCount = data.filter((r) => !r.erreur || r.donnees_partielles).length;
  const errorCount = data.filter((r) => r.erreur && !r.donnees_partielles).length;
  const partialCount = data.filter((r) => r.donnees_partielles).length;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-500" />
              <span className="text-sm text-gray-600 dark:text-gray-300">
                {successCount} succes
              </span>
            </div>
            {partialCount > 0 && (
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-500" />
                <span className="text-sm text-gray-600 dark:text-gray-300">
                  {partialCount} partiels
                </span>
              </div>
            )}
            {errorCount > 0 && (
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <span className="text-sm text-gray-600 dark:text-gray-300">
                  {errorCount} erreurs
                </span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                  bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                  focus:ring-2 focus:ring-blue-500 focus:border-transparent
                  text-sm w-48"
              />
            </div>

            <button
              onClick={() => onDownload('csv')}
              className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600
                text-white rounded-lg transition-colors text-sm font-medium"
            >
              <Download className="w-4 h-4" />
              CSV
            </button>
            <button
              onClick={() => onDownload('xlsx')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600
                text-white rounded-lg transition-colors text-sm font-medium"
            >
              <Download className="w-4 h-4" />
              Excel
            </button>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400
                    uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600
                    transition-colors whitespace-nowrap"
                  style={{ minWidth: col.width }}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {sortColumn === col.key && (
                      sortDirection === 'asc'
                        ? <ChevronUp className="w-3 h-3" />
                        : <ChevronDown className="w-3 h-3" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredAndSortedData.map((row, idx) => (
              <tr
                key={row.siret + idx}
                className={`
                  hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors
                  ${row.erreur && !row.donnees_partielles
                    ? 'bg-red-50 dark:bg-red-900/20'
                    : row.donnees_partielles
                    ? 'bg-yellow-50 dark:bg-yellow-900/20'
                    : ''
                  }
                `}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className="px-3 py-2 text-gray-900 dark:text-gray-100 whitespace-nowrap"
                    title={row[col.key] || ''}
                  >
                    {row[col.key] || '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredAndSortedData.length === 0 && (
        <div className="p-8 text-center text-gray-500 dark:text-gray-400">
          Aucun resultat trouve
        </div>
      )}
    </div>
  );
}

export default ResultsTable;
