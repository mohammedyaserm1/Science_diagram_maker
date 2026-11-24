import { useRef } from 'react';
import { canPreview } from '../util/diagram_util';

export default function DiagramPreview({ diagram }) {
    const dialogRef = useRef(null);
    if (!canPreview(diagram)) {
        return <div className="preview-empty">No validated preview</div>;
    }

    const imageUrl = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(diagram.svg)}`;
    const name = diagram.concept.name;
    const headingId = `preview-title-${diagram.concept.id}`;
    return (
        <>
            <button
                type="button"
                className="preview-button"
                aria-label={`Enlarge ${name} preview`}
                onClick={() => dialogRef.current.showModal()}
            >
                <img src={imageUrl} alt={`Animated diagram of ${name}`} />
                <span aria-hidden="true">↗</span>
            </button>
            <dialog className="preview-dialog" ref={dialogRef} aria-labelledby={headingId}>
                <div className="dialog-heading">
                    <h2 id={headingId}>{name}</h2>
                    <button type="button" onClick={() => dialogRef.current.close()}>Close</button>
                </div>
                <img src={imageUrl} alt={`Animated diagram of ${name}`} />
            </dialog>
        </>
    );
}
