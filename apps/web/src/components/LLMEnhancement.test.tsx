import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/renderWithProviders';
import { server } from '@/test/mocks/server';
import { LLMEnhancement } from './LLMEnhancement';

describe('LLMEnhancement', () => {
  it('renders provider selector and disables trigger without plan id', async () => {
    server.use(
      http.get('/api/llm/config', () =>
        HttpResponse.json({
          currentProvider: 'claude',
          fallbackOrder: ['claude', 'gpt'],
          availableProviders: ['claude', 'gpt'],
        }),
      ),
    );

    renderWithProviders(<LLMEnhancement planId={null} />);

    expect(await screen.findByLabelText('首选模型')).toHaveValue('claude');
    expect(screen.getByRole('button', { name: '触发增强' })).toBeDisabled();
  });

  it('renders provider selector with English labels', async () => {
    server.use(
      http.get('/api/llm/config', () =>
        HttpResponse.json({
          currentProvider: 'claude',
          fallbackOrder: ['claude', 'gpt'],
          availableProviders: ['claude', 'gpt'],
        }),
      ),
    );

    renderWithProviders(<LLMEnhancement planId={null} />, { locale: 'en-US' });

    expect(await screen.findByLabelText('Preferred model')).toHaveValue('claude');
    expect(screen.getByRole('region', { name: 'LLM enhancement panel' })).toHaveTextContent('LLM-enhanced review');
    expect(screen.getByRole('button', { name: 'Trigger enhancement' })).toBeDisabled();
  });

  it('renders backend status progress', () => {
    renderWithProviders(
      <LLMEnhancement
        planId="plan-001"
        status={{
          planId: 'plan-001',
          status: 'processing',
          progress: 60,
          currentStep: '生成风险建议',
          updatedAt: '2026-07-04T00:00:00.000Z',
        }}
      />,
    );

    expect(screen.getByRole('region', { name: 'LLM 增强状态' })).toHaveTextContent('生成风险建议');
    expect(screen.getByRole('progressbar', { name: 'LLM 增强进度' })).toHaveAttribute('aria-valuenow', '60');
  });

  it('renders backend status progress with English labels', () => {
    renderWithProviders(
      <LLMEnhancement
        planId="plan-001"
        status={{
          planId: 'plan-001',
          status: 'processing',
          progress: 60,
          currentStep: 'Generating risk recommendations',
          updatedAt: '2026-07-04T00:00:00.000Z',
        }}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('region', { name: 'LLM enhancement status' })).toHaveTextContent('Generating risk recommendations');
    expect(screen.getByRole('progressbar', { name: 'LLM enhancement progress' })).toHaveAttribute('aria-valuenow', '60');
  });

  it('triggers enhance with selected provider and renders result', async () => {
    server.use(
      http.get('/api/llm/config', () =>
        HttpResponse.json({
          currentProvider: 'claude',
          fallbackOrder: ['claude', 'gpt'],
          availableProviders: ['claude', 'gpt'],
        }),
      ),
      http.post('/api/llm/claude/enhance', async ({ request }) => {
        const body = (await request.json()) as { planId: string; enhancementType: string };
        expect(body).toMatchObject({ planId: 'plan-001', enhancementType: 'risk' });
        return HttpResponse.json({
          summary: '风险摘要已生成',
          recommendations: [{ title: '补充保底院校', detail: '建议增加 2 所稳妥院校。', priority: 'high' }],
          provider: 'claude',
        });
      }),
    );

    const { user } = renderWithProviders(<LLMEnhancement planId="plan-001" enhancementType="risk" />);

    await user.click(screen.getByRole('button', { name: '触发增强' }));

    expect(await screen.findByRole('region', { name: 'LLM 增强结果' })).toHaveTextContent('风险摘要已生成');
    expect(screen.getByText('补充保底院校')).toBeInTheDocument();
    expect(screen.getByText('优先级：高')).toBeInTheDocument();
  });

  it('renders enhance result priority with English labels', async () => {
    server.use(
      http.get('/api/llm/config', () =>
        HttpResponse.json({
          currentProvider: 'claude',
          fallbackOrder: ['claude', 'gpt'],
          availableProviders: ['claude', 'gpt'],
        }),
      ),
      http.post('/api/llm/claude/enhance', () => {
        return HttpResponse.json({
          summary: 'Risk summary generated',
          recommendations: [{ title: 'Add safety schools', detail: 'Add two safer schools.', priority: 'high' }],
          provider: 'claude',
        });
      }),
    );

    const { user } = renderWithProviders(<LLMEnhancement planId="plan-001" enhancementType="risk" />, { locale: 'en-US' });

    await user.click(screen.getByRole('button', { name: 'Trigger enhancement' }));

    expect(await screen.findByRole('region', { name: 'LLM enhancement result' })).toHaveTextContent('Risk summary generated');
    expect(screen.getByText('Add safety schools')).toBeInTheDocument();
    expect(screen.getByText('Priority: High')).toBeInTheDocument();
  });

  it('renders localized failure copy without leaking backend error text', async () => {
    server.use(
      http.get('/api/llm/config', () =>
        HttpResponse.json({
          currentProvider: 'claude',
          fallbackOrder: ['claude'],
          availableProviders: ['claude'],
        }),
      ),
      http.post('/api/llm/claude/enhance', () => {
        return HttpResponse.json({ message: 'raw backend stack trace' }, { status: 503 });
      }),
    );

    const { user } = renderWithProviders(<LLMEnhancement planId="plan-001" enhancementType="risk" />);

    await user.click(screen.getByRole('button', { name: '触发增强' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('增强暂时失败');
    expect(alert).toHaveTextContent('原始审核结果仍可继续使用');
    expect(screen.queryByText('raw backend stack trace')).not.toBeInTheDocument();
  });
});
