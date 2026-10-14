# Build Mainframe Hero Landing Page

We will replace the existing, heavy Framer-based landing page code with a brand new React, TypeScript, and Tailwind CSS landing page for the creative agency "Mainframe". 

Instead of serving a static compiled HTML inside an `iframe` under `/landing.html`, we will natively build this page directly in the Next.js `frontend/app/page.tsx` file. This is highly performant, fully responsive, and cleaner to maintain. We will also clean up the unused static files inside the `landing-page/` and `frontend/public/` directories to remove the old landing page code.

## Proposed Changes

### Clean up unused files

We will delete the following old landing page source files and public assets:
- `[DELETE]` [landing-page/index.html](file:///Volumes/WD_Subharup/major%20project%202/Ai-legal-explainer/landing-page/index.html)
- `[DELETE]` [landing-page/styles.css](file:///Volumes/WD_Subharup/major%20project%202/Ai-legal-explainer/landing-page/styles.css)
- `[DELETE]` [frontend/public/landing.html](file:///Volumes/WD_Subharup/major%20project%202/Ai-legal-explainer/frontend/public/landing.html)
- `[DELETE]` [frontend/public/styles.css](file:///Volumes/WD_Subharup/major%20project%202/Ai-legal-explainer/frontend/public/styles.css)
- Any Framer bundle `.mjs` files inside `frontend/public/` that are no longer used by the application.
- `[DELETE]` [update_landing.py](file:///Volumes/WD_Subharup/major%20project%202/Ai-legal-explainer/update_landing.py) since it is only used to patch the old Framer page.

---

### Frontend Configuration

#### [MODIFY] [layout.tsx](file:///Volumes/WD_Subharup/major%20project%202/Ai-legal-explainer/frontend/app/layout.tsx)
- Load the two HelveticaNowDisplay fonts in the HTML head via `<link>` tags:
  - Heading: `https://db.onlinewebfonts.com/c/5ac3fe7c6abd2f62067f266d89671492?family=HelveticaNowDisplay-Medium`
  - Body: `https://db.onlinWebFonts.com/c/1aa3377e489837a26d019bba501e779d?family=HelveticaNowDisplayW01-Rg`

#### [MODIFY] [globals.css](file:///Volumes/WD_Subharup/major%20project%202/Ai-legal-explainer/frontend/app/globals.css)
- Define CSS variables:
  ```css
  :root {
    --font-heading: 'HelveticaNowDisplay-Medium', 'Helvetica Neue', Arial, sans-serif;
    --font-body: 'HelveticaNowDisplayW01-Rg', 'Helvetica Neue', Arial, sans-serif;
  }
  body {
    font-family: var(--font-body);
  }
  ```
- Add the `@keyframes blink` animation rule for the blinking typewriter cursor:
  ```css
  @keyframes blink {
    from, to { opacity: 1; }
    50% { opacity: 0; }
  }
  .animate-blink {
    animation: blink 1s step-end infinite;
  }
  ```

#### [MODIFY] [page.tsx](file:///Volumes/WD_Subharup/major%20project%202/Ai-legal-explainer/frontend/app/page.tsx)
- Replace the client-side page code with the new full-screen hero landing page component for "Mainframe".
- Implement the custom hook `useTypewriter` inside the file or in a separate hook.
- Implement the mouse scrub logic for the background video:
  - Handle `mousemove` on `window` to track horizontal movements.
  - Apply `targetTime` calculation: `(delta / window.innerWidth) * SENSITIVITY * video.duration` with `SENSITIVITY = 0.8`.
  - Avoid seek flooding by using the `onSeeked` handler of the `<video>` element to schedule subsequent seeks.
- Build the responsive layout:
  - Navbar: Logo and asterisk (left), Desktop navigation links (center), Desktop CTA (right), and Mobile hamburger menu + full-screen overlay for mobile screen sizes.
  - Hero Section: Blurred intro label, typewriter text with blinking cursor, and action buttons (4 white pill buttons, 1 copyable email button).
  - Implement copy-to-clipboard functionality on clicking the email button.
  - Implement a 400ms fade-in + slide-up entrance animation for the action pill buttons.

## Verification Plan

### Automated Tests
- Since there are no automated tests for the landing page in this repository, we will verify correct compilation and layout.
- Build the application locally to make sure TypeScript and Next.js compiler produce no errors:
  - `cd frontend && npm run build`

### Manual Verification
- We will boot the local Next.js development server:
  - `cd frontend && npm run dev`
- Launch the browser subagent to navigate to `http://localhost:3000` to verify:
  - Layout alignment and responsive styling (both desktop and mobile viewports).
  - Correct font rendering for heading and body texts.
  - Typing animation of the hero text with blinking cursor.
  - Mouse movement horizontal scrubbing on the background video.
  - Mobile hamburger icon animations and overlay transitions.
  - Clicking the email pill copies it to the clipboard and triggers copy feedback.
