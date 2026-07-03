import { useSyncExternalStore } from 'react';

function getOnlineSnapshot(): boolean {
  if (typeof navigator === 'undefined') {
    return true;
  }
  return navigator.onLine;
}

function subscribeToOnlineStatus(onStoreChange: () => void): () => void {
  if (typeof window === 'undefined') {
    return () => undefined;
  }

  window.addEventListener('online', onStoreChange);
  window.addEventListener('offline', onStoreChange);

  return () => {
    window.removeEventListener('online', onStoreChange);
    window.removeEventListener('offline', onStoreChange);
  };
}

export function useOnlineStatus(): boolean {
  return useSyncExternalStore(subscribeToOnlineStatus, getOnlineSnapshot, () => true);
}
