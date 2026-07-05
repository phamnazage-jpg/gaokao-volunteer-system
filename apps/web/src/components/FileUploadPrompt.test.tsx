import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/renderWithProviders';
import { FileUploadPrompt } from './FileUploadPrompt';

describe('FileUploadPrompt', () => {
  it('renders upload prompt actions', () => {
    renderWithProviders(<FileUploadPrompt data={{ type: 'file_upload_prompt', acceptedFormats: ['pdf', 'xlsx'], maxSize: 1024 * 1024 }} />);

    expect(screen.getByText('上传你的志愿方案')).toBeInTheDocument();
    expect(screen.getByText('支持 PDF / XLSX · 最大 1.0 MB')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '📝 粘贴文本' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '📄 上传 PDF' })).toBeInTheDocument();
  });

  it('renders upload prompt actions with English labels', () => {
    renderWithProviders(<FileUploadPrompt data={{ type: 'file_upload_prompt', acceptedFormats: ['pdf', 'xlsx'], maxSize: 1024 * 1024 }} />, { locale: 'en-US' });

    expect(screen.getByText('Upload your application plan')).toBeInTheDocument();
    expect(screen.getByText('Supports PDF / XLSX · max 1.0 MB')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '📝 Paste text' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '📄 Upload PDF' })).toBeInTheDocument();
  });
});
