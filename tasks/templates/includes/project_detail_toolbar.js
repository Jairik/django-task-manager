/**
 * Project detail task toolbar: filter/sort popovers, chip removal, and clear actions.
 */
(function () {
    var filterTrigger = document.getElementById('task-filter-trigger');
    var sortTrigger = document.getElementById('task-sort-trigger');
    var filterPopover = document.getElementById('task-filter-popover');
    var sortPopover = document.getElementById('task-sort-popover');
    var filterClearBtn = document.getElementById('task-filter-clear');
    var chipsClearAllBtn = document.getElementById('task-chips-clear-all');

    if (!filterTrigger || !sortTrigger || !filterPopover || !sortPopover) {
        return;
    }

    var openPopover = null;

    /** Show one popover and hide the other. */
    function setPopoverOpen(popover) {
        var isFilter = popover === filterPopover;
        filterPopover.classList.toggle('hidden', !isFilter);
        sortPopover.classList.toggle('hidden', isFilter);
        filterTrigger.setAttribute('aria-expanded', isFilter ? 'true' : 'false');
        sortTrigger.setAttribute('aria-expanded', !isFilter ? 'true' : 'false');
        openPopover = popover;
    }

    /** Close any open popover and restore aria state. */
    function closePopovers() {
        filterPopover.classList.add('hidden');
        sortPopover.classList.add('hidden');
        filterTrigger.setAttribute('aria-expanded', 'false');
        sortTrigger.setAttribute('aria-expanded', 'false');
        openPopover = null;
    }

    /** Toggle the popover tied to a trigger button. */
    function togglePopover(popover, trigger) {
        if (openPopover === popover) {
            closePopovers();
            trigger.focus();
            return;
        }
        setPopoverOpen(popover);
    }

    /** Navigate to a new query string, preserving the current path. */
    function navigateWithParams(params) {
        var query = params.toString();
        var target = window.location.pathname + (query ? '?' + query : '');
        window.location.assign(target);
    }

    /** Read the current page query string as URLSearchParams. */
    function currentParams() {
        return new URLSearchParams(window.location.search);
    }

    /** Remove every filter param while keeping search and sort. */
    function clearFilterParams() {
        var params = currentParams();
        params.delete('priority');
        params.delete('due');
        navigateWithParams(params);
    }

    /** Remove one value from a comma-separated GET param, or drop the param. */
    function removeChipValue(param, value) {
        var params = currentParams();

        if (param === 'due') {
            params.delete('due');
            navigateWithParams(params);
            return;
        }

        var raw = params.get(param);
        if (!raw) {
            return;
        }

        var remaining = raw.split(',').filter(function (part) {
            return part.trim() !== value;
        });

        if (remaining.length) {
            params.set(param, remaining.join(','));
        } else {
            params.delete(param);
        }

        navigateWithParams(params);
    }

    filterTrigger.addEventListener('click', function (event) {
        event.stopPropagation();
        togglePopover(filterPopover, filterTrigger);
    });

    sortTrigger.addEventListener('click', function (event) {
        event.stopPropagation();
        togglePopover(sortPopover, sortTrigger);
    });

    if (filterClearBtn) {
        filterClearBtn.addEventListener('click', function () {
            clearFilterParams();
        });
    }

    if (chipsClearAllBtn) {
        chipsClearAllBtn.addEventListener('click', function () {
            clearFilterParams();
        });
    }

    document.querySelectorAll('.task-chip-remove').forEach(function (button) {
        button.addEventListener('click', function () {
            removeChipValue(button.getAttribute('data-chip-param'), button.getAttribute('data-chip-value'));
        });
    });

    document.addEventListener('click', function (event) {
        if (!openPopover) {
            return;
        }

        var target = event.target;
        if (filterPopover.contains(target) || sortPopover.contains(target)) {
            return;
        }
        if (filterTrigger.contains(target) || sortTrigger.contains(target)) {
            return;
        }

        closePopovers();
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && openPopover) {
            var trigger = openPopover === filterPopover ? filterTrigger : sortTrigger;
            closePopovers();
            trigger.focus();
        }
    });
})();
