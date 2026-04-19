import { useEffect, useState } from 'react'
import { Crosshair, RefreshCw, ChevronDown, ChevronUp, ArrowRight } from 'lucide-react'
import { graph } from '../utils/api'
import styles from './AttackPathsPage.module.css'

function PathCard({ path }) {
  const [open, setOpen] = useState(false)

  return (
    <div className={`${styles.card} ${styles[`sev_${path.severity}`]}`}>
      <div className={styles.cardHeader} onClick={() => setOpen(o => !o)}>
        <div className={styles.cardLeft}>
          <span className={`badge badge-${path.severity}`}>{path.severity}</span>
          <span className={styles.cardTitle}>{path.name}</span>
        </div>
        <div className={styles.cardRight}>
          <span className={styles.likelihood}>Probabilité: {path.likelihood}</span>
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </div>

      {open && (
        <div className={styles.cardBody}>
          <p className={styles.desc}>{path.description}</p>

          {/* Node path visualization */}
          {path.nodes?.length > 0 && (
            <div className={styles.nodePath}>
              {path.nodes.map((n, i) => (
                <div key={i} className={styles.pathItem}>
                  <div className={styles.pathNode} data-type={n.type}>
                    <span className={styles.nodeType}>{n.type}</span>
                    <span className={styles.nodeLabel}>{n.label}</span>
                  </div>
                  {i < path.nodes.length - 1 && (
                    <ArrowRight size={12} className={styles.pathArrow} />
                  )}
                </div>
              ))}
            </div>
          )}

          {path.steps?.length > 0 && (
            <div className={styles.stepsWrap}>
              <div className={styles.stepsTitle}>Étapes d'exploitation</div>
              <div className={styles.steps}>
                {path.steps.map((s, i) => (
                  <div key={i} className={styles.step}>
                    <span className={styles.stepNum}>{i + 1}</span>
                    <span>{s.replace(/^\d+\.\s*/, '')}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className={styles.impactRow}>
            <div className={styles.impactBadge}>
              <span className={styles.impactLabel}>Impact</span>
              <span className={styles.impactVal}>{path.impact}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function AttackPathsPage() {
  const [paths, setPaths] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    graph.attackPaths()
      .then(r => setPaths(r.data))
      .catch(() => setPaths([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const sevOrder = { critique: 0, haute: 1, moyenne: 2, basse: 3 }
  const sorted = [...paths].sort((a, b) => (sevOrder[a.severity] ?? 9) - (sevOrder[b.severity] ?? 9))

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <div className={styles.tag}>// priorisation des scénarios</div>
          <h1 className={styles.title}>Chemins d'Attaque</h1>
        </div>
        <div className={styles.controls}>
          <div className={styles.counter}>
            <Crosshair size={13} />
            {paths.length} scénario{paths.length !== 1 ? 's' : ''} identifié{paths.length !== 1 ? 's' : ''}
          </div>
          <button className={styles.iconBtn} onClick={load}><RefreshCw size={14} /></button>
        </div>
      </div>

      {loading ? (
        <div className={styles.loading}>Calcul des chemins d'attaque...</div>
      ) : sorted.length === 0 ? (
        <div className={styles.empty}>
          <Crosshair size={18} />
          Aucune donnée. Lancez une reconnaissance.
        </div>
      ) : (
        <div className={styles.list}>
          {sorted.map(p => <PathCard key={p.id} path={p} />)}
        </div>
      )}
    </div>
  )
}
