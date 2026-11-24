import DiagramPreview from './diagram_preview';
import ReviewControls from './review_controls';
import { formatCost, validationLabels } from '../util/diagram_util';

function ValidationChecks({ result }) {
    const checks = result.validation?.checks ?? [];
    const hasSvg = Boolean(result.attempts?.length || result.svg);
    const failedChecks = hasSvg ? checks.filter((check) => !check.passed) : [];
    return (
        <>
            <ul className="check-list" aria-label="Individual validation checks">
                {Object.entries(validationLabels).map(([name, label]) => {
                    const check = checks.find((item) => item.name === name);
                    const status = !check || !hasSvg ? 'Not run' : check.passed ? 'Pass' : 'Fail';
                    const tone = { Pass: 'pass-text', Fail: 'fail-text' }[status];
                    return (
                        <li key={name} title={check?.message}>
                            <span>{label}</span>
                            <span className={`check-status ${tone ?? ''}`}>{status}</span>
                        </li>
                    );
                })}
            </ul>
            {failedChecks.length > 0 && (
                <details className="check-details">
                    <summary>Failure details</summary>
                    <ul>
                        {failedChecks.map((check) => <li key={check.name}>{check.message}</li>)}
                    </ul>
                </details>
            )}
        </>
    );
}

function TokenUsage({ usage }) {
    if (!usage) return null;
    const counts = [
        ['Input', usage.input_tokens],
        ['Output', usage.output_tokens],
        ['Thinking', usage.thinking_tokens],
    ].filter(([, count]) => count != null);
    const label = usage.total_tokens == null
        ? 'Token usage'
        : `${usage.total_tokens.toLocaleString()} tokens`;
    if (!counts.length) {
        return usage.total_tokens == null ? null : <span className="muted">{label}</span>;
    }
    return (
        <details className="check-details">
            <summary>{label}</summary>
            <ul>
                {counts.map(([name, count]) => <li key={name}>{name} {count.toLocaleString()}</li>)}
            </ul>
        </details>
    );
}

export default function DiagramRow({ diagram, preview, generation, review, onReview, onGenerate }) {
    const result = generation?.result ?? diagram.latestFailure ?? diagram;
    const status = result.passed ? 'Passed' : result.validation ? 'Failed' : 'Not generated';
    const tone = { Passed: 'passed', Failed: 'failed', 'Not generated': 'pending' }[status];
    const error = generation?.error ?? result.error;
    return (
        <tr>
            <th scope="row" data-label="Concept">
                <span className="subject">{diagram.concept.subject}</span>
                <span className="concept-name">{diagram.concept.name}</span>
                <p className="concept-description">{diagram.concept.description}</p>
            </th>
            <td data-label="Animated preview">
                <DiagramPreview diagram={preview} />
                {preview.source === 'local' && (
                    <>
                        <p className="validation-caption">Local fallback · {preview.sourceReason}</p>
                        <p className="validation-caption">SVG checks passed · Science reviewed</p>
                    </>
                )}
                {preview.source === 'gemini' && (
                    <p className="validation-caption">
                        Gemini-generated · {preview.scientificallyReviewed ? 'Science reviewed' : 'Scientific review pending'}
                    </p>
                )}
            </td>
            <td data-label="Validation">
                {preview.source === 'local' && (
                    <p className="validation-caption">Gemini generation</p>
                )}
                <span className={`badge ${tone}`}>{status}</span>
                {generation?.result && (
                    <p className="validation-caption">Latest attempt</p>
                )}
                <ValidationChecks result={result} />
            </td>
            <td data-label="Generation">
                <div className="generation-cell">
                    <strong className="cost">{formatCost(result.estimated_cost_usd)}</strong>
                    <span className="muted">Estimated USD</span>
                    <TokenUsage usage={result.token_usage} />
                    <p className="retry-count">
                        <strong>{result.retries?.total_retries ?? '—'}</strong> retries
                        {result.retries && (
                            <span className="muted">
                                {result.retries.api_retries} API · {result.retries.validation_retries} validation
                            </span>
                        )}
                    </p>
                    <button
                        type="button"
                        className="generate-button"
                        aria-label={`Generate ${diagram.concept.name}`}
                        disabled={generation?.isGenerating}
                        onClick={onGenerate}
                    >{generation?.isGenerating ? 'Generating…' : 'Generate'}</button>
                    <div aria-live="polite">
                        {!generation?.isGenerating && error && <p className="row-error">{error}</p>}
                        {generation?.updated && <p className="row-success">New diagram ready for review.</p>}
                        {generation?.updated && !generation.savedForSession && (
                            <p className="row-error">This preview will reset on refresh because browser storage is unavailable.</p>
                        )}
                    </div>
                </div>
            </td>
            <td data-label="Reviewer"><ReviewControls diagram={diagram} review={review} onChange={onReview} /></td>
        </tr>
    );
}
