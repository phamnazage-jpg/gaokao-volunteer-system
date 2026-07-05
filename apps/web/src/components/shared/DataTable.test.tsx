import { describe, expect, it } from 'vitest';
import { screen, within } from '@testing-library/react';
import { DataTable, type DataTableColumn } from './DataTable';
import { renderWithProviders } from '@/test/renderWithProviders';

interface Row {
  batch: string;
  score: number;
}

const columns: DataTableColumn<Row>[] = [
  { key: 'batch', header: '批次', accessor: (row) => row.batch, sortable: true },
  { key: 'score', header: '分数', accessor: (row) => row.score, align: 'right', sortable: true },
];

const rows: Row[] = [
  { batch: '专科批', score: 180 },
  { batch: '本科批', score: 435 },
];

describe('DataTable', () => {
  it('renders table rows and caption', () => {
    renderWithProviders(<DataTable data={rows} columns={columns} getRowKey={(row) => row.batch} caption="分数线表格" />);

    expect(screen.getByText('分数线表格')).toHaveClass('sr-only');
    expect(screen.getByText('本科批')).toBeInTheDocument();
    expect(screen.getByText('435')).toBeInTheDocument();
  });

  it('sorts rows when sortable header is clicked', async () => {
    const { user } = renderWithProviders(<DataTable data={rows} columns={columns} getRowKey={(row) => row.batch} caption="分数线表格" />);

    await user.click(screen.getByRole('button', { name: /分数/ }));
    const bodyRows = screen.getAllByRole('row').slice(1);

    expect(within(bodyRows[0]).getByText('专科批')).toBeInTheDocument();
    expect(within(bodyRows[1]).getByText('本科批')).toBeInTheDocument();
  });

  it('renders localized empty text when no rows exist', () => {
    renderWithProviders(<DataTable data={[]} columns={columns} getRowKey={(row) => row.batch} caption="空表格" />);

    expect(screen.getByText('暂无表格数据')).toBeInTheDocument();
  });

  it('renders English empty text and sort label', () => {
    renderWithProviders(<DataTable data={[]} columns={columns} getRowKey={(row) => row.batch} caption="Empty table" />, { locale: 'en-US' });

    expect(screen.getByText('No table data')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '分数, Not sorted, click to sort' })).toBeInTheDocument();
  });
  it('includes dark mode table surfaces', () => {
    renderWithProviders(<DataTable data={rows} columns={columns} getRowKey={(row) => row.batch} caption="Scores" />, { locale: 'en-US' });

    expect(screen.getByRole('table').closest('div')?.parentElement).toHaveClass('dark:border-gray-800', 'dark:bg-gray-900');
    expect(screen.getAllByRole('row')[0]).toHaveClass('dark:bg-gray-800', 'dark:text-gray-300');
    expect(screen.getByText('435').closest('td')).toHaveClass('dark:text-gray-200');
  });
});
