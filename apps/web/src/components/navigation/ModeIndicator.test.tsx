/**
 * V10 选项 B · ModeIndicator 单测
 *
 * 覆盖 V10 不变量 C2: 4-mode 决策树
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { ModeIndicator, deriveMode } from '@/components/navigation/ModeIndicator';
import { messages } from '@/i18n/messages';

function renderModeIndicator(mode: Parameters<typeof ModeIndicator>[0]['mode']) {
  return render(
    <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
      <ModeIndicator mode={mode} />
    </IntlProvider>,
  );
}

describe('ModeIndicator (V10 不变量 C2)', () => {
  it('渲染 4 种 mode 的 label', () => {
    const { rerender } = renderModeIndicator('explore');
    expect(screen.getByText('自由探索')).toBeInTheDocument();

    rerender(
      <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
        <ModeIndicator mode="generating" />
      </IntlProvider>,
    );
    expect(screen.getByText('方案生成中')).toBeInTheDocument();

    rerender(
      <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
        <ModeIndicator mode="auditing" />
      </IntlProvider>,
    );
    expect(screen.getByText('方案审核中')).toBeInTheDocument();

    rerender(
      <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
        <ModeIndicator mode="adjusting" />
      </IntlProvider>,
    );
    expect(screen.getByText('方案调整中')).toBeInTheDocument();
  });

  it('deriveMode 决策树: audit 优先', () => {
    expect(deriveMode({}, null, true)).toBe('auditing');
  });

  it('deriveMode: 有 currentPlan + 无 audit → adjusting', () => {
    expect(deriveMode({ province: '广东', score: 620 }, { id: 'p1' }, false)).toBe('adjusting');
  });

  it('deriveMode: 有 province + score → generating', () => {
    expect(deriveMode({ province: '广东', score: 620 }, null, false)).toBe('generating');
  });

  it('deriveMode: 缺核心信息 → explore', () => {
    expect(deriveMode({}, null, false)).toBe('explore');
    expect(deriveMode({ province: '广东' }, null, false)).toBe('explore');
    expect(deriveMode({ score: 620 }, null, false)).toBe('explore');
  });
});
