/**
 * MCP Apps bridge for postMessage communication with host.
 *
 * When rendered in Claude Desktop, VS Code, or other MCP hosts,
 * these functions communicate via postMessage to the parent frame.
 */

import type { FlightFinderData } from '@/types/flightfinder';

// ─────────────────────────────────────────────────────────────────────────────
// Data Initialization
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Get the data injected by the Python server.
 * The server replaces <!--INJECT_DATA--> with a script setting window.__FLIGHTFINDER_DATA__
 */
export function getInjectedData<T extends FlightFinderData>(): T | null {
  return (window.__FLIGHTFINDER_DATA__ as T) ?? null;
}

// ─────────────────────────────────────────────────────────────────────────────
// MCP Apps PostMessage API
// ─────────────────────────────────────────────────────────────────────────────

interface ToolMessage {
  type: 'tool';
  payload: {
    toolName: string;
    params: Record<string, unknown>;
  };
}

interface LinkMessage {
  type: 'link';
  payload: {
    url: string;
  };
}

interface PromptMessage {
  type: 'prompt';
  payload: {
    prompt: string;
  };
}

type MCPMessage = ToolMessage | LinkMessage | PromptMessage;

/**
 * Send a message to the MCP host.
 */
function postToHost(message: MCPMessage): void {
  if (window.parent !== window) {
    window.parent.postMessage(message, '*');
  } else {
    // Fallback for development/testing
    console.log('[MCP Bridge]', message);
  }
}

/**
 * Call an MCP tool from the UI.
 * The host will execute the tool and may update the UI with new data.
 *
 * @example
 * callTool('search_flights', { origin: 'SFO', destination: 'NRT' });
 */
export function callTool(name: string, params: Record<string, unknown>): void {
  postToHost({
    type: 'tool',
    payload: { toolName: name, params },
  });
}

/**
 * Open a URL in the user's browser.
 * The host handles opening the link appropriately.
 *
 * @example
 * openLink('https://www.kiwi.com/booking/123456');
 */
export function openLink(url: string): void {
  postToHost({
    type: 'link',
    payload: { url },
  });
}

/**
 * Send a prompt to the chat.
 * The host will add this as a user message in the conversation.
 *
 * @example
 * sendPrompt('Search for cheaper flights to Tokyo in March');
 */
export function sendPrompt(prompt: string): void {
  postToHost({
    type: 'prompt',
    payload: { prompt },
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Utility Functions
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Format a price with currency symbol.
 */
export function formatPrice(price: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price);
}

/**
 * Format a date string for display.
 */
export function formatDate(isoDate: string): string {
  const date = new Date(isoDate);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format a datetime string for display.
 */
export function formatDateTime(isoDateTime: string): string {
  const date = new Date(isoDateTime);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

/**
 * Format stops as human-readable text.
 */
export function formatStops(stops: number): string {
  if (stops === 0) return 'Direct';
  if (stops === 1) return '1 stop';
  return `${stops} stops`;
}

/**
 * Generate star rating display.
 */
export function formatRating(rating: number | null | undefined): string {
  if (rating == null) return 'N/A';
  const fullStars = Math.floor(rating);
  const halfStar = rating % 1 >= 0.5;
  const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
  return '★'.repeat(fullStars) + (halfStar ? '☆' : '') + '☆'.repeat(emptyStars);
}
