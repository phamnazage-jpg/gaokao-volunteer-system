'use client';

import React from 'react';

interface Props {
  modes: string[];
}

export function FileUploadPrompt({ modes }: Props) {
  return (
    <div className="bg-white border border-dashed border-blue-300 rounded-2xl rounded-tl-md shadow-sm p-5">
      <div className="text-center mb-4">
        <div className="text-3xl mb-2">📎</div>
        <h4 className="text-sm font-semibold text-gray-800">上传你的志愿方案</h4>
        <p className="text-xs text-gray-500 mt-1">支持以下方式提交</p>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <button className="py-3 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-700 hover:bg-blue-100 transition-colors">
          📝 粘贴文本
        </button>
        <button className="py-3 bg-green-50 border border-green-200 rounded-xl text-sm text-green-700 hover:bg-green-100 transition-colors">
          📊 上传Excel
        </button>
        <button className="py-3 bg-purple-50 border border-purple-200 rounded-xl text-sm text-purple-700 hover:bg-purple-100 transition-colors">
          📷 上传图片
        </button>
        <button className="py-3 bg-orange-50 border border-orange-200 rounded-xl text-sm text-orange-700 hover:bg-orange-100 transition-colors">
          📄 上传PDF
        </button>
      </div>
      <p className="text-xs text-gray-400 text-center mt-3">
        💡 也可以直接在输入框粘贴方案文本
      </p>
    </div>
  );
}
