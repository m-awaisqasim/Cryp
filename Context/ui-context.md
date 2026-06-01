# UI Context — MARK-XXXIX

## Theme

Dark only. No light mode. The design language is a dark technical workspace — near-black backgrounds, layered surfaces with subtle elevation, and vivid cyan/blue accents for interactive elements. The aesthetic is "JARVIS terminal meets modern dashboard" — clean, dense, information-rich, and slightly futuristic.

## Colors

All components must use these CSS custom properties — no hardcoded hex values anywhere.

| Role | CSS Variable | Value | Usage |
|------|-------------|-------|-------|
| Page background | `--bg-base` | `#0a0a0f` | Main app background |
| Surface (card/panel) | `--bg-surface` | `#12121a` | Chat area, sidebar, panels |
| Surface elevated | `--bg-elevated` | `#1a1a25` | Modals, dropdowns, hover states |
| Primary text | `--text-primary` | `#e8e8ef` | Headings, main content |
| Secondary text | `--text-secondary` | `#9ca3af` | Labels, metadata, timestamps |
| Muted text | `--text-muted` | `#6b7280` | Disabled, placeholders |
| Primary accent | `--accent-primary` | `#06b6d4` | Buttons, links, active states, orb glow |
| Accent hover | `--accent-hover` | `#22d3ee` | Button hover, link hover |
| Accent muted | `--accent-muted` | `#0891b2` | Secondary accents, badges |
| Border default | `--border-default` | `#27272a` | Dividers, card borders |
| Border focus | `--border-focus` | `#06b6d4` | Focus rings, active inputs |
| Error | `--state-error` | `#ef4444` | Errors, destructive actions |
| Success | `--state-success` | `#22c55e` | Success states, confirmations |
| Warning | `--state-warning` | `#f59e0b` | Warnings, deadlines approaching |
| User message bg | `--msg-user` | `#1e3a5f` | User chat bubbles |
| MARK-XXXIX message bg | `--msg-crypton` | `#1a1a25` | MARK-XXXIX chat bubbles |
| Voice active glow | `--voice-glow` | `rgba(6, 182, 212, 0.4)` | Orb animation when listening |

## Typography

| Role | Font | Variable | Usage |
|------|------|----------|-------|
| UI text | Inter | `--font-sans` | All interface text, labels, buttons |
| Code/mono | JetBrains Mono | `--font-mono` | Code blocks, JSON, logs, timestamps |
| Display | Inter (semibold) | `--font-display` | Headings, "MARK-XXXIX" branding |

### Scale

| Token | Size | Weight | Usage |
|-------|------|--------|-------|
| `text-xs` | 12px | 400 | Timestamps, metadata, badges |
| `text-sm` | 14px | 400 | Body secondary, labels |
| `text-base` | 16px | 400 | Body primary, chat messages |
| `text-lg` | 18px | 500 | Section headings |
| `text-xl` | 20px | 600 | Modal titles, important labels |
| `text-2xl` | 24px | 700 | Page titles |

## Border Radius

| Context | Value | Tailwind |
|---------|-------|----------|
| Inline / small UI | 4px | `rounded-sm` |
| Buttons, inputs, badges | 8px | `rounded-lg` |
| Cards, panels | 12px | `rounded-xl` |
| Modals, overlays | 16px | `rounded-2xl` |
| Full circle (orb, avatars) | 9999px | `rounded-full` |

## Component Library

- **Base**: shadcn/ui components (Button, Input, Card, Dialog, Dropdown, ScrollArea, Tooltip)
-- **Custom**: All MARK-XXXIX-specific components built on top of shadcn primitives
- **Installation**: Use `npx shadcn add [component]` — never write shadcn components from scratch
-- **Styling**: Override shadcn defaults with MARK-XXXIX color tokens in `globals.css`

## Layout Patterns

### Main App Layout
```
+---------------------------------------------------------+
|  Sidebar (280px)    |  Main Chat Area (flex-1)         |
|  - Memory context    |  - Header (title + voice toggle) |
|  - Active tasks      |  - Messages scroll area          |
|  - Deadline list     |  - Input bar (text + mic)        |
|  - Persona switcher  |                                  |
|  (collapsible)       |                                  |
+---------------------------------------------------------+
```

### Chat Message Pattern
- User messages: right-aligned, `--msg-user` background, sharp bottom-right corner
-- MARK-XXXIX messages: left-aligned, `--msg-crypton` background, sharp bottom-left corner
- Timestamps: `text-xs`, `--text-muted`, below each message
- Code blocks: `--bg-elevated` background, `--font-mono`, syntax highlighted, copy button

### Voice Mode Pattern
- Central orb animation (pulsing cyan glow when listening)
- Text transcript appears below orb in real-time
- Response spoken via Gemini Live audio, transcript shown after completion
- "Tap to speak" / "Listening..." / "Thinking..." state indicators

### Modal Pattern
- Centered overlay with `--bg-elevated` background
- Backdrop: `rgba(0, 0, 0, 0.7)` with blur
- Close button top-right, Escape key dismisses
- Max width: 560px for forms, 720px for content

## Icons

- **Library**: Lucide React (`lucide-react`)
- **Style**: Stroke-based only (no fill icons)
- **Sizes**: `h-4 w-4` for inline text, `h-5 w-5` for buttons, `h-6 w-6` for navigation
- **Color**: Inherit from parent text color, or `--accent-primary` for active states

## Animation

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Message appear | Fade + slide up | 200ms | `ease-out` |
| Orb pulse | Scale + opacity pulse | 1.5s | `ease-in-out`, infinite |
| Sidebar toggle | Width transition | 250ms | `ease-in-out` |
| Modal open | Fade backdrop + scale content | 200ms | `ease-out` |
| Toast notification | Slide in from right | 300ms | `ease-out` |
| Typing indicator | Bouncing dots | 1s | `ease-in-out`, infinite |

## Responsive Breakpoints

| Breakpoint | Width | Behavior |
|------------|-------|----------|
| Mobile | < 768px | Sidebar hidden behind hamburger, full-width chat |
| Tablet | 768-1024px | Sidebar collapsible to 80px icons-only |
| Desktop | > 1024px | Full sidebar (280px), optimal layout |

## Accessibility

- Minimum contrast ratio: 4.5:1 for all text
- Focus rings: 2px solid `--border-focus` with 2px offset
- Reduced motion: Respect `prefers-reduced-motion` — disable orb pulse, message slide
- Screen reader: All interactive elements have `aria-label`, chat messages have `role="log"`
