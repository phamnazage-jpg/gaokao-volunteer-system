import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { Accordion, type AccordionItem } from './Accordion';
import { renderWithProviders } from '@/test/renderWithProviders';

const items: AccordionItem[] = [
  { id: 'one', title: '第一个问题', content: '第一个答案' },
  { id: 'two', title: '第二个问题', content: '第二个答案' },
];

describe('Accordion', () => {
  it('opens the first item by default', () => {
    renderWithProviders(<Accordion items={items} />);

    expect(screen.getByLabelText('折叠面板')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '第一个问题' })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('region', { name: '第一个问题' })).toHaveTextContent('第一个答案');
  });

  it('renders English default label', () => {
    renderWithProviders(<Accordion items={items} />, { locale: 'en-US' });

    expect(screen.getByLabelText('Accordion panel')).toBeInTheDocument();
  });

  it('switches open item when another trigger is clicked', async () => {
    const { user } = renderWithProviders(<Accordion items={items} label="测试折叠面板" />);

    await user.click(screen.getByRole('button', { name: '第二个问题' }));

    expect(screen.getByRole('button', { name: '第一个问题' })).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByRole('button', { name: '第二个问题' })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('region', { name: '第二个问题' })).toHaveTextContent('第二个答案');
  });
  it('includes dark mode accordion surfaces', () => {
    renderWithProviders(<Accordion items={[{ id: 'one', title: 'Question one', content: 'Answer one' }]} />, { locale: 'en-US' });

    expect(screen.getByRole('button', { name: 'Question one' }).closest('section')).toHaveClass('dark:border-gray-800', 'dark:bg-gray-900');
    expect(screen.getByRole('button', { name: 'Question one' })).toHaveClass('dark:text-gray-100', 'dark:hover:bg-gray-800');
    expect(screen.getByRole('region', { name: 'Question one' })).toHaveClass('dark:border-gray-800', 'dark:text-gray-300');
  });
});
