import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { RefreshCw, ZoomIn, ZoomOut, Maximize2, Info } from 'lucide-react'
import { graph } from '../utils/api'
import styles from './GraphPage.module.css'

const NODE_COLORS = {
  User:     '#3b82f6',
  Computer: '#a855f7',
  Group:    '#f97316',
  Domain:   '#ef4444',
  OU:       '#22c55e',
}

const NODE_RADIUS = { User: 8, Computer: 10, Group: 9, Domain: 14, OU: 8 }

export default function GraphPage() {
  const svgRef = useRef(null)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] })
  const zoomRef = useRef(null)

  const load = () => {
    setLoading(true)
    setSelected(null)
    graph.full()
      .then(r => setGraphData(r.data))
      .catch(() => setGraphData({ nodes: [], edges: [] }))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    if (loading || !svgRef.current) return
    const { nodes, edges } = graphData
    if (!nodes.length) return

    const el = svgRef.current
    const W = el.clientWidth
    const H = el.clientHeight

    d3.select(el).selectAll('*').remove()

    const svg = d3.select(el)
    const g = svg.append('g')

    // Zoom
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', e => g.attr('transform', e.transform))
    svg.call(zoom)
    zoomRef.current = zoom

    // Arrow markers
    const defs = svg.append('defs')
    Object.entries(NODE_COLORS).forEach(([type, color]) => {
      defs.append('marker')
        .attr('id', `arrow-${type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', color)
        .attr('opacity', 0.6)
    })

    // Prepare node map
    const nodeById = {}
    nodes.forEach(n => { nodeById[n.id] = n })

    const validEdges = edges.filter(e => nodeById[e.source] && nodeById[e.target])

    // Simulation
    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(validEdges)
        .id(d => d.id)
        .distance(d => {
          if (d.source.type === 'Domain' || d.target.type === 'Domain') return 120
          return 80
        })
        .strength(0.4))
      .force('charge', d3.forceManyBody().strength(-220))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide(18))

    // Edges
    const link = g.append('g')
      .selectAll('line')
      .data(validEdges)
      .join('line')
      .attr('stroke', d => NODE_COLORS[nodeById[d.target.id || d.target]?.type] || '#2a2a45')
      .attr('stroke-opacity', 0.35)
      .attr('stroke-width', 1.2)
      .attr('marker-end', d => {
        const targetType = nodeById[d.target.id || d.target]?.type || 'User'
        return `url(#arrow-${targetType})`
      })

    // Edge labels
    const linkLabel = g.append('g')
      .selectAll('text')
      .data(validEdges)
      .join('text')
      .attr('font-size', 8)
      .attr('font-family', 'Share Tech Mono, monospace')
      .attr('fill', '#475569')
      .attr('text-anchor', 'middle')
      .text(d => (d.relation || '').replace(/_/g, ' '))

    // Node groups
    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) sim.alphaTarget(0.3).restart()
          d.fx = d.x; d.fy = d.y
        })
        .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
        .on('end', (event, d) => {
          if (!event.active) sim.alphaTarget(0)
          d.fx = null; d.fy = null
        })
      )
      .on('click', (_, d) => setSelected(d))

    // Glow filter
    const filter = defs.append('filter').attr('id', 'glow')
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur')
    const feMerge = filter.append('feMerge')
    feMerge.append('feMergeNode').attr('in', 'coloredBlur')
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

    // Circle
    node.append('circle')
      .attr('r', d => NODE_RADIUS[d.type] || 8)
      .attr('fill', d => NODE_COLORS[d.type] || '#64748b')
      .attr('fill-opacity', 0.85)
      .attr('stroke', d => NODE_COLORS[d.type] || '#64748b')
      .attr('stroke-width', d => d.risk_score > 60 ? 2.5 : 1)
      .attr('filter', d => d.risk_score > 60 ? 'url(#glow)' : null)

    // Risk ring for high-risk nodes
    node.filter(d => d.risk_score > 60)
      .append('circle')
      .attr('r', d => (NODE_RADIUS[d.type] || 8) + 4)
      .attr('fill', 'none')
      .attr('stroke', '#ef4444')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '3 3')
      .attr('opacity', 0.5)

    // Label
    node.append('text')
      .attr('dy', d => (NODE_RADIUS[d.type] || 8) + 12)
      .attr('text-anchor', 'middle')
      .attr('font-size', 9)
      .attr('font-family', 'Share Tech Mono, monospace')
      .attr('fill', '#94a3b8')
      .text(d => {
        const lbl = d.label || ''
        return lbl.length > 18 ? lbl.slice(0, 16) + '…' : lbl
      })

    // Tick
    sim.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)

      linkLabel
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2)

      node.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    return () => sim.stop()
  }, [graphData, loading])

  const zoomIn  = () => d3.select(svgRef.current).transition().call(zoomRef.current?.scaleBy, 1.4)
  const zoomOut = () => d3.select(svgRef.current).transition().call(zoomRef.current?.scaleBy, 0.7)
  const zoomFit = () => d3.select(svgRef.current).transition().call(zoomRef.current?.transform, d3.zoomIdentity)

  const empty = !loading && graphData.nodes.length === 0

  return (
    <div className={styles.page}>
      <div className={styles.topbar}>
        <div>
          <div className={styles.tag}>// visualisation des relations</div>
          <h1 className={styles.title}>Graphe Active Directory</h1>
        </div>
        <div className={styles.controls}>
          <span className={styles.stat}>{graphData.nodes.length} nœuds</span>
          <span className={styles.stat}>{graphData.edges.length} liens</span>
          <button className={styles.iconBtn} onClick={zoomIn}><ZoomIn size={15} /></button>
          <button className={styles.iconBtn} onClick={zoomOut}><ZoomOut size={15} /></button>
          <button className={styles.iconBtn} onClick={zoomFit}><Maximize2 size={15} /></button>
          <button className={styles.iconBtn} onClick={load}><RefreshCw size={15} /></button>
        </div>
      </div>

      <div className={styles.canvasWrap}>
        {loading && (
          <div className={styles.overlay}>
            <div className={styles.loadMsg}>Chargement du graphe...</div>
          </div>
        )}
        {empty && (
          <div className={styles.overlay}>
            <Info size={20} style={{ color: 'var(--text-muted)' }} />
            <div className={styles.loadMsg}>Aucune donnée. Lancez une reconnaissance.</div>
          </div>
        )}
        <svg ref={svgRef} className={styles.svg} />

        {/* Legend */}
        <div className={styles.legend}>
          {Object.entries(NODE_COLORS).map(([type, color]) => (
            <div key={type} className={styles.legendItem}>
              <div className={styles.legendDot} style={{ background: color }} />
              <span>{type}</span>
            </div>
          ))}
          <div className={styles.legendItem}>
            <div className={styles.legendRing} />
            <span>Risque élevé</span>
          </div>
        </div>

        {/* Node detail */}
        {selected && (
          <div className={styles.detail}>
            <div className={styles.detailHeader}>
              <div className={styles.detailBadge} style={{ background: NODE_COLORS[selected.type] || '#64748b' }}>
                {selected.type}
              </div>
              <button className={styles.closeBtn} onClick={() => setSelected(null)}>✕</button>
            </div>
            <div className={styles.detailName}>{selected.label}</div>
            <div className={styles.detailRisk}>
              Score risque:
              <span style={{ color: selected.risk_score > 60 ? 'var(--red-core)' : selected.risk_score > 30 ? 'var(--yellow)' : 'var(--green)' }}>
                {' '}{selected.risk_score.toFixed(0)}/100
              </span>
            </div>
            <div className={styles.detailProps}>
              {Object.entries(selected.properties || {}).slice(0, 8).map(([k, v]) => (
                v !== null && v !== undefined && v !== '' && (
                  <div key={k} className={styles.prop}>
                    <span className={styles.propKey}>{k}</span>
                    <span className={styles.propVal}>{String(v).slice(0, 60)}</span>
                  </div>
                )
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
