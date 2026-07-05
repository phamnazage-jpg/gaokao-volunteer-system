import { describe, expect, it } from 'vitest';
import { screen, within } from '@testing-library/react';
import { AdminPostersPage } from './PostersPage';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('AdminPostersPage', () => {
  it('loads poster jobs with thumbnails and status badges', async () => {
    renderWithProviders(<AdminPostersPage />);

    expect(screen.getByRole('status')).toHaveTextContent('正在加载海报任务');
    expect(await screen.findByText('poster-job-1')).toBeInTheDocument();
    expect(screen.getByText('poster-job-2')).toBeInTheDocument();
    expect(screen.getByText('poster-job-3')).toBeInTheDocument();
    expect(screen.getByAltText('poster-job-1 海报缩略图')).toHaveAttribute('src', 'https://example.test/posters/poster-job-1.png');

    const grid = screen.getByRole('region', { name: '海报任务网格' });
    expect(within(grid).getByText('已完成')).toBeInTheDocument();
    expect(within(grid).getByText('生成中')).toBeInTheDocument();
    expect(within(grid).getByText('已失败')).toBeInTheDocument();
  });

  it('filters poster jobs by status and template', async () => {
    const { user } = renderWithProviders(<AdminPostersPage />);

    expect(await screen.findByText('poster-job-1')).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('生成状态'), 'processing');
    expect(await screen.findByText('poster-job-2')).toBeInTheDocument();
    expect(screen.queryByText('poster-job-1')).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('海报模板'), 'minimal');
    const grid = screen.getByRole('region', { name: '海报任务网格' });
    expect(await within(grid).findByText('暂无符合条件的海报任务')).toBeInTheDocument();
  });
});
