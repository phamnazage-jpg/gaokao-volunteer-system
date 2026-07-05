import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/renderWithProviders';
import { PosterPreview } from './PosterPreview';

describe('PosterPreview', () => {
  it('renders template selector and emits selected template', async () => {
    const handleTemplateChange = vi.fn();
    const { user } = renderWithProviders(
      <PosterPreview template="classic" statusSnapshot={null} onTemplateChange={handleTemplateChange} onGenerate={vi.fn()} />,
    );

    await user.click(screen.getByRole('button', { name: '现代' }));

    expect(screen.getByRole('button', { name: '经典' })).toHaveAttribute('aria-pressed', 'true');
    expect(handleTemplateChange).toHaveBeenCalledWith('modern');
  });

  it('renders template selector with English labels', async () => {
    const handleTemplateChange = vi.fn();
    const { user } = renderWithProviders(
      <PosterPreview template="classic" statusSnapshot={null} onTemplateChange={handleTemplateChange} onGenerate={vi.fn()} />,
      { locale: 'en-US' },
    );

    await user.click(screen.getByRole('button', { name: 'Modern' }));

    expect(screen.getByRole('region', { name: 'Poster preview component' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Classic' })).toHaveAttribute('aria-pressed', 'true');
    expect(handleTemplateChange).toHaveBeenCalledWith('modern');
  });

  it('renders async generation progress', () => {
    renderWithProviders(
      <PosterPreview
        template="classic"
        statusSnapshot={{
          jobId: 'poster-1',
          status: 'processing',
          progress: 40,
          posterUrl: null,
          qrCode: null,
          expiresAt: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        }}
        onTemplateChange={vi.fn()}
        onGenerate={vi.fn()}
      />,
    );

    expect(screen.getByRole('region', { name: '海报生成状态' })).toHaveTextContent('生成中');
    expect(screen.getByRole('progressbar', { name: '海报生成进度' })).toHaveAttribute('aria-valuenow', '40');
    expect(screen.queryByAltText('海报预览')).not.toBeInTheDocument();
  });

  it('renders async generation progress with English labels', () => {
    renderWithProviders(
      <PosterPreview
        template="classic"
        statusSnapshot={{
          jobId: 'poster-1',
          status: 'processing',
          progress: 40,
          posterUrl: null,
          qrCode: null,
          expiresAt: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        }}
        onTemplateChange={vi.fn()}
        onGenerate={vi.fn()}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('region', { name: 'Poster generation status' })).toHaveTextContent('Generating');
    expect(screen.getByRole('progressbar', { name: 'Poster generation progress' })).toHaveAttribute('aria-valuenow', '40');
    expect(screen.queryByAltText('Poster preview')).not.toBeInTheDocument();
  });

  it('renders failed status', () => {
    renderWithProviders(
      <PosterPreview
        template="classic"
        statusSnapshot={{
          jobId: 'poster-2',
          status: 'failed',
          progress: 100,
          posterUrl: null,
          qrCode: null,
          expiresAt: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        }}
        onTemplateChange={vi.fn()}
        onGenerate={vi.fn()}
      />,
    );

    expect(screen.getByRole('alert')).toHaveTextContent('海报生成失败，请稍后重试。');
  });

  it('renders generation request failure without a status snapshot', () => {
    renderWithProviders(
      <PosterPreview
        template="classic"
        statusSnapshot={null}
        isGenerateError
        onTemplateChange={vi.fn()}
        onGenerate={vi.fn()}
      />,
    );

    expect(screen.getByRole('alert')).toHaveTextContent('海报生成失败，请稍后重试。');
  });

  it('renders failed status with English labels', () => {
    renderWithProviders(
      <PosterPreview
        template="classic"
        statusSnapshot={{
          jobId: 'poster-2',
          status: 'failed',
          progress: 100,
          posterUrl: null,
          qrCode: null,
          expiresAt: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        }}
        onTemplateChange={vi.fn()}
        onGenerate={vi.fn()}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('alert')).toHaveTextContent('Poster generation failed. Try again later.');
  });

  it('renders preview actions and copies qr code', async () => {
    const handleCopy = vi.fn();
    const { user } = renderWithProviders(
      <PosterPreview
        template="modern"
        statusSnapshot={{
          jobId: 'poster-3',
          status: 'completed',
          progress: 100,
          posterUrl: 'https://example.test/poster.png',
          qrCode: 'https://example.test/qr.png',
          expiresAt: '2026-08-01T00:00:00Z',
          updatedAt: '2026-07-04T00:00:00.000Z',
        }}
        onTemplateChange={vi.fn()}
        onGenerate={vi.fn()}
        onCopyQrCode={handleCopy}
      />,
    );

    expect(screen.getByRole('region', { name: '海报预览结果' })).toBeInTheDocument();
    expect(screen.getByAltText('海报预览')).toHaveAttribute('src', 'https://example.test/poster.png');
    expect(screen.getByRole('link', { name: /下载/ })).toHaveAttribute('href', 'https://example.test/poster.png');

    await user.click(screen.getByRole('button', { name: '复制二维码' }));

    expect(handleCopy).toHaveBeenCalledWith('https://example.test/qr.png');
  });

  it('renders preview actions with English labels', async () => {
    const handleCopy = vi.fn();
    const { user } = renderWithProviders(
      <PosterPreview
        template="modern"
        statusSnapshot={{
          jobId: 'poster-3',
          status: 'completed',
          progress: 100,
          posterUrl: 'https://example.test/poster.png',
          qrCode: 'https://example.test/qr.png',
          expiresAt: '2026-08-01T00:00:00Z',
          updatedAt: '2026-07-04T00:00:00.000Z',
        }}
        onTemplateChange={vi.fn()}
        onGenerate={vi.fn()}
        onCopyQrCode={handleCopy}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('region', { name: 'Poster preview result' })).toBeInTheDocument();
    expect(screen.getByAltText('Poster preview')).toHaveAttribute('src', 'https://example.test/poster.png');
    expect(screen.getByRole('link', { name: /Download/ })).toHaveAttribute('href', 'https://example.test/poster.png');

    await user.click(screen.getByRole('button', { name: 'Copy QR code' }));

    expect(handleCopy).toHaveBeenCalledWith('https://example.test/qr.png');
  });
});
