import { useState, useEffect, useRef } from 'react'
import { Radar, Play, Trash2, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { recon } from '../utils/api'
import styles from './ReconPage.module.css'

const INITIAL = {
  dc_host: '',
  domain: '',
  username: '',
  password: '',
  ldap_port: 389,
  use_ssl: false,
}

const LOG_MSGS = [
  '[LDAP] Connexion au contrôleur de domaine...',
  '[LDAP] Authentification NTLM...',
  '[ENUM] Récupération des informations du domaine...',
  '[ENUM] Énumération des objets utilisateurs...',
  '[ENUM] Résolution des groupes et appartenances...',
  '[ENUM] Énumération des machines et OS...',
  '[GRAPH] Ingestion dans Neo4j...',
  '[GRAPH] Calcul des relations...',
  '[DONE] Reconnaissance terminée.',
]

export default function ReconPage() {
  const [form, setForm] = useState(INITIAL)
  const [status, setStatus] = useState(null)
  const [logs, setLogs] = useState([])
  const logRef = useRef(null)
  const pollRef = useRef(null)
  const logIdxRef = useRef(0)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  useEffect(() => {
    // Check ongoing recon on mount
    recon.status().then(r => setStatus(r.data)).catch(() => {})
    return () => clearInterval(pollRef.current)
  }, [])

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [logs])

  const addLog = (msg) => {
    setLogs(l => [...l, { msg, ts: new Date().toLocaleTimeString('fr-FR') }])
  }

  const startPoll = () => {
    pollRef.current = setInterval(async () => {
      try {
        const { data } = await recon.status()
        setStatus(data)

        // Simulate progressive logs based on progress
        const idx = Math.floor((data.progress / 100) * LOG_MSGS.length)
        while (logIdxRef.current < idx) {
          addLog(LOG_MSGS[logIdxRef.current])
          logIdxRef.current++
        }

        if (!data.running) {
          clearInterval(pollRef.current)
          if (data.done) {
            addLog('[OK] Données disponibles dans le graphe.')
            toast.success('Reconnaissance terminée avec succès')
          } else if (data.error) {
            addLog(`[ERR] ${data.error}`)
            toast.error(`Erreur: ${data.error}`)
          }
        }
      } catch {
        clearInterval(pollRef.current)
      }
    }, 1200)
  }

  const handleStart = async () => {
    if (!form.dc_host || !form.domain || !form.username || !form.password) {
      toast.error('Remplissez tous les champs obligatoires')
      return
    }
    setLogs([])
    logIdxRef.current = 0
    addLog(`[INIT] Cible: ${form.domain} (${form.dc_host})`)
    try {
      await recon.start(form)
      startPoll()
      toast('Reconnaissance démarrée', { icon: '🎯' })
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur de démarrage')
    }
  }

  const handleClear = async () => {
    await recon.clear()
    setStatus(null)
    setLogs([])
    logIdxRef.current = 0
    toast('Graphe effacé', { icon: '🗑️' })
  }

  const running = status?.running

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div className={styles.tag}>// enumération active directory</div>
        <h1 className={styles.title}>Reconnaissance AD</h1>
      </div>

      <div className={styles.layout}>
        {/* Form */}
        <div className={styles.formPanel}>
          <div className={styles.panelTitle}><Radar size={14} /> Configuration cible</div>

          <div className={styles.field}>
            <label>Contrôleur de domaine (IP / FQDN) *</label>
            <input
              value={form.dc_host}
              onChange={e => set('dc_host', e.target.value)}
              placeholder="192.168.1.1 ou dc01.corp.local"
              disabled={running}
            />
          </div>
          <div className={styles.field}>
            <label>Domaine *</label>
            <input
              value={form.domain}
              onChange={e => set('domain', e.target.value)}
              placeholder="corp.local"
              disabled={running}
            />
          </div>
          <div className={styles.twoFields}>
            <div className={styles.field}>
              <label>Nom d'utilisateur *</label>
              <input
                value={form.username}
                onChange={e => set('username', e.target.value)}
                placeholder="administrator"
                disabled={running}
              />
            </div>
            <div className={styles.field}>
              <label>Mot de passe *</label>
              <input
                type="password"
                value={form.password}
                onChange={e => set('password', e.target.value)}
                placeholder="••••••••"
                disabled={running}
              />
            </div>
          </div>
          <div className={styles.twoFields}>
            <div className={styles.field}>
              <label>Port LDAP</label>
              <input
                type="number"
                value={form.ldap_port}
                onChange={e => set('ldap_port', parseInt(e.target.value))}
                disabled={running}
              />
            </div>
            <div className={styles.field}>
              <label>SSL/TLS</label>
              <select
                value={form.use_ssl ? 'true' : 'false'}
                onChange={e => set('use_ssl', e.target.value === 'true')}
                disabled={running}
              >
                <option value="false">Désactivé (LDAP)</option>
                <option value="true">Activé (LDAPS)</option>
              </select>
            </div>
          </div>

          <div className={styles.actions}>
            <button
              className={`${styles.btn} ${styles.btnPrimary}`}
              onClick={handleStart}
              disabled={running}
            >
              {running
                ? <><Loader2 size={15} className={styles.spin} /> En cours...</>
                : <><Play size={15} /> Lancer la reconnaissance</>
              }
            </button>
            <button
              className={`${styles.btn} ${styles.btnDanger}`}
              onClick={handleClear}
              disabled={running}
            >
              <Trash2 size={14} /> Effacer les données
            </button>
          </div>

          {/* Status */}
          {status && (
            <div className={styles.statusBox}>
              {status.running && (
                <div className={styles.progressBar}>
                  <div className={styles.progressFill} style={{ width: `${status.progress}%` }} />
                </div>
              )}
              <div className={styles.statusRow}>
                {status.done
                  ? <CheckCircle2 size={14} className={styles.iconOk} />
                  : status.error
                  ? <XCircle size={14} className={styles.iconErr} />
                  : <Loader2 size={14} className={`${styles.iconInfo} ${styles.spin}`} />
                }
                <span className={styles.statusMsg}>
                  {status.message || status.error || 'En attente'}
                </span>
                {status.running && (
                  <span className={styles.pct}>{status.progress}%</span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Terminal log */}
        <div className={styles.termPanel}>
          <div className={styles.panelTitle}>
            <span className={styles.termDot} style={{ background: '#ef4444' }} />
            <span className={styles.termDot} style={{ background: '#eab308' }} />
            <span className={styles.termDot} style={{ background: '#22c55e' }} />
            <span style={{ marginLeft: 8 }}>Output terminal</span>
          </div>
          <div className={styles.term} ref={logRef}>
            {logs.length === 0 ? (
              <span className={styles.termPlaceholder}>
                {'> '}<span className={styles.cursor}>_</span>
              </span>
            ) : (
              logs.map((l, i) => (
                <div key={i} className={styles.termLine}>
                  <span className={styles.termTs}>{l.ts}</span>
                  <span className={
                    l.msg.includes('[ERR]') ? styles.termErr :
                    l.msg.includes('[OK]') || l.msg.includes('[DONE]') ? styles.termOk :
                    styles.termText
                  }>{l.msg}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
