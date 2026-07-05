import { describe, expect, it } from 'vitest';
import { screen, within } from '@testing-library/react';
import { AdminSchoolsPage } from './SchoolsPage';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('AdminSchoolsPage', () => {
  it('loads schools and opens the detail dialog', async () => {
    const { user } = renderWithProviders(<AdminSchoolsPage />);

    expect(screen.getByRole('status')).toHaveTextContent('正在加载院校库...');
    expect(await screen.findByText('中山大学')).toBeInTheDocument();
    expect(screen.getByText('华南理工大学')).toBeInTheDocument();

    const grid = screen.getByRole('region', { name: '院校库卡片' });
    expect(within(grid).getAllByText('广东').length).toBeGreaterThan(0);
    expect(within(grid).getAllByText('985').length).toBeGreaterThan(0);

    await user.click(screen.getByRole('button', { name: '查看 中山大学 详情' }));

    const dialog = screen.getByRole('dialog', { name: '中山大学' });
    expect(dialog).toHaveTextContent('所在省份：广东');
    expect(within(dialog).getByText('school-sysu')).toBeInTheDocument();
  });

  it('filters schools by keyword', async () => {
    const { user } = renderWithProviders(<AdminSchoolsPage />);

    expect(await screen.findByText('中山大学')).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText('搜索院校名称、省份或 985/211 标签…'), '深圳');

    expect(await screen.findByText('深圳大学')).toBeInTheDocument();
    expect(screen.queryByText('中山大学')).not.toBeInTheDocument();
  });
});
