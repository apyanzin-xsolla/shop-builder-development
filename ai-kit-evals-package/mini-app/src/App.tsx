import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import dashboardData from './data/dashboard-data.json';

type Variant = 'AI Kit' | 'Docs baseline' | 'No-context baseline';

const colors: Record<Variant | 'Neutral', string> = {
  'AI Kit': '#6ee7b7',
  'Docs baseline': '#93c5fd',
  'No-context baseline': '#fbbf24',
  Neutral: '#a1a1aa',
};

function zipCases(cases: string[], values: Record<string, number[]>) {
  return cases.map((name, index) => ({
    name,
    ...Object.fromEntries(Object.entries(values).map(([key, rows]) => [key, rows[index] ?? 0])),
  }));
}

const tokenRows = zipCases(dashboardData.prompt_only.cases, {
  'AI Kit': dashboardData.prompt_only.ai_kit_tokens,
  'No-context baseline': dashboardData.prompt_only.no_context_tokens,
});

const confidenceRows = zipCases(dashboardData.prompt_only.cases, {
  'AI Kit skill rubric': dashboardData.prompt_only.ai_kit_skill_rubric_pct,
  'AI Kit validated confidence': dashboardData.prompt_only.ai_kit_validated_confidence_pct,
  'No-context validated confidence': dashboardData.prompt_only.no_context_validated_confidence_pct,
});

const productionRows = zipCases(dashboardData.production.cases, {
  'AI Kit': dashboardData.production.ai_kit_validated_confidence_pct,
  'Docs baseline': dashboardData.production.docs_validated_confidence_pct,
  'No-context baseline': dashboardData.production.no_context_validated_confidence_pct,
});

const effortRows = [
  {
    name: 'AI Kit',
    Clarifications: dashboardData.production.clarifications[0],
    Corrections: dashboardData.production.manual_corrections[0],
  },
  {
    name: 'Docs',
    Clarifications: dashboardData.production.clarifications[1],
    Corrections: dashboardData.production.manual_corrections[1],
  },
  {
    name: 'No context',
    Clarifications: dashboardData.production.clarifications[2],
    Corrections: dashboardData.production.manual_corrections[2],
  },
];

const safetyRows = [
  { name: 'AI Kit', value: dashboardData.production.safety_errors[0] },
  { name: 'Docs', value: dashboardData.production.safety_errors[1] },
  { name: 'No context', value: dashboardData.production.safety_errors[2] },
];

const efficiencyRows = zipCases(dashboardData.prompt_only.cases, {
  'Efficiency gain': dashboardData.prompt_only.ai_kit_efficiency_gain_pct,
});

function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <section className="stat-card">
      <strong>{value}</strong>
      <span>{label}</span>
    </section>
  );
}

function ChartCard({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return (
    <section className="chart-card">
      <header>
        <h2>{title}</h2>
        <p>{description}</p>
      </header>
      <div className="chart-body">{children}</div>
    </section>
  );
}

function Bars({
  data,
  series,
  yMax,
  suffix = '',
  reference,
}: {
  data: Array<Record<string, string | number>>;
  series: string[];
  yMax?: number;
  suffix?: string;
  reference?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 20, right: 16, left: 0, bottom: 24 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.10)" />
        <XAxis dataKey="name" tick={{ fill: '#a1a1aa', fontSize: 12 }} />
        <YAxis domain={yMax ? [0, yMax] : undefined} tick={{ fill: '#a1a1aa', fontSize: 12 }} />
        <Tooltip
          contentStyle={{ background: '#111318', border: '1px solid #2a2f3a', color: '#f4f4f5' }}
          formatter={(value) => [`${value}${suffix}`, '']}
        />
        <Legend />
        {reference ? <ReferenceLine y={reference} stroke="#6ee7b7" label="threshold" /> : null}
        {series.map((name) => (
          <Bar key={name} dataKey={name} fill={colors[name as Variant] ?? '#a78bfa'} radius={[4, 4, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

function SafetyBars() {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={safetyRows} margin={{ top: 20, right: 16, left: 0, bottom: 24 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.10)" />
        <XAxis dataKey="name" tick={{ fill: '#a1a1aa', fontSize: 12 }} />
        <YAxis allowDecimals={false} tick={{ fill: '#a1a1aa', fontSize: 12 }} />
        <Tooltip contentStyle={{ background: '#111318', border: '1px solid #2a2f3a', color: '#f4f4f5' }} />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {safetyRows.map((row) => (
            <Cell key={row.name} fill={row.name === 'No context' ? '#f87171' : '#6ee7b7'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export default function App() {
  return (
    <main className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">AI Kit Evaluation</p>
          <h1>{dashboardData.metadata.title}</h1>
          <p className="subtitle">
            Production-ready view for comparing AI Kit skills against docs and no-context baselines.
            The dashboard separates skill-rubric coverage from validated confidence.
          </p>
        </div>
      </section>

      <section className="stats-grid">
        <StatCard value={`${dashboardData.aggregate.avg_efficiency_gain_pct}%`} label="Avg AI Kit efficiency gain" />
        <StatCard value={`${dashboardData.aggregate.token_reduction_pct}%`} label="All-run token reduction" />
        <StatCard value="80%" label="Current AI Kit validated confidence" />
        <StatCard value="0" label="AI Kit safety errors" />
      </section>

      <section className="metrics">
        <h2>What we measure</h2>
        <div className="metric-list">
          <span>Tokens to accepted result</span>
          <span>Clarifications</span>
          <span>Manual corrections</span>
          <span>Skill-rubric coverage</span>
          <span>Validated confidence</span>
          <span>Safety errors</span>
        </div>
      </section>

      <section className="chart-grid">
        <ChartCard title="Tokens to accepted result" description="Y-axis: estimated tokens. X-axis: ready skill. Lower is better.">
          <Bars data={tokenRows} series={['AI Kit', 'No-context baseline']} suffix=" tokens" />
        </ChartCard>

        <ChartCard title="Skill rubric vs validated confidence" description="Y-axis: percent. 100% rubric is not 100% production confidence.">
          <Bars
            data={confidenceRows}
            series={['AI Kit skill rubric', 'AI Kit validated confidence', 'No-context validated confidence']}
            yMax={100}
            suffix="%"
          />
        </ChartCard>

        <ChartCard title="Production-risk validated confidence" description="Y-axis: validated confidence. X-axis: production-informed case.">
          <Bars data={productionRows} series={['AI Kit', 'Docs baseline', 'No-context baseline']} yMax={100} suffix="%" />
        </ChartCard>

        <ChartCard title="Clarifications and manual corrections" description="Y-axis: count across production-informed cases. Lower is better.">
          <Bars data={effortRows} series={['Clarifications', 'Corrections']} />
        </ChartCard>

        <ChartCard title="Safety errors" description="Y-axis: critical safety errors. Target is zero.">
          <SafetyBars />
        </ChartCard>

        <ChartCard title="AI Kit efficiency gain" description="Y-axis: weighted gain. Strong value threshold is 25%.">
          <Bars data={efficiencyRows} series={['Efficiency gain']} yMax={80} suffix="%" reference={25} />
        </ChartCard>
      </section>

      <section className="decision">
        <h2>Final decision</h2>
        <p>
          Use AI Kit for ready skills and keep docs as the fair baseline. The value is fewer missed
          failure modes and fewer correction loops, not only token savings.
        </p>
        <div className="pill-row">
          {dashboardData.metadata.ready_skills.map((skill) => (
            <span key={skill} className="pill active">{skill}</span>
          ))}
        </div>
        <p className="muted">
          Exclude until real content exists: {dashboardData.metadata.excluded_skills.join(', ')}.
        </p>
      </section>
    </main>
  );
}
