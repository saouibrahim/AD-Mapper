import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, Monitor, Users2, ShieldAlert, Key, AlertTriangle, Crosshair, ArrowRight } from 'lucide-react'
import { graph, misconfigs } from '../utils/api'
import styles from './Dashboard.module.css'

const StatCard = ({ icon: Icon, label, value, color, sub }) => (
  <div className={styles.statCard} style={{ '--accent': color }}>
    <div className={styles.statIcon}><Icon size={20} /></div>
    <div className={styles.statBody}>
      <div className={styles.statValue}>{value ?? '—'}</div>
      <div className={styles.statLabel}>{label}</div>
      {sub && <div className={styles.statSub}>{sub}</div>}
    </div>
  </div>
)

const SEV_ORDER = ['critique', 'haute', 'moyenne', 'basse']

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [findings, setFindings] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([graph.statistics(), misconfigs.list()])
      .then(([s, m]) => {
        setStats(s.data)
        setFindings(m.data)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const sevCount = SEV_ORDER.reduce((acc, s) => {
    acc[s] = findings.filter(f => f.severity === s).length
    return acc
  }, {})

  const criticalFindings = findings
    .filter(f => f.severity === 'critique' || f.severity === 'haute')
    .slice(0, 4)

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <div className={styles.tag}>// vue d'ensemble</div>
          <h1 className={styles.title}>Dashboard</h1>
        </div>
        <div className={styles.timestamp}>
          {new Date().toLocaleString('fr-FR')}
        </div>
      </div>

      {loading ? (
        <div className={styles.loading}>
          <span className={styles.cursor}>_</span> Chargement des données...
        </div>
      ) : (
        <>
          <div className={styles.statsGrid}>
            <StatCard icon={Users}      label="Utilisateurs"     value={stats?.users}        color="var(--blue)"   />
            <StatCard icon={Monitor}    label="Machines"          value={stats?.computers}    color="var(--purple)" />
            <StatCard icon={Users2}     label="Groupes"           value={stats?.groups}       color="var(--green)"  />
            <StatCard icon={ShieldAlert} label="Comptes Admin"   value={stats?.admin_users}  color="var(--orange)" sub="adminCount=1" />
            <StatCard icon={Key}        label="Kerberoastables"   value={stats?.kerberoastable} color="var(--red-core)" sub="SPN exposés" />
            <StatCard icon={AlertTriangle} label="Mauvaises configs" value={findings.length} color="var(--yellow)" />
          </div>

          <div className={styles.twoCol}>
            {/* Severity breakdown */}
            <div className={styles.panel}>
              <div className={styles.panelHeader}>
                <AlertTriangle size={14} />
                Répartition par sévérité
              </div>
              <div className={styles.sevList}>
                {SEV_ORDER.map(sev => (
                  <div key={sev} className={styles.sevRow}>
                    <div className={`badge badge-${sev}`}>{sev}</div>
                    <div className={styles.sevBar}>
                      <div
                        className={styles.sevFill}
                        style={{
                          width: findings.length ? `${(sevCount[sev] / findings.length) * 100}%` : '0%',
                          background: `var(--sev-${sev})`,
                        }}
                      />
                    </div>
                    <div className={styles.sevCount}>{sevCount[sev]}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top critical findings */}
            <div className={styles.panel}>
              <div className={styles.panelHeader}>
                <Crosshair size={14} />
                Findings critiques
              </div>
              {criticalFindings.length === 0 ? (
                <div className={styles.empty}>Aucune donnée. Lancez une reconnaissance.</div>
              ) : (
                <div className={styles.findingList}>
                  {criticalFindings.map(f => (
                    <div key={f.id} className={styles.findingRow}>
                      <span className={`badge badge-${f.severity}`}>{f.severity}</span>
                      <span className={styles.findingTitle}>{f.title}</span>
                    </div>
                  ))}
                </div>
              )}
              <button className={styles.viewAll} onClick={() => navigate('/misconfigs')}>
                Voir tout <ArrowRight size={13} />
              </button>
            </div>
          </div>

          {stats?.users === 0 && (
            <div className={styles.callout}>
              <ShieldAlert size={18} />
              <div>
                <strong>Aucune donnée AD importée.</strong>{' '}
                Rendez-vous sur la page{' '}
                <span className={styles.link} onClick={() => navigate('/recon')}>Reconnaissance</span>{' '}
                pour lancer une énumération.
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
