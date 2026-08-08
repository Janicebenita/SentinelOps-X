import { lazy, Suspense, useEffect, useState } from 'react';

const Landing = lazy(() => import('../pages/LandingPage'));
const CommandCentre = lazy(() => import('../App'));
const AgentPage = lazy(() => import('../pages/AgentPage'));
const ApprovalPage = lazy(() => import('../pages/ApprovalPage'));
const ResourcePage = lazy(() => import('../pages/ResourcePage'));
const PlatformStatusPage = lazy(() => import('../pages/PlatformStatusPage'));
const JudgeDemoPage = lazy(() => import('../pages/JudgeDemoPage'));
const ArchitecturePage = lazy(() => import('../pages/ArchitecturePage'));

export function navigate(path: string) {
  if (location.pathname === path) return;
  history.pushState({}, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}

export default function Router() {
  const [path, setPath] = useState(location.pathname);

  useEffect(() => {
    const handlePopState = () => setPath(location.pathname);
    window.addEventListener('popstate', handlePopState);

    // Global click listener to intercept internal relative anchor clicks for SPA navigation
    const handleGlobalClick = (e: MouseEvent) => {
      const target = (e.target as HTMLElement).closest('a');
      if (!target) return;

      const href = target.getAttribute('href');
      // Only intercept relative links starting with / and not external links or anchors
      if (href && href.startsWith('/') && !href.startsWith('//') && !target.hasAttribute('target')) {
        e.preventDefault();
        navigate(href);
      }
    };

    document.addEventListener('click', handleGlobalClick);

    return () => {
      window.removeEventListener('popstate', handlePopState);
      document.removeEventListener('click', handleGlobalClick);
    };
  }, []);

  let Page = Landing;
  if (path === '/') Page = Landing;
  else if (path === '/command-centre') Page = CommandCentre;
  else if (path === '/judge-demo') Page = JudgeDemoPage;
  else if (path === '/architecture') Page = ArchitecturePage;
  else if (path === '/agents' || path.startsWith('/agents/')) Page = AgentPage;
  else if (['/integrations', '/observability', '/security-status', '/model-evaluation', '/google-stack'].includes(path)) Page = PlatformStatusPage;
  else if (/\/workflows\/\d+\/approval/.test(path)) Page = ApprovalPage;
  else Page = ResourcePage;

  return (
    <Suspense fallback={<div className="route-loading">Loading SentinelOps Nexus…<b>PRODUCTION ACTION: NOT EXECUTED</b></div>}>
      <Page />
    </Suspense>
  );
}
