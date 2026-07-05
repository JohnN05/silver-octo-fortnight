# Decibel Dispatch // Dashboard Design Specification
**Date:** 2026-07-05
**Status:** Approved

This specification defines the user interface design system and layout rules for the Decibel Dispatch EDM Ticket Valuation dashboard.

---

## 1. Design Philosophy
- **Ultra-Minimalism:** Eliminate all background glows, glass gradients, cards, and box-shadows. Let typography, clean grids, and whitespace structure the page.
- **Hardware Dial Accent:** A single visual connection to electronic music hardware (mixers, pre-amps, synthesizers) represented by a small, color-coded solid status dot (LED) next to event titles.
- **Precision Typography:** Use a high-contrast geometric sans-serif for UI labels and titles, and a precise typewriter monospace font for pricing and date columns.

---

## 2. Design Tokens

### A. Color Palette
- `--bg-main`: `#0a0b0d` — Matte charcoal backdrop.
- `--border-color`: `#1a1d24` — Muted hairline grid borders.
- `--text-primary`: `#f8f9fa` — Cold high-contrast off-white.
- `--text-muted`: `#6e7681` — Slate gray for labels and structural subtitles.
- `--success-green`: `#10b981` — Soft green for positive valuation/ROI.
- `--alert-red`: `#ef4444` — Muted coral red for negative ROI or pricing errors.

### B. Performer Priority LEDs (Status Dots)
- `CRITICAL`: `#ef4444` (Coral red) — Highest resale velocity and ROI.
- `HIGH`: `#f59e0b` (Amber) — Significant markup potential.
- `MEDIUM`: `#3b82f6` (Blue) — Standard demand and margins.
- `LOW`: `#6b7280` (Slate gray) — Minimal/no margin.

### C. Typography
- **Primary/UI Font:** `Inter` or `Plus Jakarta Sans`
- **Data/Numeric Font:** `JetBrains Mono`

---

## 3. UI Structure

### Header Section
- A border-bottom divided header displaying the title (`DECIBEL DISPATCH`) and subtitle (`// EDM TICKET VALUATION ENGINE`).
- Right-aligned metadata displaying the last database scan timestamp and real-time dashboard health statistics.

### Controls Bar
- Flex-based row containing text button filters for Venue selection and Sorting parameters (ROI, Date, Popularity). Active filters are highlighted with solid white background and dark text.

### Opportunity Index Table
- A spacious table layout showing:
  1. **Event / Artist** with the performer priority LED dot and the SeatGeek popularity percentage.
  2. **Venue**
  3. **Date**
  4. **Face Value** (Right aligned)
  5. **Lowest Resale** (Right aligned)
  6. **ROI Potential** (Right aligned, color-coded green/red)
  7. **Actions** (Center aligned, outline buttons)

---

## 4. Visual Mockup Reference
The approved mockup can be opened directly at:
- [mockup-ultra-minimalist.jpg](file:///C:/Users/johnn/Desktop/gemini/edm_ticket_tracker/docs/mockup-ultra-minimalist.jpg)
