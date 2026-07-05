import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/renderWithProviders';
import { UploadBar } from './UploadBar';

describe('UploadBar', () => {
  it('renders upload options and submits pasted text', async () => {
    const handleUpload = vi.fn();
    const { user } = renderWithProviders(<UploadBar onUpload={handleUpload} />);

    expect(screen.getByText('📎 上传方案文件')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '上传 粘贴' }));
    await user.type(screen.getByPlaceholderText('粘贴你的志愿方案文本...'), '方案文本');
    await user.click(screen.getByRole('button', { name: '提交' }));

    expect(handleUpload).toHaveBeenCalledWith('text', undefined, '方案文本');
  });

  it('renders upload options with English labels', async () => {
    const handleUpload = vi.fn();
    const { user } = renderWithProviders(<UploadBar onUpload={handleUpload} />, { locale: 'en-US' });

    expect(screen.getByText('📎 Upload plan file')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Upload Paste' }));

    expect(screen.getByPlaceholderText('Paste your application plan text...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
  });

  it('does not render when collapsed', () => {
    renderWithProviders(<UploadBar onUpload={vi.fn()} collapsed />);

    expect(screen.queryByTestId('upload-bar')).not.toBeInTheDocument();
  });
});
