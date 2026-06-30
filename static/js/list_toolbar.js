/**
 * Shared list toolbar: filter/sort popovers, chip removal, and clear actions.
 * Initialized per page via data-toolbar-prefix ("project" or "task").
 */
(function () {
    var script = document.currentScript;
    var prefix = script && script.getAttribute('data-toolbar-prefix');
    if (!prefix) {
        return;
    }

    var filterTrigger = document.getElementById(prefix + '-filter-trigger');
    var sortTrigger = document.getElementById(prefix + '-sort-trigger');
    var filterPopover = document.getElementById(prefix + '-filter-popover');
    var sortPopover = document.getElementById(prefix + '-sort-popover');
    var filterClearBtn = document.getElementById(prefix + '-filter-clear');
    var chipsClearAllBtn = document.getElementById(prefix + '-chips-clear-all');
    var dueFilterSelect = document.getElementById(prefix + '-due-filter');
    var dueOnInput = document.getElementById(prefix + '-due-on-input');

    if (!filterTrigger || !sortTrigger || !filterPopover || !sortPopover) {
        return;
    }

    var openPopover = null;
    var POPOVER_TRANSITION_MS = 200;

    /** Fade and scale a popover open after removing `hidden`. */
    function openPopoverEl(el) {
        el.classList.remove('hidden');
        requestAnimationFrame(function () {
            el.classList.remove('opacity-0', 'scale-95', 'pointer-events-none');
            el.classList.add('opacity-100', 'scale-100');
        });
    }

    /** Fade and scale a popover closed, then apply `hidden`. */
    function closePopoverEl(el) {
        el.classList.remove('opacity-100', 'scale-100');
        el.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
        window.setTimeout(function () {
            el.classList.add('hidden');
        }, POPOVER_TRANSITION_MS);
    }

    /** Show one popover and hide the other. */
    function setPopoverOpen(popover) {
        var isFilter = popover === filterPopover;
        if (isFilter) {
            closePopoverEl(sortPopover);
            openPopoverEl(filterPopover);
        } else {
            closePopoverEl(filterPopover);
            openPopoverEl(sortPopover);
        }
        filterTrigger.setAttribute('aria-expanded', isFilter ? 'true' : 'false');
        sortTrigger.setAttribute('aria-expanded', !isFilter ? 'true' : 'false');
        openPopover = popover;
    }

    /** Close any open popover and restore aria state. */
    function closePopovers() {
        closePopoverEl(filterPopover);
        closePopoverEl(sortPopover);
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
        params.delete('due_on');
        navigateWithParams(params);
    }

    /** Remove one value from a comma-separated GET param, or drop the param. */
    function removeChipValue(param, value) {
        var params = currentParams();

        if (param === 'due') {
            params.delete('due');
            params.delete('due_on');
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

    if (dueFilterSelect && dueOnInput) {
        /** Show the calendar input only when "By date" is selected. */
        function syncDueOnVisibility() {
            var showCalendar = dueFilterSelect.value === 'by_date';
            dueOnInput.classList.toggle('hidden', !showCalendar);
        }

        dueFilterSelect.addEventListener('change', syncDueOnVisibility);
        syncDueOnVisibility();
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

    document.querySelectorAll('.' + prefix + '-chip-remove').forEach(function (button) {
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
