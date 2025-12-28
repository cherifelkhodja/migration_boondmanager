import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText } from 'lucide-react';

function FileUploader({ onFileUpload, disabled }) {
  const onDrop = useCallback(
    (acceptedFiles) => {
      if (acceptedFiles.length > 0 && !disabled) {
        onFileUpload(acceptedFiles[0]);
      }
    },
    [onFileUpload, disabled]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    maxFiles: 1,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
        transition-all duration-200
        ${isDragActive
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-4">
        {isDragActive ? (
          <>
            <FileText className="w-12 h-12 text-blue-500" />
            <p className="text-blue-500 font-medium">Deposez le fichier ici...</p>
          </>
        ) : (
          <>
            <Upload className="w-12 h-12 text-gray-400 dark:text-gray-500" />
            <div>
              <p className="text-gray-600 dark:text-gray-300 font-medium">
                Glissez-deposez un fichier CSV ici
              </p>
              <p className="text-gray-400 dark:text-gray-500 text-sm mt-1">
                ou cliquez pour selectionner un fichier
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default FileUploader;
