/**
 * V10 选项 B · ConsultationsPage
 */
import { useConsultationsQuery } from '@/hooks/useConsultationQueries';

export function ConsultationsPage() {
  const { data, isLoading } = useConsultationsQuery();

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <h1 className="text-lg font-bold mb-4">💬 咨询记录</h1>
      {isLoading && <p className="text-sm text-gray-500">加载中...</p>}
      <div className="space-y-3">
        {data?.consultations.map((c) => (
          <div key={c.id} className="bg-white border border-gray-200 rounded-2xl p-4">
            <h2 className="text-sm font-medium text-gray-800">{c.title}</h2>
            <p className="text-xs text-gray-500 mt-1">
              {c.messageCount} 条消息 · {new Date(c.updatedAt).toLocaleString('zh-CN')}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}