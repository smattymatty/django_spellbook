/**
 * Django Spellbook - Table of Contents Module
 * Handles TOC initialization, expansion, and state management
 */

const TOC_ACTIVE_PAGE_KEY = "spellbook_active_page";

/**
 * Get current page info from the active TOC item
 * @returns {Object|null} Page info with activePageId, parentPath, and fullPath
 */
function getCurrentPageInfo() {
  const activeItem = document.querySelector(".toc-item.active");
  if (!activeItem) return null;

  const tocId = activeItem.dataset.tocId;
  const parentPath = [];
  let current = activeItem;

  // Build the path from root to active item
  while (current && current.dataset.tocId) {
    parentPath.unshift(current.dataset.tocId);
    // Move up to parent toc item
    const parentSublist = current.parentElement.closest(".toc-sublist");
    if (parentSublist) {
      current = parentSublist.parentElement.closest(".toc-item");
    } else {
      break;
    }
  }

  return {
    activePageId: tocId,
    parentPath: parentPath,
    fullPath: parentPath.join(".")
  };
}

/**
 * Save current active page to localStorage
 */
function saveCurrentPage() {
  try {
    const pageInfo = getCurrentPageInfo();
    if (pageInfo) {
      localStorage.setItem(TOC_ACTIVE_PAGE_KEY, JSON.stringify(pageInfo));
    }
  } catch (e) {
    console.warn("Failed to save active page to localStorage:", e);
  }
}

/**
 * Get stored active page from localStorage
 * @returns {Object|null} Stored page info
 */
function getStoredActivePage() {
  try {
    const stored = localStorage.getItem(TOC_ACTIVE_PAGE_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch (e) {
    console.warn("Failed to parse active page from localStorage:", e);
    return null;
  }
}

/**
 * Expand a TOC item
 * @param {HTMLElement} tocItem - The TOC item element
 * @param {HTMLElement} sublist - The sublist to expand
 * @param {HTMLElement} toggle - The toggle button
 */
function expandTocItem(tocItem, sublist, toggle) {
  if (!sublist) return;

  // First, remove collapsed class so scrollHeight calculates correctly
  sublist.classList.remove("collapsed");

  const totalHeight = sublist.scrollHeight;
  sublist.style.maxHeight = totalHeight + "px";

  if (toggle) {
    toggle.classList.remove("collapsed");
  }

  // Update parent heights if this item is nested
  let parent = sublist.parentElement.closest(".toc-sublist");
  while (parent) {
    parent.classList.remove("collapsed");
    parent.style.maxHeight = parent.scrollHeight + "px";
    parent = parent.parentElement.closest(".toc-sublist");
  }
}

/**
 * Collapse a TOC item
 * @param {HTMLElement} tocItem - The TOC item element
 * @param {HTMLElement} sublist - The sublist to collapse
 * @param {HTMLElement} toggle - The toggle button
 */
function collapseTocItem(tocItem, sublist, toggle) {
  if (!sublist) return;

  // Collapse this sublist and all nested sublists
  sublist.style.maxHeight = "0px";
  sublist.classList.add("collapsed");

  if (toggle) {
    toggle.classList.add("collapsed");
  }

  // Collapse all nested items
  sublist.querySelectorAll(".toc-sublist").forEach((nested) => {
    nested.style.maxHeight = "0px";
    nested.classList.add("collapsed");
    const nestedToggle = nested.previousElementSibling?.querySelector(".toc-toggle");
    if (nestedToggle) {
      nestedToggle.classList.add("collapsed");
    }
  });
}

/**
 * Expand the path to the active item
 * @param {Array<string>} parentPath - Array of toc-ids forming the path
 */
function expandPathToActiveItem(parentPath) {
  if (!parentPath || parentPath.length === 0) return;

  // Expand each parent level - we exclude the last item because that's the current page itself
  // The current page doesn't need expansion, only its ancestors do
  for (let i = 0; i < parentPath.length - 1; i++) {
    const tocId = parentPath[i];
    const tocItem = document.querySelector(`[data-toc-id="${tocId}"]`);

    if (tocItem) {
      const sublist = tocItem.querySelector(":scope > .toc-sublist");
      const toggle = tocItem.querySelector(":scope > .toc-item-header > .toc-toggle");

      if (sublist) {
        expandTocItem(tocItem, sublist, toggle);
      }
    }
  }

  // ALSO expand the active item itself IF it has children (directory index case)
  // This handles the case where we're viewing a directory index page
  const activeItemId = parentPath[parentPath.length - 1];
  const activeItem = document.querySelector(`[data-toc-id="${activeItemId}"]`);
  if (activeItem) {
    const sublist = activeItem.querySelector(":scope > .toc-sublist");
    const toggle = activeItem.querySelector(":scope > .toc-item-header > .toc-toggle");

    // If the active item has children, expand it
    if (sublist) {
      expandTocItem(activeItem, sublist, toggle);
    }
  }
}

/**
 * Try to restore active item from storage
 * @param {Object} storedPage - Stored page info from localStorage
 */
function restoreActiveItemFromStorage(storedPage) {
  // Find the stored active item
  const activeItem = document.querySelector(`[data-toc-id="${storedPage.activePageId}"]`);
  if (activeItem) {
    // Add active class if not already present
    if (!activeItem.classList.contains("active")) {
      activeItem.classList.add("active");
    }

    // Expand path to this item
    expandPathToActiveItem(storedPage.parentPath);
  }
}

/**
 * Initialize TOC state based on current active page
 * This is the main initialization function that runs on page load
 */
function initializeTocState() {
  // Get current page info FIRST before collapsing
  const currentPageInfo = getCurrentPageInfo();

  // Collapse everything by default (no transition due to toc-no-transition class)
  document.querySelectorAll(".toc-sublist").forEach((sublist) => {
    sublist.style.maxHeight = "0px";
    sublist.classList.add("collapsed");
  });

  document.querySelectorAll(".toc-toggle").forEach((toggle) => {
    toggle.classList.add("collapsed");
  });

  if (currentPageInfo) {
    // Save current page as the active page
    saveCurrentPage();

    // Expand path to current active item
    expandPathToActiveItem(currentPageInfo.parentPath);
  } else {
    // No active item found, check if we have a stored active page
    const storedPage = getStoredActivePage();
    if (storedPage) {
      // Try to restore the active state and expand its path
      restoreActiveItemFromStorage(storedPage);
    }
  }

  // Enable transitions after initial expansion is complete
  // Small delay ensures expansion has finished without visible animation
  setTimeout(() => {
    const tocWrapper = document.querySelector('.toc-wrapper');
    if (tocWrapper) {
      tocWrapper.classList.remove('toc-no-transition');
    }
  }, 50); // 50ms delay, imperceptible to users but ensures DOM updates are complete
}

/**
 * Set up click event listeners for TOC items
 */
function setupEventListeners() {
  document.querySelectorAll(".toc-item-header").forEach((header) => {
    header.addEventListener("click", (e) => {
      const tocItem = header.closest(".toc-item");
      const toggle = header.querySelector(".toc-toggle");
      const link = header.querySelector(".toc-link");
      const sublist = header.nextElementSibling;

      // If there's a sublist, toggle it
      if (sublist && sublist.classList.contains("toc-sublist")) {
        e.preventDefault();

        if (sublist.classList.contains("collapsed")) {
          expandTocItem(tocItem, sublist, toggle);
        } else {
          collapseTocItem(tocItem, sublist, toggle);
        }
      } else if (link && link.href) {
        // When clicking a link, save this as the new active page
        const linkTocId = tocItem.dataset.tocId;
        if (linkTocId) {
          // Remove active class from current item
          document.querySelectorAll(".toc-item.active").forEach(item => {
            item.classList.remove("active");
          });

          // Add active class to clicked item
          tocItem.classList.add("active");

          // Save the new active page
          saveCurrentPage();
        }

        window.location.href = link.href;
      }
    });
  });
}

/**
 * Initialize the TOC module
 */
function init() {
  initializeTocState();
  setupEventListeners();
}

// Run initialization when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  // DOM is already loaded, run immediately
  init();
}
