/**
 * TaskFlow Kanban Drag-and-Drop Controller
 * Implements native HTML5 drag events with asynchronous database state sync.
 */
document.addEventListener('DOMContentLoaded', () => {
    let draggedCard = null;

    const cards = document.querySelectorAll('.kanban-card');
    const dropZones = document.querySelectorAll('.kanban-cards');

    // Retrieve CSRF token from base meta tag or fallback hidden input
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';

    // Attach drag events to all task cards
    cards.forEach(card => {
        card.addEventListener('dragstart', (e) => {
            draggedCard = card;
            card.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', card.dataset.taskId);
        });

        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            draggedCard = null;
        });
    });

    // Attach dropzone events to column containers
    dropZones.forEach(zone => {
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            zone.classList.add('drag-over');
        });

        zone.addEventListener('dragenter', (e) => {
            e.preventDefault();
            zone.classList.add('drag-over');
        });

        zone.addEventListener('dragleave', () => {
            zone.classList.remove('drag-over');
        });

        zone.addEventListener('drop', async (e) => {
            e.preventDefault();
            zone.classList.remove('drag-over');

            if (!draggedCard) return;

            const targetStatus = zone.dataset.status;
            const taskId = draggedCard.dataset.taskId;
            const originContainer = draggedCard.parentElement;

            // If dropped in the same column, do nothing
            if (originContainer === zone) return;

            // Optimistic UI update: relocate DOM node immediately
            zone.appendChild(draggedCard);
            recalculateCounters();

            try {
                const response = await fetch(`/tasks/${taskId}/update-status`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ status: targetStatus })
                });

                const data = await response.json();

                if (!response.ok || !data.success) {
                    throw new Error(data.message || 'Server rejected status change');
                }
            } catch (err) {
                // Rollback DOM alteration on failure
                originContainer.appendChild(draggedCard);
                recalculateCounters();
                console.error('Failed to sync Kanban state with server:', err);
                alert(`Could not save status change: ${err.message}`);
            }
        });
    });

    /**
     * Recounts card badges across all columns after DOM mutations
     */
    function recalculateCounters() {
        dropZones.forEach(zone => {
            const count = zone.querySelectorAll('.kanban-card').length;
            const statusKey = zone.dataset.status;
            const counterElement = document.getElementById(`count-${statusKey}`);
            if (counterElement) {
                counterElement.textContent = count;
            }
        });
    }
});       