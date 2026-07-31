import { getDashboard, type DashboardSummary } from "@/lib/api";

export const dynamic = "force-dynamic";

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const integer = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

type CardProps = {
  label: string;
  value: string;
  hint: string;
};

function MetricCard({ label, value, hint }: CardProps) {
  return (
    <article className="metric-card">
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-hint">{hint}</p>
    </article>
  );
}

function Dashboard({ summary }: { summary: DashboardSummary }) {
  return (
    <>
      <section className="metrics" aria-label="Marketplace metrics">
        <MetricCard
          label="Revenue"
          value={currency.format(summary.revenue)}
          hint={`Last ${summary.period_days} days`}
        />
        <MetricCard
          label="Orders"
          value={integer.format(summary.orders)}
          hint={`${currency.format(summary.average_order_value)} average order`}
        />
        <MetricCard
          label="Catalog"
          value={integer.format(summary.sku_count)}
          hint={`${summary.stores} connected stores`}
        />
        <MetricCard
          label="Stock alerts"
          value={integer.format(summary.stock_alerts)}
          hint="Requires operator review"
        />
      </section>

      <section className="workflow-panel">
        <div>
          <p className="eyebrow">Nightly workflow</p>
          <h2>From provider APIs to decision-ready dashboards</h2>
          <p>
            Scheduled ingestion normalizes marketplace data, persists auditable metrics,
            refreshes Redis-backed summaries, and keeps pricing decisions behind explicit
            margin rules and human review.
          </p>
        </div>
        <ol className="workflow" aria-label="Data workflow">
          <li>Collect</li>
          <li>Normalize</li>
          <li>Validate</li>
          <li>Report</li>
        </ol>
      </section>
    </>
  );
}

export default async function HomePage() {
  let summary: DashboardSummary | null = null;
  let error: string | null = null;

  try {
    summary = await getDashboard(30);
  } catch (caught) {
    error = caught instanceof Error ? caught.message : "Dashboard API is unavailable";
  }

  return (
    <main>
      <header className="hero">
        <div>
          <p className="eyebrow">Portfolio edition</p>
          <h1>Marketplace Analytics Platform</h1>
          <p className="hero-copy">
            Next.js and FastAPI architecture for multi-store reporting, asynchronous sync,
            and decision support across more than 30,000 SKUs.
          </p>
        </div>
        <span className="status">Synthetic data only</span>
      </header>

      {summary ? (
        <Dashboard summary={summary} />
      ) : (
        <section className="error-panel" role="status">
          <p className="eyebrow">API status</p>
          <h2>Backend connection required</h2>
          <p>{error}</p>
          <code>uv run uvicorn marketplace_analytics.main:app --reload</code>
        </section>
      )}

      <footer>
        <span>Next.js + FastAPI + PostgreSQL + Redis</span>
        <a href="https://github.com/Arbitr3103">Vladimir Bragin</a>
      </footer>
    </main>
  );
}
