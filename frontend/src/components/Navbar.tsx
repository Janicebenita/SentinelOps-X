import React, { useState } from 'react';
import { ShieldCheck, ChevronRight, Menu, X, Terminal, Compass, Users, Network, FileText, Lock, Activity } from 'lucide-react';
import { navigate } from '../routes/Router';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Command Centre', path: '/command-centre', icon: <Compass className="w-4 h-4" /> },
  { label: 'Guided Demo', path: '/judge-demo', icon: <Terminal className="w-4 h-4" /> },
  { label: 'AI Workforce', path: '/agents', icon: <Users className="w-4 h-4" /> },
  { label: 'Architecture', path: '/architecture', icon: <Network className="w-4 h-4" /> },
  { label: 'Platform Status', path: '/google-stack', icon: <Activity className="w-4 h-4" /> },
  { label: 'Docs', path: '/docs', icon: <FileText className="w-4 h-4" /> },
  { label: 'Safety', path: '/safety', icon: <Lock className="w-4 h-4" /> },
];

function getBreadcrumbs(path: string): { label: string; path: string }[] {
  const crumbs = [{ label: 'Nexus', path: '/' }];
  if (path === '/') return crumbs;

  const parts = path.split('/').filter(Boolean);
  let currentPath = '';

  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    currentPath += `/${part}`;

    if (part === 'command-centre') crumbs.push({ label: 'Command Centre', path: '/command-centre' });
    else if (part === 'judge-demo') crumbs.push({ label: 'Guided Demo', path: '/judge-demo' });
    else if (part === 'architecture') crumbs.push({ label: 'Architecture', path: '/architecture' });
    else if (part === 'agents') crumbs.push({ label: 'AI Workforce', path: '/agents' });
    else if (part === 'docs') crumbs.push({ label: 'Documentation', path: '/docs' });
    else if (part === 'safety') crumbs.push({ label: 'Safety & Governance', path: '/safety' });
    else if (part === 'workflows') crumbs.push({ label: 'Workflows', path: '/command-centre' });
    else if (i === 1 && parts[0] === 'agents') {
      const formatted = part.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
      crumbs.push({ label: formatted, path: currentPath });
    } else if (i === 1 && parts[0] === 'workflows') {
      crumbs.push({ label: `Workflow #${part}`, path: currentPath });
    } else if (i === 2 && parts[0] === 'workflows') {
      const formatted = part.charAt(0).toUpperCase() + part.slice(1);
      crumbs.push({ label: formatted, path: currentPath });
    } else {
      const formatted = part.replaceAll('-', ' ');
      crumbs.push({ label: formatted.charAt(0).toUpperCase() + formatted.slice(1), path: currentPath });
    }
  }

  return crumbs;
}

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const currentPath = window.location.pathname;
  const crumbs = getBreadcrumbs(currentPath);

  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, path: string) => {
    e.preventDefault();
    setMobileOpen(false);
    navigate(path);
  };

  const isActive = (itemPath: string) => {
    if (itemPath === '/') return currentPath === '/';
    return currentPath === itemPath || currentPath.startsWith(`${itemPath}/`);
  };

  return (
    <header className="global-navbar">
      <div className="nav-container">
        {/* Brand */}
        <a href="/" onClick={(e) => handleNavClick(e, '/')} className="nav-brand">
          <ShieldCheck className="brand-icon" />
          <span className="brand-text">
            SENTINEL<span className="brand-highlight">OPS NEXUS</span>
          </span>
        </a>

        {/* Desktop Nav Items */}
        <nav className="nav-menu desktop-menu" aria-label="Main Navigation">
          {NAV_ITEMS.map((item) => {
            const active = isActive(item.path);
            return (
              <a
                key={item.path}
                href={item.path}
                onClick={(e) => handleNavClick(e, item.path)}
                className={`nav-item ${active ? 'active' : ''}`}
                aria-current={active ? 'page' : undefined}
              >
                {item.icon}
                <span>{item.label}</span>
              </a>
            );
          })}
        </nav>

        {/* Safety Badge & Mobile Toggle */}
        <div className="nav-right">
          <div className="nav-safety-badge" title="Permanent System Safety Boundary">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>HUMAN GOVERNED</span>
          </div>

          <button
            className="mobile-menu-toggle"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileOpen && (
        <div className="mobile-menu-drawer">
          {NAV_ITEMS.map((item) => {
            const active = isActive(item.path);
            return (
              <a
                key={item.path}
                href={item.path}
                onClick={(e) => handleNavClick(e, item.path)}
                className={`mobile-nav-item ${active ? 'active' : ''}`}
              >
                {item.icon}
                <span>{item.label}</span>
              </a>
            );
          })}
        </div>
      )}

      {/* Breadcrumb Rail */}
      {currentPath !== '/' && (
        <div className="breadcrumb-bar" aria-label="Breadcrumb Navigation">
          <div className="breadcrumb-container">
            {crumbs.map((crumb, idx) => (
              <React.Fragment key={crumb.path + idx}>
                {idx > 0 && <ChevronRight className="breadcrumb-separator" />}
                {idx === crumbs.length - 1 ? (
                  <span className="breadcrumb-current">{crumb.label}</span>
                ) : (
                  <a
                    href={crumb.path}
                    onClick={(e) => handleNavClick(e, crumb.path)}
                    className="breadcrumb-link"
                  >
                    {crumb.label}
                  </a>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
