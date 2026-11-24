import { formatCost } from '../util/diagram_util';

export default function DashboardSummary({ diagrams }) {
    const costs = diagrams.map((diagram) => diagram.estimated_cost_usd).filter((cost) => cost != null);
    const totalCost = costs.length ? costs.reduce((total, cost) => total + cost, 0) : null;
    const stats = [
        { label: 'Concepts', value: diagrams.length },
        { label: 'Gemini passed', value: diagrams.filter((diagram) => diagram.passed).length, tone: 'pass-text' },
        { label: 'Gemini failed', value: diagrams.filter((diagram) => diagram.passed === false).length, tone: 'fail-text' },
        { label: 'Estimated cost', value: formatCost(totalCost), detail: `${costs.length} of ${diagrams.length} recorded in USD` },
        { label: 'Total retries', value: diagrams.reduce((total, diagram) => total + (diagram.retries?.total_retries ?? 0), 0) },
    ];
    return (
        <dl className="summary" aria-label="Generation summary">
            {stats.map(({ label, value, detail, tone }) => (
                <div key={label}>
                    <dt>{label}</dt>
                    <dd className={tone}>{value}</dd>
                    {detail && <dd className="summary-detail">{detail}</dd>}
                </div>
            ))}
        </dl>
    );
}
