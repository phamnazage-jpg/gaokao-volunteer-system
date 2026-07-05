import { describe, expect, it } from 'vitest';
import { screen, within } from '@testing-library/react';
import { AdminMajorsPage } from './MajorsPage';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('AdminMajorsPage', () => {
  it('loads majors and opens the detail dialog', async () => {
    const { user } = renderWithProviders(<AdminMajorsPage />);

    expect(screen.getByRole('status')).toHaveTextContent('正在加载专业库');
    expect(await screen.findByText('计算机科学与技术')).toBeInTheDocument();
    expect(screen.getByText('临床医学')).toBeInTheDocument();

    const table = screen.getByRole('region', { name: '专业库表格' });
    expect(within(table).getByText('工学')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '查看 计算机科学与技术 详情' }));

    const dialog = screen.getByRole('dialog', { name: '计算机科学与技术' });
    expect(dialog).toHaveTextContent('专业类别：工学');
    expect(within(dialog).getByText('major-cs')).toBeInTheDocument();
  });

  it('filters majors by keyword', async () => {
    const { user } = renderWithProviders(<AdminMajorsPage />);

    expect(await screen.findByText('计算机科学与技术')).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText('搜索专业、类别或培养方向…'), '医学');

    expect(await screen.findByText('临床医学')).toBeInTheDocument();
    expect(screen.queryByText('计算机科学与技术')).not.toBeInTheDocument();
  });
});
