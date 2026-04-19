import { useEffect, useState } from 'react'
import { FileText, Download, RefreshCw, Loader2, Plus } from 'lucide-react'
import toast from 'react-hot-toast'
import { reports } from '../utils/api'
import styles from './ReportsPage.module.css'

const INITIAL = {
  title: 'Rapport Red Team – Active Directory',
  mission: '',
  operator: '',
  include_graph: true,
  include_misconfigs: true,
  include_paths: true,
  severity_filter: [],
}

export default function ReportsPage() {
  const [form, setForm] = useState(INITIAL)
  const [reportList, setReportList] = useState([])
  const [generating, setGenerating] = useState(false)
  const [loadingList, setLoadingList] = useState(true)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const loadList = () => {
    setLoadingList(true)
    reports.list()
      .then(r => setReportList(r.data))
      .catch(() => setReportList([]))
      .finally(() => setLoadingList(false))
  }

  useEffect(() => { loadList() }, [])

  const handleGenerate = async () => {
    if (!form.title.trim()) { toast.error('Titre requis'); return }
    setGenerating(true)
    try {
      const { data } = await reports.generate(form)
      toast.success('Rapport généré avec succès')
      loadList()
      // Auto-download
      const a = document.createElement('a')
      a.href = reports.downloadUrl(data.filename)
      a.download = data.filename
      a.click()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur de génération')
    } finally {
      setGenerating(false)
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <div className={styles.tag}>// documentation opérationnelle</div>
          <h1 className={styles.title}>Rapports Red Team</h1>
        </div>
      </div>

      <div className={styles.layout}>
        {/* Generator form */}
        <div className={styles.panel}>
          <div className={styles.panelTitle}><Plus size={13} /> Nouveau rapport</div>

          <div className={styles.field}>
            <label>Titre du rapport *</label>
            <input
              value={form.title}
              onChange={e => set('title', e.target.value)}
              placeholder="Rapport Red Team – Corp AD"
            />
          </div>

          <div className={styles.twoFields}>
            <div className={styles.field}>
              <label>Mission / Référence</label>
              <input
                value={form.mission}
                onChange={e => set('mission', e.target.value)}
                placeholder="RT-2025-001"
              />
            </div>
            <div className={styles.field}>
              <label>Opérateur</label>
              <input
                value={form.operator}
                onChange={e => set('operator', e.target.value)}
                placeholder="John Doe"
              />
            </div>
          </div>

          <div className={styles.checkGroup}>
            <div className={styles.checkGroupTitle}>Sections à inclure</div>
            {[
              { key: 'include_misconfigs', label: 'Mauvaises configurations' },
              { key: 'include_paths',      label: 'Chemins d\'attaque' },
            ].map(({ key, label }) => (
              <label key={key} className={styles.checkRow}>
                <input
                  type="checkbox"
                  checked={form[key]}
                  onChange={e => set(key, e.target.checked)}
                />
                <span>{label}</span>
              </label>
            ))}
          </div>

          <div className={styles.field} style={{ marginTop: 14 }}>
            <label>Filtrer par sévérité (vide = tout inclure)</label>
            <div className={styles.sevCheckList}>
              {['critique', 'haute', 'moyenne', 'basse'].map(sev => (
                <label key={sev} className={styles.sevCheck}>
                  <input
                    type="checkbox"
                    checked={form.severity_filter.includes(sev)}
                    onChange={e => {
                      if (e.target.checked) {
                        set('severity_filter', [...form.severity_filter, sev])
                      } else {
                        set('severity_filter', form.severity_filter.filter(s => s !== sev))
                      }
                    }}
                  />
                  <span className={`badge badge-${sev}`}>{sev}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            className={styles.generateBtn}
            onClick={handleGenerate}
            disabled={generating}
          >
            {generating
              ? <><Loader2 size={15} className={styles.spin} /> Génération en cours...</>
              : <><FileText size={15} /> Générer le rapport PDF</>
            }
          </button>
        </div>

        {/* Report list */}
        <div className={styles.panel}>
          <div className={styles.panelTitle}>
            <FileText size={13} /> Rapports générés
            <button className={styles.refreshBtn} onClick={loadList}>
              <RefreshCw size={12} />
            </button>
          </div>

          {loadingList ? (
            <div className={styles.loading}>Chargement...</div>
          ) : reportList.length === 0 ? (
            <div className={styles.empty}>Aucun rapport généré.</div>
          ) : (
            <div className={styles.reportList}>
              {reportList.map(r => (
                <div key={r.filename} className={styles.reportRow}>
                  <div className={styles.reportInfo}>
                    <div className={styles.reportName}>{r.filename}</div>
                    <div className={styles.reportMeta}>{formatSize(r.size)}</div>
                  </div>
                  <a
                    href={reports.downloadUrl(r.filename)}
                    download={r.filename}
                    className={styles.downloadBtn}
                  >
                    <Download size={13} />
                    Télécharger
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
