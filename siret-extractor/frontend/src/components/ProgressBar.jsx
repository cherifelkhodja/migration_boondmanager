import { Loader2 } from 'lucide-react';

function ProgressBar({ progress, total, status }) {
  const percentage = total > 0 ? Math.round((progress / total) * 100) : 0;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
          <span className="font-medium text-gray-700 dark:text-gray-200">
            Extraction en cours...
          </span>
        </div>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {progress} / {total} SIRET traites
        </span>
      </div>

      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
        <div
          className="bg-blue-500 h-3 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>

      <p className="text-right text-sm text-gray-500 dark:text-gray-400 mt-2">
        {percentage}%
      </p>
    </div>
  );
}

export default ProgressBar;
