import { Outlet, NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Radar, GitFork, AlertTriangle,
  Crosshair, FileText, Shield
} from 'lucide-react'
import styles from './Layout.module.css'

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/recon', icon: Radar, label: 'Reconnaissance' },
  { to: '/graph', icon: GitFork, label: 'Graphe AD' },
  { to: '/misconfigs', icon: AlertTriangle, label: 'Mauvaises Configs' },
  { to: '/attack-paths', icon: Crosshair, label: 'Chemins d\'attaque' },
  { to: '/reports', icon: FileText, label: 'Rapports' },
]

export default function Layout() {
  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.logo}>
          <Shield size={22} className={styles.logoIcon} />
          <div>
            <div className={styles.logoTitle}>AD MAPPER</div>
          </div>
        </div>

        <nav className={styles.nav}>
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ''}`
              }
            >
              <Icon size={16} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <div className={styles.statusDot} />
          <span>v1.0.0 Ibrahim SAOU</span>
        </div>
      </aside>

      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
