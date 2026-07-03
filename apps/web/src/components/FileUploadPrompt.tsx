/**
 * V10 选项 B · FileUploadPrompt 组件 (重写)
 * 使用 FileUploadPromptMessageData 类型, 0 any
 */
import type { FileUploadPromptMessageData } from '@/types/message';

interface Props {
  data: FileUploadPromptMessageData;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function FileUploadPrompt({ data }: Props) {
  return (
    <div className="mt-2 bg-white border border-dashed border-blue-300 rounded-2xl rounded-tl-md shadow-sm p-4">
      <div className="text-center mb-3">
        <div className="text-3xl mb-2">📎</div>
        <h4 className="text-sm font-semibold text-gray-800">上传你的志愿方案</h4>
        <p className="text-xs text-gray-500 mt-1">
          支持 {data.acceptedFormats.map((f) => f.toUpperCase()).join(' / ')} · 最大 {formatSize(data.maxSize)}
        </p>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          className="py-3 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-700 hover:bg-blue-100 transition-colors"
        >
          📝 粘贴文本
        </button>
        <button
          type="button"
          className="py-3 bg-green-50 border border-green-200 rounded-xl text-sm text-green-700 hover:bg-green-100 transition-colors"
        >
          📊 上传表格
        </button>
        <button
          type="button"
          className="py-3 bg-purple-50 border border-purple-200 rounded-xl text-sm text-purple-700 hover:bg-purple-100 transition-colors"
        >
          📷 上传图片
        </button>
        <button
          type="button"
          className="py-3 bg-orange-50 border border-orange-200 rounded-xl text-sm text-orange-700 hover:bg-orange-100 transition-colors"
        >
          📄 上传 PDF
        </button>
      </div>
    </div>
  );
}