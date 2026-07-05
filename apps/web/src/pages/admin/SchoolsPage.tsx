import { useState } from 'react';
import { useIntl } from 'react-intl';
import { Modal } from '@/components/shared/Modal';
import { useSchoolsQuery, type SchoolsResponse } from '@/hooks/useDataQuery';

type SchoolRow = SchoolsResponse['schools'][number];

function getSchoolTags(school: SchoolRow, fallbackLabel: string): string[] {
  const tags = [];
  if (school.is985) tags.push('985');
  if (school.is211) tags.push('211');
  return tags.length > 0 ? tags : [fallbackLabel];
}

export function AdminSchoolsPage() {
  const intl = useIntl();
  const [keyword, setKeyword] = useState('');
  const [selectedSchool, setSelectedSchool] = useState<SchoolRow | null>(null);
  const schoolsQuery = useSchoolsQuery(keyword);
  const schools = schoolsQuery.data?.schools ?? [];
  const total = schoolsQuery.data?.total ?? schools.length;
  const regularLabel = intl.formatMessage({ id: 'admin.schools.tag.regular' });
  const featuredCount = schools.filter((school) => school.is985 || school.is211).length;

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold text-blue-600 dark:text-blue-300">T-E-16</p>
            <h2 className="mt-1 text-2xl font-black text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.schools.title' })}</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              {intl.formatMessage({ id: 'admin.schools.description' })}
            </p>
          </div>
          <label className="flex min-w-full flex-col gap-1 lg:min-w-[22rem]">
            <span className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.schools.searchLabel' })}</span>
            <input
              type="search"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder={intl.formatMessage({ id: 'admin.schools.searchPlaceholder' })}
              className="min-h-12 rounded-xl border border-slate-200 px-3 text-sm text-slate-800 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            />
          </label>
        </div>
      </section>

      {schoolsQuery.isLoading && (
        <div role="status" className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
          {intl.formatMessage({ id: 'admin.schools.loading' })}
        </div>
      )}

      {schoolsQuery.isError && (
        <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
          {intl.formatMessage({ id: 'admin.schools.error' })}
        </div>
      )}

      {!schoolsQuery.isLoading && !schoolsQuery.isError && (
        <section aria-label={intl.formatMessage({ id: 'admin.schools.gridAriaLabel' })}>
          <div className="mb-3 flex flex-col gap-1 text-sm sm:flex-row sm:items-center sm:justify-between">
            <h3 className="font-bold text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.schools.resultTitle' })}</h3>
            <span className="text-slate-500 dark:text-slate-400">
              {intl.formatMessage({ id: 'admin.schools.summary' }, { total, featured: featuredCount })}
            </span>
          </div>

          {schools.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
              {intl.formatMessage({ id: 'admin.schools.empty' })}
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {schools.map((school) => (
                <article
                  key={school.id}
                  className="flex min-h-56 flex-col rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-300">{school.province}</p>
                      <h4 className="mt-2 text-lg font-black text-slate-950 dark:text-white">{school.name}</h4>
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                      {school.id}
                    </span>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {getSchoolTags(school, regularLabel).map((tag) => (
                      <span
                        key={tag}
                        className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-200"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>

                  <p className="mt-4 flex-1 text-sm leading-6 text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.schools.cardNote' })}</p>

                  <button
                    type="button"
                    onClick={() => setSelectedSchool(school)}
                    className="mt-5 inline-flex min-h-10 items-center justify-center rounded-xl bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
                  >
                    {intl.formatMessage({ id: 'admin.schools.viewDetail' }, { name: school.name })}
                  </button>
                </article>
              ))}
            </div>
          )}
        </section>
      )}

      <Modal
        open={selectedSchool !== null}
        title={selectedSchool?.name ?? intl.formatMessage({ id: 'admin.schools.detailTitleFallback' })}
        description={selectedSchool ? intl.formatMessage({ id: 'admin.schools.detailDescription' }, { province: selectedSchool.province }) : undefined}
        onClose={() => setSelectedSchool(null)}
      >
        {selectedSchool && (
          <dl className="space-y-3">
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">{intl.formatMessage({ id: 'admin.schools.columns.id' })}</dt>
              <dd className="font-semibold text-slate-950">{selectedSchool.id}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">{intl.formatMessage({ id: 'admin.schools.columns.province' })}</dt>
              <dd className="font-semibold text-slate-950">{selectedSchool.province}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">{intl.formatMessage({ id: 'admin.schools.columns.tags' })}</dt>
              <dd className="font-semibold text-slate-950">{getSchoolTags(selectedSchool, regularLabel).join(' / ')}</dd>
            </div>
            <p className="rounded-2xl bg-slate-50 p-4 text-sm leading-6 text-slate-600">
              {intl.formatMessage({ id: 'admin.schools.detailNote' })}
            </p>
          </dl>
        )}
      </Modal>
    </div>
  );
}
