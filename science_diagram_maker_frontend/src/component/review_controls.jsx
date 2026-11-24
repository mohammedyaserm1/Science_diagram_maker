const reviewLabels = {
    pending: 'Pending review',
    approved: 'Approved',
    rejected: 'Rejected',
};

export default function ReviewControls({ diagram, review, onChange }) {
    const notesId = `notes-${diagram.concept.id}`;
    return (
        <div className="review-controls">
            <span className={`badge ${review.status}`}>{reviewLabels[review.status]}</span>
            <div className="review-actions">
                <button
                    type="button"
                    aria-pressed={review.status === 'approved'}
                    onClick={() => onChange({ status: 'approved' })}
                >Approve</button>
                <button
                    type="button"
                    aria-pressed={review.status === 'rejected'}
                    onClick={() => onChange({ status: 'rejected' })}
                >Reject</button>
            </div>
            <label htmlFor={notesId}>Reviewer notes</label>
            <textarea
                id={notesId}
                value={review.notes}
                onChange={(event) => onChange({ notes: event.target.value })}
                placeholder="Add a note…"
                rows={2}
            />
        </div>
    );
}
