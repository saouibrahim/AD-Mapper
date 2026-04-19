import { useEffect, useState } from 'react'
import { AlertTriangle, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import { misconfigs } from '../utils/api'
import styles from './MisconfigsPage.module.css'

const SEV_ORDER = { critique: 0, haute: 1, moyenne: 2, basse: 3, info: 4 }

function FindingCard({ f }) {
  const [open, setOpen] = useState(false)

  return (
    <div className={`${styles.card} ${styles[`sev_${f.severity}`]}`}>
      <div className={styles.cardHeader} onClick={() => setOpen(o => !o)}>
        <div className={styles.cardLeft}>
          <span className={`badge badge-${f.severity}`}>{f.severity}</span>
          <span className={styles.cardTitle}>{f.title}</span>
          {f.cvss_score && (
            <span className={styles.cvss}>CVSS {f.cvss_score}</span>
          )}
        </div>
        <div className={styles.cardRight}>
          <span className={styles.cardId}>{f.id}</span>
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </div>

      {open && (
        <div className={styles.cardBody}>
          <p className={styles.desc}>{f.description}</p>

          {f.affected_objects?.length > 0 && (
            <div className={styles.section}>
              <div className={styles.sectionTitle}>Objets affectés ({f.affected_objects.length})</div>
              <div className={styles.tagList}>
                {f.affected_objects.slice(0, 20).map((o, i) => (
                  <span key={i} className={styles.objTag}>{o}</span>
                ))}
                {f.affected_objects.length > 20 && (
                  <span className={styles.objTag}>+{f.affected_objects.length - 20}</span>
                )}
              </div>
            </div>
          )}

          {f.evidence && Object.keys(f.evidence).length > 0 && (
            <div className={styles.section}>
              <div className={styles.sectionTitle}>Preuves</div>
              <div className={styles.evidence}>
                {Object.entries(f.evidence).map(([k, v]) => (
                  <div key={k} className={styles.evidRow}>
                    <span className={styles.evidKey}>{k}</span>
                    <span className={styles.evidVal}>{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className={styles.recommendation}>
            <span className={styles.recLabel}>↳ Recommandation :</span>
            {f.recommendation}
          </div>
        </div>
      )}
    </div>
  )
}

export default function MisconfigsPage() {
  const [findings, setFindings] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  const load = () => {
    setLoading(true)
    misconfigs.list()
      .then(r => setFindings(r.data.sort((a, b) => SEV_ORDER[a.severity] - SEV_ORDER[b.severity])))
      .catch(() => setFindings([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const visible = filter === 'all' ? findings : findings.filter(f => f.severity === filter)

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <div className={styles.tag}>// analyse de la surface d'attaque</div>
          <h1 className={styles.title}>Mauvaises Configurations</h1>
        </div>
        <div className={styles.controls}>
          <div className={styles.filters}>
            {['all', 'critique', 'haute', 'moyenne', 'basse'].map(s => (
              <button
                key={s}
                className={`${styles.filterBtn} ${filter === s ? styles.active : ''}`}
                onClick={() => setFilter(s)}
              >
                {s === 'all' ? 'Tous' : s}
                {s !== 'all' && (
                  <span className={styles.filterCount}>
                    {findings.filter(f => f.severity === s).length}
                  </span>
                )}
              </button>
            ))}
          </div>
          <button className={styles.iconBtn} onClick={load}><RefreshCw size={14} /></button>
        </div>
      </div>

      {loading ? (
        <div className={styles.loading}>Analyse en cours...</div>
      ) : visible.length === 0 ? (
        <div className={styles.empty}>
          <AlertTriangle size={18} />
          {findings.length === 0
            ? 'Aucune donnée. Lancez une reconnaissance.'
            : 'Aucun résultat pour ce filtre.'}
        </div>
      ) : (
        <div className={styles.list}>
          {visible.map(f => <FindingCard key={f.id} f={f} />)}
        </div>
      )}
    </div>
  )
}
