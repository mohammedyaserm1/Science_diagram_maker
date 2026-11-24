export const validationLabels = {
    svg_validity: 'SVG valid',
    viewbox_bounds: 'Within viewBox',
    title_and_labels: 'Title and labels',
    animation: 'SMIL animation',
    security: 'SVG security',
};

export function formatCost(cost) {
    return cost == null ? 'Unavailable' : `$${cost.toFixed(8)}`;
}

export function canPreview(diagram) {
    return Boolean(diagram?.svg && diagram.passed
        && diagram.validation?.checks.some((check) => check.name === 'security' && check.passed));
}
