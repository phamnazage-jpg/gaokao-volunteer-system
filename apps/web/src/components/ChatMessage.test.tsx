import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { renderWithProviders } from '@/test/renderWithProviders';
import type { Message } from '@/types/message';

import { ChatMessage } from './ChatMessage';

const timestamp = new Date('2026-07-04T00:00:00.000Z');

describe('ChatMessage', () => {
  it('includes dark mode system and assistant bubbles', () => {
    const systemMessage: Message = {
      id: 'system-1',
      role: 'system',
      content: 'System update',
      timestamp,
      data: { type: 'system', level: 'info' },
    };
    const assistantMessage: Message = {
      id: 'assistant-1',
      role: 'assistant',
      content: 'Assistant reply',
      timestamp,
    };

    const { rerender } = renderWithProviders(<ChatMessage message={systemMessage} />);
    expect(screen.getByText('System update')).toHaveClass('dark:bg-gray-800', 'dark:text-gray-300');

    rerender(<ChatMessage message={assistantMessage} />);
    expect(screen.getByText('Assistant reply').closest('.rounded-2xl')).toHaveClass(
      'dark:border-gray-800',
      'dark:bg-gray-900',
    );
  });
});
