# STEPS_FRONTEND.md — LegalTech AI Contract Scanner
**Complete Frontend Build Guide — No Backend**
**Read PRD.md, TECH_STACK.md, FOLDER_STRUCTURE.md, STEPS_BACKEND.md, and STEPS.md before starting any step.**

---

## How to Use This Document

This file covers the complete frontend of the LegalTech AI Contract Scanner — every page, every component, every animation, every user-facing feature — in the exact order they must be built. The backend (`services/api/`, `services/ai/`, `apps/worker/`) is assumed to be complete and all API endpoints are live before frontend work begins.

Each step explains what to build, how it should look and behave, and which backend API endpoints it connects to. No code is included here — only clear instructions of what each step must accomplish. The agent reads this alongside PRD.md, TECH_STACK.md, and FOLDER_STRUCTURE.md to understand full context and write the actual code.

Where a verification is listed, it describes what to confirm visually in the browser or by checking the network tab. Some steps have no formal verification — that is fine.

Never skip a step. Never partially complete a step and move on. Fix anything broken before proceeding.

**The tech stack for the frontend:**
- Next.js 15 with App Router, TypeScript, no Pages Router
- TailwindCSS v4 for all styling
- Framer Motion v11 for all animations
- Shadcn/ui for accessible base components
- Zustand v5 for client-side state
- Uploadthing v7 for file uploads
- Clerk for authentication UI
- React PDF for PDF preview

---

## PHASE 0 — Project Bootstrap

---

### STEP 0.1 — Initialize the Next.js Application

Inside `apps/web/`, initialize a new Next.js 15 application using the App Router. Use TypeScript. Do not use the Pages Router anywhere — this project is App Router only. During initialization, say no to the example app so the directory starts clean.

After initialization: configure TailwindCSS v4. Run the Shadcn/ui init command and accept all defaults — this installs the base component library and creates `components.json`. Install Framer Motion v11, Zustand v5, React PDF, and the Uploadthing Next.js package.

Create the `next.config.ts` file. It needs: image domain configuration to allow Uploadthing image domains and any other external image sources, environment variable exposure for all `NEXT_PUBLIC_` variables, and any necessary configuration for SSE streams (disable response buffering for the streaming routes).

Create `components.json` for Shadcn/ui configuration. Create `app/globals.css` with the TailwindCSS v4 base directives. Create a minimal `app/layout.tsx` that wraps the app with necessary providers (to be expanded in later steps). Create a minimal `app/page.tsx` with a placeholder heading.

**Verification:**
Run `npm run dev`. The browser shows a page with the placeholder heading. No TypeScript errors in the console. TailwindCSS utility classes apply correctly when added to the heading.

---

### STEP 0.2 — Configure Clerk Authentication

Install Clerk for Next.js. Wrap the root `app/layout.tsx` with the Clerk provider, passing the publishable key from the `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` environment variable.

Create `middleware.ts` at the `apps/web/` root. This is the Clerk auth middleware — the most important security file in the frontend. Configure it to protect all routes under the `(app)/` route group: any unauthenticated request to an `(app)/` route must redirect to `/sign-in`. Routes outside `(app)/` are public — the landing page, sign-in, sign-up, and the shared report viewer are all public.

Create `(auth)/sign-in/page.tsx` using Clerk's prebuilt `<SignIn />` component. Create `(auth)/sign-up/page.tsx` using Clerk's `<SignUp />` component. Both pages should be centered on the page with minimal styling — authentication UI design will be polished in the landing page phase.

Create `app/api/webhooks/clerk/route.ts` as a Next.js API route. This route receives Clerk webhook events and forwards them to the FastAPI backend webhook endpoint. This ensures user records are created in the application database when someone signs up.

Create `.env.local` with all frontend environment variable keys: `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `NEXT_PUBLIC_API_URL` (pointing to `http://localhost:8000`), `UPLOADTHING_SECRET`, `UPLOADTHING_APP_ID`.

**Verification:**
Navigate to any `(app)/` route while logged out — confirm redirect to `/sign-in`. Sign in with a Google or GitHub account. Confirm redirect back to the app after sign-in. Confirm the Clerk session is active by checking the browser console or using Clerk's dev toolbar.

---

### STEP 0.3 — Build the Typed API Client

In `apps/web/lib/api.ts`, build the typed HTTP client that all frontend components use to communicate with the FastAPI backend. This is the single source of truth for all API calls — no component should ever use raw `fetch` directly.

The client must: automatically attach the Clerk JWT as a Bearer token on every request (retrieve the token using Clerk's `getToken()` method), handle 401 responses by redirecting to `/sign-in`, handle network errors by throwing a typed error that callers can display to the user, and be fully typed with TypeScript generics so every call returns a typed response without casting.

Implement typed methods for every backend endpoint: `upload`, `getScanJob`, `getClauses`, `getAnalysis`, `getSummary`, `getPower`, `getPrecedent`, `generateCounterOffer`, `getCounterOffer`, `generateReport`, `getReport`, `chat`, `translate`, `getDashboard`. Each method's return type must match the corresponding Pydantic schema from the backend.

In `apps/web/types/`, create TypeScript interface files that mirror the backend Pydantic schemas: `scan.ts` (ScanJob, ScanStatus), `clause.ts` (Clause, RiskLevel, ConsequenceData), `analysis.ts` (AnalysisResult, PowerResult, SummaryResult), `report.ts` (Report), `chat.ts` (ChatMessage, ChatRequest), `api.ts` (ApiError, ApiResponse generic).

**Verification:**
Import the API client in a test component and call `getDashboard()`. Confirm it makes a request to the backend with the correct Authorization header (check the Network tab). Confirm it returns typed data.

---

### STEP 0.4 — Set Up Client-Side Encryption Utilities

In `apps/web/lib/crypto.ts`, implement the WebCrypto AES-256-GCM encryption utilities. The WebCrypto API is browser-native — no external library is needed.

The module must expose: `generateKey()` which uses `window.crypto.subtle.generateKey` to generate an AES-256-GCM `CryptoKey`, `encryptFile(file: File, key: CryptoKey)` which reads the file as an ArrayBuffer, generates a random 96-bit IV, runs AES-256-GCM encryption, and returns the encrypted bytes concatenated with the IV as a new `Blob`, and `exportKeyAsHex(key: CryptoKey)` which exports the raw key bytes as a hex string for display to the user.

In `apps/web/hooks/useEncryption.ts`, build a React hook that wraps these utilities. The hook manages the key lifecycle: it generates a key when a file is selected (not before, not after), encrypts the file, holds the `CryptoKey` in React state only — never in `localStorage`, `sessionStorage`, `cookie`, or any other persistent store — and exposes a `clearKey()` function that sets the key to null, simulating session end. When the browser tab is closed or the component unmounts, the key is gone.

This hook is the only place in the application that holds the encryption key. All other components that need to upload files use this hook.

No browser verification needed for this step — the hook is tested when the upload flow is built.

---

### STEP 0.5 — Set Up Uploadthing

Create `app/api/uploadthing/route.ts` as the Uploadthing file router. Define the upload endpoint with allowed file types (PDF and DOCX only) and a maximum file size of 25MB. This route handles the actual file upload to Uploadthing's CDN.

In `apps/web/lib/uploadthing.ts`, configure the Uploadthing React client using `generateReactHelpers`. Export the typed upload hooks that components will use.

In `apps/web/hooks/useUpload.ts`, build a React hook that orchestrates the full upload flow: accepts a `File`, calls the encryption hook to encrypt it before uploading, uploads the encrypted blob to Uploadthing using the file router, and returns the resulting Uploadthing file URL. The hook exposes `uploadState` (idle/encrypting/uploading/complete/error), `progress` (0–100), and `fileUrl` (the final URL once complete).

**Verification:**
Test the upload by temporarily calling `useUpload` with a test PDF file. Check the Network tab and confirm the bytes sent to Uploadthing are not a readable PDF (confirming encryption happened before upload). Confirm the hook returns a valid Uploadthing URL.

---

### STEP 0.6 — Set Up Zustand State Stores

In `apps/web/store/`, create all five Zustand v5 stores. These stores are the client-side memory of the application. Initialize them with the correct shape now — they will be populated as features are built.

`scanStore.ts` — Manages the state of the active scan. Shape: `jobId` (string or null), `contractId` (string or null), `status` (ScanStatus enum), `progressPct` (number), `error` (string or null). Actions: `setScanJob`, `updateProgress`, `setComplete`, `setFailed`, `reset`.

`clauseStore.ts` — Manages all clause data for the currently viewed contract. Shape: `clauses` (array of Clause objects), `selectedClauseId` (string or null), `filter` (RiskLevel or "ALL"). Actions: `addClause` (for streaming — adds one clause as it arrives), `setClauses` (for loading a completed scan), `selectClause`, `setFilter`, `reset`.

`reportStore.ts` — Manages report generation state. Shape: `reportId` (string or null), `shareUuid` (string or null), `status` ("idle" | "generating" | "ready"), `expiresAt` (string or null). Actions: `setGenerating`, `setReady`, `reset`.

`languageStore.ts` — Manages the active display language. Shape: `activeLanguage` (string, default "en"), `detectedLanguage` (string or null), `isTranslating` (boolean). Actions: `setDetectedLanguage`, `switchLanguage`, `setTranslating`, `setTranslatingComplete`.

`uiStore.ts` — Manages UI state that needs to be shared across components. Shape: `isCounterOfferPanelOpen` (boolean), `isPrecedentPanelOpen` (boolean), `activePanel` ("consequence" | "counter-offer" | "precedent" | null). Actions: `openCounterOfferPanel`, `openPrecedentPanel`, `closePanel`.

No verification needed — stores are tested as features are built.

---

### STEP 0.7 — Set Up the SSE Hook

In `apps/web/hooks/useSSE.ts`, build the SSE consumer hook. This hook is used by the scan results page to receive real-time clause events from the backend.

The hook accepts a `jobId` and `token` and manages the `EventSource` connection lifecycle. It must: open an `EventSource` connection to `/api/v1/scan/{jobId}/stream` with the Authorization token passed as a query parameter (EventSource does not support custom headers — pass the token as `?token=...`), parse every incoming `data:` message as JSON and call the appropriate callback based on the `type` field, handle the `complete` event by closing the connection and calling an `onComplete` callback, handle reconnection automatically if the connection drops (with exponential backoff up to 30 seconds), and close the connection cleanly when the component unmounts.

The hook exposes: `isConnected` (boolean), `lastEvent` (the most recently received event object), and `connectionError` (string or null for display).

Note: because EventSource does not support custom headers, the JWT must be passed as a query parameter for SSE routes specifically. The FastAPI backend must accept the token as either a header or query parameter for the `/scan/{jobId}/stream` endpoint.

No browser verification at this step — tested when the scan results page is built.

---

## PHASE 1 — App Shell and Navigation

---

### STEP 1.1 — Build the App Layout and Navigation

In `apps/web/app/(app)/layout.tsx`, build the protected app shell layout. This layout wraps every page inside `(app)/` and provides the navigation structure.

Build `components/layout/Navbar.tsx`. The navbar must include: the product logo and name ("LegalTech AI" or the chosen brand name) on the left, navigation links in the center ("Dashboard", "Upload"), and the Clerk user avatar with a dropdown menu on the right. The dropdown should have "Account", "Sign Out" options using Clerk's `<UserButton />` component. The navbar should be sticky at the top and have a subtle border or shadow to separate it from the page content.

Build `components/layout/Sidebar.tsx`. The sidebar shows a compact list of the user's 5 most recent contracts with their overall risk score badge. Each item links to the scan results page for that contract. On mobile, the sidebar collapses into a slide-out drawer. The sidebar does not appear on the scan results page (that page uses all available horizontal space for its own layout).

Build `components/layout/Footer.tsx`. A minimal footer with the "not legal advice" disclaimer that appears on all pages.

The `(app)/layout.tsx` must: wrap the page with the Navbar, conditionally show the Sidebar (hide it on the scan results page using the URL pattern), and apply the main content area styling.

**Verification:**
Visit any `(app)/` page after signing in. Confirm the navbar renders with the logo and user avatar. Confirm the sidebar renders with recent contract stubs (empty state for new accounts). Confirm the footer shows the disclaimer.

---

## PHASE 2 — Landing Page

---

### STEP 2.1 — Build the Landing Page

In `apps/web/app/page.tsx`, build the public landing page. This is the first thing non-authenticated users see and it must communicate the product's value immediately.

The landing page is the marketing face of the product. Design it with clear visual hierarchy and a specific aesthetic direction. The tone should be: authoritative, trustworthy, modern legal-tech — not playful, not startup-generic. Think: the intersection of a law firm's gravitas and a modern SaaS product's clarity. The visual design should feel premium enough that someone would trust it with their employment contract.

The page must have these sections:

**Hero Section** — A large headline that names the core problem: something like "Your Contract Is Full of Traps. We Find Them." or equivalent high-impact language that speaks directly to the fear of signing something you do not understand. Below the headline: a one-sentence sub-headline about the speed and completeness of the analysis. A primary CTA button "Analyze Your Contract Free" that links to `/sign-up`. Below the button: social proof elements (e.g., "Analyzes Employment, NDA, Freelance, SaaS contracts" with small icons). A mock risk badge in the hero showing "3 HIGH RISK · 7 MEDIUM · 12 SAFE" with the correct colors — this immediately communicates what the product does.

**Feature Grid** — Six feature cards, each corresponding to one of the six most impactful features from PRD.md: Risk Scanner, Power Asymmetry Meter, Counter-Offer Generator, Legal Precedent, Q&A Chat, Multilingual. Each card has an icon, a feature name, and a one-sentence description that speaks to a user pain point, not a technical description.

**How It Works** — A three-step horizontal process: "1. Upload your contract (encrypted)" → "2. Scan completes in under 10 seconds" → "3. Get a full risk report you can share." Each step has a brief description and an icon.

**Risk Demo Preview** — A static visual mockup of what the scan results look like. Show a few fake clause cards with HIGH/MEDIUM/SAFE badges and truncated clause text. This gives users a concrete preview before they sign up. This section is purely visual — no interactivity needed.

**CTA Section** — A bottom call-to-action section with the headline "Ready to understand what you're signing?" and the primary CTA button again.

The landing page must be fully responsive. On mobile, the feature grid collapses to a single column and the hero section stacks vertically.

**Verification:**
The landing page renders without errors. The CTA button navigates to `/sign-up`. The page is readable and visually coherent on both desktop and mobile. The "not legal advice" footer disclaimer is present.

---

## PHASE 3 — Upload Flow

---

### STEP 3.1 — Build the Upload Page

In `apps/web/app/(app)/upload/page.tsx`, build the contract upload page. This is a single focused page — its only purpose is to guide the user through uploading their contract and starting a scan.

Build `features/upload/UploadZone.tsx`. This is the drag-and-drop upload area. It must: accept drag-and-drop of PDF and DOCX files, accept click-to-browse file selection, show a large dashed border drop zone with an upload icon and instructional text ("Drop your contract here or click to browse · PDF or DOCX · Max 25MB"), animate the border and background color when a file is being dragged over the zone (the drop zone should glow or highlight to signal it is ready to accept), reject invalid file types with an inline error message below the zone ("Only PDF and DOCX files are accepted"), reject files over 25MB with an inline error message, and display the selected file name and size once a file is chosen.

Build `features/upload/EncryptionBadge.tsx`. This component shows during the encryption and upload steps. It must: show a lock icon with a subtle pulse animation, the text "Your document is encrypted before leaving your device", and a brief explanation of what this means. The badge should animate into view (fade + slide up) when a file is selected and the upload process begins.

Build `features/upload/UploadProgress.tsx`. A progress bar that fills during the upload. It shows two phases: "Encrypting..." (from 0% to ~10%, the encryption step is fast), then "Uploading..." (from 10% to 100%, the Uploadthing upload). The progress bar should have a smooth fill animation. Show the file name and current phase label above the bar.

Build `features/upload/EncryptionStatus.tsx`. This component shows after the session ends or when the user explicitly requests it. It displays: "Contract data will be deleted from servers after processing" and "Session key: [truncated hex hash]" for transparency. This component is accessible from the contract detail page later.

The upload page flow is:
1. User arrives at the page and sees the UploadZone
2. User selects or drops a file
3. The EncryptionBadge animates in and the encryption starts
4. The UploadProgress bar appears and fills
5. After upload completes, the API client calls `POST /api/v1/upload` with the Uploadthing file URL
6. On success, the user is redirected to `/scan/{jobId}` with the scan job ID

Handle errors at each stage: encryption failure, upload failure, API call failure. Each error shows a user-friendly message with a "Try again" option.

**Verification:**
Navigate to the upload page. Drag and drop a PDF file. Confirm the encryption badge appears, the progress bar fills, and after completion the browser navigates to `/scan/{jobId}`. Try uploading a `.txt` file — confirm the error message. Try uploading a file over 25MB — confirm the size error.

---

## PHASE 4 — Scan Results Page (Core)

---

### STEP 4.1 — Build the Scan Results Page Layout

In `apps/web/app/(app)/scan/[jobId]/page.tsx`, build the core scan results page. This is the most complex and most important page in the entire application — every feature is accessible from this single page. Get the layout right before building individual components.

The page is a Server Component that fetches the scan job server-side on initial load (to handle refreshes and direct links gracefully), then hands off to a Client Component for the live SSE streaming experience.

The layout structure as described in PRD.md Section 8.1:

**Top section — Summary Card** (full width): Shows the summary card hero element once the scan is complete. Shows a skeleton placeholder while loading. Has its own loading state separate from the clause list below.

**Below left — Clause List** (takes about 45% of width on desktop): The scrollable list of clause cards that stream in. Includes a filter bar at the top with four buttons: ALL / HIGH / MEDIUM / SAFE. The list is scrollable — the page does not need to scroll when browsing clauses.

**Below right — Detail Panel** (takes about 55% of width on desktop): The detail area that shows consequence, counter-offer, and precedent information for the selected clause. Shows an empty state ("Select a clause to see details") when no clause is selected.

**Floating — Power Asymmetry Meter**: Anchored to the right side of the viewport, always visible while scrolling the clause list. On mobile this becomes a fixed bottom bar.

**Bottom section — Pros/Cons Snapshot** (full width): Renders below the clause list and detail panel once the scan is complete.

On mobile: the detail panel becomes a slide-up sheet (modal drawer) that opens when a clause is tapped. The power meter becomes a compact bar at the top of the page below the summary card.

**Verification:**
Navigate to `/scan/{jobId}` for a completed scan. Confirm the layout renders correctly on desktop (two-column below the summary card). Confirm on mobile the layout stacks correctly and the detail panel opens as a sheet.

---

### STEP 4.2 — Build the Clause Card and Clause List

Build `features/analysis/RiskBadge.tsx`. A small pill-shaped badge that shows the risk level. HIGH is red, MEDIUM is amber/yellow, LOW is light green, SAFE is gray. Must accept a `risk_level` prop and render the appropriate color and label. Used in many places throughout the app.

Build `features/analysis/ClauseCard.tsx`. This is the primary UI element of the entire product — every user spends most of their time interacting with clause cards.

The card must show: the first 120 characters of the clause text with a fade-out gradient at the bottom (the full text is visible in the detail panel), the RiskBadge for the risk level, the risk category as a small label ("IP Assignment", "Non-Compete", etc.), and a `confidence` indicator — if confidence is below 0.7 show a "⚠️ Verify with attorney" warning text in amber.

The card must have three visual states: default (showing the above), hovered (subtle lift shadow and border color change), and selected (a stronger border and background tint matching the risk level color — red tint for HIGH, amber for MEDIUM, green for LOW/SAFE). 

On click, the card updates the `clauseStore` with the selected clause ID and opens the detail panel.

Build `features/analysis/RiskCounter.tsx`. The live counter at the top of the clause list. Shows "3 HIGH · 7 MEDIUM · 12 SAFE" with each count in the appropriate color. The numbers animate up as new clauses arrive via SSE — use a number counter animation that ticks up rather than jumping.

Build `features/analysis/ClauseList.tsx`. This is the scrollable container for all clause cards. It must: render the RiskCounter at the top, show the filter buttons (ALL / HIGH / MEDIUM / SAFE) that filter the visible clauses using the `clauseStore`, render ClauseCards sorted by `position_index`, and animate new cards in as they arrive during a live scan using Framer Motion's stagger animation. Each new card entering during streaming should slide in from the bottom with a brief fade. The filter animation should also be smooth — when switching between filter levels, cards that are filtered out should exit with a brief fade, and remaining cards should reflow smoothly.

Build `features/analysis/ScanProgress.tsx`. A progress bar and status text shown at the top of the clause list during an active scan. Shows "Analyzing clause 4 of 23..." and the current pipeline step ("Detecting risk patterns...", "Running AI analysis...", "Generating consequences..."). Disappears when the scan is complete.

**Verification:**
Navigate to a completed scan. Confirm clause cards render with correct risk badge colors. Click a clause card — confirm it shows as selected. Click the HIGH filter — confirm only HIGH clauses are shown with a smooth animation. Confirm the "⚠️ Verify with attorney" warning appears on clauses with confidence below 0.7.

---

### STEP 4.3 — Build the Live SSE Streaming for the Scan Page

Implement the real-time streaming behavior on the scan results page. This is what makes the product feel alive — clauses animate in one by one as the backend processes them.

In `apps/web/hooks/useScan.ts`, build the scan state management hook. It uses the `useSSE` hook to subscribe to the scan stream and coordinates updates across the stores. On each incoming SSE event: if the event type is `clause_result`, add the clause to `clauseStore` using `addClause` and animate it in; if the event type is `power_result`, store the power data in the `scanStore` and trigger the PowerMeter animation; if the event type is `complete`, update the scan status and trigger a final data fetch from the API to load the summary card. Also update the `scanStore.progressPct` to match the backend's `progress_pct` polling updates.

The scan page uses `useScan` to drive all state updates. The SSE connection opens when the page mounts. If the scan is already complete (the user refreshed or navigated back), skip the SSE connection entirely and load all data from the REST endpoints instead.

For the Framer Motion stagger animation on new clause cards: configure the `ClauseList` to use `AnimatePresence` so that new items entering the list use the entry animation. Each `ClauseCard` must be wrapped in a Framer Motion `motion.div` with a slide-up and fade-in entrance animation. When multiple clauses arrive in quick succession (like an initial batch), they stagger with a 50ms delay between each to create the cascade effect.

**Verification:**
Upload a new contract and navigate to the scan results page while the scan is in progress. Confirm clause cards animate in one by one as they arrive. Confirm the RiskCounter ticks up as each clause arrives. Confirm the progress bar at the top advances. After the scan completes, confirm all data (summary card, power meter, pros/cons) renders. Refresh the page and confirm all data loads from the REST API without SSE reconnection.

---

### STEP 4.4 — Build the Consequence Panel

Build `features/analysis/ConsequencePanel.tsx`. This panel slides open in the detail panel area when a clause is selected. It is the first thing users see in the detail area.

The panel must show: the full clause text (not truncated) in a slightly muted text style to distinguish it from the analysis, then below that the consequence analysis. The consequence section has a clear visual treatment: the `headline` should be large and bold — this is the "visceral moment" for this feature. The `financial_exposure` field should be displayed prominently, in large red text with a dollar sign, if the value is a dollar amount. A "$2,000,000 potential liability" rendered large in red is what makes users stop and pay attention. Below the headline: the `scenario` paragraph in normal readable text. Below that: a row showing `probability` (Low/Medium/High) as a colored badge and the `similar_case` as a small italic reference if it exists. At the bottom: a `negotiable` indicator — if the clause is marked negotiable, show a green "Negotiable ✓" label; if not, show a gray "Typically Non-Negotiable" label.

The panel must also show the three tabs: "Consequence" (default, the panel described above), "Counter-Offer" (implemented in Phase 5), "Precedent" (implemented in Phase 5). Tab switching must be smooth — use Framer Motion to animate the content transition between tabs with a horizontal slide.

**Verification:**
Select a HIGH-risk clause on the scan results page. Confirm the consequence panel slides open in the detail area with the full clause text and consequence data. Confirm the financial exposure amount is large and red. Confirm the Negotiable badge shows correctly. Switch between the three tabs — confirm smooth animation.

---

### STEP 4.5 — Build the Summary Card

Build `features/summary/SummaryCard.tsx`. This is the hero element at the top of the scan results page — it renders after the full scan is complete.

The card must show as a wide, visually prominent hero section: on the left a large `overall_risk_score` number (0–100) in a circular progress ring with color coding (0–30 green, 31–60 amber, 61–100 red), next to it the `should_you_sign` verdict in large bold text ("YES WITH CHANGES" or "NO" or "YES AS-IS") with appropriate color. Below these two main data points: the `negotiating_power` rating as a smaller label. On the right side of the card: the `one_liner` sentence in italic, and below it the `top_3_concerns` as a bulleted list with red X icons, and the `top_2_positives` with green check icons.

Build `features/summary/RiskScoreMeter.tsx`. The circular progress ring around the risk score. Use SVG to render the ring. The ring should fill from 0 to the actual score with an animation that plays once on first render — the ring fills up clockwise over about 1 second. The center of the ring shows the score number counting up.

Build `features/summary/SignVerdict.tsx`. The verdict display component. "YES AS-IS" renders in green, "YES WITH CHANGES" in amber, "NO" in red. The verdict should have a bold visual treatment.

The SummaryCard has a loading skeleton that shows while the scan is in progress — a gray pulsing skeleton placeholder shaped like the final card. The skeleton transitions to the actual card with a fade-in animation once the data arrives.

**Verification:**
On a completed scan page, confirm the summary card renders at the top with the risk score ring animating in. Confirm the risk score ring color matches the score range (red for high scores). Confirm the three concerns and two positives show correctly. Confirm the skeleton placeholder shows on an in-progress scan and transitions to the real card on completion.

---

### STEP 4.6 — Build the Power Asymmetry Meter

Build `features/power/PowerMeter.tsx`. The animated gauge component that visualizes the power imbalance between contract parties.

The meter is a semicircular gauge (like a speedometer). The semicircle goes from -100 (far left, red zone) through 0 (center, green zone) to +100 (far right, red zone). Both extremes are red because a heavily one-sided contract in either direction is concerning. The center green zone indicates a balanced contract. The gauge has labeled tick marks at -100, -50, 0, +50, +100.

A needle points from the center of the semicircle base to the current `power_score` position. When the power result first arrives via SSE, the needle animates from 0 to the correct position using Framer Motion's spring animation — it should swing to the final position with a slight overshoot and settle, like a physical gauge needle. This animation is one of the "visceral moments" described in PRD.md and must feel impactful.

Below the gauge: the `power_label` text (e.g., "Strongly Favors Counterparty") in bold with the appropriate color, and below that a sentence describing the magnitude (e.g., "This contract gives the other party 3.2× more termination rights than you" — compute this from the `key_imbalances` data).

Build `features/power/LeveragePoints.tsx`. A list below the power meter showing the user's `leverage_points` as actionable items. Each item has a green checkmark icon and the leverage point text. Label this section "Your Negotiating Leverage."

The PowerMeter component must be in a floating position — anchored to the right side of the viewport on desktop, always visible regardless of scroll position. On mobile, it moves to a fixed bar at the top below the summary card.

**Verification:**
On a completed scan, confirm the power meter needle animates to the correct position on first render. The spring animation should be visually smooth with a subtle overshoot. Confirm the power label text matches the score. Confirm the meter stays fixed to the right side of the screen while scrolling the clause list.

---

### STEP 4.7 — Build the Pros/Cons Snapshot

Build `features/summary/ProsConsSnapshot.tsx`. The two-column summary card that appears at the bottom of the scan results page once the scan is complete.

The component renders two columns side by side. Left column is "Pros" with a green header and green check icons. Right column is "Cons" with a red header and red X icons. Each item in the list shows a small colored dimension badge (Financial, Liability, IP, Exit Rights, or Obligations) and the description text below it.

Items animate in with a stagger effect on first render: each item slides in from its respective side (pros from the left, cons from the right) and fades in. The stagger delay is 80ms between items, alternating sides. This means the animation plays: first pro animates in from the left, then first con from the right, then second pro from left, then second con from right, etc. This creates an engaging alternating reveal.

At the bottom of the snapshot: the `verdict` sentence in italic with slightly larger text as a final summary statement.

**Verification:**
On a completed scan, scroll to the bottom of the page. Confirm the pros/cons snapshot renders with the correct two-column layout. Confirm the stagger animation plays on first scroll-into-view. Confirm dimension badges have the correct colors. Confirm the verdict sentence renders below both columns.

---

## PHASE 5 — Scan Results Page (Advanced Features)

---

### STEP 5.1 — Build the Counter-Offer Panel

Build `features/counter-offer/CounterOfferPanel.tsx`. This is the second tab in the clause detail panel, visible when a HIGH-risk clause is selected.

The panel shows a "Generate Counter-Offer" button as the primary action for any HIGH-risk clause that does not yet have a counter-offer generated. When clicked, the button calls `POST /api/v1/counter-offer/{clauseId}`, shows a loading state while the Celery task processes (a spinner with "Generating counter-offer..." text), and polls `GET /api/v1/counter-offer/{clauseId}` every 3 seconds until a result is returned.

Once the counter-offer is ready, the panel transitions from the loading state to the full counter-offer view.

Build `features/counter-offer/VersionTabs.tsx`. Three tabs labeled "Aggressive", "Balanced", and "Conservative". The default tab is "Balanced". Switching tabs swaps the displayed clause rewrite.

Build `features/counter-offer/ClauseDiff.tsx`. The side-by-side diff view. Left side shows the original clause text with a red-tinted background and a label "Original Clause." Right side shows the rewritten clause text with a green-tinted background and a label "Proposed Rewrite." Below each clause text: the `explanation` from the counter-offer data (a sentence explaining why this version is better for the user). The diff should visually highlight the key changed words or phrases using bolding or a slight underline — a word-level diff is ideal but character-level is acceptable.

Build `features/counter-offer/NegotiationEmail.tsx`. The email component below the diff view. Shows the `negotiation_email` text in a styled email-like box with a light gray background and monospace-adjacent font. The hero CTA is a "Copy Email" button. When clicked: copy the email text to clipboard, show a green checkmark with "Copied!" text that replaces the button for 2 seconds, then reset. This copy-success animation is the "one visceral moment" for the counter-offer feature per PRD.md.

The counter-offer panel is only available for HIGH-risk clauses. For LOW/SAFE clauses, show a message "Counter-offers are generated for high-risk clauses only."

**Verification:**
Select a HIGH-risk clause on the scan results page. Switch to the "Counter-Offer" tab. Click "Generate Counter-Offer." Confirm the loading state shows. Wait for completion and confirm the diff view renders with the original and rewrite side by side. Switch between Aggressive/Balanced/Conservative tabs and confirm different clause text. Click "Copy Email" and confirm the clipboard contains the negotiation email text and the success animation plays.

---

### STEP 5.2 — Build the Legal Precedent Panel

Build `features/precedent/PrecedentPanel.tsx`. This is the third tab in the clause detail panel, visible for HIGH-risk clauses.

The panel shows: the `precedent_summary` paragraph as the main body text. Below that, the enforcement likelihood as a prominent label. Below that, a row of up to 3 `CaseCard` components.

Build `features/precedent/CaseCard.tsx`. A compact card for each cited case. Shows: the case name in bold (e.g., "Smith v. Acme Corp"), the year, the jurisdiction, and the outcome text. The outcome should have color coding — outcomes favorable to the user (clause was unenforceable) show in green, outcomes unfavorable (clause was enforced) show in red.

Build `features/precedent/ConfidenceBadge.tsx`. A badge showing the confidence score percentage. Above 75%: green badge. Between 50–74%: amber badge. Below 50%: red badge with the "⚠️ Verify with attorney" subtext. The percentage number animates up from 0 to the final value on first render — a number counting animation over 800ms.

Build `features/precedent/EnforcementBadge.tsx`. A pill badge for the `enforcement_likelihood` field. "Very Likely" is red, "Likely" is amber, "Uncertain" is yellow, "Unlikely" is green. Positioned prominently below the summary paragraph.

The precedent panel is only available for HIGH-risk clauses. For other risk levels, show a message "Legal precedent analysis is available for high-risk clauses."

**Verification:**
Select a HIGH-risk clause and switch to the "Precedent" tab. Confirm the precedent summary, case cards, confidence badge, and enforcement likelihood all render correctly. Confirm the confidence score percentage animates up on first render. Confirm the case outcome colors match the outcome content.

---

## PHASE 6 — Q&A Chat Page

---

### STEP 6.1 — Build the Chat Page and Chat Window

In `apps/web/app/(app)/chat/[contractId]/page.tsx`, build the full contract Q&A chat page.

The page shows the contract name and scan summary at the top (a compact version of the risk score and contract type) as context for the conversation. Below is the chat interface filling the remaining screen height.

Build `features/chat/ChatWindow.tsx`. The main chat container. Must maintain a scrollable conversation history that auto-scrolls to the bottom when new messages arrive. Shows a placeholder state with 5 suggested starter questions when no conversation exists yet ("Can I work for a competitor after I leave?", "Who owns the code I write on weekends?", "What happens if I'm terminated?", etc.) — clicking a suggested question populates the input and sends it automatically.

Build `features/chat/ChatMessage.tsx`. A message bubble component used for both user messages and AI responses. User messages are right-aligned with a colored background. AI messages are left-aligned with a white/light background. AI messages stream token by token using the SSE approach — text appears progressively as it arrives. Below each AI message: a clause citation pill component (`ClauseCitation`) if the response includes a citation.

Build `features/chat/ClauseCitation.tsx`. A small clickable pill showing the clause reference (e.g., "Section 4.2 — Non-Compete"). When clicked, it navigates to the scan results page for this contract and automatically selects and highlights the referenced clause. Use URL parameters to pass the clause ID: `/scan/{jobId}?clause={clauseId}`.

Build `features/chat/ChatInput.tsx`. The text input at the bottom of the chat. Multi-line text area that auto-expands up to 4 lines. Sends on Enter key press (Shift+Enter for a newline). Shows a Send button on the right. The input and button are disabled while an AI response is streaming. Show a subtle "AI is typing..." indicator above the input while streaming.

Build `apps/web/hooks/useChat.ts`. The chat state management hook. It manages: the conversation history array, the current streaming response text being received, the loading state, and the SSE connection for streaming responses. It calls `POST /api/v1/chat/{contractId}` and processes the streaming response events, appending tokens to the current message as they arrive.

**Verification:**
Navigate to `/chat/{contractId}` for a completed scan. Confirm the suggested starter questions show. Click one — confirm it sends and a streaming response appears token by token. Confirm the clause citation pill appears below the response. Click the pill — confirm it navigates to the correct clause on the scan results page. Type a follow-up question — confirm the conversation history is maintained and the model uses context from the previous exchange.

---

## PHASE 7 — Multilingual UI

---

### STEP 7.1 — Build the Language Detection Banner

Build `features/multilingual/LanguageDetectionBanner.tsx`. This banner appears at the top of the scan results page when the uploaded contract is in a non-English language.

The banner must show: a globe icon, the message "Spanish contract detected — analyzing from employee perspective" (substituting the correct detected language and role), and a button "Change Language Detection" that opens a small dropdown with the 10 contract types and allows the user to manually override if the detection was wrong. The banner uses the `languageStore.detectedLanguage` to know when to show and what language to display.

The banner should animate down from the top of the page (Framer Motion slide-down entrance) and can be dismissed by the user with an X button. Dismissal is remembered in the `uiStore` so it does not re-appear on page refresh.

Build `features/multilingual/BilingualToggle.tsx`. A toggle control that appears in the navbar area on the scan results page when a non-English contract has been scanned. It shows two options: "English" and the original language name (e.g., "Español"). Selecting a language calls `POST /api/v1/translate/{contractId}` and updates `languageStore.isTranslating` to true. While translating, show a spinner next to the toggle. When the translation task completes (poll the task status or receive a push event), refresh the clause and analysis data from the REST endpoints and update the displayed text.

All text in the clause cards, consequence panels, counter-offer explanations, and summary card must read from the translated fields when the active language matches the non-English option, and from the English fields when English is selected. The `clauseStore` must hold both the English and translated versions of all text fields.

Build `apps/web/hooks/useLanguage.ts`. The hook managing language state. It reads from `languageStore`, calls the translate endpoint when the language is switched, polls for completion, and triggers a data refresh when done.

**Verification:**
Upload a Spanish contract and navigate to the scan results page. Confirm the language detection banner appears. Switch to Spanish using the BilingualToggle. Confirm the page shows a loading state during translation. After translation completes, confirm clause explanations and consequence text are displayed in Spanish. Switch back to English — confirm English text returns.

---

## PHASE 8 — Report Page and Sharing

---

### STEP 8.1 — Build the Report Generation UI

Build `features/report/ShareButton.tsx`. The "Share Report" button that appears on the scan results page. When clicked: call `POST /api/v1/report/generate` to trigger PDF generation, show a loading spinner with "Generating report..." text while the Celery task runs (poll `GET /api/v1/report/{reportId}` until status is "ready"), once ready copy the share URL to clipboard, show a success state with a link icon and "Link copied!" text that stays for 3 seconds then resets to the default state, and store the `reportId` and `shareUuid` in `reportStore`.

Build `features/report/DownloadButton.tsx`. The "Download PDF" button. If a report has already been generated (the `reportStore` has a `reportId`), this button directly calls `GET /api/v1/report/{reportId}` and triggers a browser file download. If no report exists yet, it generates one first (same flow as ShareButton) then downloads. Show a downloading spinner state during the download.

In `apps/web/app/(app)/report/[reportId]/page.tsx`, build the in-app report viewer. This page shows the report for authenticated users. It embeds the PDF using React PDF (`<Document>` and `<Page>` components from `react-pdf`) so the report is viewable directly in the browser without downloading. Shows the ShareButton and DownloadButton at the top for quick sharing.

**Verification:**
On a completed scan page, click "Share Report." Confirm the loading state shows. After the report generates, confirm a URL is copied to clipboard. Confirm the report can be downloaded as a PDF file. Navigate to `/report/{reportId}` — confirm the PDF renders in the browser.

---

### STEP 8.2 — Build the Public Shared Report Viewer

In `apps/web/app/report/share/[shareUuid]/page.tsx`, build the publicly accessible report viewer. This page is outside the `(app)/` route group — it is not protected by Clerk middleware. Anyone with the share link can view this page without an account.

The page calls `GET /api/v1/report/share/{shareUuid}` and renders the PDF in-browser using React PDF. It must: show the product branding and name prominently at the top, show a banner saying "This report was generated with LegalTech AI" with a CTA to sign up, render the PDF using React PDF, and show an "Expired" message if the report has expired (the API returns 404 — catch this and show a helpful message).

The "Share Report" feature doubles as a marketing asset — anyone who receives a shared link sees the product and can sign up. The page design must reflect this: it should look professional enough to make an impression on the contract counterparty who receives the link.

**Verification:**
Generate a share link from the scan results page. Open the link in an incognito window (no auth session). Confirm the report PDF renders correctly. Confirm the product branding and sign-up CTA are visible. Confirm the page works with no Authorization header.

---

## PHASE 9 — Dashboard

---

### STEP 9.1 — Build the Dashboard Page

In `apps/web/app/(app)/dashboard/page.tsx`, build the contract history dashboard.

The page title and description make clear what this is: "Your Contracts — All previously analyzed contracts." The page uses `GET /api/v1/dashboard` to fetch all contracts for the authenticated user.

For each contract, render a `ContractCard` component showing: the file name, the contract type badge, the `overall_risk_score` as a small colored number, the `should_sign` verdict as a colored badge, the scan date formatted as "January 15, 2025", the ScanJob status (if still processing, show a spinner with progress), and a "View Analysis" link to the scan results page.

Sort contracts with most recently scanned first.

If the user has 3 or more completed scans, show a "Power Trend" insight card above the contract list: "Your last 5 contracts averaged a power score of -42 — you consistently sign unfavorable contracts." Display this with a miniature power meter gauge. This insight is generated from the `power_trend` field in the dashboard API response.

**Empty state**: For a new user with no contracts, show a large welcoming empty state with an illustration, the message "You haven't analyzed any contracts yet," and a large CTA button to go to the upload page.

**Loading state**: Show skeleton cards while the dashboard data is loading.

**Verification:**
After completing at least one scan, navigate to the dashboard. Confirm the contract appears with the correct risk score, verdict, and contract type. Click "View Analysis" — confirm navigation to the scan results page. Sign in with a fresh account and confirm the empty state shows.

---

## PHASE 10 — Animations and Polish

---

### STEP 10.1 — Define and Apply Animation Variants

In `apps/web/animations/variants.ts`, define all shared Framer Motion animation variants that are used across the application. Centralizing animation variants prevents inconsistency and makes the feel of the product cohesive.

Define variants for: `fadeIn` (simple opacity 0 to 1), `slideUp` (translate Y +20px to 0 with fade), `slideInFromRight` (translate X +30px to 0 with fade), `slideInFromLeft` (translate X -30px to 0 with fade), `scaleIn` (scale 0.95 to 1 with fade), `staggerContainer` (a container variant that applies a stagger delay to children), and `listItem` (used with staggerContainer — each list item slides up with the stagger timing applied by the parent).

In `apps/web/animations/transitions.ts`, define shared transition presets: `spring` (a spring configuration for physically satisfying transitions — used for the power meter needle and the risk score ring), `snappy` (a fast cubic bezier for UI interactions — used for tab switches and panel opens), `smooth` (a slower ease-out for page-level transitions).

In `apps/web/animations/PowerMeterAnim.ts`, define the specific spring animation configuration for the power meter needle. The needle must overshoot slightly and settle — configure the stiffness, damping, and mass values of the Framer Motion spring to achieve this physical feeling. Higher stiffness and lower damping produces the overshoot effect.

Apply these animation variants consistently across all components built in previous phases. Each component should use the shared variants rather than defining inline animation properties. Go back through every component built in Phases 1–9 and apply the appropriate entrance animation from the variants file.

No formal browser verification — but review the application and confirm that all transitions feel cohesive and use consistent timing.

---

### STEP 10.2 — Error States and Empty States

Every page and component must have a properly designed error state and empty state. Go through the entire application and ensure no component renders a blank screen or a raw error object.

For the scan results page: if the SSE connection fails, show an error banner with a "Reconnecting..." status and a manual retry button. If the scan job failed on the backend, show a clear error message with the error text and a "Try uploading again" CTA.

For the chat page: if the streaming response fails mid-stream, show an inline error message in the chat bubble with a "Retry" button.

For the counter-offer generation: if the Celery task fails, show an error state in the panel with a "Try again" button.

For the report generation: if PDF generation fails, show an error toast and keep the ShareButton in its default state so the user can try again.

For the dashboard: if the API call fails, show an error state with a "Refresh" button rather than a blank page.

For the upload page: network failures, Uploadthing errors, and API errors all need distinct messages that help the user understand what went wrong.

All error messages must be user-friendly — never show stack traces, error codes, or internal system messages to the user. Log technical details to the console only.

No formal verification — review the application manually by temporarily breaking API calls and confirming error states render correctly.

---

### STEP 10.3 — Loading Skeletons

Every page that loads data must have a skeleton loading state. Skeletons should match the shape and size of the real content so the page does not jump when data arrives.

Add skeletons to: the dashboard page (skeleton contract cards while loading), the scan results page summary card (a skeleton shaped like the summary card while the scan completes), the clause list (show 3–5 skeleton clause cards while waiting for the first SSE event), the power meter (a grayed-out skeleton gauge before the power result arrives), the pros/cons snapshot (two-column skeleton while loading), the precedent panel (skeleton case cards while loading), and the report viewer (skeleton PDF pages while loading).

Use Shadcn/ui's `<Skeleton />` component as the base. Apply a subtle pulse animation. All skeletons should use the same background color and pulse animation to feel cohesive.

No formal verification — review each page in a throttled network environment and confirm skeletons render before data.

---

### STEP 10.4 — Responsive Design Pass

Go through every page and component and verify the mobile experience. The application must be fully functional on a 375px wide mobile screen.

Pages that need specific mobile attention:

**Scan results page**: The two-column layout collapses to a single column on mobile. The detail panel becomes a Shadcn/ui `Sheet` (slide-up drawer) instead of a side panel. The power meter moves from the floating right position to a fixed bar at the top below the summary card. The summary card stacks its content vertically.

**Upload page**: The upload zone must be tap-friendly on mobile — the drop zone should work as a tap-to-browse on touch screens. The minimum tap target for all buttons must be at least 44×44px.

**Dashboard**: The contract card grid changes from 2 or 3 columns to 1 column on mobile.

**Chat page**: The input bar must stay anchored to the bottom of the viewport on mobile (use `position: fixed` or CSS sticky) so it is always reachable without scrolling.

**Landing page**: The hero section, feature grid, and how-it-works section all stack to single-column on mobile.

Use TailwindCSS responsive prefixes (`sm:`, `md:`, `lg:`) consistently. Never use pixel-based breakpoints in custom CSS — use Tailwind's breakpoint system.

**Verification:**
Open the browser DevTools and use the mobile responsive view at 375px width. Navigate through every page: landing, sign-in, upload, scan results (with a clause selected), chat, dashboard, report viewer. Confirm all content is readable and all interactive elements are accessible by tap.

---

## PHASE 11 — Performance and Final Polish

---

### STEP 11.1 — Implement React Server Components Correctly

Audit the entire application and ensure Server Components and Client Components are used correctly per Next.js 15 App Router conventions.

Pages that should be Server Components (they fetch data on the server and pass it as props to client children): `dashboard/page.tsx` (fetch initial contract list server-side), `scan/[jobId]/page.tsx` (fetch the initial scan job server-side to check if it is complete), `report/[reportId]/page.tsx` (fetch report metadata server-side), `report/share/[shareUuid]/page.tsx` (fetch share metadata server-side).

Components that must be Client Components (they use hooks, event handlers, or browser APIs): all Zustand store consumers, all Framer Motion animations, the UploadZone (drag-and-drop requires browser events), the ClauseList (SSE streaming updates), all form inputs and interactive UI. Mark these with `"use client"` at the top of the file.

The goal is to ensure that the initial page render sends actual content to the browser (for performance and SEO), while interactive elements hydrate on the client. Avoid marking entire pages as `"use client"` — only the interactive leaf components need it.

No formal verification — review the component tree and confirm the Server/Client boundary is intentional.

---

### STEP 11.2 — Add Page Transitions

Add smooth page transition animations between routes using Framer Motion's `AnimatePresence`. The transitions should feel like a professional SaaS application — not flashy, but polished.

The transition between pages should be a subtle fade (opacity 0 to 1 over 200ms). The transition when navigating from the upload page to the scan results page should be slightly more dramatic — a cross-fade that makes it feel like the product is "opening" the analysis.

Configure the transitions in the root layout or in a transition wrapper component. The `AnimatePresence` component wraps the page content in the layout with `mode="wait"` so the outgoing page exits before the incoming page enters.

No formal verification — navigate between pages and confirm transitions feel smooth.

---

### STEP 11.3 — Accessibility Audit

Review the entire application for accessibility. The product should be usable by people who rely on screen readers or keyboard navigation.

Key accessibility requirements: All interactive elements (buttons, links, inputs, clause cards) must be keyboard-focusable and have visible focus indicators. All images and icons must have `alt` text or `aria-label` attributes. Color alone must never be the only way information is conveyed — risk levels should use both color AND text ("HIGH" not just a red badge). The contrast ratio of all text against backgrounds must meet WCAG AA (4.5:1 for normal text, 3:1 for large text). Modal dialogs and slide-up sheets must trap keyboard focus while open. The chat input must have an `aria-label`. The power meter gauge must have a text alternative describing the score.

Use Shadcn/ui components as the base — they are built with accessibility in mind. Do not override their ARIA attributes unless necessary.

No formal automated verification — do a keyboard navigation test: tab through the entire scan results page and confirm every interactive element is reachable and operable by keyboard alone.

---

### STEP 11.4 — SEO and Metadata

Configure Next.js metadata for all public-facing pages.

The root layout should export a base `metadata` object with the application name, description, and Open Graph image. Each page should override the metadata as needed:
- Landing page: title "LegalTech AI — AI Contract Scanner", description targeting the primary user pain point, Open Graph image showing the product.
- Sign-in page: title "Sign In — LegalTech AI".
- The shared report page: title "[Contract Name] Risk Report — LegalTech AI", description showing the risk score (this makes sharing on Slack/email look professional).

All `(app)/` pages are behind authentication and do not need extensive SEO metadata — they will not appear in search results. Focus SEO effort on the landing page and the public share page.

No formal verification — check the page title in the browser tab and inspect the `<head>` element of the landing page to confirm Open Graph tags are present.

---

## PHASE 12 — CI/CD and Deployment

---

### STEP 12.1 — Configure GitHub Actions for Frontend

In `.github/workflows/ci.yml` (the same CI file as the backend, or a separate `ci-frontend.yml`), add frontend CI jobs that run on every PR.

The frontend CI jobs must: run `npm run lint` (ESLint), run `npx tsc --noEmit` (TypeScript type checking), run Vitest component tests (once written in Step 12.2), and run `npm run build` to confirm the Next.js production build succeeds. The build job is the most important — a passing TypeScript check and lint does not guarantee the build succeeds.

Cache `node_modules` between CI runs to keep the pipeline fast.

**Verification:**
Introduce an intentional TypeScript error (use a wrong prop type). Confirm the CI pipeline fails on the type check step. Fix it and confirm the pipeline passes.

---

### STEP 12.2 — Write Frontend Component Tests

In `apps/web/`, install and configure Vitest with React Testing Library. Write component tests for the most critical UI components.

Tests to write:

`ClauseCard` — renders a HIGH-risk clause with a red badge, renders a SAFE clause with a gray badge, shows the "⚠️ Verify with attorney" warning when confidence is below 0.7.

`RiskBadge` — renders the correct color class for each risk level: HIGH is red, MEDIUM is amber, LOW is green, SAFE is gray.

`RiskCounter` — displays the correct counts for HIGH, MEDIUM, and SAFE.

`SummaryCard` — renders the risk score, the should_you_sign verdict, the three concerns, and the two positives when given mock data.

`UploadZone` — rejects a `.txt` file with an error message, accepts a `.pdf` file without an error.

`ChatInput` — disables the input and send button while `isStreaming` is true.

`CounterOfferPanel` — shows the "Generate Counter-Offer" button for a HIGH-risk clause, does not show it for a SAFE clause, shows all three version tabs after generation.

`ConfidenceBadge` — renders green for scores above 75, amber for 50–74, red for below 50.

**Verification:**
Run `npm run test` and confirm all component tests pass with zero failures.

---

### STEP 12.3 — Deploy the Frontend to Vercel

Connect the `apps/web/` directory to a Vercel project. Configure: the root directory as `apps/web/`, the build command as `next build`, the output directory as `.next`. Set all `NEXT_PUBLIC_` environment variables in Vercel's environment settings. Set the production `NEXT_PUBLIC_API_URL` to the Railway API URL. Set `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` to the production Clerk key.

Configure automatic deployment: every push to the `main` branch triggers a Vercel production deployment. Pull requests get preview deployments with their own URL.

In the Clerk dashboard, add the production Vercel URL and all Vercel preview URL patterns to the allowed origins.

In the Uploadthing dashboard, configure the allowed origins to include the production Vercel URL.

**Verification:**
Push to main. Confirm Vercel deploys successfully (no build errors). Visit the production URL. Sign in with Clerk. Upload a contract. Confirm the full scan pipeline works end-to-end in the production environment: upload → scan → clause streaming → summary card → power meter → counter-offer → chat → report download. Check the browser Network tab to confirm all API calls go to the Railway backend URL, not localhost.

---

## Final Frontend Verification Checklist

Before considering the frontend complete, verify all of the following in the browser:

**Authentication**
- Landing page is accessible without authentication
- All `(app)/` routes redirect to `/sign-in` when not authenticated
- After sign-in, redirect back to the originally requested page
- Sign-out works and redirects to the landing page

**Upload Flow**
- PDF and DOCX files can be drag-dropped or selected
- Invalid file types show an error message
- Files over 25MB show a size error
- During upload: the encryption badge animates in, the progress bar fills
- After upload: the browser navigates to `/scan/{jobId}`

**Scan Results Page**
- Clause cards animate in one by one during a live scan
- The RiskCounter ticks up as clauses arrive
- Filtering by risk level works with smooth animation
- Selecting a clause opens the detail panel with consequence data
- The financial exposure amount is large and visually prominent
- The power meter needle animates to the correct position on first render
- The summary card skeleton shows during the scan and transitions to real data
- The pros/cons stagger animation plays on first render
- Page refresh loads all data from REST endpoints (no SSE reconnect needed)

**Counter-Offer**
- "Generate Counter-Offer" button only appears on HIGH-risk clauses
- Loading state shows while generation runs
- All three version tabs show different clause text
- The diff view shows original in red and rewrite in green
- The "Copy Email" button copies to clipboard with success animation

**Legal Precedent**
- Precedent tab is only available on HIGH-risk clauses
- Case cards show name, year, jurisdiction, and outcome
- Confidence score animates up on first render
- Enforcement likelihood badge color matches the likelihood level

**Q&A Chat**
- Suggested starter questions show on an empty conversation
- Clicking a starter question sends it and shows a streaming response
- Clause citations appear below AI responses
- Clicking a citation navigates to the correct clause
- Follow-up questions use conversation history
- Input is disabled while a response is streaming

**Multilingual**
- Language detection banner shows for non-English contracts
- BilingualToggle appears on scan results for non-English contracts
- Switching language shows a loading state during translation
- All clause and consequence text updates to the selected language

**Reports**
- ShareButton generates a report and copies the share link
- DownloadButton triggers a PDF file download
- The share link opens in incognito without authentication and shows the PDF
- Expired share links show a 404 message

**Dashboard**
- All previously scanned contracts appear with correct metadata
- Power trend shows if user has 3+ completed scans
- Empty state shows for a fresh account

**Mobile**
- All pages are usable on a 375px wide screen
- The scan results detail panel opens as a slide-up sheet on mobile
- The power meter is visible at the top on mobile
- The chat input is anchored to the bottom on mobile

**Performance and Quality**
- All pages have loading skeleton states
- All pages have error states
- All interactive elements are keyboard-accessible
- No console errors on any page in production

---

## Build Order Summary

```
PHASE 0  — Project Bootstrap                     (Steps 0.1–0.7)
PHASE 1  — App Shell and Navigation              (Step 1.1)
PHASE 2  — Landing Page                          (Step 2.1)
PHASE 3  — Upload Flow                           (Step 3.1)
PHASE 4  — Scan Results Page (Core)              (Steps 4.1–4.7)
PHASE 5  — Scan Results Page (Advanced)          (Steps 5.1–5.2)
PHASE 6  — Q&A Chat Page                         (Step 6.1)
PHASE 7  — Multilingual UI                       (Step 7.1)
PHASE 8  — Report Page and Sharing               (Steps 8.1–8.2)
PHASE 9  — Dashboard                             (Step 9.1)
PHASE 10 — Animations and Polish                 (Steps 10.1–10.4)
PHASE 11 — Performance and Final Polish          (Steps 11.1–11.4)
PHASE 12 — CI/CD and Deployment                  (Steps 12.1–12.3)
```

**Total: 37 frontend steps across 12 phases.**

Complete every step fully before moving to the next. The backend must be fully operational before frontend work begins — the frontend assumes all API endpoints are live and returning correct data.

---

*This document covers only the frontend. No backend code is included or implied. All file paths reference FOLDER_STRUCTURE.md. All feature behaviors reference PRD.md. All tools and versions reference TECH_STACK.md. Read all four documents before writing any code.*