import React from "react";

type GlobalErrorDialogProps = {
  message: string | null;
  onClose: () => void;
};

const GlobalErrorDialog: React.FC<GlobalErrorDialogProps> = ({
  message,
  onClose,
}) => {
  if (!message) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50 text-center">
      <div className="bg-zinc-200 dark:bg-zinc-800 rounded-xl p-6 shadow-xl max-w-md w-full mx-4">
        <h2 className="font-semibold text-xl text-orange-500 dark:text-oragne-400 mb-4">
          Wystąpił problem z serwerem
        </h2>
        <p className="mb-8 text-md text-zinc-900 dark:text-zinc-200">{message}</p>
        <div className="w-full items-end justify-end flex">
          <button
            className="btn-gradient-primary px-4 py-2 text-md"
            onClick={onClose}
          >
            Zamknij
          </button>
        </div>
      </div>
    </div>
  );
};

export default GlobalErrorDialog;
