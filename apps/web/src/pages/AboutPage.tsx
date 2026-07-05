import { Link } from 'react-router-dom';
import { FormattedMessage, useIntl } from 'react-intl';
import { Accordion, type AccordionItem } from '@/components/shared/Accordion';
import { Tree, type TreeNode } from '@/components/shared/Tree';

const CAPABILITIES = [
  { icon: '💬', titleId: 'about.capabilities.consulting.title', descId: 'about.capabilities.consulting.description' },
  { icon: '📋', titleId: 'about.capabilities.plans.title', descId: 'about.capabilities.plans.description' },
  { icon: '✅', titleId: 'about.capabilities.review.title', descId: 'about.capabilities.review.description' },
  { icon: '📱', titleId: 'about.capabilities.mobile.title', descId: 'about.capabilities.mobile.description' },
] as const;

const HELP_ITEM_DEFINITIONS = [
  {
    id: 'ai-consulting',
    titleId: 'about.faq.aiConsulting.title',
    contentId: 'about.faq.aiConsulting.content',
  },
  {
    id: 'plan-review',
    titleId: 'about.faq.planReview.title',
    contentId: 'about.faq.planReview.content',
  },
  {
    id: 'official-source',
    titleId: 'about.faq.officialSource.title',
    contentId: 'about.faq.officialSource.content',
  },
] as const;

const CAPABILITY_TREE_DEFINITIONS = [
  {
    id: 'planning',
    labelId: 'about.tree.planning.label',
    descriptionId: 'about.tree.planning.description',
    children: [
      { id: 'planning-chat', labelId: 'about.tree.planning.chat.label', descriptionId: 'about.tree.planning.chat.description' },
      { id: 'planning-plan', labelId: 'about.tree.planning.plan.label', descriptionId: 'about.tree.planning.plan.description' },
      { id: 'planning-review', labelId: 'about.tree.planning.review.label', descriptionId: 'about.tree.planning.review.description' },
    ],
  },
  {
    id: 'data',
    labelId: 'about.tree.data.label',
    descriptionId: 'about.tree.data.description',
    children: [
      { id: 'data-score', labelId: 'about.tree.data.score.label', descriptionId: 'about.tree.data.score.description' },
      { id: 'data-school', labelId: 'about.tree.data.school.label', descriptionId: 'about.tree.data.school.description' },
    ],
  },
] as const;

export function AboutPage() {
  const intl = useIntl();
  const helpItems: AccordionItem[] = HELP_ITEM_DEFINITIONS.map((item) => ({
    id: item.id,
    title: intl.formatMessage({ id: item.titleId }),
    content: intl.formatMessage({ id: item.contentId }),
  }));
  const capabilityTree: TreeNode[] = CAPABILITY_TREE_DEFINITIONS.map((node) => ({
    id: node.id,
    label: intl.formatMessage({ id: node.labelId }),
    description: intl.formatMessage({ id: node.descriptionId }),
    children: node.children.map((child) => ({
      id: child.id,
      label: intl.formatMessage({ id: child.labelId }),
      description: intl.formatMessage({ id: child.descriptionId }),
    })),
  }));

  return (
    <main className="flex-1 overflow-y-auto px-4 py-6 pb-20 lg:pb-6">
      <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 text-xl text-white">
          🎓
        </div>
        <h1 className="mt-4 text-xl font-bold text-gray-900 dark:text-gray-100">
          <FormattedMessage id="shell.appName" />
        </h1>
        <p className="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
          <FormattedMessage id="about.hero.description" />
        </p>
      </section>

      <section className="mt-5 grid gap-3 sm:grid-cols-2">
        {CAPABILITIES.map((item) => (
          <article key={item.titleId} className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
            <div className="text-2xl" aria-hidden="true">{item.icon}</div>
            <h2 className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
              <FormattedMessage id={item.titleId} />
            </h2>
            <p className="mt-1 text-xs leading-5 text-gray-500 dark:text-gray-400">
              <FormattedMessage id={item.descId} />
            </p>
          </article>
        ))}
      </section>

      <div className="mt-6 rounded-2xl bg-amber-50 p-4 text-xs leading-5 text-amber-800 dark:bg-amber-500/10 dark:text-amber-200">
        <FormattedMessage id="about.disclaimer" />
      </div>

      <section className="mt-5">
        <h2 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
          <FormattedMessage id="about.faq.title" />
        </h2>
        <Accordion items={helpItems} label={intl.formatMessage({ id: 'about.faq.ariaLabel' })} />
      </section>

      <section className="mt-5">
        <h2 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
          <FormattedMessage id="about.capabilityMap.title" />
        </h2>
        <Tree nodes={capabilityTree} label={intl.formatMessage({ id: 'about.capabilityMap.ariaLabel' })} defaultExpandedIds={['planning']} />
      </section>

      <Link to="/" className="mt-6 inline-flex rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
        <FormattedMessage id="about.backToChat" />
      </Link>
    </main>
  );
}
