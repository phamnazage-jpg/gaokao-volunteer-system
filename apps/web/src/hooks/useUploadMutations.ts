/**
 * V10 选项 B · useUploadMutations
 * 替代原型 UploadBar 中的 handleFileUpload
 */
import { useMutation } from '@tanstack/react-query';
import { UploadResponseSchema, type UploadResponse } from '@/lib/api-schemas';

export interface UploadInput {
  file: File;
  onProgress?: (percent: number) => void;
}

export function useUploadMutation() {
  return useMutation<UploadResponse, Error, UploadInput>({
    mutationFn: async ({ file, onProgress }) => {
      const formData = new FormData();
      formData.append('file', file);

      // 用 XHR 而非 fetch 来支持进度回调
      return new Promise<UploadResponse>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/upload');
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable && onProgress) {
            onProgress(Math.round((e.loaded / e.total) * 100));
          }
        });
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const data = JSON.parse(xhr.responseText) as unknown;
              resolve(UploadResponseSchema.parse(data));
            } catch (err) {
              reject(err instanceof Error ? err : new Error('Parse failed'));
            }
          } else {
            reject(new Error(`HTTP ${xhr.status}`));
          }
        });
        xhr.addEventListener('error', () => reject(new Error('Network error')));
        xhr.addEventListener('abort', () => reject(new Error('Aborted')));
        xhr.send(formData);
      });
    },
  });
}